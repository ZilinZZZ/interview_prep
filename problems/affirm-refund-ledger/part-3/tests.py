import pytest
from solution import outstanding_balance


@pytest.mark.sample
def test_as_of_excludes_later_events():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-10"},
    ]
    result = outstanding_balance(500.00, events, as_of="2026-01-07")
    assert result == {"outstanding": 400.00}


@pytest.mark.sample
def test_as_of_is_inclusive_of_same_day_event():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-10"},
    ]
    result = outstanding_balance(500.00, events, as_of="2026-01-10")
    assert result == {"outstanding": 440.00}


def test_as_of_before_any_event_returns_full_principal():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-10"},
    ]
    result = outstanding_balance(500.00, events, as_of="2026-01-01")
    assert result == {"outstanding": 500.00}


def test_omitting_as_of_matches_full_ledger():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-10"},
    ]
    result = outstanding_balance(500.00, events)
    assert result == {"outstanding": 440.00}


def test_out_of_order_events_are_sorted_by_at():
    # refund-1 is listed before the payment it reverses, but it happened later.
    events = [
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 15.00, "at": "2026-01-05"},
        {"id": "pay-1", "type": "payment", "amount": 40.00, "at": "2026-01-01"},
    ]
    result = outstanding_balance(100.00, events)
    assert result == {"outstanding": 75.00}


def test_reversal_cap_respects_as_of_cutoff():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-01"},
        {"id": "cb-1", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-02"},
        {"id": "cb-2", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-03"},
    ]
    partial = outstanding_balance(200.00, events, as_of="2026-01-02")
    assert partial == {"outstanding": 160.00}
    full = outstanding_balance(200.00, events, as_of="2026-01-03")
    assert full == {"outstanding": 200.00}


@pytest.mark.trap("float-precision")
def test_as_of_filtering_stays_exact():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 0.10, "at": "2026-01-01"},
        {"id": "pay-2", "type": "payment", "amount": 0.20, "at": "2026-01-02"},
    ]
    result = outstanding_balance(0.30, events, as_of="2026-01-01")
    assert result == {"outstanding": 0.20}
