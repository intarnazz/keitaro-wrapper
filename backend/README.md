# Keitaro wrapper

Обёртка над Keitaro Admin API на FastAPI: справочники, создание кампании с двумя потоками и редактор офферов существующей кампании (черновик, доли, закрепление, публикация).

## Быстрый старт (Windows, PowerShell)

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env          # затем впиши KEITARO_URL и KEITARO_API_KEY
alembic upgrade head            # миграции: создаёт app.db с таблицами редактора
uvicorn app.main:app --reload
```

- Swagger (интерактивная документация): http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

### Миграции

Схема БД (потоки и офферы редактора) создаётся Alembic. После `git pull` с новыми миграциями выполни `alembic upgrade head`.

```powershell
alembic upgrade head                                   # применить все миграции
alembic downgrade -1                                   # откатить последнюю
alembic revision --autogenerate -m "описание"          # новая миграция после правки app/models.py
alembic check                                          # модели и миграции совпадают?
```

Без выполненных миграций эндпоинты редактора вернут 500 (`no such table`).

### Работа без Keitaro (фейковый режим)

Если Keitaro недоступен, поставь в `.env` `KEITARO_FAKE=true`. Бэкенд будет работать с Keitaro в памяти (данные живут, пока запущен процесс): 12 офферов, домены, группы, источники и демо-кампания `Demo AU` (id 1001) с тремя потоками, как в видео из ТЗ. Фейк повторяет формат API и ошибки Keitaro (уникальное имя, в том числе в архиве, обязательные поля потока).

### Тесты

```powershell
pytest
```

Тесты используют фейковый Keitaro и БД в памяти, в настоящий Keitaro не ходят.

### Переменные окружения (`backend/.env`)

| Переменная | Обязательна | Описание |
|---|---|---|
| `KEITARO_URL` | да (если не `KEITARO_FAKE`) | Базовый URL Admin API, например `https://tlgk.host/admin_api/v1` |
| `KEITARO_API_KEY` | да (если не `KEITARO_FAKE`) | Ключ из админки Keitaro, отправляется заголовком `Api-Key` |
| `DATABASE_URL` | нет | По умолчанию `sqlite:///./app.db` |
| `KEITARO_FAKE` | нет | `true`: Keitaro в памяти вместо настоящего |
| `CORS_ORIGINS` | нет | JSON-список разрешённых источников, по умолчанию `["http://localhost:5173"]`. Через прокси Vite CORS не нужен |

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

---

## Редактор кампании

Редактор работает с **черновиком**: правки хранятся у нас в БД и попадают в Keitaro только после `push`. Состояние потока:

- `dirty: true` (в интерфейсе «жёлтый»): есть неопубликованные изменения;
- оффер `status: "removed"`: удалён из потока (серый, доля 0%, лежит в архиве и его можно вернуть);
- оффер `pinned: true`: его доля закреплена и не меняется при пересчёте;
- `is_new: true`: оффер добавлен в черновике, в Keitaro его ещё нет.

Доли целые, сумма активных всегда 100%: остаток делится поровну между незакреплёнными, лишние единицы достаются первым (три оффера: 34/33/33).

Все эндпоинты потока возвращают поток целиком (`StreamView`):

```json
{
  "success": true,
  "message": "success",
  "data": {
    "id": 2,
    "keitaro_stream_id": 5002,
    "campaign_id": 1001,
    "name": "Offers",
    "position": 2,
    "is_editable": true,
    "dirty": true,
    "total_share": 100,
    "offers": [
      {"offer_id": 1, "name": "Casino Alpha", "status": "active", "share": 25, "pinned": true, "is_new": false, "changed": true},
      {"offer_id": 2, "name": "Crypto Beta", "status": "removed", "share": 0, "pinned": false, "is_new": false, "changed": true}
    ]
  }
}
```

| Поле потока | Описание |
|---|---|
| `id` | ID потока у нас (используется во всех путях ниже) |
| `keitaro_stream_id` | ID потока в Keitaro |
| `is_editable` | `false`, если в потоке нет офферов. Такие потоки только показываются, их содержимое (фильтры, редирект) не разбирается |
| `dirty` | Есть неопубликованные изменения |
| `total_share` | Сумма долей активных офферов |
| `offers[].changed` | Оффер отличается от Keitaro |

Активные офферы идут первыми, удалённые в конце.

### `GET /api/campaigns`

Список кампаний Keitaro (без архивных). `data`: массив `{id, name, alias, state}`.

### `GET /api/campaigns/{campaign_id}`

Одна кампания: `{id, name, alias, state}`. Ошибка Keitaro (например, 404) передаётся как есть.

### `POST /api/campaigns/{campaign_id}/fetch`

**Fetch streams.** Загружает потоки кампании из Keitaro и сводит их с локальным состоянием. `data`: массив `StreamView`.

