import pytest
from decimal import Decimal
from app.models import StreamOffer
from app.domain.weight_allocator import WeightAllocator
from app.exceptions import ValidationError


def make_offer(weight: float, fixed: bool = False, deleted: bool = False) -> StreamOffer:
    return StreamOffer(
        keitaro_offer_id=1,
        weight=Decimal(str(weight)),
        is_weight_fixed=fixed,
        is_deleted_in_kt=deleted,
    )


@pytest.fixture
def allocator():
    return WeightAllocator()


def test_recalculate_proportional(allocator):
    
    o1, o2, o3 = make_offer(20), make_offer(30), make_offer(50)
    offers = [o1, o2, o3]

    offers.remove(o1)
    allocator.recalculate(offers)
    assert o2.weight == Decimal("37.50")
    assert o3.weight == Decimal("62.50")
    assert o2.weight + o3.weight == Decimal("100.00")


def test_recalculate_with_fixed(allocator):
    
    o1, o2, o3 = make_offer(30, fixed=True), make_offer(40), make_offer(40)
    offers = [o1, o2, o3]

    allocator.recalculate(offers)

    assert o1.weight == Decimal("30.00")
    assert o2.weight == Decimal("35.00")
    assert o3.weight == Decimal("35.00")
    assert o1.weight + o2.weight + o3.weight == Decimal("100.00")


def test_fixed_sum_exceeds_100(allocator):
    
    o1, o2 = make_offer(60, fixed=True), make_offer(50, fixed=True)
    offers = [o1, o2]
    with pytest.raises(ValidationError, match=r"exceeds 100%"):
        allocator.recalculate(offers)


def test_allocate_for_new(allocator):
    
    o1, o2 = make_offer(50), make_offer(50)
    offers = [o1, o2]
    new_offer = make_offer(0)

    allocator.allocate_for_new(offers + [new_offer], new_offer)

    assert o1.weight == Decimal("33.33")
    assert o2.weight == Decimal("33.33")
    assert new_offer.weight == Decimal("33.34")
    assert sum(o.weight for o in offers + [new_offer]) == Decimal("100.00")


def test_allocate_for_new_with_fixed(allocator):
    
    o1 = make_offer(40, fixed=True)
    o2 = make_offer(60)
    new_offer = make_offer(0)

    allocator.allocate_for_new([o1, o2, new_offer], new_offer)

    assert o1.weight == Decimal("40.00")
    assert o2.weight == Decimal("30.00")
    assert new_offer.weight == Decimal("30.00")


def test_recalculate_ignores_deleted(allocator):
    
    o1, o2, o3 = make_offer(50), make_offer(50), make_offer(0, deleted=True)
    offers = [o1, o2, o3]

    allocator.recalculate(offers)

    assert o1.weight == Decimal("50.00")
    assert o2.weight == Decimal("50.00")
    assert o3.weight == Decimal("0.00")
