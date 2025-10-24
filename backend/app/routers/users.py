from fastapi import APIRouter

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/ping")
def ping():
    return {"users": "pong"}
