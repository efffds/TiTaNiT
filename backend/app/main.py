from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from .routers import auth, users, recommendations
from .db import Base, engine # Импортируем engine и Base из db.py

from .routers import analytics

# Асинхронная функция для создания таблиц
async def create_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: создаем таблицы при запуске приложения
    print("Creating tables...")
    await create_tables()
    print("Tables created.")
    yield # Приложение работает
    # Shutdown (опционально)
    print("Shutting down...")

app = FastAPI(
    title="TITANIT API",
    version="0.2.0",
    lifespan=lifespan # <-- Добавляем lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"], # Убедитесь, что это ваш адрес фронтенда
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# УДАЛЕНО: Base.metadata.create_all(bind=engine)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(recommendations.router)
app.include_router(analytics.router)

@app.get("/health")
def health():
    return {"status": "ok"}

# Если у вас есть другие корневые маршруты, добавьте их здесь
@app.get("/")
def read_root():
    return {"message": "Welcome to TITANIT API"}