from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_async_session
from ..models import User
from ..security import hash_password, create_access_token
from ..schemas import UserCreate

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/signup")
async def signup(payload: UserCreate, db: AsyncSession = Depends(get_async_session)):
    # проверить, что email свободен
    res = await db.execute(select(User).where(User.email == payload.email))
    if res.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="Email already registered")

    # создать пользователя
    user = User(
        email=payload.email,
        name=payload.name,
        city=payload.city,
        hashed_password=hash_password(payload.password),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)

    # выдать токен
    token = create_access_token({"sub": str(user.id)})
    return {"access_token": token, "token_type": "bearer"}
