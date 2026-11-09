
import httpx

from app.auth.config import settings
from app.services.push_event_service import process_push_event_service
from fastapi import APIRouter, HTTPException, Request

import hashlib
import hmac
import json
import logging



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



async def process_push_event(
    payload: dict,
    installation_id: int,
):
    process_push_event_service(payload,installation_id)

    



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
