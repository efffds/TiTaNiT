from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import databases
import sqlalchemy
from sqlalchemy import MetaData, Table, Column, Integer, String, Text, JSON, DateTime, Boolean
from sqlalchemy.sql import func
import jwt
import os
from passlib.context import CryptContext
import redis
import pickle
import asyncio
from auth import get_current_user_id

app = FastAPI(title="Titanit Backend API")

# --- Настройки ---
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here") # Заменить на .env
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 720 # 12 часов

# --- Подключение к БД ---
DATABASE_URL = "sqlite:///./titanit.db" # Использовать PostgreSQL на проде
database = databases.Database(DATABASE_URL)
metadata = MetaData()

# --- Определение таблиц (упрощено) ---
users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("email", String, unique=True, index=True, nullable=False),
    Column("hashed_password", String, nullable=False),
    Column("is_active", Boolean, default=True),
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
)

profiles = Table(
    "profiles",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user_id", Integer, nullable=False), # Индекс отдельно
    Column("name", String, index=True),
    Column("age", Integer),
    Column("city", String, index=True),
    Column("photo_url", String), # URL фото
    Column("bio", Text), # "О себе"
    Column("interests", JSON), # ["python", "ml", "running"]
    Column("skills", JSON), # ["python", "sql", "leadership"]
    Column("goals", JSON), # ["friendship", "project_collaboration", "mentorship"]
    Column("created_at", DateTime(timezone=True), server_default=func.now()),
    Column("updated_at", DateTime(timezone=True), onupdate=func.now()),
)

matches = Table(
    "matches",
    metadata,
    Column("id", Integer, primary_key=True, index=True),
    Column("user1_id", Integer, nullable=False),
    Column("user2_id", Integer, nullable=False),
    # Уникальность пары (user1_id, user2_id) или (user2_id, user1_id)
    # Добавить вручную или через триггер
    Column("compatibility_score", sqlalchemy.Float),
    Column("matched_at", DateTime(timezone=True), server_default=func.now()),
)

# --- Pydantic модели ---
class UserCreate(BaseModel):
    email: str
    password: str

class UserOut(BaseModel):
    id: int
    email: str
    is_active: bool

class ProfileCreateUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    photo_url: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    goals: Optional[List[str]] = []

class ProfileOut(BaseModel):
    user_id: int
    name: Optional[str]
    age: Optional[int]
    city: Optional[str]
    photo_url: Optional[str]
    bio: Optional[str]
    interests: List[str]
    skills: List[str]
    goals: List[str]

class Recommendation(BaseModel):
    user_id: int
    name: Optional[str]
    city: Optional[str]
    photo_url: Optional[str]
    bio: Optional[str]
    compatibility_score: float
    interests: List[str]
    skills: List[str]

class ChatMessage(BaseModel):
    sender_id: int
    receiver_id: int
    message: str

# --- Утилиты ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

def create_access_token(data: dict):
    to_encode = data.copy()
    # expired_delta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    # expire = datetime.utcnow() + expired_delta
    # to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- Подключение к Redis для кэширования ---
redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True) # Настройте хост/порт

# --- Имитация ML-модели (заменить на реальную) ---
def calculate_compatibility_score(profile1: dict, profile2: dict) -> float:
    # Простой пример: пересечение интересов и навыков
    # Реальная модель будет сложнее (векторизация, эмбеддинги, обучение на взаимодействиях)
    interests1 = set(profile1.get("interests", []))
    interests2 = set(profile2.get("interests", []))
    skills1 = set(profile1.get("skills", []))
    skills2 = set(profile2.get("skills", []))

    intersection_interests = len(interests1.intersection(interests2))
    union_interests = len(interests1.union(interests2))
    score_interests = intersection_interests / union_interests if union_interests > 0 else 0

    intersection_skills = len(skills1.intersection(skills2))
    union_skills = len(skills1.union(skills2))
    score_skills = intersection_skills / union_skills if union_skills > 0 else 0

    # Веса можно настраивать
    final_score = 0.5 * score_interests + 0.5 * score_skills
    return min(1.0, final_score) # Ограничиваем до 1.0

# --- Роуты ---

