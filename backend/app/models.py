# backend/app/models.py

from sqlalchemy import Column, Integer, String, Text, DateTime, func, JSON # Импортируем JSON
from .db import Base # Импортируем Base из db.py

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False) # Соответствует полю в схеме UserCreate (hashed_password)
    name = Column(String(120), nullable=False)
    city = Column(String(120), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

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