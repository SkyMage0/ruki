# Свободные руки — биржа разнорабочих

MVP: Telegram-бот + веб-админка. Backend: FastAPI, БД: PostgreSQL, кэш/очереди: Redis. Мониторинг: Sentry, Prometheus, JSON-логи.

## Стек

- **Backend:** Python 3.11+, FastAPI (REST API)
- **Bot:** python-telegram-bot v20+
- **DB:** PostgreSQL 15+, SQLAlchemy 2.0, Alembic
- **Auth:** JWT + Telegram Login Widget
- **Cache/Queue:** Redis (rate limiting, уведомления)
- **Monitoring:** Sentry, Prometheus, structlog (JSON в stdout)
- **Deploy:** Docker + docker-compose

## Быстрый старт

1. Скопировать `.env.example` в `.env` и заполнить:
   - `TELEGRAM_BOT_TOKEN`
   - `ENCRYPTION_KEY` (сгенерировать: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`)
   - при необходимости `SENTRY_DSN`, `CORS_ORIGINS`

2. Запуск через Docker:

```bash
docker-compose up -d postgres redis
# Первый запуск: миграции
docker-compose run --rm api alembic upgrade head
# Запуск API и бота
docker-compose up -d api bot
```

3. Локально (без Docker):

```bash
python -m venv .venv
.venv\Scripts\activate   # или source .venv/bin/activate
pip install -r requirements.txt
# PostgreSQL и Redis должны быть запущены, в .env указаны DATABASE_URL, REDIS_URL
alembic upgrade head
uvicorn api.main:app --reload --port 8000
# В другом терминале:
python -m bot.main
```

## Эндпоинты API

- `GET /` — информация о сервисе
- `GET /health` — проверка БД и Redis
- `GET /ready` — readiness для k8s/docker
- `GET /metrics` — Prometheus-метрики
- `GET /admin/` — админ-панель (дашборд, города, верификация, пользователи, заказы)

## Бот

- `/start` — регистрация (телефон, город, роль)
- `/new_task` — создать заказ (город → категория → описание → адрес → оплата → подтверждение)
- `/my_tasks` — мои заказы (как заказчик / как исполнитель)
- `/tasks` — открытые заказы в городе пользователя
- `/profile` — профиль, рейтинг, верификация
- `/support` — связь с поддержкой

Отклик по заказу: кнопка «Откликнуться», при необходимости ввод своей цены. Заказчик получает уведомление с кнопками «Принять» / «Отклонить». После принятия обе стороны видят контакты (телефоны показываются только после принятия).

## Безопасность

- Телефоны и номера документов хранятся в БД в зашифрованном виде (Fernet). Ключ — в `ENCRYPTION_KEY`.
- Rate limiting в Redis: создание заказа (5/час), отклики (20/час), сообщения (30/мин), верификация (3/день).
- В логах и метриках нет телефонов и адресов, только ID.
- CORS настроен по `CORS_ORIGINS`.

## Метрики Prometheus

- `bot_commands_total{command="..."}` — счётчики команд
- `tasks_created_total{city="..."}` — созданные заказы по городам
- `bids_total` — отклики
- `active_users_gauge` — активные пользователи за последний час
- `http_requests_total`, `request_duration_seconds` — запросы к API

## Структура проекта

```
project/
├── bot/           # Telegram-бот (handlers, keyboards, middlewares)
├── api/           # FastAPI (health, metrics, admin routes)
├── core/          # Модели, схемы, сервисы, security, monitoring
├── admin/         # Шаблоны Jinja2 для админки
├── migrations/    # Alembic
├── docker-compose.yml
├── Dockerfile
├── .env.example
└── README.md
```

## Критерии приёмки

- Бот запускается и пишет в БД
- Телефоны в БД зашифрованы
- Rate limiting работает (Redis)
- При ошибке событие уходит в Sentry (если задан SENTRY_DSN)
- На `/metrics` доступны описанные метрики
- `docker-compose up` поднимает сервисы без ошибок
- Обработка ошибок с логированием, конфигурация через .env
