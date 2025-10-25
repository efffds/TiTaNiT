# backend/app/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON, Boolean, UniqueConstraint
from .db import Base
from sqlalchemy.orm import Mapped, mapped_column

class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True, nullable=False)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    city: Mapped[str | None] = mapped_column(String(100), nullable=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

# --- Профиль пользователя ---
class Profile(Base):
    __tablename__ = "profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True)
    name = Column(String(120), index=True)
    age = Column(Integer)
    city = Column(String(120), index=True)
    photo_url = Column(String(500))
    bio = Column(Text)
    interests = Column(JSON)
    skills = Column(JSON)
    goals = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# --- Лайки/дизлайки между пользователями ---
class Like(Base):
    __tablename__ = "likes"

    id = Column(Integer, primary_key=True, index=True)
    from_user_id = Column(Integer, index=True, nullable=False)
    to_user_id = Column(Integer, index=True, nullable=False)
    is_like = Column(Boolean, nullable=False)  # True = like, False = dislike
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("from_user_id", "to_user_id", name="uq_like_from_to"),
    )

# --- Матч при взаимном лайке ---
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user1_id = Column(Integer, index=True, nullable=False)
    user2_id = Column(Integer, index=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("user1_id", "user2_id", name="uq_match_pair"),
    )

# class Message(Base): ...

# ... (ваш существующий models.py) ...
# ... (User, Profile) ...

# --- НОВОЕ: Модель для хранения совпадений ---
class Match(Base):
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False, index=True) # ID пользователя, для которого найдены совпадения
    matched_user_ids = Column(JSON) # Массив ID совпавших пользователей (например, [1, 5, 10])
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# ... (остальные модели) ...