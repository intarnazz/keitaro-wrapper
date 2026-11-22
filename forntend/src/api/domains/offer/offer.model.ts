import { reactive } from 'vue'
import { toNum, toStr } from '@/api/builders/utilte'
import type { Raw } from '@/api/builders/utilte'

/** Оффер Keitaro из справочника (для поиска и выбора). */
export const DefaultOffer = () => ({
  id: 0,
  name: '',
  state: '',
})

export class Offer {
  private data: ReturnType<typeof DefaultOffer>

  constructor(raw: Raw<ReturnType<typeof DefaultOffer>> = {}) {
    this.data = reactive({
      ...DefaultOffer(),
      id: toNum(raw.id),
      name: toStr(raw.name),
      state: toStr(raw.state),
    })
  }

  public get id(): number {
    return this.data.id
  }

  public get name(): string {
    return this.data.name
  }

  public get state(): string {
    return this.data.state
  }

  /** Подпись для списков: `#7 VPN Eta` */
  public get label(): string {
    return `#${this.data.id} ${this.data.name}`.trim()
  }
}
