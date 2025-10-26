# backend/app/routers/photos.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
# Импортируем aiofiles
import aiofiles
import aiofiles.os # Для асинхронного удаления файла, если нужно
from ..db import get_async_session
from ..models import UserPhoto # Импортируем модель UserPhoto
from ..security import get_current_user_id # Импортируем зависимость для аутентификации
import os
import uuid
from pathlib import Path

router = APIRouter(
    prefix="/profile", # Префикс для всех эндпоинтов в этом роутере
    tags=["photos"],
    # Требуем аутентификацию для всех эндпоинтов в этом роутере
    dependencies=[Depends(get_current_user_id)]
)

# Определяем директорию для загрузки.
# Убедитесь, что путь корректен относительно запуска вашего main.py
# Path(__file__) дает путь к этому файлу, .parent.parent поднимает на уровень backend/app
# UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
# Более простой и надежный способ: относительно текущей рабочей директории (где запущен uvicorn)
UPLOAD_DIR = Path("uploads")
# Создаем папку, если её нет. Это синхронная операция, но допустима при старте.
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/photos", status_code=status.HTTP_201_CREATED) # Эндпоинт для загрузки фото
async def upload_photo(
    file: UploadFile = File(...), # Принимаем файл
    current_user_id: int = Depends(get_current_user_id), # Получаем ID текущего пользователя
    db: AsyncSession = Depends(get_async_session) # Получаем сессию БД
):
    """
    Загружает фотографию для текущего пользователя асинхронно с использованием aiofiles.
    """
    # 1. Базовая проверка типа файла (опционально, но рекомендуется)
    # if not file.content_type.startswith("image/"):
    #     raise HTTPException(status_code=400, detail="Uploaded file must be an image.")

    # 2. Генерируем уникальное имя файла, чтобы избежать конфликтов
    # Можно также сохранить оригинальное имя или часть его
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    # Используем абсолютный путь для надежности
    file_path = UPLOAD_DIR / unique_filename
    absolute_file_path = file_path.resolve()

    # 3. Асинхронно сохраняем файл на диск с помощью aiofiles
    try:
        # Открываем файл асинхронно для записи в бинарном режиме
        async with aiofiles.open(absolute_file_path, "wb") as buffer:
            # Читаем и записываем файл по частям, чтобы не перегружать память
            while chunk := await file.read(64 * 1024):  # Читаем по 64KB
                await buffer.write(chunk)
        # После выхода из контекстного менеджера, файл автоматически закрывается
    except Exception as e:
        # Если произошла ошибка при сохранении, пытаемся удалить возможно созданный файл и возвращаем ошибку
        # Используем aiofiles.os.remove для асинхронного удаления
        if await aiofiles.os.path.exists(absolute_file_path):
            try:
                await aiofiles.os.remove(absolute_file_path)
            except Exception as del_err:
                # Логируем ошибку удаления, но не прерываем основную ошибку
                print(f"Failed to delete partial file {absolute_file_path} after upload error: {del_err}")
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    # 4. Создаем запись в БД
    try:
        # Сохраняем путь относительно корня проекта или абсолютный путь, как удобнее для фронта
        # Здесь сохраняем относительный путь от UPLOAD_DIR или просто имя файла, если UPLOAD_DIR корневая папка для фото
        # Для простоты будем хранить относительный путь от проекта (например, uploads/filename.jpg)
        # Если UPLOAD_DIR = "uploads", то photo_path = f"uploads/{unique_filename}"
        # Но так как file_path уже содержит uploads/, можно просто str(file_path)
        # Или можно хранить только имя файла: photo_path = unique_filename
        # Выберем хранение относительного пути от корня проекта
        db_photo = UserPhoto(user_id=current_user_id, photo_path=str(file_path.as_posix())) # as_posix() для прямых слешей
        db.add(db_photo)
        await db.commit()
        await db.refresh(db_photo) # Обновляем объект, чтобы получить id

        return {
            "id": db_photo.id,
            "photo_path": str(db_photo.photo_path), # Возвращаем путь
            "message": "Photo uploaded successfully"
        }
    except Exception as e:
        # Если ошибка при сохранении в БД, удаляем файл с диска асинхронно
        if await aiofiles.os.path.exists(absolute_file_path):
            try:
                await aiofiles.os.remove(absolute_file_path)
            except Exception as del_err:
                 # Логируем ошибку удаления, но не прерываем основную ошибку
                print(f"Failed to delete file {absolute_file_path} after DB error: {del_err}")
        raise HTTPException(status_code=500, detail=f"Failed to save photo info to database: {str(e)}")

# Добавьте другие эндпоинты для работы с фото, если нужно:
# - GET /profile/photos - получить список фото текущего пользователя
# - DELETE /profile/photos/{photo_id} - удалить конкретное фото
# - PUT /profile/photos/{photo_id}/set_primary - установить фото как основное
