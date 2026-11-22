import { computed, reactive, shallowRef } from 'vue'
import { asArray, asRecord, toBool, toNum, toStr } from '@/api/builders/utilte'
import type { Raw } from '@/api/builders/utilte'
import request from '@/api/web_services/request'
import Task from '@/api/web_services/task'
import { StreamOffer } from './stream-offer.model'

/** Поток кампании. Редактировать можно только потоки с офферами. */
export const DefaultStream = () => ({
  id: 0,
  keitaro_stream_id: 0,
  campaign_id: 0,
  name: '',
  position: 0,
  /** у потока есть офферы */
  is_editable: false,
  /** есть неопубликованные изменения (поток «жёлтый») */
  dirty: false,
})

export class Stream {
  private data: ReturnType<typeof DefaultStream>
  private _offers = shallowRef<StreamOffer[]>([])
  private task = new Task()

  private _active_offers = computed<StreamOffer[]>(() => this._offers.value.filter((o) => o.is_active))
  private _removed_offers = computed<StreamOffer[]>(() => this._offers.value.filter((o) => o.is_removed))
  private _total_share = computed<number>(() =>
    this._active_offers.value.reduce((sum, o) => sum + o.share, 0),
  )
  /** доли активных офферов дают 100% (или активных офферов нет) */
  private _is_balanced = computed<boolean>(
    () => this._active_offers.value.length === 0 || this._total_share.value === 100,
  )

  constructor(raw: Raw<ReturnType<typeof DefaultStream>> & { offers?: unknown } = {}) {
    this.data = reactive(DefaultStream())
    this.apply(raw)
  }

  // ─── Данные ──────────────────────────────────────────────────────────────

  public get id(): number {
    return this.data.id
  }

  public get keitaro_stream_id(): number {
    return this.data.keitaro_stream_id
  }

  public get campaign_id(): number {
    return this.data.campaign_id
  }

  public get name(): string {
    return this.data.name
  }

  public get position(): number {
    return this.data.position
  }

  public get is_editable(): boolean {
    return this.data.is_editable
  }

  public get dirty(): boolean {
    return this.data.dirty
  }

  public get offers(): StreamOffer[] {
    return this._offers.value
  }

  public get active_offers(): StreamOffer[] {
    return this._active_offers.value
  }

  public get removed_offers(): StreamOffer[] {
    return this._removed_offers.value
  }

  public get total_share(): number {
    return this._total_share.value
  }

  public get is_balanced(): boolean {
    return this._is_balanced.value
  }

  public get is_loading(): boolean {
    return this.task.is_loading
  }

  public get error(): string | null {
    return this.task.error
  }

  // ─── Действия. Каждое отправляет запрос и обновляет поток ответом сервера ──

  public add_offer(offer_id: number): Promise<boolean> {
    return this.act(() => request.post(`streams/${this.id}/offers`, { offer_id }))
  }

  public remove_offer(offer: StreamOffer): Promise<boolean> {
    return this.act(() => request.post(`streams/${this.id}/offers/${offer.offer_id}/remove`))
  }

  /** Bring back */
  public restore_offer(offer: StreamOffer): Promise<boolean> {
    return this.act(() => request.post(`streams/${this.id}/offers/${offer.offer_id}/restore`))
  }

  /** Закрепляет (или открепляет) долю оффера. При закреплении можно задать новую долю. */
  public pin_offer(offer: StreamOffer, pinned: boolean, share?: number): Promise<boolean> {
    const body: Record<string, unknown> = { pinned }
    if (share !== undefined) body['share'] = share
    return this.act(() => request.put(`streams/${this.id}/offers/${offer.offer_id}/pin`, body))
  }

  /** Push to Keitaro: публикует черновик */
  public push(): Promise<boolean> {
    return this.act(() => request.post(`streams/${this.id}/push`))
  }

  /** Отменяет неопубликованные изменения */
  public cancel(): Promise<boolean> {
    return this.act(() => request.post(`streams/${this.id}/cancel`))
  }

  // ─── Внутреннее ──────────────────────────────────────────────────────────

  private async act(action: () => Promise<unknown>): Promise<boolean> {
    const raw = await this.task.run(action)
    if (raw === null) return false
    this.apply(asRecord(raw))
    return true
  }

  /** Обновляет поток данными сервера (вид потока целиком) */
  private apply(raw: Raw<ReturnType<typeof DefaultStream>> & { offers?: unknown }): void {
    Object.assign(this.data, {
      id: toNum(raw.id),
      keitaro_stream_id: toNum(raw.keitaro_stream_id),
      campaign_id: toNum(raw.campaign_id),
      name: toStr(raw.name),
      position: toNum(raw.position),
      is_editable: toBool(raw.is_editable),
      dirty: toBool(raw.dirty),
    })
    this._offers.value = asArray(raw.offers).map((item) => new StreamOffer(asRecord(item)))
  }
}
