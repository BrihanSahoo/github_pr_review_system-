import hmac
import hashlib

from fastapi import FastAPI,Request,HTTPException


app = FastAPI()

SECRET = "GITHUB_SECRET_123#0-=123"


def verify_signature(body:bytes,signature:str|None) ->bool:
    
    if not signature :
        return False
    
    expected = "sha256=" + hmac.new(
        SECRET.encode(),
        body,
        hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected,signature)
    

@app.post("/webhooks/github")
async def webhook(request : Request):
    payload = await request.json()
    
    signature = request.headers.get(
        "X-Hub-Signature-256"
    )
    
    if not verify_signature(payload,signature):
        raise HTTPException(
            status_code=401,
            detail="Invalid signature"
        )
    
    print("Repository")
    print(payload["repository"]["full_name"])
    print("Branch:")
    print(payload["ref"])
    
    for commit in payload["commits"] :
        print("Commit",commit["id"])
        print("Message",commit["message"])
    return {
        "status":"received"
    }
        