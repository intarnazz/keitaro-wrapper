class EditorError(Exception):
    """Ошибка бизнес-логики редактора (не ошибка Keitaro и не ошибка валидации)."""

    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status = status
        self.message = message
