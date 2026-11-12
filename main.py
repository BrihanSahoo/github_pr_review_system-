from fastapi import FastAPI
from app.routers.auth_router import auth_route
from app.routers.github_webhook_router import webhook_router
from app.routers.user_router import user_router

app = FastAPI()
app.include_router(auth_route)
app.include_router(webhook_router)
app.include_router(user_router)

@app.get("/")
def root():
    return {
        "status":"Backend running"
    }