import pytest
from solution import outstanding_balance


@pytest.mark.sample
def test_refund_adds_back_to_balance():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-06"},
    ]
    assert outstanding_balance(500.00, events) == {"outstanding": 440.00}


@pytest.mark.sample
def test_chargeback_reversals_capped_at_original_payment():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "cb-1", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-06"},
        {"id": "cb-2", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-07"},
    ]
    assert outstanding_balance(500.00, events) == {"outstanding": 500.00}


def test_partial_refunds_across_two_payments():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-01"},
        {"id": "pay-2", "type": "payment", "amount": 50.00, "at": "2026-01-02"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 20.00, "at": "2026-01-03"},
        {"id": "refund-2", "type": "refund", "ref": "pay-2", "amount": 50.00, "at": "2026-01-04"},
    ]
    assert outstanding_balance(300.00, events) == {"outstanding": 220.00}


def test_full_refund_of_a_payment():
    events = [
        {"id": "pay-1", "type": "payment", "amount": 30.00, "at": "2026-01-01"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 30.00, "at": "2026-01-02"},
    ]
    assert outstanding_balance(30.00, events) == {"outstanding": 30.00}


@pytest.mark.trap("remainder-distribution")
def test_dime_refund_cascade_is_exact():
    # float: 0.40 - 0.10 - 0.20 + 0.05 leaves a residue, not exactly 0.15
    events = [
        {"id": "pay-1", "type": "payment", "amount": 0.10, "at": "2026-01-01"},
        {"id": "pay-2", "type": "payment", "amount": 0.20, "at": "2026-01-02"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 0.05, "at": "2026-01-03"},
    ]
    assert outstanding_balance(0.40, events) == {"outstanding": 0.15}
