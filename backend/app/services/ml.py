# backend/app/services/ml.py

import os
from typing import List

try:
    import httpx  # type: ignore
except Exception:  # pragma: no cover
    httpx = None  # type: ignore

ML_SERVICE_URL = os.getenv("ML_SERVICE_URL", "http://127.0.0.1:8001")

async def get_recommendations_for_user(user_id: int) -> List[int]:
    """
    Обращается к внешнему ML-сервису за списком рекомендаций для данного пользователя.
    Ожидаемый ответ: {"user_ids": [2,5,10, ...]} или {"items": [2,5,10]}
    В случае ошибки или недоступности сервиса — возвращает пустой список.
    """
    if httpx is None:
        return []
    url = f"{ML_SERVICE_URL.rstrip('/')}/recommendations"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(url, json={"user_id": user_id})
            if resp.status_code != 200:
                return []
            data = resp.json()
            if isinstance(data, dict):
                if isinstance(data.get("user_ids"), list):
                    return [int(x) for x in data.get("user_ids") if x != user_id]
                if isinstance(data.get("items"), list):
                    return [int(x) for x in data.get("items") if x != user_id]
            # Если вернули просто список
            if isinstance(data, list):
                return [int(x) for x in data if x != user_id]
            return []
    except Exception:
        return []
