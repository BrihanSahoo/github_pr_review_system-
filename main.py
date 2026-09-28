import hashlib
import hmac
import json
import os
import secrets
from urllib.parse import urlencode

import httpx
from dotenv import load_dotenv

from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware


load_dotenv()


app = FastAPI()


# ---------------------------------------------------------
# CONFIG
# ---------------------------------------------------------

GITHUB_CLIENT_ID = os.environ["GITHUB_CLIENT_ID"]
GITHUB_CLIENT_SECRET = os.environ["GITHUB_CLIENT_SECRET"]
GITHUB_REDIRECT_URI = os.environ["GITHUB_REDIRECT_URI"]

GITHUB_WEBHOOK_SECRET = os.environ["GITHUB_WEBHOOK_SECRET"]
SESSION_SECRET = os.environ["SESSION_SECRET"]


app.add_middleware(
    SessionMiddleware,
    secret_key=SESSION_SECRET,
)


# ---------------------------------------------------------
# HOME
# ---------------------------------------------------------

@app.get("/root")
async def home():
    return {
        "message": "GitHub OAuth Demo"
    }


# ---------------------------------------------------------
# 1. START GITHUB OAUTH
# ---------------------------------------------------------

@app.get("/auth/github")
async def github_login(request: Request):

    # CSRF protection
    state = secrets.token_urlsafe(32)

    request.session["github_oauth_state"] = state

    params = {
        "client_id": GITHUB_CLIENT_ID,
        "redirect_uri": GITHUB_REDIRECT_URI,

        # repo gives repository access, including private repos,
        # subject to what the user themselves can access.
        "scope": "repo",

        "state": state,
    }

    github_url = (
        "https://github.com/login/oauth/authorize?"
        + urlencode(params)
    )

    return RedirectResponse(github_url)


# ---------------------------------------------------------
# 2. GITHUB CALLBACK
# ---------------------------------------------------------

@app.get("/auth/github/callback")
async def github_callback(
    request: Request,
    code: str,
    state: str,
):

    # -----------------------------------------------------
    # Validate OAuth state
    # -----------------------------------------------------

    saved_state = request.session.get(
        "github_oauth_state"
    )

    # YOUR ORIGINAL CODE HAD THIS REVERSED
    #
    # You had:
    #
    # if not saved_state or compare_digest(saved_state, state):
    #
    # It should be:
    #
    # if not saved_state OR NOT compare_digest(...)

    if (
        not saved_state
        or not secrets.compare_digest(
            saved_state,
            state,
        )
    ):
        raise HTTPException(
            status_code=400,
            detail="Invalid OAuth state",
        )

    # State should not be reused
    request.session.pop(
        "github_oauth_state",
        None,
    )

    # -----------------------------------------------------
    # Exchange authorization code for access token
    # -----------------------------------------------------

    async with httpx.AsyncClient() as client:

        token_response = await client.post(
            "https://github.com/login/oauth/access_token",

            data={
                "client_id": GITHUB_CLIENT_ID,
                "client_secret": GITHUB_CLIENT_SECRET,
                "code": code,
                "redirect_uri": GITHUB_REDIRECT_URI,
            },

            headers={
                "Accept": "application/json",
            },
        )

    if token_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Failed to exchange GitHub code",
        )

    token_data = token_response.json()

    if "error" in token_data:
        raise HTTPException(
            status_code=400,
            detail=token_data,
        )

    access_token = token_data["access_token"]

    # -----------------------------------------------------
    # Store token in session temporarily
    #
    # DON'T do this in production long-term.
    # Store encrypted token in your DB instead.
    # -----------------------------------------------------

    request.session["github_access_token"] = access_token

    # -----------------------------------------------------
    # Get GitHub user
    # -----------------------------------------------------

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    async with httpx.AsyncClient() as client:

        user_response = await client.get(
            "https://api.github.com/user",
            headers=headers,
        )

    if user_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve GitHub user",
        )

    github_user = user_response.json()

    github_user_id = github_user["id"]
    github_username = github_user["login"]

    # -----------------------------------------------------
    # IMPORTANT:
    #
    # In production:
    #
    # save:
    #
    # your_user_id
    # github_user_id
    # github_username
    # encrypted_access_token
    #
    # to PostgreSQL/etc.
    # -----------------------------------------------------

    # -----------------------------------------------------
    # Get repositories
    # -----------------------------------------------------

    async with httpx.AsyncClient() as client:

        repos_response = await client.get(
            "https://api.github.com/user/repos",
            headers=headers,
            params={
                "per_page": 100,
                "affiliation": "owner,collaborator,organization_member",
            },
        )

    if repos_response.status_code != 200:
        raise HTTPException(
            status_code=400,
            detail="Could not retrieve repositories",
        )

    repositories = repos_response.json()

    # -----------------------------------------------------
    # Create webhook for repositories
    # -----------------------------------------------------

    webhook_results = []

    for repo in repositories:

        owner = repo["owner"]["login"]
        repo_name = repo["name"]

        result = await create_repository_webhook(
            access_token=access_token,
            owner=owner,
            repo=repo_name,
        )

        webhook_results.append({
            "repository": repo["full_name"],
            "result": result,
        })

    return {
        "message": "GitHub connected successfully",
        "github_user": {
            "id": github_user_id,
            "login": github_username,
        },
        "repositories": [
            repo["full_name"]
            for repo in repositories
        ],
        "webhooks": webhook_results,
    }


