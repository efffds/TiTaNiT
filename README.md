# TITANIT (Hackaton)

## Backend (FastAPI)

Команды для запуска бэкенда локально:

cd backend
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --lifespan=off

После запуска открой: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Структура проекта
- **backend/app**  код API (FastAPI)
- **.venv**  локальное окружение (не коммитится)
- **\*.db**, **\_\_pycache\_\_**, **\*.pyc**  игнорируются
- **scratch/**  локальные черновики (игнорируются)

---

## Git команды
Основной цикл работы:
`ash
git add .
git commit -m "описание изменений"
git pull --rebase origin main
git push
