import { reactive, shallowRef, computed } from 'vue'
import { asArray, asRecord, toNum, toStr } from '@/api/builders/utilte'
import type { Raw } from '@/api/builders/utilte'
import Loader from '@/api/web_services/loader'
import request from '@/api/web_services/request'
import Task from '@/api/web_services/task'
import { Stream } from '../stream/stream.model'

/**
 * Кампания Keitaro.
 * `null` в полях означает «ещё не загружено»: геттер сам запускает загрузку.
 */
export const DefaultCampaign = () => ({
  id: 0,
  name: null as string | null,
  alias: null as string | null,
  state: null as string | null,
})

export class Campaign {
  private data: ReturnType<typeof DefaultCampaign>
  private _streams = shallowRef<Stream[] | null>(null)

  private info_loader: Loader
  private streams_loader: Loader
  private fetch_task = new Task()

  private _is_dirty = computed<boolean>(() => (this._streams.value ?? []).some((s) => s.dirty))
  private _editable_streams = computed<Stream[]>(() =>
    (this._streams.value ?? []).filter((s) => s.is_editable),
  )

  constructor(raw: Raw<ReturnType<typeof DefaultCampaign>> = {}) {
    this.data = reactive({
      id: toNum(raw.id),
      name: raw.name == null ? null : toStr(raw.name),
      alias: raw.alias == null ? null : toStr(raw.alias),
      state: raw.state == null ? null : toStr(raw.state),
    })
    this.info_loader = new Loader(() => this.init_info())
    this.streams_loader = new Loader(() => this.init_streams())
  }

  // ─── Данные ──────────────────────────────────────────────────────────────

  public get id(): number {
    return this.data.id
  }

  public get name(): string | null {
    if (this.data.name === null) this.info_loader.ensure()
    return this.data.name
  }

  public get alias(): string | null {
    if (this.data.alias === null) this.info_loader.ensure()
    return this.data.alias
  }

  public get state(): string | null {
    if (this.data.state === null) this.info_loader.ensure()
    return this.data.state
  }

  /** Потоки кампании или `null`, пока они не загружены */
  public get streams(): Stream[] | null {
    this.streams_loader.ensure()
    return this._streams.value
  }

  /** Потоки, в которых можно редактировать офферы */
  public get editable_streams(): Stream[] {
    return this._editable_streams.value
  }

  /** В кампании есть неопубликованные изменения */
  public get is_dirty(): boolean {
    return this._is_dirty.value
  }

  public get is_loading(): boolean {
    return this.info_loader.is_loading || this.streams_loader.is_loading || this.fetch_task.is_loading
  }

  public get error(): string | null {
    return this.fetch_task.error ?? this.streams_loader.error ?? this.info_loader.error
  }

  // ─── Действия ────────────────────────────────────────────────────────────

  /** Fetch streams: подтягивает потоки из Keitaro. Неопубликованные правки сохраняются. */
  public async fetch_streams(): Promise<boolean> {
    const raw = await this.fetch_task.run(() => request.post(`campaigns/${this.id}/fetch`))
    if (raw === null) return false
    this._streams.value = this.build_streams(raw)
    return true
  }

  // ─── Внутреннее ──────────────────────────────────────────────────────────

  private async init_info(): Promise<void> {
    const raw = asRecord(await request.get(`campaigns/${this.id}`))
    Object.assign(this.data, {
      name: toStr(raw['name']),
      alias: toStr(raw['alias']),
      state: toStr(raw['state']),
    })
  }

  /** Локальное состояние потоков; если его ещё нет (первое открытие), сразу делает Fetch */
  private async init_streams(): Promise<void> {
    const local = this.build_streams(await request.get(`campaigns/${this.id}/streams`))
    if (local.length > 0) {
      this._streams.value = local
      return
    }
    this._streams.value = this.build_streams(await request.post(`campaigns/${this.id}/fetch`))
  }

  private build_streams(raw: unknown): Stream[] {
    return asArray(raw).map((item) => new Stream(asRecord(item)))
  }
}
