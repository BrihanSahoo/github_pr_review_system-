from app.config import settings
from fastapi import APIRouter, HTTPException, Request
import hashlib
import hmac
import json
import logging

webhook_router = APIRouter()
logger = logging.getLogger(__name__)


def verify_github_signature(body:bytes,signature:str | None)->bool:
    
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
    
    

@webhook_router.post("/github/webhook")
async def github_webhook(request:Request):
    
    body = await request.body()
    signature = request.headers.get(
        "X-Hub-Signature-256"
    )
    if not verify_github_signature(body, signature):
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
    repository = payload.get("repository") or {}
    installation = payload.get("installation") or {}

    repo_name = repository.get("full_name")
    installation_id = installation.get("id")

    logger.info(
        "GitHub webhook: event=%s action=%s "
        "repository=%s installation=%s delivery=%s",
        event,
        action,
        repo_name,
        installation_id,
        delivery_id,
    )
    

