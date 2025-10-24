from fastapi import APIRouter

router = APIRouter(tags=["recommendations"])

@router.get("/recommendations/ping")
def ping():
    return {"recs": "pong"}
