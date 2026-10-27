from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import RedirectResponse
from app.config import settings

auth_route = APIRouter()

@auth_route.get("/github/connect")
async def connect_github():
    install_url = (
        f"https://github.com/apps/"
        f"{settings.GITHUB_APP_SLUG}/installations/new"
    )
    
    return RedirectResponse(
        url=install_url,
        status_code=302,
    )
    
    
@auth_route.get("/github/setup")
async def github_setup(
    installation_id: int,
    setup_action: str = Query(...),
):
    if setup_action not in {"install", "update"}:
        raise HTTPException(
            status_code=400,
            detail="Invalid setup action",
        )


    return {
        "message": "GitHub installation redirect received",
        "installation_id": installation_id,
        "setup_action": setup_action,
    }