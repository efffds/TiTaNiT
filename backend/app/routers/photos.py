# backend/app/routers/photos.py

from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
import aiofiles
from ..db import get_async_session
from ..models import UserPhoto
from ..security import get_current_user_id
import uuid
from pathlib import Path

router = APIRouter(
    prefix="/profile",
    tags=["photos"],
    dependencies=[Depends(get_current_user_id)]
)

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

@router.post("/photos", status_code=status.HTTP_201_CREATED)
async def upload_photo(
    file: UploadFile = File(...),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session)
):
    """Загружает фотографию для текущего пользователя."""
    unique_filename = f"{uuid.uuid4()}_{file.filename}"
    file_path = UPLOAD_DIR / unique_filename
    absolute_file_path = file_path.resolve()

    try:
        async with aiofiles.open(absolute_file_path, "wb") as buffer:
            while chunk := await file.read(64 * 1024):
                await buffer.write(chunk)
    except Exception as e:
        if absolute_file_path.exists():
            try:
                absolute_file_path.unlink(missing_ok=True)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to save file: {str(e)}")

    try:
        db_photo = UserPhoto(user_id=current_user_id, photo_path=str(file_path.as_posix()))
        db.add(db_photo)
        await db.commit()
        await db.refresh(db_photo)
        return {
            "id": db_photo.id,
            "photo_path": str(db_photo.photo_path),
            "is_primary": bool(getattr(db_photo, "is_primary", False)),
            "message": "Photo uploaded successfully",
        }
    except Exception as e:
        if absolute_file_path.exists():
            try:
                absolute_file_path.unlink(missing_ok=True)
            except Exception:
                pass
        raise HTTPException(status_code=500, detail=f"Failed to save photo info to database: {str(e)}")
