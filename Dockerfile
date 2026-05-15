# Railway builds with Dockerfile when present (more reliable than Railpack start heuristics).
FROM python:3.12-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpq5 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

# Migrations run in Railway preDeploy (see railway.json) so this process binds quickly for health checks.
# gthread is required when using --threads (sync worker ignores / may reject --threads on some gunicorn versions).
CMD ["sh", "-c", "exec gunicorn aaramkart.wsgi:application --bind 0.0.0.0:${PORT:-8080} --worker-class gthread --workers 2 --threads 4 --timeout 120 --graceful-timeout 30 --access-logfile - --error-logfile -"]
