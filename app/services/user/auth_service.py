from pydantic import EmailStr

from app.auth.supabase import supabase
from app.auth.password import hash_password, verify_password
from app.auth.jwt_handler import create_access_token



def register_user(username:str,email:EmailStr,password:str):
    hashed_password = hash_password(password)
    response = supabase.table("github_users").insert({
        "email": email,
        "username": username,
        "password": hashed_password
    }).execute()
    
    user = response.data[0]
    
    token = create_access_token(user["id"])
    
    return {
        "message": "User registered successfully",
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"]
        }
    }
    
    
    
def login_user(email:EmailStr,password:str):
    response = (
        supabase.table("github_users")
        .select("*")
        .eq("email", email)
        .limit(1)
        .execute()
    )
    
    if not response.data:
        return None
    
    user = response.data[0]
    
    if not verify_password(password, user["password"]):
        return None

    token = create_access_token(user["id"])
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": {
            "id": user["id"],
            "email": user["email"],
            "username": user["username"]
        }
    }