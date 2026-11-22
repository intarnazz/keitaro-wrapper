import { reactive } from 'vue'
import { ApiError } from './api-error'

/**
 * Выполняет асинхронное действие и хранит его состояние: идёт ли оно и чем закончилось.
 * Ошибка запроса не выбрасывается наружу, а попадает в `error`.
 */
export default class Task {
  private data = reactive({
    is_loading: false,
    error: null as string | null,
    field_errors: {} as Record<string, string>,
  })

  public get is_loading(): boolean {
    return this.data.is_loading
  }

  public get error(): string | null {
    return this.data.error
  }

  public set error(error: string | null) {
    this.data.error = error
  }

  /** Ошибки валидации по полям (если бэкенд их вернул) */
  public get field_errors(): Record<string, string> {
    return this.data.field_errors
  }

  /**
   * @returns результат или `null`, если действие завершилось ошибкой
   */
  public async run<T>(action: () => Promise<T>): Promise<T | null> {
    this.data.is_loading = true
    this.data.error = null
    this.data.field_errors = {}
    try {
      return await action()
    } catch (error) {
      if (error instanceof Error && error.name === 'AbortError') return null
      this.data.error = error instanceof ApiError ? error.message : 'Something went wrong'
      if (error instanceof ApiError) this.data.field_errors = error.field_errors
      if (!(error instanceof ApiError)) console.error(error)
      return null
    } finally {
      this.data.is_loading = false
    }
  }
}
