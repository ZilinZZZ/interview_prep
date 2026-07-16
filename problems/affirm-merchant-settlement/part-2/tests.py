import pytest
from solution import compute_merchant_payouts


def breakdown(result, merchant_id):
    for payout in result["payouts"]:
        if payout["merchant_id"] == merchant_id:
            return [(b["transaction_id"], b["fee"]) for b in payout["fee_breakdown"]]
    raise AssertionError(f"no payout for {merchant_id}")


def payout_for(result, merchant_id):
    for payout in result["payouts"]:
        if payout["merchant_id"] == merchant_id:
            return payout
    raise AssertionError(f"no payout for {merchant_id}")


@pytest.mark.sample
def test_fee_breakdown_sums_to_merchant_fee():
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-1", "amount": 1.33},
            {"id": "t2", "merchant_id": "merchant-1", "amount": 2.67},
            {"id": "t3", "merchant_id": "merchant-1", "amount": 4.00},
        ],
        0.1,
    )
    payout = payout_for(result, "merchant-1")
    assert payout["gross"] == 8.00
    assert payout["fee"] == 0.80
    assert payout["net"] == 7.20
    assert breakdown(result, "merchant-1") == [
        ("t1", 0.13),
        ("t2", 0.27),
        ("t3", 0.40),
    ]
    assert sum(fee for _, fee in breakdown(result, "merchant-1")) == payout["fee"]


@pytest.mark.sample
def test_part_1_payout_fields_unchanged():
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-42", "amount": 100.00},
            {"id": "t2", "merchant_id": "merchant-42", "amount": 50.00},
        ],
        0.03,
    )
    payout = payout_for(result, "merchant-42")
    assert (payout["gross"], payout["fee"], payout["net"]) == (150.00, 4.50, 145.50)


def test_evenly_divisible_fee_needs_no_apportionment():
    result = compute_merchant_payouts(
        [{"id": "t1", "merchant_id": "merchant-1", "amount": 10.00}], 0.10
    )
    assert breakdown(result, "merchant-1") == [("t1", 1.00)]


def test_multiple_merchants_each_get_own_breakdown():
    result = compute_merchant_payouts(
        [
            {"id": "a1", "merchant_id": "merchant-a", "amount": 10.00},
            {"id": "b1", "merchant_id": "merchant-b", "amount": 20.00},
        ],
        0.05,
    )
    assert breakdown(result, "merchant-a") == [("a1", 0.50)]
    assert breakdown(result, "merchant-b") == [("b1", 1.00)]


@pytest.mark.trap("remainder-distribution")
def test_tied_remainders_go_to_earliest_transaction():
    # Each $1.00 transaction owes a raw fee of 0.33 cents -- a three-way
    # tie. The merchant's total fee rounds to 1 cent, so only one
    # transaction can have it: whichever came first.
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-1", "amount": 1.00},
            {"id": "t2", "merchant_id": "merchant-1", "amount": 1.00},
            {"id": "t3", "merchant_id": "merchant-1", "amount": 1.00},
        ],
        0.0033,
    )
    payout = payout_for(result, "merchant-1")
    assert payout["fee"] == 0.01
    assert breakdown(result, "merchant-1") == [
        ("t1", 0.01),
        ("t2", 0.0),
        ("t3", 0.0),
    ]


@pytest.mark.trap("float-precision")
def test_dime_amounts_breakdown_is_exact():
    # 0.10 + 0.20 + 0.30 accumulates float noise; the per-cent breakdown
    # must still land on exact pennies summing to the exact merchant fee.
    result = compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-1", "amount": 0.10},
            {"id": "t2", "merchant_id": "merchant-1", "amount": 0.20},
            {"id": "t3", "merchant_id": "merchant-1", "amount": 0.30},
        ],
        0.05,
    )
    payout = payout_for(result, "merchant-1")
    assert payout["fee"] == 0.03
    assert breakdown(result, "merchant-1") == [
        ("t1", 0.01),
        ("t2", 0.01),
        ("t3", 0.01),
    ]
