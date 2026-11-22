import { computed, reactive, shallowRef } from 'vue'
import { toNum } from '@/api/builders/utilte'
import request from '@/api/web_services/request'
import Task from '@/api/web_services/task'
import directory from '../directory/directory.model'
import campaigns from './campaign.service'
import { CreatedCampaign } from './created-campaign.model'

/** Значения формы создания кампании. Домен, группа и источник `null`: берутся по умолчанию. */
export const DefaultCampaignForm = () => ({
  name: '',
  geo: '',
  offer_id: '',
  domain_id: null as number | null,
  group_id: null as number | null,
  traffic_source_id: null as number | null,
  /** показывать ли ошибки валидации (после первой попытки отправки) */
  show_errors: false,
})

type Field = 'name' | 'geo' | 'offer_id'

/**
 * Форма «New campaign»: name, geo, offer_id.
 *
 * Домен, группа и источник трафика по умолчанию берутся из справочников Keitaro
 * (первые активные), пользователь может выбрать другие.
 */
export class CampaignForm {
  private data = reactive(DefaultCampaignForm())
  private _result = shallowRef<CreatedCampaign | null>(null)
  private task = new Task()

  private _client_errors = computed<Partial<Record<Field, string>>>(() => {
    const errors: Partial<Record<Field, string>> = {}
    if (!this.data.name.trim()) errors.name = 'Enter a campaign name'
    if (!/^[A-Z]{2}$/.test(this.data.geo)) errors.geo = 'Two-letter country code, e.g. AU'
    if (!/^[1-9]\d*$/.test(this.data.offer_id.trim())) errors.offer_id = 'Enter an offer ID'
    return errors
  })
  private _is_valid = computed<boolean>(() => Object.keys(this._client_errors.value).length === 0)

  // ─── Поля ────────────────────────────────────────────────────────────────

  public get name(): string {
    return this.data.name
  }

  public set name(name: string) {
    this.data.name = name
  }

  public get geo(): string {
    return this.data.geo
  }

  /** Только латинские буквы, не больше двух, в верхнем регистре */
  public set geo(geo: string) {
    this.data.geo = geo.replace(/[^a-zA-Z]/g, '').slice(0, 2).toUpperCase()
  }

  /** ID оффера как текст поля ввода */
  public get offer_id(): string {
    return this.data.offer_id
  }

  public set offer_id(offer_id: string) {
    this.data.offer_id = offer_id.replace(/\D/g, '')
  }

  public get domain_id(): number | null {
    return this.data.domain_id ?? directory.first_domain_id
  }

  public set domain_id(domain_id: number | null) {
    this.data.domain_id = domain_id
  }

  public get group_id(): number | null {
    return this.data.group_id ?? directory.first_group_id
  }

  public set group_id(group_id: number | null) {
    this.data.group_id = group_id
  }

  public get traffic_source_id(): number | null {
    return this.data.traffic_source_id ?? directory.first_traffic_source_id
  }

  public set traffic_source_id(traffic_source_id: number | null) {
    this.data.traffic_source_id = traffic_source_id
  }

  // ─── Состояние ───────────────────────────────────────────────────────────

  public get is_valid(): boolean {
    return this._is_valid.value
  }

  /** Ошибка поля: сначала ответ сервера, потом проверка на клиенте (после первой отправки) */
  public field_error(field: Field): string | null {
    const server = this.task.field_errors[field]
    if (server) return server
    return this.data.show_errors ? (this._client_errors.value[field] ?? null) : null
  }

  public get is_loading(): boolean {
    return this.task.is_loading
  }

  /** Общая ошибка отправки (сообщение сервера) */
  public get error(): string | null {
    return this.task.error
  }

  public get result(): CreatedCampaign | null {
    return this._result.value
  }

  // ─── Действия ────────────────────────────────────────────────────────────

  public async submit(): Promise<boolean> {
    this.data.show_errors = true
    this._result.value = null
    if (!this._is_valid.value) return false

    const body: Record<string, unknown> = {
      name: this.data.name.trim(),
      geo: this.data.geo,
      offer_id: toNum(this.data.offer_id),
    }
    if (this.domain_id !== null) body['domain_id'] = this.domain_id
    if (this.group_id !== null) body['group_id'] = this.group_id
    if (this.traffic_source_id !== null) body['traffic_source_id'] = this.traffic_source_id

    const raw = await this.task.run(() => request.post('campaigns', body))
    if (raw === null) return false

    this._result.value = new CreatedCampaign(raw as Record<string, unknown>)
    void campaigns.reload()
    this.reset()
    return true
  }

  /** Очищает поля (результат остаётся) */
  public reset(): void {
    const keep = { domain_id: this.data.domain_id, group_id: this.data.group_id,
      traffic_source_id: this.data.traffic_source_id }
    Object.assign(this.data, DefaultCampaignForm(), keep)
  }
}
