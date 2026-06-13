# Двухсервисная система LLM-консультаций

Распределённая система из двух независимых сервисов: один отвечает за аутентификацию и выпуск JWT, второй — за функциональность LLM-консультаций через Telegram-бота. Сервисы разделены по принципу ответственности: бот ничего не знает о пользователях и паролях и доверяет только корректно подписанному и не истёкшему JWT, который выпускает сервис авторизации.

## Архитектура

Система состоит из двух логически и технически независимых сервисов.

**Auth Service (FastAPI)** — единственное место, где создаются пользователи и выпускаются токены. Предоставляет HTTP-API и Swagger. Хранит пользователей в SQLite, пароли — только в виде bcrypt-хеша. Выдаёт JWT с полями `sub`, `role`, `iat`, `exp`.

**Bot Service (aiogram + Celery)** — Telegram-бот. Принимает JWT от пользователя, проверяет его подпись и срок действия (без обращения к базе Auth Service), и при валидном токене ставит запрос к LLM в очередь. Сам токены не создаёт и пользователей не хранит.

Связь между сервисами обеспечивается общим секретом `JWT_SECRET` (алгоритм HS256): Auth Service подписывает токен, Bot Service проверяет подпись тем же секретом.

### Роли инфраструктурных компонентов

- **RabbitMQ** — брокер задач Celery. Bot Service публикует в него задачу «LLM-запрос».
- **Celery worker** — забирает задачу из очереди, обращается к LLM (OpenRouter) и отправляет ответ пользователю в Telegram.
- **Redis** — backend результатов Celery, а также хранилище JWT-токенов, привязанных к Telegram `user_id` (ключ `token:<user_id>`).
- **OpenRouter** — внешний провайдер LLM.

Запросы к LLM не выполняются в хэндлерах бота — это гарантирует, что бот остаётся отзывчивым, а долгие операции не блокируют обработку новых сообщений.

## Пользовательский сценарий

1. Пользователь регистрируется в Auth Service через Swagger и получает JWT (`/auth/register` → `/auth/login`).
2. Пользователь отправляет токен боту командой `/token <jwt>`. Бот сохраняет токен в Redis, привязав его к своему Telegram `user_id`.
3. Пользователь пишет боту обычное сообщение. Бот проверяет наличие и валидность токена, публикует задачу в RabbitMQ и отвечает «Запрос принят».
4. Celery worker обрабатывает задачу, обращается к LLM и присылает ответ пользователю.
5. Без токена или с невалидным/истёкшим токеном бот отказывает в доступе и просит авторизоваться через Auth Service.

## Структура проекта

```
llm-project/
├── docker-compose.yml          # rabbitmq, redis, auth, bot, worker
│
├── auth_service/               # СЕРВИС 1 — выпуск JWT (FastAPI)
│   ├── Dockerfile
│   ├── .dockerignore
│   ├── .env
│   ├── pyproject.toml
│   ├── pytest.ini
│   ├── app/
│   │   ├── main.py             # сборка FastAPI, /health, создание таблиц
│   │   ├── core/               # config, security (хеши + JWT), exceptions
│   │   ├── db/                 # base, session, models (User)
│   │   ├── schemas/            # RegisterRequest, TokenResponse, UserPublic
│   │   ├── repositories/       # доступ к БД (users)
│   │   ├── usecases/           # бизнес-логика: register/login/me
│   │   └── api/                # deps, routes_auth, router
│   └── tests/                  # unit (хеши/JWT) + интеграционные (HTTP)
│
└── bot_service/                # СЕРВИС 2 — Telegram-бот (aiogram + Celery)
    ├── Dockerfile
    ├── .dockerignore
    ├── .env
    ├── pyproject.toml
    ├── pytest.ini
    ├── app/
    │   ├── main.py             # FastAPI /health
    │   ├── run_bot.py          # запуск бота (polling)
    │   ├── core/               # config, jwt (только проверка токена)
    │   ├── infra/              # redis, celery_app (broker=RabbitMQ, backend=Redis)
    │   ├── services/           # openrouter_client
    │   ├── tasks/              # llm_tasks (Celery-задача llm_request)
    │   └── bot/                # dispatcher, handlers (/token, обработка текста)
    └── tests/                  # JWT, моки хэндлеров (fakeredis), respx
```

## Запуск

### Требования

- Docker Desktop
- Для запуска тестов локально — менеджер `uv`

### Настройка переменных окружения

В `bot_service/.env` нужно заполнить:

```
TELEGRAM_BOT_TOKEN=<токен от @BotFather>
OPENROUTER_API_KEY=<ключ с openrouter.ai>
OPENROUTER_MODEL=meta-llama/llama-3.3-70b-instruct:free
```

Значение `JWT_SECRET` в `auth_service/.env` и `bot_service/.env` должно совпадать.

### Старт

Из корня проекта:

```
docker compose up --build
```

После старта будут доступны:

- Swagger Auth Service — http://127.0.0.1:8000/docs
- RabbitMQ Management UI — http://localhost:15672 (логин `guest`, пароль `guest`)

Остановка: `Ctrl+C`, затем `docker compose down`.

## Тесты

Тесты используют моки (`fakeredis`, `pytest-mock`, `respx`) и in-memory SQLite, поэтому реальные Redis, RabbitMQ и внешние сервисы для них не нужны.

Auth Service:

```
cd auth_service
uv run pytest -v
```

Bot Service:

```
cd bot_service
uv run pytest -v
```

## API Auth Service

| Метод | Путь             | Описание                          |
|-------|------------------|-----------------------------------|
| POST  | `/auth/register` | Создаёт пользователя              |
| POST  | `/auth/login`    | Возвращает JWT                    |
| GET   | `/auth/me`       | Профиль по валидному JWT          |
