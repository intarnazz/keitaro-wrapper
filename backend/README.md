# Keitaro wrapper

Обёртка над Keitaro Admin API на FastAPI. Сейчас реализовано: справочники (домены, группы, источники) и создание кампании с двумя потоками. Редактор существующей кампании (офферы, доли, черновики) в работе.

## Быстрый старт (Windows, PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install python-multipart   # для form-data; затем: pip freeze > requirements.txt
copy ..\.env.example .env      # затем впиши KEITARO_API_KEY
uvicorn app.main:app --reload
```

- Swagger (интерактивная документация): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Переменные окружения (`backend/.env`)

| Переменная | Обязательна | Описание |
|---|---|---|
| `KEITARO_URL` | да | Базовый URL Admin API, например `https://tlgk.host/admin_api/v1` |
| `KEITARO_API_KEY` | да | Ключ из админки Keitaro, отправляется заголовком `Api-Key` |
| `DATABASE_URL` | нет | По умолчанию `sqlite:///./app.db` |

Ключ остаётся только на бэкенде и клиенту не передаётся.

## Формат ответов

Все ответы, успешные и с ошибкой, приходят в одном формате:

```json
{
  "success": true,
  "message": "success",
  "data": {}
}
```

| Поле | Тип | Описание |
|---|---|---|
| `success` | boolean | `true` при успехе, `false` при ошибке |
| `message` | string | `"success"` либо краткий текст ошибки |
| `data` | any | Полезная нагрузка. При ошибке: детали или `null` |

HTTP-статус при этом тоже настоящий (`201`, `422`, `502` и т. д.), так что клиент может опираться и на него, и на `success`.

## Ошибки

| Код | Когда | `message` | `data` |
|---|---|---|---|
| `422` | Неверный запрос к нашему API | `Validation error: ...` | `errors`, `required_fields`, `optional_fields` |
| `400`, `404`, `422` | Keitaro отклонил запрос, код передаётся как есть | `Keitaro: <краткий текст>` | `keitaro_status`, `detail` (полный текст Keitaro, до 500 символов) |
| `502` | Keitaro недоступен или вернул другую ошибку (401, 403, 5xx) | `Keitaro: <краткий текст>` | `keitaro_status`, `detail` |
| `404`, `405` | Нет такого маршрута или метод не разрешён | `Not Found`, `Method Not Allowed` | `null` |
| `500` | Непредвиденная ошибка сервера | `Internal server error` | `null` |

Если ошибка пришла с кодом 422, отличить валидацию от ответа Keitaro можно по `data`: у валидации есть `errors`, у Keitaro есть `keitaro_status`.

### Ошибка валидации (422)

Пример: запрос без тела.

```json
{
  "success": false,
  "message": "Validation error: missing required fields: name, geo, offer_id",
  "data": {
    "errors": [
      {"type": "missing", "loc": ["body", "name"], "msg": "Field required", "input": null},
      {"type": "missing", "loc": ["body", "geo"], "msg": "Field required", "input": null}
    ],
    "required_fields": ["name", "geo", "offer_id"],
    "optional_fields": ["alias", "domain_id", "group_id", "traffic_source_id"]
  }
}
```

Если тело передано частично, в `errors` останутся только недостающие или неверные поля, а `required_fields` и `optional_fields` содержат полный список.

### Ошибка Keitaro

Пример: неверный `offer_id`.

```json
{
  "success": false,
  "message": "Keitaro: Offer 999 not found",
  "data": {"keitaro_status": 422, "detail": "{\"error\":\"Offer 999 not found\"}"}
}
```

---

## Эндпоинты

### `GET /api/health`

Проверка, что сервис запущен.

**Ответ 200:**

```json
{"success": true, "message": "success", "data": {"ok": true}}
```

---

### `GET /api/domains`

Список доменов Keitaro (проксируется `GET /domains`).

**Ответ 200:** `data` содержит массив доменов. Нужные поля: `id`, `name`, `state`.

```json
{"success": true, "message": "success", "data": [{"id": 1, "name": "example.com", "state": "active"}]}
```

---

### `GET /api/groups`

Группы кампаний (проксируется `GET /groups?type=campaigns`).

**Ответ 200:** `data` содержит массив групп. Нужные поля: `id`, `name`.

```json
{"success": true, "message": "success", "data": [{"id": 2, "name": "Default", "position": 1, "type": "campaigns"}]}
```

---

### `GET /api/traffic-sources`

Источники трафика (проксируется `GET /traffic_sources`).

**Ответ 200:** `data` содержит массив источников. Нужные поля: `id`, `name`.

```json
{"success": true, "message": "success", "data": [{"id": 3, "name": "Facebook", "state": "active"}]}
```

---

### `POST /api/campaigns`

Создаёт кампанию и два потока.

**Формат тела.** Принимаются три варианта, поля одинаковые:

| Content-Type | Как отправить |
|---|---|
| `application/json` | raw JSON |
| `multipart/form-data` | Postman: Body → form-data |
| `application/x-www-form-urlencoded` | Postman: Body → x-www-form-urlencoded |

В формах пустые значения считаются «не переданы» (удобно для необязательных полей), файлы игнорируются. Для JSON и форм нужен заголовок `Content-Type`: Postman и curl ставят его сами. Другой тип тела вернёт 422.

**Поля:**

