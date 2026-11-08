
import httpx

from app.config import settings
from fastapi import APIRouter, HTTPException, Request

import hashlib
import hmac
import json
import logging

from app.github_auth import create_installation_token

webhook_router = APIRouter()
GITHUB_API = "https://api.github.com"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)

logger = logging.getLogger(__name__)


def verify_github_signature(
    body: bytes,
    signature: str | None
) -> bool:

    if not signature:
        return False

    secret = settings.GITHUB_WEBHOOK_SECRET.encode("utf-8")

    expected_signature = "sha256=" + hmac.new(
        secret,
        body,
        hashlib.sha256,
    ).hexdigest()

    return hmac.compare_digest(
        expected_signature,
        signature,
    )


async def get_commit_changes(
    installation_id: int,
    repository_full_name: str,
    commit_sha: str,
) -> dict:

    """
    Fetch actual file changes for a GitHub commit.
    """

    token = await create_installation_token(
        str(installation_id)
    )

    owner, repo = repository_full_name.split("/", 1)

    url = (
        f"{GITHUB_API}/repos/{owner}/{repo}"
        f"/commits/{commit_sha}"
    )

    async with httpx.AsyncClient(timeout=30) as client:

        response = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )

        response.raise_for_status()
        data = response.json()

    files = []

    for file in data.get("files", []):

        files.append({
            "filename": file.get("filename"),
            "status": file.get("status"),
            "additions": file.get("additions"),
            "deletions": file.get("deletions"),
            "changes": file.get("changes"),
            "patch": file.get("patch"),
            "blob_url": file.get("blob_url"),
            "raw_url": file.get("raw_url"),
        })

    return {
        "commit_sha": data.get("sha"),
        "commit_message": data.get("commit", {}).get(
            "message"
        ),
        "author": data.get("commit", {}).get(
            "author", {}
        ),
        "total_additions": data.get("stats", {}).get(
            "additions"
        ),
        "total_deletions": data.get("stats", {}).get(
            "deletions"
        ),
        "total_changes": data.get("stats", {}).get(
            "total"
        ),
        "files": files,
    }


async def process_push_event(
    payload: dict,
    installation_id: int,
):

    repository = payload.get("repository") or {}
    sender = payload.get("sender") or {}

    repo_name = repository.get("full_name")
    branch = payload.get("ref")
    username = sender.get("login")

    commits = payload.get("commits", [])

    logger.info("========== GITHUB PUSH EVENT ==========")
    logger.info("Repository: %s", repo_name)
    logger.info("Branch: %s", branch)
    logger.info("Pushed by: %s", username)
    logger.info("Total commits: %s", len(commits))

    for commit in commits:

        commit_sha = commit.get("id")

        logger.info("-----------------------------------")
        logger.info("Fetching commit: %s", commit_sha)

        try:
            changes = await get_commit_changes(
                installation_id=installation_id,
                repository_full_name=repo_name,
                commit_sha=commit_sha,
            )

            logger.info(
                "Commit message: %s",
                changes["commit_message"],
            )

            logger.info(
                "Total additions: %s",
                changes["total_additions"],
            )

            logger.info(
                "Total deletions: %s",
                changes["total_deletions"],
            )

            for file in changes["files"]:

                logger.info(
                    "FILE: %s | STATUS: %s | +%s | -%s",
                    file["filename"],
                    file["status"],
                    file["additions"],
                    file["deletions"],
                )

                patch = file.get("patch")

                if patch:
                    logger.info(
                        "ACTUAL CODE CHANGES:\n%s",
                        patch,
                    )
                else:
                    logger.info(
                        "Patch unavailable for: %s",
                        file["filename"],
                    )

        except httpx.HTTPStatusError as exc:
            logger.exception(
                "GitHub API error for commit %s: %s",
                commit_sha,
                exc.response.text,
            )

        except Exception:
            logger.exception(
                "Failed to process commit: %s",
                commit_sha,
            )

    logger.info("========== END PUSH EVENT ==========")



@webhook_router.post("/webhooks/github")
async def github_webhook(request: Request):

    body = await request.body()

    signature = request.headers.get(
        "X-Hub-Signature-256"
    )

    if not verify_github_signature(body, signature):
        logger.warning("Invalid GitHub webhook signature")

        raise HTTPException(
            status_code=401,
            detail="Invalid GitHub webhook signature",
        )

    event = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")

    try:
        payload = json.loads(body)
    except json.JSONDecodeError:
        raise HTTPException(
            status_code=400,
            detail="Invalid JSON payload",
        )

    action = payload.get("action")
    installation = payload.get("installation") or {}

    logger.info(
        "GitHub webhook received: event=%s action=%s "
        "installation=%s delivery=%s",
        event,
        action,
        installation.get("id"),
        delivery_id,
    )

    if event == "push":

        installation_id = installation.get("id")

        if not installation_id:
            raise HTTPException(
                status_code=400,
                detail="Missing installation ID",
            )

        await process_push_event(
            payload,
            installation_id,
        )

    elif event == "installation":
        logger.info(
            "Installation event: action=%s installation=%s",
            action,
            installation.get("id"),
        )

    elif event == "installation_repositories":
        logger.info(
            "Repository access changed: action=%s",
            action,
        )

    else:
        logger.info("Unhandled GitHub event: %s", event)

    return {"status": "success"}
