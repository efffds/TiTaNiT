# run_ml_test.py

import asyncio
import sys
import os
# Добавляем корневую директорию проекта в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.db import engine, Base, get_async_session # Используем engine из db.py
from backend.app.ml_processing import run_ml_pipeline # Импортируем основную функцию из ml_processing.py

async def test_ml_pipeline():
    """
    Асинхронная функция для тестирования ML-пайплайна.
    """
    print("Запуск теста ML-пайплайна...")

    # Создаем сессию для работы с БД
    # Используем engine напрямую, как в примере DB Browser
    async with AsyncSession(engine) as session:
        try:
            # Запускаем основной пайплайн
            print("Запуск run_ml_pipeline...")
            await run_ml_pipeline(session)
            print("ML pipeline завершен успешно!")

            # --- Проверка: загрузка и вывод совпадений из БД ---
            from sqlalchemy import select
            from backend.app.models import Match # Импортируем модель Match
            print("\n--- Проверка совпадений в БД ---")
            result = await session.execute(select(Match))
            saved_matches = result.scalars().all()

            if saved_matches:
                for match_record in saved_matches:
                    print(f"Пользователь {match_record.user_id} совпал с: {match_record.matched_user_ids}")
            else:
                print("В таблице 'matches' не найдено записей после выполнения пайплайна.")
                print("Возможные причины:")
                print("  - В таблице 'profiles' не было достаточно данных для вычисления совместимости.")
                print("  - Никакие пары пользователей не превысили порог совместимости (0.7).")
                print("  - Произошла ошибка во время выполнения пайплайна (смотрите сообщения выше).")


        except Exception as e:
            print(f"Произошла ошибка во время теста: {e}")
            import traceback
            traceback.print_exc() # Печатает полный стек вызовов ошибки

# Точка входа для запуска теста
if __name__ == "__main__":
    # Запускаем асинхронную функцию тестирования
    asyncio.run(test_ml_pipeline())
