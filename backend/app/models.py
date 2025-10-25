# backend/app/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON # Импортируем JSON
from .db import Base # Импортируем Base из db.py
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

# --- НОВОЕ: Модель Profile ---
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True) # Внешний ключ (если есть отдельная таблица users)
    name = Column(String(120), index=True) # Можно дублировать из User или хранить отдельно
    age = Column(Integer)
    city = Column(String(120), index=True) # Индекс для поиска и аналитики
    photo_url = Column(String(500)) # URL фото
    bio = Column(Text) # "О себе"
    # Хранение списков как JSON
    interests = Column(JSON) # Массив строк ["python", "ml", "running"]
    skills = Column(JSON)   # Массив строк ["python", "sql", "leadership"]
    goals = Column(JSON)    # Массив строк ["friendship", "project_collaboration", "mentorship"]
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# Если у вас есть другие таблицы (например, для матчей, чатов), добавьте их сюда.
# class Match(Base): ...
# class Message(Base): ...
