# CLAUDE.md — заметки для себя

Проект: тестовое задание «обёртка над Keitaro». Пользователь проходит собеседование, срок 5 дней. Язык общения: русский.

## ТЗ кратко
1. **Создаватор кампаний.** Принимает name, geo, offer_id. Создаёт кампанию (домен, группа, источник) и 2 потока: поток 1 страна -> Google, поток 2 остальные -> оффер.
2. **Редактор кампании** (по видео): добавление и удаление офферов в потоке с пересчётом долей, pin доли, черновик (жёлтый поток), Push, Cancel, архив удалённых (Bring back), Fetch streams. Подробная логика в разделе «Редактор» ниже.
3. Стек: FastAPI + SQLAlchemy, фронт любой (выбран Vue 3 + TS + Vite + vue-router, без Pinia). Сдача: GitHub, README с запуском и миграциями.

## Решения пользователя (не переспрашивать)
- Создание кампании идёт через FastAPI, без черновиков и без БД.
- Оффер не проверяем (`GET /offers/{id}` не вызываем), ошибку отдаёт Keitaro.
- Нет `DEFAULT_*_ID` в конфиге. Обязательные поля тела: только `name`, `geo`, `offer_id` (как в форме ТЗ). `domain_id`, `group_id`, `traffic_source_id` необязательны: если не переданы, бэкенд берёт первый (активный) элемент справочников Keitaro до создания кампании. Нет значений -> 400, ничего не создаётся. (Раньше они были обязательными, поменял по просьбе пользователя.)
- Работать поверх его оригинальных файлов, а не переписывать структуру. Маршруты живут в `main.py`, без `routers/`.
- Он сам добавляет `.env.example`.
- Окончания строк в его файлах CRLF, сохранять.
- Тело `POST /api/campaigns` принимается как JSON, multipart/form-data и x-www-form-urlencoded (он тестирует form-data в Postman). Реализовано зависимостью `campaign_payload` в `main.py`; нужен пакет `python-multipart` (сказать ему установить и обновить requirements.txt). Пустые значения формы = не передано. Новые POST-маршруты делать так же.
- Все ответы в формате `{"success": bool, "message": "success" | краткий текст ошибки, "data": ...}`. HTTP-статусы остаются настоящими. Новые маршруты возвращать как `ApiResponse(data=...)` с `response_model=ApiResponse[...]`, ошибки через `fail()` в `main.py`.
- Отдавать результат архивом `app.zip` (папка `app/`), README.md и CLAUDE.md отдельными файлами.
- Windows 10, PowerShell, без Cursor.

## Состояние
Готово:
- `GET /api/health`, `/api/domains`, `/api/groups`, `/api/traffic-sources` (протестированы им).
- `POST /api/campaigns` (минимум name, geo, offer_id): кампания + 2 потока + откат (DELETE кампании) при ошибке потока. Проверено на моке, на реальном Keitaro не проверено.
- Единый конверт ответов + обработчики: KeitaroError, RequestValidationError, HTTPException, Exception (все в `main.py`).
- Обработчик 422: в `data` лежат `errors`, `required_fields`, `optional_fields`, при пустом теле `errors` раскладывается по полям.
- README.md с полной документацией API.

Не проверено (взято по памяти, сверить с `GET /stream_filters` и `GET /streams_actions`):
- `GEO_FILTER_NAME = "country"`, `REDIRECT_ACTION_TYPE = "http"`.
- `alias` по спеке обязателен, хотя в описании сказано «пусто = автогенерация». Мы всегда его шлём.
- Тип второго потока (`regular` без фильтров) и `schema: "landings"` для офферов. Keitaro требует `action_type` у любого потока (422 `Action Type is required`), у потока 2 стоит `http` как заглушка, что Keitaro на это скажет, не проверено.

TODO:
- Модели SQLAlchemy 2.0 + Alembic для редактора, функция `distribute()` + тесты.
- Эндпоинты редактора, Fetch, Push, Cancel.
- Vue-фронт (3 экрана: создание, список кампаний, редактор).
- Dockerfile и docker-compose, обновить README (миграции).

## Заметки по технике
- Keitaro Admin API: base `/admin_api/v1`, заголовок `Api-Key`. Спека лежала в `openapi.yaml` (загружал пользователь).
- `GET /groups` требует `?type=campaigns`.
- `DELETE /campaigns/{id}` переносит в архив, не удаляет насовсем. Имя остаётся занятым и в архиве (422 `Name has already been used in the archive`). Поэтому откат сначала переименовывает кампанию (PUT, не проверено на реальном API, ошибки игнорируются), потом удаляет. Архив: `GET /campaigns/deleted`, `POST /campaigns/{id}/restore`. `clean_archive` у пользователя закрыт.
- Офферы потока: `offers: [{offer_id, share:int, state}]`, `share` целое. Список офферов только целиком (`GET /offers`), поиска нет.
- FastAPI 0.165 / Pydantic v2: тип тела в обработчике ищется через `route.body_field.field_info.annotation` (`type_` пустой).
- Ошибки Keitaro: 400/404/422 проксируются, остальное 502; `data = {keitaro_status, detail}`, `message = "Keitaro: <кратко>"` (из JSON-поля error/message/detail). Валидация: `data.errors`. Различать по наличию `errors` / `keitaro_status`.
- Тест на моке: `httpx.MockTransport` через параметр `transport` в `KeitaroClient`.

## Редактор (дизайн, по видео)
Модель: `streams(keitaro_stream_id, campaign_id, name)` и `stream_offers(stream_id, offer_id, offer_name, status active|removed, share, pinned, base_status, base_share)`.
`base_*` снимок после последнего Fetch/Push. Поток «жёлтый» (dirty), если `(status, share) != (base_status, base_share)` у любого оффера.
- Fetch: обновляет `base_*`, у потоков без офферов только имя. Оффер, пропавший в Keitaro, получает `removed`.
- Add: строка с `base_status=NULL`, пересчёт долей. Remove: `removed`, доля 0. Bring back: `active`.
- Push: `PUT /streams/{id}` с активными офферами, затем `base_* = текущее`. Запретить push без активных офферов.
- Cancel: `base_status IS NULL` -> удалить строку, иначе откат к `base_*`. Pin не откатывается.
- `distribute()`: чистая функция. Закреплённые не трогаем, остаток делим поровну целыми (первым достаётся +1). Сумма закреплённых > 100 -> ошибка.
