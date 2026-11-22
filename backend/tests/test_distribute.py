from dataclasses import dataclass

import pytest

from app.services.distribute import DistributionError, distribute


@dataclass
class O:
    status: str = "active"
    share: int = 0
    pinned: bool = False


def shares(offers):
    return [o.share for o in offers]


def test_three_offers_split_34_33_33():
    offers = [O(), O(), O()]
    distribute(offers)
    assert shares(offers) == [34, 33, 33]


def test_four_offers_split_25():
    offers = [O(), O(), O(), O()]
    distribute(offers)
    assert shares(offers) == [25, 25, 25, 25]


def test_pinned_keeps_share_rest_is_split():
    offers = [O(share=25, pinned=True), O(), O()]
    distribute(offers)
    assert shares(offers) == [25, 38, 37]


def test_removed_gets_zero_and_is_ignored():
    offers = [O(), O(status="removed", share=50), O()]
    distribute(offers)
    assert shares(offers) == [50, 0, 50]


def test_sum_is_always_100():
    for n in range(1, 12):
        offers = [O() for _ in range(n)]
        distribute(offers)
        assert sum(shares(offers)) == 100


def test_pinned_sum_over_100_fails():
    with pytest.raises(DistributionError):
        distribute([O(share=70, pinned=True), O(share=50, pinned=True), O()])


def test_all_pinned_must_sum_to_100():
    with pytest.raises(DistributionError):
        distribute([O(share=40, pinned=True), O(share=40, pinned=True)])
    offers = [O(share=40, pinned=True), O(share=60, pinned=True)]
    distribute(offers)
    assert shares(offers) == [40, 60]


def test_pinned_100_with_free_offers_fails():
    with pytest.raises(DistributionError):
        distribute([O(share=100, pinned=True), O()])


def test_no_active_offers_is_ok():
    offers = [O(status="removed", share=10)]
    distribute(offers)
    assert shares(offers) == [0]
