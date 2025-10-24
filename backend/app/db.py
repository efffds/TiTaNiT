# backend/app/database.py

# Импорты для асинхронной работы
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
import os

# Используем SQLite для асинхронной работы.
# ВНИМАНИЕ: Для асинхронной работы с SQLite нужен драйвер aiosqlite.
# Установите его: pip install aiosqlite
DATABASE_URL = "sqlite+aiosqlite:///./titanit.db"

# Создаем асинхронный движок
engine = create_async_engine(
    DATABASE_URL,
    # echo=True # Раскомментируйте для логирования SQL-запросов
    connect_args={"check_same_thread": False} # Для SQLite, чтобы избежать ошибок в разных потоках
)

# Создаем асинхронную фабрику сессий
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession, # Указываем, что нужно создавать AsyncSession
    expire_on_commit=False # Важно для асинхронных сессий
)

# Базовый класс для моделей SQLAlchemy
Base = declarative_base()

# Зависимость для получения асинхронной сессии базы данных в роутах
async def get_async_session():
    async with AsyncSessionLocal() as session:
        yield session

# Если вам *всё равно* нужна синхронная сессия для *каких-то других частей* кода,
# вы можете оставить старую синхронную, но лучше использовать асинхронную везде.
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# sync_engine = create_engine(DATABASE_URL.replace("+aiosqlite", ""))
# SyncSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=sync_engine)