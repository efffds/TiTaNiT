# backend/app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import auth, users, recommendations, analytics
from .routers import chat as chat_router
from .db import Base, engine  # <-- импорт именно из db.py
from .routers import photos # <-- НОВОЕ: Импортируем photos
from fastapi.staticfiles import StaticFiles

# Создание таблиц при запуске
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    await create_tables()
    yield

app = FastAPI(
    title="TITANIT API",
    version="0.2.0",
    lifespan=lifespan
)

# Разрешаем фронт
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключаем роутеры
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recommendations.router)
app.include_router(analytics.router)
app.include_router(chat_router.router)
app.include_router(photos.router) # <-- НОВОЕ: Подключаем роутер photos
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

# Роутер свайпов (лайки/дизлайки)
from .routers import likes as likes_router  # импорт после создания app, чтобы избежать циклов
app.include_router(likes_router.router)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/")
def read_root():
    return {"message": "Welcome to TITANIT API"}