| Поле | Тип | Обязательно | Описание |
|---|---|---|---|
| `name` | string | да | Название кампании, 1 до 255 символов, пробелы по краям обрезаются |
| `geo` | string | да | Код страны, две латинские буквы (`au`, `AU`). Регистр приводится к верхнему |
| `offer_id` | integer | да | ID оффера в Keitaro, больше 0. Существование оффера не проверяется |
| `domain_id` | integer | нет | ID домена. Если не передан, берётся первый активный домен Keitaro |
| `group_id` | integer | нет | ID группы кампаний. Если не передан, берётся первая группа |
| `traffic_source_id` | integer | нет | ID источника трафика. Если не передан, берётся первый источник |
| `alias` | string | нет | Алиас кампании. Если не передан, генерируется из названия с суффиксом (`my-test-a1b2c3`) |

**Пример (JSON):**

```bash
curl -X POST http://localhost:8000/api/campaigns \
  -H "Content-Type: application/json" \
  -d '{
    "name": "test_campaign",
    "geo": "au",
    "offer_id": 5
  }'
```

**Пример (form-data):**

```bash
curl -X POST http://localhost:8000/api/campaigns \
  -F name=test_campaign -F geo=au -F offer_id=5
```

**Ответ 201:**

```json
{
  "success": true,
  "message": "success",
  "data": {
    "campaign_id": 216813,
    "alias": "test-campaign-a1b2c3",
    "domain_id": 10,
    "group_id": 2,
    "traffic_source_id": 3,
    "streams": [4501, 4502]
  }
}
```

Поля `data`:

| Поле | Описание |
|---|---|
| `campaign_id` | ID созданной кампании в Keitaro |
| `alias` | Алиас кампании (переданный или сгенерированный) |
| `domain_id`, `group_id`, `traffic_source_id` | Значения, с которыми кампания реально создана (переданные или выбранные автоматически) |
| `streams` | ID потоков: сначала поток по гео, затем поток с оффером |

**Что создаётся в Keitaro:**

0. Если `domain_id`, `group_id` или `traffic_source_id` не переданы, запрашиваются `GET /domains`, `GET /groups?type=campaigns`, `GET /traffic_sources` и берётся первый элемент (для доменов и источников первый со статусом `active`). Это происходит до создания кампании.
1. `POST /campaigns` с `name`, `alias`, `domain_id`, `group_id`, `traffic_source_id`.
2. `POST /streams`, **поток 1** (`position: 1`): фильтр страны `accept` со значением `geo`, редирект на `https://www.google.com`.
3. `POST /streams`, **поток 2** (`position: 2`): без фильтров, ловит всех, кого не поймал первый. Оффер `offer_id` с долей 100%. Поле `action_type` обязательно для любого потока, поэтому передаётся и здесь (`http`), хотя при схеме `landings` трафик идёт на оффер.

**Откат.** Если любой из двух потоков не создался, кампания сначала переименовывается в `<имя> (rollback xxxxxx)` (Keitaro требует уникальное имя даже среди архивных, иначе повторный запрос с тем же именем вернул бы `Name has already been used in the archive`), затем удаляется (`DELETE /campaigns/{id}`, в Keitaro это перенос в архив). Клиент получает исходную ошибку Keitaro. Если сам откат не удался, исходная ошибка всё равно возвращается, но кампания может остаться в Keitaro.

**Ошибки:**

| Код | Причина |
|---|---|
| `422` (есть `errors`) | Не хватает полей или значения неверны, см. «Ошибка валидации» |
| `400`, `404`, `422` (есть `keitaro_status`) | Keitaro отклонил запрос, например неверный `offer_id` или имя уже занято (`Name has already been used in the archive`) |
| `400` (`data: null`) | В Keitaro нет ни домена, ни группы, ни источника, и соответствующий id не передан. Кампания не создаётся |
| `502` | Keitaro недоступен, неверный `Api-Key` и т. п. |

**Минимальный запрос** содержит только `name`, `geo`, `offer_id`. Чтобы выбрать другие домен, группу или источник, получи списки через `GET /api/domains`, `GET /api/groups`, `GET /api/traffic-sources` и передай нужные id.

---

## Настройка потоков

Значения, зависящие от версии Keitaro, вынесены в константы в начале `backend/app/services/campaigns.py`:

```python
GEO_FILTER_NAME = "country"
REDIRECT_ACTION_TYPE = "http"
REDIRECT_URL = "https://www.google.com"
```

Допустимые значения смотри в ответах Keitaro `GET /stream_filters` и `GET /streams_actions`.

## Структура

```
backend/app/
├── main.py                # маршруты, единый формат ответов, обработчики ошибок
├── config.py              # настройки из .env
├── db.py                  # engine, сессия SQLAlchemy
├── schemas.py             # Pydantic-схемы (ApiResponse, CampaignCreate, ...)
├── keitaro/client.py      # клиент Keitaro Admin API (httpx)
└── services/campaigns.py  # создание кампании, двух потоков, откат
```

## Архивные кампании Keitaro

`DELETE /campaigns/{id}` в Keitaro переносит кампанию в архив, а имя остаётся занятым. Если нужно освободить имя вручную (напрямую в Keitaro Admin API):

| Что | Метод |
|---|---|
| Список архивных кампаний | `GET /campaigns/deleted` |
| Вернуть из архива | `POST /campaigns/{id}/restore` |
| Переименовать | `PUT /campaigns/{id}` с `{"name": "..."}` |