- Потоки без офферов сохраняются как потоки, их содержимое не разбирается.
- Неопубликованные правки не теряются: обновляется только снимок Keitaro. Если сумма долей черновика при этом перестала быть 100%, она пересчитывается.
- Оффер, который мы знали, но которого больше нет в Keitaro, получает статус `removed` (как будто удалён вручную) и доступен для `restore`.
- Новые офферы из Keitaro добавляются.
- Потоки, удалённые в Keitaro, удаляются и у нас.

### `GET /api/campaigns/{campaign_id}/streams`

Локальное состояние потоков (с черновиками), без обращения к Keitaro. До первого `fetch` вернёт пустой массив.

### `GET /api/offers?q=&limit=20`

Поиск офферов Keitaro для выбора. `q`: ID (точное совпадение) или часть названия, без регистра. Пустой `q`: первые офферы. `limit`: 1 до 100. Список офферов Keitaro кэшируется на минуту, потому что у Keitaro нет поиска. `data`: массив `{id, name, state}`.

### `POST /api/streams/{stream_id}/offers`

Добавляет оффер в черновик и пересчитывает доли. Тело: `{"offer_id": 4}`. Если оффер в архиве потока, он возвращается (как `restore`). Существование оффера проверяет Keitaro (`GET /offers/{id}`), его ошибка передаётся как есть.

| Код | Причина |
|---|---|
| `404` | Поток не найден (сначала `fetch`) или оффера нет в Keitaro |
| `409` | Оффер уже в потоке, или в потоке нет офферов |

### `POST /api/streams/{stream_id}/offers/{offer_id}/remove`

Удаляет оффер: статус `removed`, доля 0, остальные пересчитываются. Закрепление снимается. Оффер, добавленный в черновике и ещё не опубликованный, просто забывается.

### `POST /api/streams/{stream_id}/offers/{offer_id}/restore`

**Bring back.** Возвращает удалённый оффер в поток, доли пересчитываются.

### `PUT /api/streams/{stream_id}/offers/{offer_id}/pin`

Закрепляет или открепляет долю. Тело: `{"pinned": true}` или `{"pinned": true, "share": 40}` (задать долю при закреплении, 1 до 100). Все последующие операции пересчитывают доли остальных офферов, не трогая закреплённые.

| Код | Причина |
|---|---|
| `409` | Оффер удалён (закрепить можно только активный) |
| `422` | Закреплённые офферы дают больше 100%, либо 100% и остальным ничего не остаётся, либо все закреплены и сумма не 100%. Изменения откатываются |

### `POST /api/streams/{stream_id}/push`

**Push to Keitaro.** Публикует черновик: отправляет в Keitaro активные офферы с долями (`PUT /streams/{id}`), затем фиксирует снимок. Удалённые офферы остаются у нас в архиве. Если изменений нет, ничего не делает.

| Код | Причина |
|---|---|
| `422` | Нет активных офферов или сумма долей не 100% |

### `POST /api/streams/{stream_id}/cancel`

**Cancel.** Откатывает все неопубликованные изменения: офферы, добавленные в черновике, удаляются, остальные возвращаются к состоянию Keitaro (статус и доля). Закрепления сохраняются.

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
backend/
├── alembic/                 # миграции (versions/0001_...)
├── alembic.ini
├── pytest.ini
├── requirements.txt
├── tests/                   # distribute, сервис редактора, HTTP-сценарии
└── app/
    ├── main.py              # приложение, обработчики ошибок, справочники, создание кампании
    ├── config.py            # настройки из .env
    ├── db.py                # engine, сессия SQLAlchemy
    ├── deps.py              # get_keitaro (настоящий клиент или фейк)
    ├── errors.py            # EditorError
    ├── models.py            # Stream, StreamOffer (SQLAlchemy)
    ├── schemas.py           # Pydantic: ApiResponse, CampaignCreate, StreamView, ...
    ├── keitaro/
    │   ├── client.py        # клиент Keitaro Admin API (httpx)
    │   └── fake.py          # Keitaro в памяти для разработки и тестов
    ├── routers/editor.py    # эндпоинты редактора
    └── services/
        ├── campaigns.py     # создание кампании, двух потоков, откат
        ├── distribute.py    # пересчёт долей (чистая функция)
        ├── editor.py        # Fetch, add, remove, restore, pin, push, cancel
        └── offers.py        # поиск офферов с кэшем
```

## Архивные кампании Keitaro

`DELETE /campaigns/{id}` в Keitaro переносит кампанию в архив, а имя остаётся занятым. Если нужно освободить имя вручную (напрямую в Keitaro Admin API):

| Что | Метод |
|---|---|
| Список архивных кампаний | `GET /campaigns/deleted` |
| Вернуть из архива | `POST /campaigns/{id}/restore` |
| Переименовать | `PUT /campaigns/{id}` с `{"name": "..."}` |
