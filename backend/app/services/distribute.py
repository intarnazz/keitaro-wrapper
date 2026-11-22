from collections.abc import Sequence
from typing import Protocol


class DistributionError(ValueError):
    """Доли невозможно распределить так, чтобы сумма была 100%."""


class _Offer(Protocol):
    status: str
    share: int
    pinned: bool


def distribute(offers: Sequence[_Offer]) -> None:
    """Пересчитывает доли на месте.

    - удалённые офферы получают 0 и не участвуют;
    - закреплённые (pinned) активные офферы сохраняют свою долю;
    - остаток делится поровну между остальными активными, целыми числами
      (лишние единицы достаются первым по порядку: 34/33/33).
    """
    active = [o for o in offers if o.status == "active"]
    for o in offers:
        if o.status != "active":
            o.share = 0

    pinned_sum = sum(o.share for o in active if o.pinned)
    free = [o for o in active if not o.pinned]

    if pinned_sum > 100:
        raise DistributionError(f"Сумма закреплённых долей ({pinned_sum}%) больше 100%")
    if not active:
        return
    if not free:
        if pinned_sum != 100:
            raise DistributionError(
                f"Все офферы закреплены, но их сумма {pinned_sum}%, а должна быть 100%"
            )
        return
    if pinned_sum == 100:
        raise DistributionError("Закреплённые офферы занимают 100%, остальным ничего не остаётся")

    base, extra = divmod(100 - pinned_sum, len(free))
    for i, o in enumerate(free):
        o.share = base + (1 if i < extra else 0)
