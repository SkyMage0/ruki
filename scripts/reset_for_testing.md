# Сброс БД и Redis для тестирования

Из папки проекта (`Ruki`) выполните:

**1. Очистить таблицы (данные удаляются, схема остаётся):**
```powershell
docker-compose exec postgres psql -U postgres -d ruki -c "TRUNCATE verification_requests, reviews, bids, tasks, users, cities RESTART IDENTITY CASCADE;"
```

**2. Сбросить лимиты в Redis:**
```powershell
docker-compose exec redis redis-cli FLUSHDB
```

**3. Добавить города для регистрации (если нужно):**
```powershell
docker-compose exec postgres psql -U postgres -d ruki -c "INSERT INTO cities (name, timezone, is_active) VALUES ('Москва', 'Europe/Moscow', true), ('Санкт-Петербург', 'Europe/Moscow', true);"
```

После этого можно снова проходить /start, создавать заказы без учёта лимита.
