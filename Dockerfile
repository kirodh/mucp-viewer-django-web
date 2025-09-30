# Dockerfile
FROM python:3.11-slim

# system deps for pillow/gdal etc - adapt if you need more (GDAL, libpq-dev, build-essential)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    libpq-dev \
    gcc \
    git \
    libjpeg-dev \
    zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

# Create app user
#ENV APP_HOME=/app
#RUN useradd --create-home --shell /bin/bash appuser
WORKDIR /app

# Copy dependency files first for better cache
COPY requirements.txt ./requirements.txt

# Install python deps
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r requirements.txt

## Copy project
#COPY src/ ./src/

## Keep a root-level start script and .env (compose mounts .env)
#COPY start.sh /start.sh
#RUN chmod +x /start.sh

## Create directories for static/media and give permissions
#RUN mkdir -p /vol/static /vol/media
#RUN chown -R appuser:appuser /vol/static /vol/media /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DJANGO_SETTINGS_MODULE=main.settings

EXPOSE 8000

# get the git mucp equations to install here
# Install your GitHub package
RUN pip install --no-cache-dir git+https://github.com/kirodh/mucp-algorithms-web.git

## default command uses start.sh which will run migrations + collectstatic + gunicorn
#CMD ["/start.sh"]
