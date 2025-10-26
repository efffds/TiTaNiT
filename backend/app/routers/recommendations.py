from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from ..db import get_async_session
from ..security import get_current_user_id
from ..models import Profile, User, UserPhoto
from ..services import ml

router = APIRouter(prefix="/recommendations", tags=["recommendations"])

@router.get("/ping")
def ping():
    return {"recs": "pong"}


def _tokenize(s: str | None) -> List[str]:
    if not s:
        return []
    raw = [p.strip() for chunk in s.split(",") for p in chunk.split()]  # type: ignore
    return [x.lower() for x in raw if x]


@router.get("/")
async def list_recommendations(
    current_user_id: int = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_async_session),
):
    # 1) Пытаемся получить список user_ids от ML-сервиса для текущего пользователя
    user_ids: List[int] = await ml.get_recommendations_for_user(current_user_id)

    items: List[dict] = []

    if user_ids:
        # 2) Загружаем их профили и пользователей разом
        res = await db.execute(
            select(Profile, User).join(User, User.id == Profile.user_id).where(Profile.user_id.in_(user_ids))
        )
        rows = res.all()
        # индекс для сохранения порядка, заданного ML
        order_index = {uid: i for i, uid in enumerate(user_ids)}

        # Получим основное фото одним запросом и выберем первое для каждого user_id
        photo_res = await db.execute(
            select(UserPhoto).where(UserPhoto.user_id.in_(user_ids)).order_by(
                UserPhoto.user_id.asc(),
                UserPhoto.is_primary.desc(),
                func.coalesce(UserPhoto.upload_order, 999999).asc(),
                UserPhoto.uploaded_at.desc(),
            )
        )
        primary_map: dict[int, str | None] = {}
        for p in photo_res.scalars().all():
            if p.user_id not in primary_map:
                primary_map[p.user_id] = p.photo_path

        # Для визуализации процента посчитаем простую схожесть (дополнительно к порядку ML)
        # Берём профиль текущего пользователя
        my_res = await db.execute(select(Profile).where(Profile.user_id == current_user_id))
        myp = my_res.scalar_one_or_none()
        my_i = set(_tokenize(getattr(myp, "interests", None))) if myp else set()
        my_s = set(_tokenize(getattr(myp, "skills", None))) if myp else set()
        my_g = set(_tokenize(getattr(myp, "goals", None))) if myp else set()

        def jacc(a: set[str], b: set[str]) -> float:
            if not a and not b:
                return 0.0
            inter = len(a & b)
            union = len(a | b)
            return (inter / union) if union else 0.0

        for prof, user in rows:
            pi = set(_tokenize(prof.interests))
            ps = set(_tokenize(prof.skills))
            pg = set(_tokenize(prof.goals))
            score = (jacc(my_i, pi) + jacc(my_s, ps) + jacc(my_g, pg)) / 3.0
            items.append({
                "user": {
                    "id": user.id,
                    "name": user.name,
                    "city": user.city,
                    "photo_path": primary_map.get(user.id),
                },
                # Сохраняем ранжирование ML через order_index, а score используем для отображения
                "rank": order_index.get(user.id, 10_000),
                "score": round(float(score), 4),
                "shared_interests": sorted(list(my_i & pi)) if (my_i and pi) else [],
                "shared_skills": sorted(list(my_s & ps)) if (my_s and ps) else [],
                "shared_goals": sorted(list(my_g & pg)) if (my_g and pg) else [],
            })

        # Сортируем по rank (как вернул ML)
        items.sort(key=lambda x: x["rank"])
        for it in items:
            it.pop("rank", None)
        return {"items": items[:50]}

    # 3) Фолбэк: если ML не ответил — простая локальная схожесть
    # Берём мой профиль
    my_res = await db.execute(select(Profile).where(Profile.user_id == current_user_id))
    myp = my_res.scalar_one_or_none()
    my_i = set(_tokenize(getattr(myp, "interests", None))) if myp else set()
    my_s = set(_tokenize(getattr(myp, "skills", None))) if myp else set()
    my_g = set(_tokenize(getattr(myp, "goals", None))) if myp else set()

    res = await db.execute(select(Profile, User).join(User, User.id == Profile.user_id).where(Profile.user_id != current_user_id))
    rows = res.all()

    def jacc(a: set[str], b: set[str]) -> float:
        if not a and not b:
            return 0.0
        inter = len(a & b)
        union = len(a | b)
        return (inter / union) if union else 0.0

    for prof, user in rows:
        pi = set(_tokenize(prof.interests))
        ps = set(_tokenize(prof.skills))
        pg = set(_tokenize(prof.goals))
        score = (jacc(my_i, pi) + jacc(my_s, ps) + jacc(my_g, pg)) / 3.0
        photo_res = await db.execute(
            select(UserPhoto).where(UserPhoto.user_id == user.id).order_by(
                UserPhoto.is_primary.desc(),
                func.coalesce(UserPhoto.upload_order, 999999).asc(),
                UserPhoto.uploaded_at.desc(),
            )
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
            "shared_interests": sorted(list(my_i & pi)) if (my_i and pi) else [],
            "shared_skills": sorted(list(my_s & ps)) if (my_s and ps) else [],
            "shared_goals": sorted(list(my_g & pg)) if (my_g and pg) else [],
        })

    items.sort(key=lambda x: x["score"], reverse=True)
    return {"items": items[:50]}
