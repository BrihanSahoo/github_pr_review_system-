from fastapi import APIRouter
from fastapi.responses import RedirectResponse
from app.config import settings

auth_route = APIRouter(
    prefix="/auth"
)

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