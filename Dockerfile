# Multistage build for Python
FROM python:3.11-slim as builder

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PIP_NO_CACHE_DIR=1

RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-deps -w /wheels -r requirements.txt

FROM python:3.11-slim

WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PATH="/app/.venv/bin:$PATH"

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /wheels /wheels
RUN pip install --no-cache /wheels/* && rm -rf /wheels

COPY . .
# Default: run API; override CMD for bot
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
