from fastapi import APIRouter, Depends, HTTPException # Добавлен HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..db import get_async_session
from ..models import User
from ..security import get_current_user_id # Импортируем функцию аутентификации
from ..schemas import UserRead # Импортируем схему для ответа

router = APIRouter(prefix="/users", tags=["users"])

@router.get("/ping")
def ping():
    return {"users": "pong"}

# --- НОВОЕ: Эндпоинт для получения данных текущего пользователя ---
@router.get("/me", response_model=UserRead) # <-- Добавлен эндпоинт /users/me
async def get_current_user_profile(
    current_user_id: int = Depends(get_current_user_id), # <-- Получаем ID из токена
    db: AsyncSession = Depends(get_async_session)
):
    # Найти пользователя по ID из токена
    result = await db.execute(select(User).where(User.id == current_user_id))
    user = result.scalar_one_or_none()

    if not user:
        # В принципе, этого не должно произойти, если get_current_user_id работает правильно
        # и пользователь не был удалён между логином и этим запросом
        raise HTTPException(status_code=404, detail="User not found")

    # Вернуть данные пользователя
    # Pydantic автоматически преобразует объект SQLAlchemy в UserRead
    return user

# --- (Здесь могут быть и другие эндпоинты, например, /{user_id} для получения профиля другого пользователя) ---
