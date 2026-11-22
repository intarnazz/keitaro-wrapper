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

---

## Обновление: ТЗ закрыто целиком (редактор + фронтенд)

Контекст: Keitaro был недоступен (403 nginx), поэтому всё проверено на фейке `app/keitaro/fake.py` (KEITARO_FAKE=true). Пользователь сдаёт тестовое, проект лежит в `keitaro-wrapper/` (папка фронтенда называется `forntend`, не переименовывать без просьбы).

Бэкенд (готово, 29 тестов):
- `models.py` Stream, StreamOffer (желаемое состояние + снимок base_*). `services/distribute.py`, `services/editor.py`, `routers/editor.py`, `services/offers.py` (кэш списка офферов 60 с).
- Alembic: `alembic/versions/0001_...`. `requirements.txt` перезаписан в UTF-8 (у пользователя был UTF-16 из PowerShell), добавлен python-multipart.
- Решения: удаление оффера снимает pin; draft-added оффер при remove забывается; Fetch сохраняет черновик и перебалансирует сумму, если состав изменился; push без активных офферов или при сумме != 100 запрещён; потоки без офферов не редактируются.
- Ошибки Keitaro в формате полей превращаются в `Keitaro: name: Name has already been used`.

Фронтенд (`forntend/`, vue-tsc и vite build проходят):
- Правила пользователя для слоя `src/api`: класс = источник типа (без types.ts), билдер `DefaultX`, всё через геттеры/сеттеры, закрытый `init` (ленивые геттеры возвращают null и запускают загрузку через `Loader`), действия через `Task`. Подробно в `forntend/README.md`.
- Стили: Tailwind 4 + scoped sass; глобальный sass пользователя перебивает слои Tailwind (input/button/select, `.border`).
- Проверено скриптом-смоуком на живом бэкенде: ленивые getters, add/cancel/pin/remove/push/restore, ошибки, форма.
- Браузера в песочнице нет: визуально UI не проверялся.

Не проверено на реальном Keitaro: названия фильтра/действия (country, http), PUT /streams/{id} только с offers, формат offers в GET потока.
- Форма создания: поле Offer это выпадающий список с поиском (`components/ui/OfferSelect.vue`, использует `OfferSearch`), `CampaignForm.offer_id` теперь `number | null`, а не строка.
