import jwt
import httpx
import time

from app.config import settings


GITHUB_API = "https://api.github.com"


def create_app_jwt()->str:
    """ Short Live JWT token for session"""
    now = int(time.time())
    payload = {
        "iat": now - 60,
        "exp": now + 8 * 60,
        "iss": settings.GITHUB_APP_ID,
    }
    
    return jwt.encode(payload,settings.github_private_key,algorithm="RS256")


async def create_installation_token(installation_id:str)->str:
    
    """Exchange the App JWT for an installation access token."""
    
    app_jwt = create_app_jwt()
    
    async with httpx.AsyncClient(timeout=15) as Client:
        response = await Client.post(
            f"{GITHUB_API}/app/installations/"
            f"{installation_id}/access_tokens",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )
        response.raise_for_status()
        data = response.json()

    return data['token']


async def get_installation_details(installation_id:str)->dict:
    """Fetch the installation's account details from GitHub."""
    
    app_jwt = create_app_jwt()
    
    async with httpx.AsyncClient(timeout=15) as Client:
        
        response = await Client.get(
            f"{GITHUB_API}/app/installations/"
            f"{installation_id}",
            headers={
                "Authorization": f"Bearer {app_jwt}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2026-03-10",
            },
        )
        
        response.raise_for_status()
        return response.json()
    

async def list_installation_repositories(installation_id:str)->list[dict]:
    
    """List repositories the installation can access."""
    
    token = await create_installation_token(
        installation_id
    )
    
    async with httpx.AsyncClient(timeout=15) as Client:
        response = await Client.get(
                f"{GITHUB_API}/installation/repositories",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/vnd.github+json",
                    "X-GitHub-Api-Version": "2026-03-10",
                },
            )

        response.raise_for_status()
        return response.json().get("repositories", [])
    


