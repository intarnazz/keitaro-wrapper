import { computed, reactive, shallowRef } from 'vue'
import { asArray, asRecord, toNum, toStr } from '@/api/builders/utilte'
import type { Raw } from '@/api/builders/utilte'
import Loader from '@/api/web_services/loader'
import request from '@/api/web_services/request'

/** Запись справочника Keitaro (домен, группа или источник трафика). */
export const DefaultDirectoryItem = () => ({
  id: 0,
  name: '',
  state: 'active',
})

export class DirectoryItem {
  private data: ReturnType<typeof DefaultDirectoryItem>

  constructor(raw: Raw<ReturnType<typeof DefaultDirectoryItem>> = {}) {
    this.data = reactive({
      ...DefaultDirectoryItem(),
      id: toNum(raw.id),
      name: toStr(raw.name),
      state: toStr(raw.state, 'active'),
    })
  }

  public get id(): number {
    return this.data.id
  }

  public get name(): string {
    return this.data.name
  }

  public get is_active(): boolean {
    return this.data.state === 'active'
  }
}

/** Справочник, загружаемый лениво по одному эндпоинту. */
class Catalog {
  private _items = shallowRef<DirectoryItem[] | null>(null)
  private loader: Loader
  private path: string

  constructor(path: string) {
    this.path = path
    this.loader = new Loader(() => this.init())
  }

  /** Записи справочника или `null`, пока они не загружены */
  public get items(): DirectoryItem[] | null {
    this.loader.ensure()
    return this._items.value
  }

  public get error(): string | null {
    return this.loader.error
  }

  private async init(): Promise<void> {
    const raw = await request.get(this.path)
    this._items.value = asArray(raw).map((item) => new DirectoryItem(asRecord(item)))
  }
}

/**
 * Справочники Keitaro, нужные для создания кампании: домены, группы, источники трафика.
 * Значением по умолчанию считается первая активная запись.
 */
export class Directory {
  private _domains = new Catalog('domains')
  private _groups = new Catalog('groups')
  private _traffic_sources = new Catalog('traffic-sources')

  private _first_domain_id = computed<number | null>(() => Directory.first(this._domains.items))
  private _first_group_id = computed<number | null>(() => Directory.first(this._groups.items))
  private _first_traffic_source_id = computed<number | null>(() =>
    Directory.first(this._traffic_sources.items),
  )

  public get domains(): DirectoryItem[] | null {
    return this._domains.items
  }

  public get groups(): DirectoryItem[] | null {
    return this._groups.items
  }

  public get traffic_sources(): DirectoryItem[] | null {
    return this._traffic_sources.items
  }

  public get first_domain_id(): number | null {
    return this._first_domain_id.value
  }

  public get first_group_id(): number | null {
    return this._first_group_id.value
  }

  public get first_traffic_source_id(): number | null {
    return this._first_traffic_source_id.value
  }

  private static first(items: DirectoryItem[] | null): number | null {
    if (!items) return null
    return (items.find((i) => i.is_active) ?? items[0])?.id ?? null
  }
}

const directory = new Directory()
export default directory
