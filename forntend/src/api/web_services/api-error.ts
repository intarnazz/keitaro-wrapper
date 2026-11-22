import { asArray, asRecord, toStr } from '@/api/builders/utilte'

/**
 * Ошибка запроса к нашему бэкенду.
 *
 * Бэкенд всегда отвечает `{ success, message, data }`. При `success: false`
 * `message` кратко описывает ошибку, а `data` содержит детали
 * (для валидации: `errors`, `required_fields`, `optional_fields`).
 */
export class ApiError extends Error {
  private _status: number
  private _data: unknown

  constructor(message: string, status: number = 0, data: unknown = null) {
    super(message)
    this.name = 'ApiError'
    this._status = status
    this._data = data
  }

  /** HTTP-статус ответа (0: бэкенд недоступен) */
  public get status(): number {
    return this._status
  }

  public get data(): unknown {
    return this._data
  }

  /** Ошибки валидации по полям: `{ geo: 'Value error, ...' }` */
  public get field_errors(): Record<string, string> {
    const result: Record<string, string> = {}
    for (const item of asArray(asRecord(this._data)['errors'])) {
      const err = asRecord(item)
      const field = toStr(asArray(err['loc']).at(-1))
      if (field && field !== 'body') result[field] = toStr(err['msg'])
    }
    return result
  }
}
