from app.config import settings
from app.keitaro.client import KeitaroClient
from app.keitaro.fake import FakeKeitaro

_fake: FakeKeitaro | None = None


def get_keitaro() -> KeitaroClient:
    """Клиент Keitaro. При KEITARO_FAKE=true отдаёт один и тот же клиент в памяти."""
    global _fake
    if settings.keitaro_fake:
        if _fake is None:
            _fake = FakeKeitaro()
        return _fake
    return KeitaroClient(settings.keitaro_url, settings.keitaro_api_key)
