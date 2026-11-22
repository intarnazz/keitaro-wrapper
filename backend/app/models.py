from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Stream(Base):
    """Поток Keitaro, о котором знает обёртка. Содержимое потока (фильтры, редирект) не хранится."""

    __tablename__ = "streams"

    id: Mapped[int] = mapped_column(primary_key=True)
    campaign_id: Mapped[int] = mapped_column(index=True)
    keitaro_stream_id: Mapped[int] = mapped_column(unique=True)
    name: Mapped[str]
    position: Mapped[int] = mapped_column(default=0)

    offers: Mapped[list["StreamOffer"]] = relationship(
        back_populates="stream", cascade="all, delete-orphan", order_by="StreamOffer.id"
    )

    @property
    def dirty(self) -> bool:
        """Есть неопубликованные изменения (в интерфейсе поток «жёлтый»)."""
        return any(o.changed for o in self.offers)


class StreamOffer(Base):
    """Оффер в потоке: желаемое состояние (черновик) и снимок того, что сейчас в Keitaro."""

    __tablename__ = "stream_offers"
    __table_args__ = (UniqueConstraint("stream_id", "offer_id"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    stream_id: Mapped[int] = mapped_column(ForeignKey("streams.id", ondelete="CASCADE"), index=True)
    offer_id: Mapped[int]
    offer_name: Mapped[str] = mapped_column(default="")

    # желаемое состояние (то, что видит пользователь)
    status: Mapped[str] = mapped_column(default="active")  # active | removed
    share: Mapped[int] = mapped_column(default=0)
    pinned: Mapped[bool] = mapped_column(default=False)

    # снимок Keitaro после последнего Fetch или Push; NULL: оффер ещё не публиковался
    base_status: Mapped[str | None] = mapped_column(default=None)
    base_share: Mapped[int | None] = mapped_column(default=None)

    stream: Mapped[Stream] = relationship(back_populates="offers")

    @property
    def is_new(self) -> bool:
        return self.base_status is None

    @property
    def changed(self) -> bool:
        return self.status != self.base_status or self.share != self.base_share
