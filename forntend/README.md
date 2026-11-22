# Frontend

Vue 3 + TypeScript (strict) + vue-router + Tailwind CSS 4 (`@tailwindcss/vite`) + Sass.

```powershell
yarn          # установка
yarn dev      # разработка, http://localhost:5173 (прокси /api -> localhost:8000)
yarn type-check
yarn build
```

## Строгий TypeScript

`tsconfig.app.json`: `strict`, `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`, `noImplicitOverride`, `noImplicitReturns`, `noUnusedLocals`, `noUnusedParameters`, `noPropertyAccessFromIndexSignature`, `useUnknownInCatchVariables`.

## Слой данных `src/api`

Компоненты не ходят в сеть сами: они берут модели из `@/api/api`.

```
src/api/
├── api.ts                    # точка входа: сервисы и классы
├── builders/utilte.ts        # toNum, toStr, Raw<T>, asRecord, ...
├── web_services/
│   ├── request.ts            # fetch + разбор {success, message, data}, бросает ApiError
│   ├── api-error.ts
│   ├── task.ts               # выполняет действие, хранит is_loading / error
│   ├── loader.ts             # ленивая загрузка: ensure() в геттере
│   └── promiseController.ts  # отмена устаревших запросов (поиск)
└── domains/
    ├── campaign/             # Campaign, CampaignService, CampaignForm, CreatedCampaign
    ├── stream/               # Stream, StreamOffer
    ├── offer/                # Offer, OfferSearch
    └── directory/            # Directory (домены, группы, источники)
```

Правила:

1. **Класс сам источник типа.** Отдельных `types.ts` и интерфейсов нет. Тип данных выводится из билдера: `ReturnType<typeof DefaultStream>`, а в остальном коде типом служит сам класс (`Stream`, `StreamOffer`).
2. **`DefaultX`: функция со значениями по умолчанию** (`DefaultStream`, `DefaultCampaign`, ...). Конструктор класса принимает «сырые» данные (`Raw<...>`) и приводит их к типам.
3. **Все значения только через геттеры и сеттеры.** Состояние лежит в приватном `reactive`, вычисляемые значения в приватных `computed` (`_total_share` и т. п.), наружу отдаются геттерами.
4. **`init` закрыт.** Лениво загружаемые поля возвращают `null`, пока данных нет. Первое обращение к геттеру запускает приватный `init` (через `Loader.ensure()`), и Vue сам перерисует то, что их использует. Повторно данные загружает только явный `reload()`, поэтому ошибка не приводит к циклу запросов.
5. **Действия** (`stream.push()`, `campaign.fetch_streams()`, `form.submit()`) выполняются через `Task`: ошибка не выбрасывается, а попадает в `error`.
6. Списки экземпляров моделей хранятся в `shallowRef`, чтобы Vue не оборачивал их в прокси повторно.

## Стили

Tailwind 4 кладёт утилиты в `@layer utilities`, а глобальные стили из `src/assets/sass/style.sass` лежат вне слоёв и перебивают их. Поэтому:

- для элементов `input`, `button`, `select` используются компоненты `components/ui/*` со своими scoped-стилями;
- классы Tailwind вроде `border` конфликтуют с глобальным `.border` из `style.sass`, для рамок карточек используется `ring-1` или scoped-стили;
- глобальное правило `::first-letter { text-transform: uppercase }` касается `span`, `p`, `a`, `button`, `strong` и заголовков: данные (названия офферов) выводятся в `div`.
