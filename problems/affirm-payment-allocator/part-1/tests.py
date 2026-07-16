import pytest
from solution import allocate_payment


def slim(result):
    return [(b["id"], b["remaining"]) for b in result["balances"]]


@pytest.mark.sample
def test_payment_clears_oldest_installment():
    result = allocate_payment(
        [{"id": "a", "due": 25.00}, {"id": "b", "due": 25.00}], 25.00
    )
    assert [(b["id"], b["remaining"]) for b in result["balances"]] == [
        ("a", 0.0),
        ("b", 25.0),
    ]


@pytest.mark.sample
def test_zero_payment_changes_nothing():
    result = allocate_payment([{"id": "a", "due": 10.00}], 0.0)
    assert [(b["id"], b["remaining"]) for b in result["balances"]] == [("a", 10.0)]


def test_payment_covers_everything():
    result = allocate_payment(
        [{"id": "a", "due": 10.00}, {"id": "b", "due": 20.00}], 30.00
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0)]


def test_result_preserves_input_order():
    result = allocate_payment(
        [{"id": "z", "due": 5.00}, {"id": "a", "due": 5.00}, {"id": "m", "due": 5.00}],
        5.00,
    )
    assert [b["id"] for b in result["balances"]] == ["z", "a", "m"]


@pytest.mark.trap("float-precision")
def test_dime_installments_leave_exact_zero():
    # 0.30 exactly covers the first two installments (0.10 + 0.20).
    # Float arithmetic leaves ~2.8e-17 on installment b. Cents don't.
    result = allocate_payment(
        [{"id": "a", "due": 0.10}, {"id": "b", "due": 0.20}, {"id": "c", "due": 0.30}],
        0.30,
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0), ("c", 0.30)]
