from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from ..db import get_async_session
from ..security import get_current_user_id
from ..models import Profile, User, UserPhoto

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/ping")
def ping():
    return {"recs": "pong"}

def _tokenize(s: str | None) -> List[str]:
    if not s:
        return []
    # поддерживаем как CSV-строки, так и пробел-разделённые
    raw = [p.strip() for chunk in s.split(",") for p in chunk.split()]  # type: ignore
    return [x.lower() for x in raw if x]

@router.get("/")
async def list_recommendations(
    interests: str | None = Query(None, description="CSV или пробел-разделённый список интересов"),
    skills: str | None = Query(None, description="CSV или пробел-разделённый список навыков"),
    goals: str | None = Query(None, description="CSV или пробел-разделённый список целей"),
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    # 1) Соберём токены из запроса или из собственного профиля, если есть
    my_interests = set(_tokenize(interests))
    my_skills = set(_tokenize(skills))
    my_goals = set(_tokenize(goals))

    if not (my_interests or my_skills or my_goals):
        # Попробуем взять из профиля
        res = await db.execute(select(Profile).where(Profile.user_id == current_user_id))
        myp = res.scalar_one_or_none()
        if myp:
            my_interests = set(_tokenize(myp.interests))
            my_skills = set(_tokenize(myp.skills))
            my_goals = set(_tokenize(myp.goals))

    # 2) Вытащим остальные профили
    res = await db.execute(select(Profile, User).join(User, User.id == Profile.user_id).where(Profile.user_id != current_user_id))
    rows = res.all()

    items = []
    for prof, user in rows:
        p_interests = set(_tokenize(prof.interests))
        p_skills = set(_tokenize(prof.skills))
        p_goals = set(_tokenize(prof.goals))

        # простая метрика схожести: среднее по Джакарам для интересов/скиллов/целей
        def jacc(a: set[str], b: set[str]) -> float:
            if not a and not b:
                return 0.0
            inter = len(a & b)
            union = len(a | b)
            return (inter / union) if union else 0.0

        s_i = jacc(my_interests, p_interests)
        s_s = jacc(my_skills, p_skills)
        s_g = jacc(my_goals, p_goals)
        score = (s_i + s_s + s_g) / 3.0

        # Достаём основное фото, если есть
        photo_res = await db.execute(
            select(UserPhoto).where(UserPhoto.user_id == user.id).order_by(UserPhoto.is_primary.desc(), UserPhoto.upload_order.asc().nulls_last(), UserPhoto.uploaded_at.desc())
        )
        photo = photo_res.scalars().first()

        items.append({
            "user": {
                "id": user.id,
                "name": user.name,
                "city": user.city,
                "photo_path": photo.photo_path if photo else None,
            },
            "score": round(float(score), 4),
            "shared_interests": sorted(list(my_interests & p_interests)) if (my_interests and p_interests) else [],
            "shared_skills": sorted(list(my_skills & p_skills)) if (my_skills and p_skills) else [],
            "shared_goals": sorted(list(my_goals & p_goals)) if (my_goals and p_goals) else [],
        })

    # 3) Отсортируем по убыванию score и вернём топ-50
    items.sort(key=lambda x: x["score"], reverse=True)
    return {"items": items[:50]}
