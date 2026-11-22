# Keitaro wrapper

Тестовое задание: обёртка над Keitaro (рекламный трекер). Две части:

1. **Создатель кампаний.** Форма `name`, `geo`, `offer` создаёт в Keitaro кампанию с двумя потоками: первый ловит всех из страны и отправляет на Google, второй отправляет на выбранный оффер. У кампании настроены домен, группа и источник трафика.
2. **Редактор существующей кампании.** Список кампаний из Keitaro, добавление и удаление офферов в потоках с пересчётом долей, закрепление долей, черновик с публикацией (`Push to Keitaro`) и отменой (`Cancel`), архив удалённых офферов (`Bring back`).

Стек: FastAPI + SQLAlchemy + Alembic (бэкенд), Vue 3 + TypeScript (strict) + vue-router + Tailwind CSS 4 (фронтенд).

```
backend/     FastAPI, подробная документация API: backend/README.md
forntend/    Vue 3 (имя папки как в репозитории), правила кода: forntend/README.md
```

## Требования

- Python 3.12
- Node.js 22.18+ (или 24.12+) и yarn

## Запуск

### 1. Бэкенд (PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env      # впиши KEITARO_URL и KEITARO_API_KEY
alembic upgrade head        # миграции
uvicorn app.main:app --reload
```

Swagger: http://localhost:8000/docs

**Если Keitaro недоступен**, в `backend/.env` поставь `KEITARO_FAKE=true`: бэкенд будет работать с Keitaro в памяти (демо-кампания `Demo AU` с тремя потоками, 12 офферов). Всё приложение, включая редактор, работает так же, как с настоящим Keitaro.

### 2. Фронтенд

```powershell
cd forntend
yarn
yarn dev
```

Откроется http://localhost:5173. Запросы `/api` проксируются на `http://localhost:8000` (см. `vite.config.ts`), поэтому CORS настраивать не нужно. Другой адрес бэкенда: `VITE_API_URL` в `forntend/.env`.

Страницы:

| Адрес | Что |
|---|---|
| `/` | Создание кампании |
| `/campaigns` | Список кампаний Keitaro |
| `/campaigns/:id` | Редактор выбранной кампании |

### 3. Проверки

```powershell
cd backend;  pytest          # тесты бэкенда (фейковый Keitaro, БД в памяти)
cd forntend; yarn type-check # vue-tsc, строгий TypeScript
cd forntend; yarn build      # типы + продакшен-сборка
```

## Миграции

Alembic, конфигурация в `backend/alembic/`, URL берётся из `DATABASE_URL`.

```powershell
alembic upgrade head                           # применить
alembic downgrade -1                           # откатить последнюю
alembic revision --autogenerate -m "описание"  # создать после правки backend/app/models.py
```

## Как устроен редактор

Правки хранятся у нас в БД как черновик и уходят в Keitaro только по `Push`. Для каждого оффера в потоке хранится желаемое состояние (статус, доля, закрепление) и снимок Keitaro (после последнего Fetch или Push). По разнице этих двух состояний определяется, что поток «жёлтый», и что откатывает `Cancel`. Подробности и все эндпоинты: `backend/README.md`.

## Что не проверено на настоящем Keitaro

Keitaro был недоступен (`403`), поэтому интеграция проверена на фейковом Keitaro, который повторяет формат API по спецификации `openapi.yaml`. Значения, которые нужно сверить при первом запуске с настоящим Keitaro (`GET /stream_filters`, `GET /streams_actions`):

- `backend/app/services/campaigns.py`: `GEO_FILTER_NAME`, `REDIRECT_ACTION_TYPE`, `schema: "landings"` для потока с оффером;
- формат `PUT /streams/{id}` при публикации: отправляются только `offers`.
