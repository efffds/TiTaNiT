from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from ..db import get_async_session
from ..security import get_current_user_id
from ..schemas import SwipeRequest, SwipeResponse, MatchesResponse
from ..models import Like, Match

router = APIRouter(prefix="/swipe", tags=["swipe"])

@router.post("/", response_model=SwipeResponse)
async def swipe(payload: SwipeRequest,
                current_user_id: int = Depends(get_current_user_id),
                db: AsyncSession = Depends(get_async_session)):
    if payload.target_user_id == current_user_id:
        raise HTTPException(status_code=400, detail="Нельзя лайкать собственную анкету")

    is_like = payload.action == "like"

    # Найдём существующий свайп и обновим или создадим новый
    res = await db.execute(
        select(Like).where(and_(Like.from_user_id == current_user_id,
                                 Like.to_user_id == payload.target_user_id))
    )
    like_obj = res.scalar_one_or_none()
    if like_obj:
        like_obj.is_like = is_like
    else:
        like_obj = Like(from_user_id=current_user_id, to_user_id=payload.target_user_id, is_like=is_like)
        db.add(like_obj)
    await db.commit()

    matched = False
    if is_like:
        # Проверяем взаимный лайк
        res_back = await db.execute(
            select(Like).where(and_(Like.from_user_id == payload.target_user_id,
                                     Like.to_user_id == current_user_id,
                                     Like.is_like == True))
        )
        back_like = res_back.scalar_one_or_none()
        if back_like:
            # Создаём матч, если его ещё нет
            user1 = min(current_user_id, payload.target_user_id)
            user2 = max(current_user_id, payload.target_user_id)
            res_match = await db.execute(
                select(Match).where(and_(Match.user1_id == user1, Match.user2_id == user2))
            )
            match_obj = res_match.scalar_one_or_none()
            if not match_obj:
                db.add(Match(user1_id=user1, user2_id=user2))
                await db.commit()
            matched = True

    return SwipeResponse(action=payload.action, match=matched)


@router.get("/matches", response_model=MatchesResponse)
async def list_matches(current_user_id: int = Depends(get_current_user_id),
                       db: AsyncSession = Depends(get_async_session)):
    res = await db.execute(
        select(Match).where((Match.user1_id == current_user_id) | (Match.user2_id == current_user_id))
    )
    matches = res.scalars().all()
    partner_ids = [m.user2_id if m.user1_id == current_user_id else m.user1_id for m in matches]
    return MatchesResponse(user_ids=partner_ids)