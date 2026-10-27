from fastapi import FastAPI
from app.routers.auth_router import auth_route

app = FastAPI()
app.include_router(auth_route)

@app.get("/")
def root():
    return {
        "status":"Backend running"
    }