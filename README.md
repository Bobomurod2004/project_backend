# Backend — Hisobot tizimi

Django REST API (korxonalar, hisobotlar) + AI Agent (FastAPI, Ollama).

## Tarkib

| Servis | Texnologiya | Ichki port | Host port |
|--------|-------------|-----------|-----------|
| `web`   | Django + Gunicorn | 8000 | 8001 |
| `agent` | FastAPI + Uvicorn | 8000 | 8002 |
| `db`    | PostgreSQL 16     | 5432 | — |

Agent Django API'ga `http://web:8000/api` orqali ulanadi.

---

## Docker bilan ishga tushirish (production)

```bash
# 1. Env fayllarni tayyorlang
cp .env.example .env
cp agent/.env.example agent/.env
# .env va agent/.env ni tahrirlang (SECRET_KEY, parollar, domenlar, Ollama)

# 2. Ishga tushiring
docker compose up -d --build

# 3. Superuser yaratish (ixtiyoriy)
docker compose exec web python manage.py createsuperuser
```

Migratsiya va `collectstatic` avtomatik bajariladi (entrypoint).

### Nginx (server tomonida — o'zingiz sozlaysiz)

```nginx
# Django API
location /api/    { proxy_pass http://127.0.0.1:8001; }
location /admin/  { proxy_pass http://127.0.0.1:8001; }
location /static/ { proxy_pass http://127.0.0.1:8001; }

# AI Agent
location /ai/     { proxy_pass http://127.0.0.1:8002; }
```

---

## Muhim env o'zgaruvchilar (`.env`)

| Kalit | Tavsif |
|-------|--------|
| `SECRET_KEY` | Django maxfiy kaliti (uzun tasodifiy satr) |
| `DEBUG` | `False` (production) |
| `ALLOWED_HOSTS` | `api.example.com,localhost,127.0.0.1,web` |
| `CORS_ALLOWED_ORIGINS` | Frontend domenlari |
| `POSTGRES_DB/USER/PASSWORD` | DB sozlamalari (bo'sh = SQLite) |

Agent uchun `agent/.env`: `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_API_KEY`.

---

## Lokal ishga tushirish (Docker'siz)

```bash
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver 8001

# Boshqa terminalda — agent
cd agent
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # tahrirlang
uvicorn main:app --port 8002 --reload
```
