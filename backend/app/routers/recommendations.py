from fastapi import APIRouter

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/ping")
def ping():
    return {"recs": "pong"}

@router.get("/")
def list_recommendations():
    return {"items": []}
