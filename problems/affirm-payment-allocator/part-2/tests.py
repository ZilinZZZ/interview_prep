import pytest
from solution import allocate_payment


def slim(result):
    return [(b["id"], b["remaining"]) for b in result["balances"]]


@pytest.mark.sample
def test_partial_payment_cascades_oldest_first():
    result = allocate_payment(
        [{"id": "a", "due": 10.00}, {"id": "b", "due": 10.00}], 15.00
    )
    assert [(b["id"], b["remaining"]) for b in result["balances"]] == [
        ("a", 0.0),
        ("b", 5.0),
    ]
    assert result["credit"] == 0.0


@pytest.mark.sample
def test_overpayment_returned_as_credit():
    result = allocate_payment([{"id": "a", "due": 10.00}], 12.50)
    assert result["credit"] == 2.50


def test_no_installments_full_credit():
    result = allocate_payment([], 7.00)
    assert result["balances"] == []
    assert result["credit"] == 7.00


def test_exact_payoff_zero_credit():
    result = allocate_payment(
        [{"id": "a", "due": 3.00}, {"id": "b", "due": 4.00}], 7.00
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0)]
    assert result["credit"] == 0.0


@pytest.mark.trap("remainder-distribution")
def test_credit_is_exact_after_cascading():
    # float: 0.40 - 0.10 - 0.20 = 0.10000000000000003, not 0.10
    result = allocate_payment(
        [{"id": "a", "due": 0.10}, {"id": "b", "due": 0.20}], 0.40
    )
    assert result["credit"] == 0.10


@pytest.mark.trap("remainder-distribution")
def test_boundary_installment_balance_is_exact():
    # float: the third dime ends up owing 0.050000000000000017, not 0.05
    result = allocate_payment(
        [{"id": "a", "due": 0.10}, {"id": "b", "due": 0.10}, {"id": "c", "due": 0.10}],
        0.25,
    )
    assert slim(result) == [("a", 0.0), ("b", 0.0), ("c", 0.05)]
    assert result["credit"] == 0.0
