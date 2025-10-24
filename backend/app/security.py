# backend/app/security.py

from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import jwt
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

# --- Настройки ---
# Лучше использовать переменную окружения
SECRET_KEY = os.getenv("SECRET_KEY", "change_me") # Обязательно смените на проде
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

# --- Утилиты ---
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer() # Создаем экземпляр HTTPBearer

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

def create_access_token(payload: dict, minutes: int = ACCESS_TOKEN_EXPIRE_MINUTES) -> str:
    to_encode = payload.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

# --- НОВОЕ: Функция аутентификации ---
def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> int:
    """
    Зависимость FastAPI для извлечения user_id из JWT-токена в заголовке Authorization.
    """
    token = credentials.credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub") # "sub" обычно используется для ID пользователя
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return int(user_id)
    except jwt.JWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")

# Если вы хотите возвращать не только ID, но и другую информацию (например, email),
# создайте другую функцию, возвращающую, например, Pydantic-модель UserRead.
# def get_current_user(credentials: HTTPAuthorizationCredentials = Security(security)) -> schemas.UserRead:
#    user_id = get_current_user_id(credentials)
#    # Затем загрузить пользователя из БД по ID
#    # ...