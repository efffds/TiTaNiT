# backend/app/schemas.py

from pydantic import BaseModel, EmailStr
from typing import List, Optional, Literal

# --- Существующие схемы ---
class UserCreate(BaseModel):
    email: EmailStr
    password: str
    name: str
    city: str | None = None

class UserRead(BaseModel):
    id: int
    email: EmailStr
    name: str
    city: str | None = None

    class Config:
        from_attributes = True # Обратите внимание: 'Config' устарел, в Pydantic v2 используйте model_config

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

# --- Новые схемы для аналитики ---
class SkillCount(BaseModel):
    skill: str
    count: int

class InterestCount(BaseModel):
    interest: str
    count: int

class CitySkills(BaseModel):
    city: str
    top_skills: List[SkillCount]

class UserSkillsResponse(BaseModel):
    top_skills: List[SkillCount]

class UserInterestsResponse(BaseModel):
    top_interests: List[InterestCount]

class SocialFieldResponse(BaseModel):
    data: List[CitySkills]

# --- Схемы для профиля ---
class ProfileCreateUpdate(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    city: Optional[str] = None
    photo_url: Optional[str] = None
    bio: Optional[str] = None
    interests: Optional[List[str]] = []
    skills: Optional[List[str]] = []
    goals: Optional[List[str]] = []

class ProfileOut(BaseModel):
    user_id: int
    name: Optional[str]
    age: Optional[int]
    city: Optional[str]
    photo_url: Optional[str]
    bio: Optional[str]
    interests: List[str]
    skills: List[str]
    goals: List[str]

    class Config:
        from_attributes = True

# --- Схемы для рекомендаций ---
class Recommendation(BaseModel):
    user_id: int
    name: Optional[str]
    city: Optional[str]
    photo_url: Optional[str]
    bio: Optional[str]
    compatibility_score: float
    interests: List[str]
    skills: List[str]

# --- Схемы для свайпов (лайк/дизлайк) ---
class SwipeRequest(BaseModel):
    target_user_id: int
    action: Literal["like", "dislike"]

class SwipeResponse(BaseModel):
    action: str
    match: bool = False

class MatchesResponse(BaseModel):
    user_ids: List[int]
