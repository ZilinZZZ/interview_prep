import pytest
from solution import outstanding_balance


@pytest.mark.sample
def test_two_payments_reduce_balance():
    result = outstanding_balance(500.00, [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "pay-2", "type": "payment", "amount": 50.00, "at": "2026-01-10"},
    ])
    assert result == {"outstanding": 350.00}


@pytest.mark.sample
def test_no_events_full_principal_owed():
    result = outstanding_balance(200.00, [])
    assert result == {"outstanding": 200.00}


def test_single_payment():
    result = outstanding_balance(75.00, [
        {"id": "pay-1", "type": "payment", "amount": 25.00, "at": "2026-01-01"},
    ])
    assert result == {"outstanding": 50.00}


def test_payments_paid_in_full():
    result = outstanding_balance(60.00, [
        {"id": "pay-1", "type": "payment", "amount": 20.00, "at": "2026-01-01"},
        {"id": "pay-2", "type": "payment", "amount": 20.00, "at": "2026-01-02"},
        {"id": "pay-3", "type": "payment", "amount": 20.00, "at": "2026-01-03"},
    ])
    assert result == {"outstanding": 0.0}


@pytest.mark.trap("float-precision")
def test_dime_payments_leave_exact_zero():
    # float: 0.30 - 0.10 - 0.20 leaves a tiny residue, not 0.0
    result = outstanding_balance(0.30, [
        {"id": "pay-1", "type": "payment", "amount": 0.10, "at": "2026-01-01"},
        {"id": "pay-2", "type": "payment", "amount": 0.20, "at": "2026-01-02"},
    ])
    assert result == {"outstanding": 0.0}
