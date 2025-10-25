# run_ml_pipeline_script.py
# Поместите этот файл в D:\VSCodeProjects\hackaton\hackaton\backend\app

import asyncio
import sys
import os

# Добавляем корневую директорию проекта (где лежит папка backend) в путь поиска модулей
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# --- ИМПОРТЫ СТАЛИ АБСОЛЬТНЫМИ ---
from backend.app.db import engine, Base, get_async_session
from backend.app.models import Profile, Match # Импортируем модели Profile и Match из backend.app.models
# Импортируем функции из ml_processing.py
from backend.app.ml_processing import calculate_compatibility_matrix, find_matches, save_compatibility_matrix, save_matches_to_db
# ------------------------------

async def run_pipeline_from_script():
    """
    Асинхронная функция для запуска ML-пайплайна из скрипта.
    """
    print("Запуск ML-пайплайна из скрипта...")
    async with AsyncSession(engine) as session:
        try:
            # 1. Вычислить матрицу
            user_id_to_index, matrix = await calculate_compatibility_matrix(session)

            if matrix.size == 0:
                print("No profiles to process, exiting pipeline.")
                return

            # 2. Сохранить матрицу (опционально)
            save_compatibility_matrix(user_id_to_index, matrix)

            # 3. Найти совпадения
            matches = find_matches(matrix, user_id_to_index, threshold=0.7)

            # 4. Сохранить совпадения в БД
            await save_matches_to_db(session, matches)

            print("ML pipeline completed successfully from script!")

            # --- Проверка: загрузка и вывод совпадений из БД ---
            print("\n--- Checking Matches in DB After Pipeline ---")
            result = await session.execute(select(Match))
            saved_matches = result.scalars().all()

            if saved_matches:
                for match_record in saved_matches:
                    print(f"User {match_record.user_id} matched with: {match_record.matched_user_ids}")
            else:
                print("No matches found in the database after pipeline run from script.")

        except Exception as e:
            print(f"An error occurred during the pipeline run from script: {e}")
            import traceback
            traceback.print_exc() # Печатает полный стек вызовов ошибки
        finally:
            await session.close()

if __name__ == "__main__":
    asyncio.run(run_pipeline_from_script())
