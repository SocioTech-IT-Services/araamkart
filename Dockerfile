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

# Railway injects PORT at runtime (often 8080). Middleware answers /_health/ before DB session.
CMD ["sh", "-c", "python manage.py migrate --noinput && exec gunicorn aaramkart.wsgi:application --bind 0.0.0.0:${PORT:-8080} --workers 2 --threads 4 --timeout 120 --graceful-timeout 30 --access-logfile - --error-logfile -"]
