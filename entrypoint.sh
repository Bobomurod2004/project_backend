#!/bin/sh
set -e

# Postgres ishlatilsa — tayyor bo'lguncha kutamiz
if [ -n "$POSTGRES_DB" ]; then
  echo "PostgreSQL kutilmoqda ($POSTGRES_HOST:${POSTGRES_PORT:-5432})..."
  until python -c "import socket,os,sys; s=socket.socket(); s.settimeout(2); \
    s.connect((os.getenv('POSTGRES_HOST','db'), int(os.getenv('POSTGRES_PORT','5432')))); \
    s.close()" 2>/dev/null; do
    sleep 1
  done
  echo "PostgreSQL tayyor."
fi

echo "Migratsiyalar..."
python manage.py migrate --noinput

echo "Statik fayllar..."
python manage.py collectstatic --noinput

echo "Gunicorn ishga tushmoqda..."
exec gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers "${GUNICORN_WORKERS:-3}" \
  --timeout 120
