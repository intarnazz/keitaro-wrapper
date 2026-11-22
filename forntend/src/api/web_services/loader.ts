import Task from './task'

/**
 * Ленивая загрузка данных модели.
 *
 * Геттер модели вызывает `ensure()`: первый вызов запускает загрузку (приватный `init`
 * модели), повторные ничего не делают. Пока данных нет, геттер возвращает `null`,
 * а когда загрузка закончится, Vue сам перерисует то, что их использует.
 * Так как повторный запуск делает только `reload()`, ошибка не приводит к бесконечным запросам.
 */
export default class Loader {
  private task = new Task()
  private requested = false
  private init: () => Promise<void>

  constructor(init: () => Promise<void>) {
    this.init = init
  }

  public get is_loading(): boolean {
    return this.task.is_loading
  }

  public get error(): string | null {
    return this.task.error
  }

  /** Запускает загрузку при первом обращении */
  public ensure(): void {
    if (this.requested) return
    this.requested = true
    // откладываем: геттер вызывается во время рендера, а состояние в рендере менять нельзя
    queueMicrotask(() => void this.task.run(this.init))
  }

  /** Принудительно перезагружает данные */
  public reload(): Promise<void> {
    this.requested = true
    return this.task.run(this.init).then(() => undefined)
  }
}
