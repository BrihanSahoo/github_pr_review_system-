
from app.config import settings
from fastapi import APIRouter, HTTPException, Request

import hashlib
import hmac
import json
import logging

webhook_router = APIRouter()

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


def process_push_event(payload: dict):

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
        message = commit.get("message")
        author = commit.get("author") or {}
        timestamp = commit.get("timestamp")

        added = commit.get("added", [])
        modified = commit.get("modified", [])
        removed = commit.get("removed", [])

        logger.info("-----------------------------------")
        logger.info("Commit: %s", commit_sha)
        logger.info("Message: %s", message)
        logger.info("Author: %s", author.get("name"))
        logger.info("Email: %s", author.get("email"))
        logger.info("Timestamp: %s", timestamp)

        for file in added:
            logger.info("ADDED: %s", file)

        for file in modified:
            logger.info("MODIFIED: %s", file)

        for file in removed:
            logger.info("DELETED: %s", file)

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
        process_push_event(payload)

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
