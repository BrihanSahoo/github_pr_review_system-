from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.auth.jwt_handler import verify_access_token
from app.auth.supabase import supabase

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):

    token = credentials.credentials

    payload = verify_access_token(token)

    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    user_id = payload.get("sub")

    response = (
        supabase.table("users")
        .select("id, email, username")
        .eq("id", user_id)
        .limit(1)
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=401,
            detail="User does not exist"
        )

    return response.data[0]
