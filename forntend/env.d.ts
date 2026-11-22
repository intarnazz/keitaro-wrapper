/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Адрес бэкенда. По умолчанию `/api` (проксируется Vite на FastAPI) */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
