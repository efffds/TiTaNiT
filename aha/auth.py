# auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials # Используем HTTPBearer и HTTPAuthorizationCredentials
import jwt
import os
from typing import Optional

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-here") # Заменить на .env
ALGORITHM = "HS256"

security = HTTPBearer() # Используем HTTPBearer

def get_current_user_id(credentials: HTTPAuthorizationCredentials = Security(security)) -> int: # Используем HTTPAuthorizationCredentials
    token = credentials.credentials # Доступ к токену через .credentials
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Could not validate credentials")
        return int(user_id)
    except jwt.PyJWTError:
        raise HTTPException(status_code=401, detail="Could not validate credentials")
