import NProgress from 'nprogress'
import { asRecord, toStr } from '@/api/builders/utilte'
import { ApiError } from './api-error'

/**
 * Базовый URL бэкенда. В разработке `/api` проксируется Vite на FastAPI (см. vite.config.ts).
 */
const API_URL: string = (import.meta.env.VITE_API_URL ?? '/api').replace(/\/$/, '')

type Query = Record<string, string | number | undefined>

interface SendOptions {
  query?: Query
  body?: Record<string, unknown>
  signal?: AbortSignal | undefined
}

/**
 * HTTP-клиент к нашему FastAPI.
 *
 * Разворачивает единый формат `{ success, message, data }`: при успехе возвращает `data`,
 * при ошибке бросает {@link ApiError}.
 */
class Request {
  public get(path: string, query: Query = {}, signal?: AbortSignal): Promise<unknown> {
    return this.send('GET', path, { query, signal })
  }

  public post(path: string, body: Record<string, unknown> = {}): Promise<unknown> {
    return this.send('POST', path, { body })
  }

  public put(path: string, body: Record<string, unknown> = {}): Promise<unknown> {
    return this.send('PUT', path, { body })
  }

  private async send(method: string, path: string, options: SendOptions): Promise<unknown> {
    const params = new URLSearchParams()
    for (const [key, value] of Object.entries(options.query ?? {})) {
      if (value !== undefined && value !== '') params.append(key, String(value))
    }
    const url = `${API_URL}/${path}${params.size ? `?${params}` : ''}`

    const init: RequestInit = { method, headers: { Accept: 'application/json' } }
    if (options.signal) init.signal = options.signal
    if (options.body) {
      init.headers = { ...init.headers, 'Content-Type': 'application/json' }
      init.body = JSON.stringify(options.body)
    }

    NProgress.configure({ showSpinner: false })
    NProgress.start()
    let response: Response
    try {
      response = await fetch(url, init)
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') throw error
      throw new ApiError('Backend is unavailable', 0)
    } finally {
      NProgress.done()
    }

    return this.unwrap(response)
  }

  private async unwrap(response: Response): Promise<unknown> {
    let payload: unknown
    try {
      payload = await response.json()
    } catch {
      throw new ApiError(`Unexpected response (HTTP ${response.status})`, response.status)
    }
    const envelope = asRecord(payload)
    if (response.ok && envelope['success'] === true) return envelope['data']
    throw new ApiError(
      toStr(envelope['message'], `HTTP ${response.status}`),
      response.status,
      envelope['data'],
    )
  }
}

const request = new Request()
export default request
