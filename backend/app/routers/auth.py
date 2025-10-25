from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_async_session
from ..models import User
from ..security import hash_password, create_access_token, verify_password
from ..schemas import UserCreate, Token, UserLogin

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

@router.post("/login", response_model=Token) # или используйте простой dict, как в signup
async def login_user(payload: UserLogin, # <-- ВАЖНО: для логина нужна другая схема, например, UserLogin(email, password), а не UserCreate
                     db: AsyncSession = Depends(get_async_session)):
    # Найти пользователя по email
    result = await db.execute(select(User).where(User.email == payload.email))
    user = result.scalar_one_or_none()

    # Проверить, существует ли пользователь и правильный ли пароль
    if not user or not verify_password(payload.password, user.hashed_password): # <-- hashed_password, как в модели
        raise HTTPException(status_code=401, detail="Incorrect email or password")

    # Создать токен
    token_data = {"sub": str(user.id)}
    access_token = create_access_token(payload=token_data)

    # Вернуть токен
    return {"access_token": access_token, "token_type": "bearer"}