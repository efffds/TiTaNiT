# backend/app/routers/profile.py
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, insert, delete
from ..db import get_async_session
from ..models import Profile, UserPhoto
from ..security import get_current_user_id

import aiofiles
import aiofiles.os

router = APIRouter(prefix="/profile", tags=["profile"])

def _coerce_list(value):
    # фронт пока шлёт строки; если начнёшь слать JSON-массивы — дополним
    if value is None:
        return ""
    if isinstance(value, list):
        return ", ".join([str(x).strip() for x in value])
    return str(value)

# ---------- Профиль ----------
@router.get("")
async def get_profile(
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    res = await db.execute(select(Profile).where(Profile.user_id == user_id))
    prof = res.scalar_one_or_none()
    if not prof:
        row = await db.execute(
            insert(Profile).values(
                user_id=user_id,
                name="",
                age=None,
                city="",
                bio="",
                interests="",
                skills="",
                goals="",
            ).returning(Profile.id)
        )
        await db.commit()
        prof_id = row.scalar_one()
        res = await db.execute(select(Profile).where(Profile.id == prof_id))
        prof = res.scalar_one()

    return {
        "id": prof.id,
        "user_id": prof.user_id,
        "name": prof.name,
        "age": prof.age,
        "city": prof.city,
        "bio": prof.bio,
        "interests": prof.interests or "",
        "skills": prof.skills or "",
        "goals": prof.goals or "",
    }

@router.put("")
async def update_profile(
    payload: dict,
    db: AsyncSession = Depends(get_async_session),
    user_id: int = Depends(get_current_user_id),
):
    res = await db.execute(select(Profile).where(Profile.user_id == user_id))
    prof = res.scalar_one_or_none()
    if not prof:
        raise HTTPException(status_code=404, detail="Profile not found")

    fields = {}
    for key in ["name", "age", "city", "bio", "interests", "skills", "goals"]:
        if key in payload:
            val = payload[key]
            if key in ["interests", "skills", "goals"]:
                val = _coerce_list(val)
            fields[key] = val

    if fields:
        await db.execute(update(Profile).where(Profile.user_id == user_id).values(**fields))
        await db.commit()

    return {"ok": True, "updated": list(fields.keys())}

# ---------- Фото ----------
@router.get("/photos")
async def list_photos(
    db: AsyncSession = Depends(get_async_session),
    current_user_id: int = Depends(get_current_user_id),
):
    res = await db.execute(select(UserPhoto).where(UserPhoto.user_id == current_user_id))
    photos = res.scalars().all()
    return {
        "items": [
            {
                "id": p.id,
                "photo_path": str(p.photo_path),
                "is_primary": bool(getattr(p, "is_primary", False)),
            }
            for p in photos
        ]
    }

@router.put("/photos/{photo_id}/set_primary")
async def set_primary_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user_id: int = Depends(get_current_user_id),
):
    await db.execute(
        update(UserPhoto)
        .where(UserPhoto.user_id == current_user_id)
        .values(is_primary=False)
    )
    res = await db.execute(
        update(UserPhoto)
        .where(UserPhoto.user_id == current_user_id, UserPhoto.id == photo_id)
        .values(is_primary=True)
        .returning(UserPhoto.id)
    )
    row = res.first()
    await db.commit()

    if not row:
        raise HTTPException(status_code=404, detail="Photo not found")

    return {"ok": True, "id": row.id}

@router.delete("/photos/{photo_id}")
async def delete_photo(
    photo_id: int,
    db: AsyncSession = Depends(get_async_session),
    current_user_id: int = Depends(get_current_user_id),
):
    res = await db.execute(
        select(UserPhoto).where(UserPhoto.id == photo_id, UserPhoto.user_id == current_user_id)
    )
    photo = res.scalar_one_or_none()
    if not photo:
        raise HTTPException(status_code=404, detail="Photo not found")

    # удалить файл с диска (если есть)
    try:
        if await aiofiles.os.path.exists(photo.photo_path):
            await aiofiles.os.remove(photo.photo_path)
    except Exception as e:
        print(f"⚠️ Не удалось удалить файл {photo.photo_path}: {e}")

    await db.execute(delete(UserPhoto).where(UserPhoto.id == photo_id))
    await db.commit()
    return JSONResponse({"ok": True})