# ---------------------------------------------------------
# 3. CREATE WEBHOOK
# ---------------------------------------------------------

async def create_repository_webhook(
    access_token: str,
    owner: str,
    repo: str,
):

    url = (
        f"https://api.github.com/"
        f"repos/{owner}/{repo}/hooks"
    )

    headers = {
        "Authorization": f"Bearer {access_token}",
        "Accept": "application/vnd.github+json",
    }

    payload = {
        "name": "web",
        "active": True,

        "events": [
            "push",
            "pull_request",
            "create",
        ],

        "config": {
            "url": (
                "https://YOUR-DOMAIN.com/"
                "webhooks/github"
            ),

            "content_type": "json",

            "secret": GITHUB_WEBHOOK_SECRET,

            "insecure_ssl": "0",
        },
    }

    async with httpx.AsyncClient() as client:

        response = await client.post(
            url,
            headers=headers,
            json=payload,
        )

    # Already exists / other error
    if response.status_code not in (201,):

        return {
            "success": False,
            "status_code": response.status_code,
            "response": response.json(),
        }

    data = response.json()

    return {
        "success": True,
        "hook_id": data["id"],
    }


# ---------------------------------------------------------
# 4. VERIFY GITHUB WEBHOOK SIGNATURE
# ---------------------------------------------------------

def verify_signature(
    body: bytes,
    signature: str | None,
) -> bool:

    if not signature:
        return False

    expected = (
        "sha256="
        + hmac.new(
            GITHUB_WEBHOOK_SECRET.encode(),
            body,
            hashlib.sha256,
        ).hexdigest()
    )

    return hmac.compare_digest(
        expected,
        signature,
    )


# ---------------------------------------------------------
# 5. GITHUB WEBHOOK
# ---------------------------------------------------------

@app.post("/webhooks/github")
async def github_webhook(
    request: Request,
):

    # VERY IMPORTANT:
    # Read the ORIGINAL bytes.
    #
    # Do NOT use request.json() before
    # signature verification.

    body = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_signature(
        body,
        signature,
    ):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature",
        )

    # -----------------------------------------------------
    # Now it is safe to parse JSON
    # -----------------------------------------------------

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:

        raise HTTPException(
            status_code=400,
            detail="Invalid JSON",
        )

    # -----------------------------------------------------
    # Identify event
    # -----------------------------------------------------

    event = request.headers.get(
        "X-GitHub-Event"
    )

    delivery_id = request.headers.get(
        "X-GitHub-Delivery"
    )

    print("=================================")
    print("GitHub event:", event)
    print("Delivery ID:", delivery_id)
    print("=================================")

    # -----------------------------------------------------
    # PUSH
    # -----------------------------------------------------

    if event == "push":

        repository = payload["repository"]["full_name"]

        ref = payload.get("ref")

        print("PUSH")
        print("Repository:", repository)
        print("Ref:", ref)

        commits = payload.get(
            "commits",
            [],
        )

        for commit in commits:

            print(
                "Commit:",
                commit["id"],
            )

            print(
                "Message:",
                commit["message"],
            )

            print(
                "Author:",
                commit["author"],
            )

    # -----------------------------------------------------
    # PULL REQUEST
    # -----------------------------------------------------

    elif event == "pull_request":

        repository = payload["repository"]["full_name"]

        action = payload["action"]

        pull_request = payload["pull_request"]

        print("PULL REQUEST")
        print("Repository:", repository)
        print("Action:", action)

        print(
            "PR number:",
            pull_request["number"],
        )

        print(
            "Title:",
            pull_request["title"],
        )

        print(
            "Author:",
            pull_request["user"]["login"],
        )

    # -----------------------------------------------------
    # CREATE
    # -----------------------------------------------------

    elif event == "create":

        repository = payload["repository"]["full_name"]

        ref_type = payload["ref_type"]

        ref = payload.get("ref")

        print("CREATE")
        print("Repository:", repository)
        print("Ref type:", ref_type)
        print("Ref:", ref)

    # -----------------------------------------------------
    # OTHER EVENT
    # -----------------------------------------------------

    else:

        print(
            "Unhandled GitHub event:",
            event,
        )

    return {
        "status": "received",
    }