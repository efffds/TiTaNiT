# backend/app/routers/analytics.py
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
import json # Для десериализации JSON-полей из БД
from ..db import get_async_session # Предполагается, что у вас есть этот файл
from ..models import Profile # Предполагается, что у вас есть модель Profile
from ..schemas import (
    UserSkillsResponse, # Pydantic модель для ответа
    UserInterestsResponse, # Pydantic модель для ответа
    SocialFieldResponse # Pydantic модель для ответа
)
from collections import Counter # Для подсчета популярности

router = APIRouter(
    prefix="/analytics",
    tags=["analytics"]
)

@router.get("/user-skills/", response_model=UserSkillsResponse)
async def get_popular_skills(db: AsyncSession = Depends(get_async_session)):
    """
    Возвращает топ популярных навыков среди всех пользователей.
    """
    # Запрос к БД для получения всех навыков
    result = await db.execute(Profile.__table__.select())
    profiles = result.fetchall()

    all_skills = []
    for profile in profiles:
        # Предполагаем, что навыки хранятся как JSON-массив в поле skills
        skills_json = profile.skills
        if skills_json:
            # Десериализуем JSON-строку в список (если хранится как строка)
            # Если хранится как JSONB, SQLAlchemy может автоматически десериализовать
            try:
                skills_list = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
                if isinstance(skills_list, list):
                    all_skills.extend(skills_list)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse skills JSON for profile {profile.user_id}: {skills_json}")
                continue

    # Подсчитываем количество вхождений каждого навыка
    skill_counts = Counter(all_skills)
    # Сортируем по убыванию
    sorted_skills = skill_counts.most_common()

    # Возвращаем топ 10 (или меньше) навыков
    top_skills = [{"skill": skill, "count": count} for skill, count in sorted_skills[:10]]

    return UserSkillsResponse(top_skills=top_skills)


@router.get("/user-interests/", response_model=UserInterestsResponse)
async def get_popular_interests(db: AsyncSession = Depends(get_async_session)):
    """
    Возвращает топ популярных интересов среди всех пользователей.
    """
    # Запрос к БД для получения всех интересов
    result = await db.execute(Profile.__table__.select())
    profiles = result.fetchall()

    all_interests = []
    for profile in profiles:
        interests_json = profile.interests
        if interests_json:
            try:
                interests_list = json.loads(interests_json) if isinstance(interests_json, str) else interests_json
                if isinstance(interests_list, list):
                    all_interests.extend(interests_list)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse interests JSON for profile {profile.user_id}: {interests_json}")
                continue

    # Подсчитываем количество вхождений каждого интереса
    interest_counts = Counter(all_interests)
    # Сортируем по убыванию
    sorted_interests = interest_counts.most_common()

    # Возвращаем топ 10 (или меньше) интересов
    top_interests = [{"interest": interest, "count": count} for interest, count in sorted_interests[:10]]

    return UserInterestsResponse(top_interests=top_interests)

# Роут для "социального поля" - упрощенный пример: популярные навыки по городам
@router.get("/social-field/", response_model=SocialFieldResponse)
async def get_social_field(db: AsyncSession = Depends(get_async_session)):
    """
    Возвращает упрощенную визуализацию "социального поля" - популярные навыки по городам.
    """
    # Запрос к БД для получения городов и навыков
    result = await db.execute(Profile.__table__.select())
    profiles = result.fetchall()

    city_skills_map = {}
    for profile in profiles:
        city = profile.city
        if not city:
            continue # Пропускаем профили без города
        skills_json = profile.skills
        if skills_json:
            try:
                skills_list = json.loads(skills_json) if isinstance(skills_json, str) else skills_json
                if isinstance(skills_list, list):
                    if city not in city_skills_map:
                        city_skills_map[city] = []
                    city_skills_map[city].extend(skills_list)
            except json.JSONDecodeError:
                print(f"Warning: Could not parse skills JSON for profile {profile.user_id}: {skills_json}")
                continue

    # Подсчитываем навыки для каждого города
    social_field_data = []
    for city, skills in city_skills_map.items():
        skill_counts = Counter(skills)
        sorted_skills = skill_counts.most_common()
        top_skills_for_city = [{"skill": skill, "count": count} for skill, count in sorted_skills[:5]] # Топ 5 для города
        social_field_data.append({
            "city": city,
            "top_skills": top_skills_for_city
        })

    # Сортируем города по количеству пользователей (приблизительно)
    social_field_data.sort(key=lambda x: sum(item['count'] for item in x['top_skills']), reverse=True)

    return SocialFieldResponse(data=social_field_data)


# Роут для персональной аналитики (например, навыки текущего пользователя)
# Требует аутентификации
from ..security import get_current_user_id # Используем вашу функцию аутентификации

@router.get("/personal-skills/", response_model=UserSkillsResponse)
async def get_personal_skills(current_user_id: int = Depends(get_current_user_id), db: AsyncSession = Depends(get_async_session)):
    """
    Возвращает навыки текущего пользователя.
    """
    # Запрос к БД для получения профиля текущего пользователя
    result = await db.execute(Profile.__table__.select().where(Profile.user_id == current_user_id))
    profile = result.fetchone()

    if not profile or not profile.skills:
        return UserSkillsResponse(top_skills=[]) # Возвращаем пустой список, если навыков нет

    user_skills = profile.skills
    try:
        skills_list = json.loads(user_skills) if isinstance(user_skills, str) else user_skills
        if not isinstance(skills_list, list):
            skills_list = []
    except json.JSONDecodeError:
        print(f"Warning: Could not parse skills JSON for current user {current_user_id}: {user_skills}")
        skills_list = []

    # Форматируем как список словарей с count для совместимости с фронтендом
    formatted_skills = [{"skill": skill, "count": 1} for skill in skills_list]

    return UserSkillsResponse(top_skills=formatted_skills)
