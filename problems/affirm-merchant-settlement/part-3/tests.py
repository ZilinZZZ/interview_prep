import pytest
from solution import schedule_disbursements


def slim(result):
    return [
        (d["merchant_id"], d["settlement_date"], d["gross"], d["refunds"], d["fee"], d["net"])
        for d in result["disbursements"]
    ]


@pytest.mark.sample
def test_captures_bucket_by_settlement_date_refund_nets_separately():
    result = schedule_disbursements(
        [
            {"id": "t1", "merchant_id": "m1", "type": "capture", "amount": 100.00, "captured_at": "2026-07-13"},
            {"id": "t2", "merchant_id": "m1", "type": "capture", "amount": 50.00, "captured_at": "2026-07-13"},
            {"id": "t3", "merchant_id": "m1", "type": "capture", "amount": 20.00, "captured_at": "2026-07-16"},
            {"id": "t4", "merchant_id": "m1", "type": "refund", "amount": 10.00, "captured_at": "2026-07-16"},
        ],
        0.03,
        2,
    )
    assert slim(result) == [
        ("m1", "2026-07-15", 150.00, 0.0, 4.50, 145.50),
        ("m1", "2026-07-20", 20.00, 10.00, 0.60, 9.40),
    ]


@pytest.mark.sample
def test_weekend_capture_settles_on_next_business_day():
    # 2026-07-18 is a Saturday; +2 business days skips the weekend to
    # land on Tuesday 2026-07-21.
    result = schedule_disbursements(
        [{"id": "t1", "merchant_id": "m1", "type": "capture", "amount": 10.00, "captured_at": "2026-07-18"}],
        0.0,
        2,
    )
    assert slim(result) == [("m1", "2026-07-21", 10.00, 0.0, 0.0, 10.00)]


def test_refund_reduces_net_but_fee_is_not_refunded():
    result = schedule_disbursements(
        [
            {"id": "t1", "merchant_id": "m1", "type": "capture", "amount": 100.00, "captured_at": "2026-07-13"},
            {"id": "t2", "merchant_id": "m1", "type": "refund", "amount": 30.00, "captured_at": "2026-07-13"},
        ],
        0.03,
        2,
    )
    assert slim(result) == [("m1", "2026-07-15", 100.00, 30.00, 3.00, 67.00)]


def test_disbursements_sorted_by_date_then_merchant():
    result = schedule_disbursements(
        [
            {"id": "t1", "merchant_id": "zeta-corp", "type": "capture", "amount": 5.00, "captured_at": "2026-07-13"},
            {"id": "t2", "merchant_id": "acme-inc", "type": "capture", "amount": 5.00, "captured_at": "2026-07-13"},
            {"id": "t3", "merchant_id": "acme-inc", "type": "capture", "amount": 5.00, "captured_at": "2026-07-01"},
        ],
        0.0,
        2,
    )
    ordered = [(d["settlement_date"], d["merchant_id"]) for d in result["disbursements"]]
    assert ordered == sorted(ordered)
    assert ordered[0] == ("2026-07-03", "acme-inc")
    assert ordered[1][0] == "2026-07-15"
    assert set(ordered[1:]) == {("2026-07-15", "acme-inc"), ("2026-07-15", "zeta-corp")}


def test_empty_transactions_returns_empty_disbursements():
    assert schedule_disbursements([], 0.03, 2) == {"disbursements": []}


@pytest.mark.trap("float-precision")
def test_dime_amounts_bucket_is_exact():
    result = schedule_disbursements(
        [
            {"id": "t1", "merchant_id": "m1", "type": "capture", "amount": 0.10, "captured_at": "2026-07-13"},
            {"id": "t2", "merchant_id": "m1", "type": "capture", "amount": 0.20, "captured_at": "2026-07-13"},
            {"id": "t3", "merchant_id": "m1", "type": "capture", "amount": 0.30, "captured_at": "2026-07-13"},
        ],
        0.05,
        2,
    )
    assert slim(result) == [("m1", "2026-07-15", 0.60, 0.0, 0.03, 0.57)]
