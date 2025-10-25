# add_test_users.py

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from backend.app.db import Base # Импортируем Base из вашего db.py
from backend.app.models import User, Profile # Импортируем модели из вашего models.py
from backend.app.security import hash_password # Импортируем функцию хеширования из вашего security.py

# Убедитесь, что строка подключения в db.py совпадает или используйте её здесь
DATABASE_URL = "sqlite+aiosqlite:///./titanit.db"
engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

async def add_users_and_profiles():
    """
    Асинхронная функция для добавления тестовых пользователей и профилей.
    """
    # Создаем таблицы, если они еще не созданы
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Создаем асинхронную сессию
    async with AsyncSessionLocal() as session:
        # --- Данные для пользователей ---
        users_data = [
            {
                "email": "anna.designer@example.com",
                "password_hash": hash_password("testpassword123"), # Хешируем пароль
                "name": "Аня",
                "city": "Москва"
            },
            {
                "email": "igor.developer@example.com",
                "password_hash": hash_password("testpassword456"), # Хешируем пароль
                "name": "Игорь",
                "city": "Санкт-Петербург"
            },
            {
                "email": "marina.artist@example.com",
                "password_hash": hash_password("testpassword789"), # Хешируем пароль
                "name": "Марина",
                "city": "Екатеринбург"
            }
        ]

        # --- Данные для профилей ---
        profiles_data = [
            {
                "user_id": 1, # Соответствует id первого пользователя
                "name": "Аня",
                "age": 24,
                "city": "Москва",
                "photo_url": "https://example.com/anna.jpg",
                "bio": "Студент-дизайнер, ищу команду для арт-проекта. Люблю иллюстрации и графический дизайн.",
                "interests": ["дизайн", "иллюстрации", "арт", "командная работа"],
                "skills": ["Adobe Illustrator", "Adobe Photoshop", "графический дизайн"],
                "goals": ["найти команду", "реализовать проект"]
            },
            {
                "user_id": 2, # Соответствует id второго пользователя
                "name": "Игорь",
                "age": 30,
                "city": "Санкт-Петербург",
                "photo_url": "https://example.com/igor.jpg",
                "bio": "IT-разработчик, ищу партнера для стартапа. Опыт в Python, Django, FastAPI.",
                "interests": ["python", "django", "fastapi", "стартапы", "предпринимательство"],
                "skills": ["Python", "Django", "FastAPI", "SQL", "ML"],
                "goals": ["найти партнера", "запустить стартап", "настроить backend"]
            },
            {
                "user_id": 3, # Соответствует id третьего пользователя
                "name": "Марина",
                "age": 27,
                "city": "Екатеринбург",
                "photo_url": "https://example.com/marina.jpg",
                "bio": "Недавно переехала. Ищу друзей по интересам: йога, кино, прогулки.",
                "interests": ["йога", "кино", "прогулки", "новые знакомства"],
                "skills": ["общение", "организация мероприятий"],
                "goals": ["найти друзей", "освоиться в городе"]
            }
        ]

        try:
            # --- Добавляем пользователей ---
            for user_data in users_data:
                new_user = User(**user_data)
                session.add(new_user)

            await session.commit() # Сохраняем пользователей
            print("Users added successfully.")

            # --- Добавляем профили ---
            for profile_data in profiles_data:
                new_profile = Profile(**profile_data)
                session.add(new_profile)

            await session.commit() # Сохраняем профили
            print("Profiles added successfully.")
            print("Test users and profiles have been added to the database.")

        except Exception as e:
            print(f"An error occurred: {e}")
            await session.rollback() # Откат изменений в случае ошибки
        finally:
            await session.close() # Закрываем сессию

# Точка входа для запуска асинхронной функции
if __name__ == "__main__":
    asyncio.run(add_users_and_profiles())