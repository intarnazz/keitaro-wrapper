import { computed, reactive } from 'vue'
import { toBool, toNum, toStr } from '@/api/builders/utilte'
import type { Raw } from '@/api/builders/utilte'

/** Оффер внутри потока: то, что видит пользователь (с неопубликованными изменениями). */
export const DefaultStreamOffer = () => ({
  offer_id: 0,
  name: '',
  status: 'active' as 'active' | 'removed',
  share: 0,
  pinned: false,
  /** добавлен в черновике, в Keitaro ещё нет */
  is_new: false,
  /** отличается от того, что сейчас в Keitaro */
  changed: false,
})

export class StreamOffer {
  private data: ReturnType<typeof DefaultStreamOffer>

  private _is_removed = computed<boolean>(() => this.data.status === 'removed')
  private _is_active = computed<boolean>(() => this.data.status === 'active')
  private _share_label = computed<string>(() => `${this.data.share}%`)
  private _title = computed<string>(() => this.data.name || `Offer ${this.data.offer_id}`)

  constructor(raw: Raw<ReturnType<typeof DefaultStreamOffer>> = {}) {
    this.data = reactive({
      ...DefaultStreamOffer(),
      offer_id: toNum(raw.offer_id),
      name: toStr(raw.name),
      status: raw.status === 'removed' ? 'removed' : 'active',
      share: toNum(raw.share),
      pinned: toBool(raw.pinned),
      is_new: toBool(raw.is_new),
      changed: toBool(raw.changed),
    })
  }

  public get offer_id(): number {
    return this.data.offer_id
  }

  public get name(): string {
    return this.data.name
  }

  public get status(): 'active' | 'removed' {
    return this.data.status
  }

  public get share(): number {
    return this.data.share
  }

  public get pinned(): boolean {
    return this.data.pinned
  }

  public get is_new(): boolean {
    return this.data.is_new
  }

  public get changed(): boolean {
    return this.data.changed
  }

  /** Оффер удалён из потока (серый, доля 0%, можно вернуть) */
  public get is_removed(): boolean {
    return this._is_removed.value
  }

  public get is_active(): boolean {
    return this._is_active.value
  }

  public get share_label(): string {
    return this._share_label.value
  }

  public get title(): string {
    return this._title.value
  }
}
