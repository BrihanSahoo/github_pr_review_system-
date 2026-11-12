
import jwt

from datetime import datetime, timedelta, timezone
from app.auth.config import Settings
from jwt.exceptions import InvalidTokenError





def create_access_token(user_id:str):
    
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=Settings.JWT_EXPIRE_MINUTES
    )
    payload = {
        "sub": str(user_id),
        "iat": datetime.now(timezone.utc),
        "exp": expire,
    }
    token = jwt.encode(
        payload,
        Settings.JWT_SECRET_KEY,
        algorithm=Settings.JWT_ALGORITHM
    )
    
    return token


def verify_access_token(token: str):

    try:
        payload = jwt.decode(
            token,
            Settings.JWT_SECRET_KEY,
            algorithms=[Settings.JWT_ALGORITHM],
            options={"require": ["sub", "exp", "iat"]}
        )

        return payload

    except InvalidTokenError:
        return None