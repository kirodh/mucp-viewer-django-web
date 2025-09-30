#!/usr/bin/env bash
set -e

# environment defaults
: "${GUNICORN_TIMEOUT:=600}"
: "${WEB_CONCURRENCY:=3}"
: "${GUNICORN_THREADS:=4}"
: "${DJANGO_MANAGE:=src/manage.py}"

echo "Starting container with DJANGO_SETTINGS_MODULE=${DJANGO_SETTINGS_MODULE} ..."
echo "WEB_CONCURRENCY=${WEB_CONCURRENCY}, GUNICORN_TIMEOUT=${GUNICORN_TIMEOUT}, THREADS=${GUNICORN_THREADS}"

# Run migrations & collectstatic (non-interactive)
cd src

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

# Start Gunicorn
echo "Starting Gunicorn..."
# Calculate workers: allow overriding via WEB_CONCURRENCY env var
exec gunicorn main.wsgi:application\
    --chdir /app/src \
    --bind 0.0.0.0:8000 \
    --workers ${WEB_CONCURRENCY} \
    --threads ${GUNICORN_THREADS} \
    --timeout ${GUNICORN_TIMEOUT} \
    --worker-class gthread \
    --log-level info \
    --access-logfile '-' \
    --error-logfile '-'