@app.on_event("startup")
async def startup():
    await database.connect()
    # Создание таблиц (только для SQLite демо, в проде миграции Alembic)
    engine = sqlalchemy.create_engine(DATABASE_URL)
    metadata.create_all(engine)


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.post("/auth/register", response_model=UserOut)
async def register(user: UserCreate):
    # Проверить, существует ли пользователь
    query = users.select().where(users.c.email == user.email)
    existing_user = await database.fetch_one(query)
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_pass = get_password_hash(user.password)
    query = users.insert().values(email=user.email, hashed_password=hashed_pass)
    user_id = await database.execute(query)
    return {"id": user_id, "email": user.email, "is_active": True}


@app.post("/auth/login")
async def login(email: str, password: str):
    query = users.select().where(users.c.email == email)
    user_record = await database.fetch_one(query)
    if not user_record or not verify_password(password, user_record["hashed_password"]):
        raise HTTPException(status_code=400, detail="Incorrect email or password")

    token_data = {"sub": str(user_record["id"])} # Использовать ID как subject
    token = create_access_token(data=token_data)
    return {"access_token": token, "token_type": "bearer"}


@app.get("/profile/me", response_model=ProfileOut)
async def get_my_profile(current_user_id: int = Depends(get_current_user_id)): # Реализуйте get_current_user_id
    query = profiles.select().where(profiles.c.user_id == current_user_id)
    profile = await database.fetch_one(query)
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    return ProfileOut(**dict(profile))


@app.put("/profile/me", response_model=ProfileOut)
async def update_my_profile(profile_data: ProfileCreateUpdate, current_user_id: int = Depends(get_current_user_id)):
    # Проверить существование профиля
    query = profiles.select().where(profiles.c.user_id == current_user_id)
    existing_profile = await database.fetch_one(query)
    if not existing_profile:
        # Создать профиль, если не существует
        query = profiles.insert().values(user_id=current_user_id, **profile_data.dict(exclude_unset=True))
        await database.execute(query)
    else:
        # Обновить профиль
        query = profiles.update().where(profiles.c.user_id == current_user_id).values(**profile_data.dict(exclude_unset=True))
        await database.execute(query)

    # Возвратить обновленный профиль
    updated_query = profiles.select().where(profiles.c.user_id == current_user_id)
    updated_profile = await database.fetch_one(updated_query)
    return ProfileOut(**dict(updated_profile))


@app.get("/recommendations/", response_model=List[Recommendation])
async def get_recommendations(current_user_id: int = Depends(get_current_user_id)):
    # 1. Получить свой профиль
    my_profile_query = profiles.select().where(profiles.c.user_id == current_user_id)
    my_profile = await database.fetch_one(my_profile_query)
    if not my_profile:
        raise HTTPException(status_code=404, detail="Your profile not found")

    # 2. Проверить кэш (Redis)
    cache_key = f"recs:{current_user_id}"
    cached_recs = redis_client.get(cache_key)
    if cached_recs:
        print("Cache hit for recommendations")
        return pickle.loads(cached_recs)

    # 3. Найти потенциальные совпадения (упрощено: все, кроме себя)
    # В реальности: фильтры (город, цели), индексация, сложные запросы
    potential_matches_query = profiles.select().where(profiles.c.user_id != current_user_id)
    potential_profiles = await database.fetch_all(potential_matches_query)

    recommendations = []
    for p in potential_profiles:
        score = calculate_compatibility_score(dict(my_profile), dict(p))
        if score > 0: # Только если есть совпадение
            rec = Recommendation(
                user_id=p["user_id"],
                name=p["name"],
                city=p["city"],
                photo_url=p["photo_url"],
                bio=p["bio"],
                compatibility_score=score,
                interests=p["interests"],
                skills=p["skills"]
            )
            recommendations.append(rec)

    # 4. Сортировать по совместимости
    recommendations.sort(key=lambda x: x.compatibility_score, reverse=True)

    # 5. Сохранить в кэш (на 10 минут)
    redis_client.setex(cache_key, 600, pickle.dumps(recommendations))

    return recommendations

# --- Вспомогательная функция для аутентификации (нужно реализовать) ---
def get_current_user_id():
    # Извлекает user_id из JWT токена в заголовке Authorization
    # Возвращает user_id или вызывает HTTPException
    # Используйте fastapi.security.HTTPBearer для извлечения токена
    pass # Заглушка - реализуйте позже

# --- Запуск ---
# uvicorn main:app --reload