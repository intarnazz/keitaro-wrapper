import { shallowRef } from 'vue'
import { asArray, asRecord } from '@/api/builders/utilte'
import Loader from '@/api/web_services/loader'
import request from '@/api/web_services/request'
import { Campaign } from './campaign.model'

/**
 * Список кампаний Keitaro и доступ к ним по id.
 *
 * @example
 * campaigns.list      // Campaign[] | null (null, пока список грузится)
 * campaigns.get(216812)
 */
class CampaignService {
  private _list = shallowRef<Campaign[] | null>(null)
  private cache = new Map<number, Campaign>()
  private loader: Loader

  constructor() {
    this.loader = new Loader(() => this.init())
  }

  public get list(): Campaign[] | null {
    this.loader.ensure()
    return this._list.value
  }

  public get is_loading(): boolean {
    return this.loader.is_loading
  }

  public get error(): string | null {
    return this.loader.error
  }

  /** Кампания по id. Экземпляры кэшируются, чтобы потоки и черновики не терялись при навигации. */
  public get(id: number): Campaign {
    let campaign = this.cache.get(id)
    if (!campaign) {
      campaign = new Campaign({ id })
      this.cache.set(id, campaign)
    }
    return campaign
  }

  /** Перезагружает список (например, после создания кампании) */
  public reload(): Promise<void> {
    return this.loader.reload()
  }

  private async init(): Promise<void> {
    const raw = await request.get('campaigns')
    this._list.value = asArray(raw).map((item) => {
      const data = asRecord(item)
      const id = Number(data['id'])
      const known = this.cache.get(id)
      if (known) return known
      const campaign = new Campaign(data)
      this.cache.set(id, campaign)
      return campaign
    })
  }
}

const campaigns = new CampaignService()
export default campaigns
