import { reactive, shallowRef } from 'vue'
import { asArray, asRecord } from '@/api/builders/utilte'
import request from '@/api/web_services/request'
import PromiseController from '@/api/web_services/promiseController'
import Task from '@/api/web_services/task'
import { Offer } from './offer.model'

const DEBOUNCE_MS = 250
const LIMIT = 20

/**
 * Поиск офферов по id или названию.
 *
 * Запрос уходит на наш бэкенд (он отдаёт отфильтрованный список Keitaro).
 * Смена `query` запускает поиск с задержкой, устаревшие запросы отменяются.
 */
export class OfferSearch {
  private data = reactive({ query: '' })
  private _results = shallowRef<Offer[] | null>(null)
  private promise_controller = new PromiseController()
  private task = new Task()
  private timer: ReturnType<typeof setTimeout> | null = null
  private requested = false
  private limit: number

  constructor(limit: number = LIMIT) {
    this.limit = limit
  }

  /** Найденные офферы. Пока ничего не загружено, `null` (первое обращение загружает первые офферы). */
  public get results(): Offer[] | null {
    if (!this.requested) {
      this.requested = true
      queueMicrotask(() => void this.search())
    }
    return this._results.value
  }

  public get query(): string {
    return this.data.query
  }

  public set query(query: string) {
    this.data.query = query
    this.requested = true
    if (this.timer) clearTimeout(this.timer)
    this.timer = setTimeout(() => void this.search(), DEBOUNCE_MS)
  }

  public get is_loading(): boolean {
    return this.promise_controller.is_loading
  }

  public get error(): string | null {
    return this.task.error
  }

  private async search(): Promise<void> {
    const query = this.data.query
    const found = await this.task.run(() =>
      this.promise_controller.await((signal) => request.get('offers', { q: query, limit: this.limit }, signal)),
    )
    if (found === null || found === false) return
    this._results.value = asArray(found).map((item) => new Offer(asRecord(item)))
  }
}
