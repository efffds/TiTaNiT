# backend/app/main.py  (можно разместить в отдельном файле, например, errors.py)

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(...)

# ----------------------------------------------------------------------
# ГЛОБАЛЬНЫЙ ОБРАБОТЧИК 422 (validation error)
# ----------------------------------------------------------------------
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Если запрос пришёл к эндпоинту из‑под /auth,
    вместо детального списка ошибок отдаём простое сообщение.
    """
    if request.url.path.startswith("/auth"):
        # 401 – «неавторизовано», т.к. это ошибка входа
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"detail": "email или пароль неверные"},
        )

    # Для всех остальных эндпоинтов оставляем оригинальное сообщение
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()},
    )
