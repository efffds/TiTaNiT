# backend/app/db.py

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

# Подключение SQLite через aiosqlite
DATABASE_URL = "sqlite+aiosqlite:///./titanit.db"

# Создаём асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    echo=False  # Поставь True, если хочешь видеть SQL-запросы в консоли
)

# Создаём фабрику асинхронных сессий
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# Зависимость для получения асинхронной сессии в роутах
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session
