from app.schemas.user import RegisterUser,LoginUser
from app.services.user.auth_service import login_user,register_user
from app.auth.dependencies import get_current_user

from fastapi import APIRouter, Depends,HTTPException


user_router = APIRouter(
    prefix="/user"
)


@user_router.post("/register")
def register(data: RegisterUser):

    try:
        return register_user(
            data.email,
            data.username,
            data.password
        )

    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Registration failed. Email or username may already exist."
        )
        
@user_router.post("/login")
async def login(user:LoginUser):
    
    user =  login_user(
        user.email,
        user.password
    )
        
    if not user:
        raise HTTPException(
            status_code=401,
            detail="Invalid email or password"
        )
    return user
        
        
@user_router.get("/me")
def get_profile(
    current_user: dict = Depends(get_current_user)
):

    return {
        "message": "User authenticated",
        "user": current_user
    }