import { reactive } from 'vue'
import { asArray, toNum, toStr } from '@/api/builders/utilte'
import type { Raw } from '@/api/builders/utilte'

/** Результат создания кампании. */
export const DefaultCreatedCampaign = () => ({
  campaign_id: 0,
  alias: '',
  domain_id: 0,
  group_id: 0,
  traffic_source_id: 0,
  streams: [] as number[],
})

export class CreatedCampaign {
  private data: ReturnType<typeof DefaultCreatedCampaign>

  constructor(raw: Raw<ReturnType<typeof DefaultCreatedCampaign>> = {}) {
    this.data = reactive({
      ...DefaultCreatedCampaign(),
      campaign_id: toNum(raw.campaign_id),
      alias: toStr(raw.alias),
      domain_id: toNum(raw.domain_id),
      group_id: toNum(raw.group_id),
      traffic_source_id: toNum(raw.traffic_source_id),
      streams: asArray(raw.streams).map((id) => toNum(id)),
    })
  }

  public get campaign_id(): number {
    return this.data.campaign_id
  }

  public get alias(): string {
    return this.data.alias
  }

  public get domain_id(): number {
    return this.data.domain_id
  }

  public get group_id(): number {
    return this.data.group_id
  }

  public get traffic_source_id(): number {
    return this.data.traffic_source_id
  }

  public get streams(): number[] {
    return this.data.streams
  }
}
