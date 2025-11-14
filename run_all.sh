#!/usr/bin/env bash
set -e

# ---------- Backend ----------
cd backend
# Use Python 3.12 instead of the default (which might be 3.14)
/opt/homebrew/bin/python3.12 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ..

# ---------- Frontend ----------
cd frontend
npm ci
cat > .env.development <<EOF
VITE_API_URL=http://127.0.0.1:8000
EOF
cd ..

# ---------- Запуск ----------
python "./Run Both Servers.py"
