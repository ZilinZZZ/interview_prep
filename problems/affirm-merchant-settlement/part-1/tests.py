import pytest
from solution import compute_merchant_payouts


def slim(result):
    return [(p["merchant_id"], p["gross"], p["fee"], p["net"]) for p in result["payouts"]]


@pytest.mark.sample
def test_aggregates_multiple_transactions_per_merchant():
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-42", "amount": 100.00},
            {"id": "t2", "merchant_id": "merchant-42", "amount": 50.00},
            {"id": "t3", "merchant_id": "merchant-7", "amount": 200.00},
        ],
        0.03,
    )
    assert slim(result) == [
        ("merchant-42", 150.00, 4.50, 145.50),
        ("merchant-7", 200.00, 6.00, 194.00),
    ]


@pytest.mark.sample
def test_single_transaction_single_merchant():
    result = compute_merchant_payouts(
        [{"id": "t1", "merchant_id": "merchant-1", "amount": 10.00}], 0.10
    )
    assert slim(result) == [("merchant-1", 10.00, 1.00, 9.00)]


def test_empty_transactions_returns_empty_payouts():
    assert compute_merchant_payouts([], 0.03) == {"payouts": []}


def test_zero_fee_rate_returns_full_gross_as_net():
    result = compute_merchant_payouts(
        [{"id": "t1", "merchant_id": "merchant-1", "amount": 25.00}], 0.0
    )
    assert slim(result) == [("merchant-1", 25.00, 0.0, 25.00)]


def test_payouts_ordered_by_first_appearance_not_alphabetical():
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "zeta-corp", "amount": 5.00},
            {"id": "t2", "merchant_id": "acme-inc", "amount": 5.00},
        ],
        0.0,
    )
    assert [p["merchant_id"] for p in result["payouts"]] == ["zeta-corp", "acme-inc"]


@pytest.mark.trap("float-precision")
def test_dime_amounts_sum_and_fee_are_exact():
    # 0.10 + 0.20 + 0.30 is 0.6000000000000001 in raw float. Cents aren't.
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-1", "amount": 0.10},
            {"id": "t2", "merchant_id": "merchant-1", "amount": 0.20},
            {"id": "t3", "merchant_id": "merchant-1", "amount": 0.30},
        ],
        0.05,
    )
    assert slim(result) == [("merchant-1", 0.60, 0.03, 0.57)]
