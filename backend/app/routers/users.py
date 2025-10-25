from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_async_session
from ..security import get_current_user_id
from ..models import User
from ..schemas import UserRead

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/ping")
def ping():
    return {"users": "pong"}

@router.get("/me", response_model=UserRead)
async def me(current_user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_async_session)):
    res = await db.execute(select(User).where(User.id == current_user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@router.get("/{user_id}", response_model=UserRead)
async def get_user(user_id: int, db: AsyncSession = Depends(get_async_session)):
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
