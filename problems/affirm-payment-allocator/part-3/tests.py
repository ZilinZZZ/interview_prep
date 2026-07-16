import pytest
from solution import allocate_payment


@pytest.mark.sample
def test_fee_paid_before_principal():
    result = allocate_payment([{"id": "a", "fee": 2.00, "principal": 8.00}], 5.00)
    balance = result["balances"][0]
    assert balance["fee_remaining"] == 0.0
    assert balance["principal_remaining"] == 5.0
    assert balance["remaining"] == 5.0
    assert result["credit"] == 0.0


def test_payment_smaller_than_fee():
    result = allocate_payment([{"id": "a", "fee": 3.00, "principal": 7.00}], 1.00)
    balance = result["balances"][0]
    assert balance["fee_remaining"] == 2.00
    assert balance["principal_remaining"] == 7.00


def test_legacy_due_shape_still_works():
    result = allocate_payment([{"id": "a", "due": 10.00}], 4.00)
    balance = result["balances"][0]
    assert balance["remaining"] == 6.00
    assert balance["fee_remaining"] == 0.0


def test_mixed_shapes_cascade_and_credit():
    result = allocate_payment(
        [{"id": "a", "fee": 1.00, "principal": 4.00}, {"id": "b", "due": 3.00}],
        9.00,
    )
    assert [b["remaining"] for b in result["balances"]] == [0.0, 0.0]
    assert result["credit"] == 1.00


@pytest.mark.trap("float-precision")
def test_fee_principal_split_is_exact():
    # float: principal_remaining comes out 0.050000000000000017, not 0.05
    result = allocate_payment([{"id": "a", "fee": 0.10, "principal": 0.20}], 0.25)
    balance = result["balances"][0]
    assert balance["fee_remaining"] == 0.0
    assert balance["principal_remaining"] == 0.05
    assert balance["remaining"] == 0.05
