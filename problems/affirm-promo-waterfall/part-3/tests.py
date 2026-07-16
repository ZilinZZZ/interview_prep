import pytest
from solution import apply_payment, apply_promo


@pytest.mark.sample
def test_payment_cascades_fee_then_interest_then_principal():
    result = apply_payment(
        {"fee_owed": 5.00, "interest_owed": 12.00, "principal_owed": 100.00}, 20.00
    )
    assert result == {
        "fee_owed": 0.0,
        "interest_owed": 0.0,
        "principal_owed": 97.0,
        "credit": 0.0,
    }


@pytest.mark.sample
def test_payment_smaller_than_fee_only_reduces_fee():
    result = apply_payment(
        {"fee_owed": 10.00, "interest_owed": 5.00, "principal_owed": 50.00}, 4.00
    )
    assert result["fee_owed"] == 6.00
    assert result["interest_owed"] == 5.00
    assert result["principal_owed"] == 50.00
    assert result["credit"] == 0.0


def test_overpayment_after_principal_becomes_credit():
    result = apply_payment(
        {"fee_owed": 0.0, "interest_owed": 0.0, "principal_owed": 10.00}, 15.00
    )
    assert result["principal_owed"] == 0.0
    assert result["credit"] == 5.00


def test_zero_payment_changes_nothing():
    result = apply_payment(
        {"fee_owed": 3.00, "interest_owed": 2.00, "principal_owed": 40.00}, 0.0
    )
    assert result == {
        "fee_owed": 3.00,
        "interest_owed": 2.00,
        "principal_owed": 40.00,
        "credit": 0.0,
    }


def test_payment_clears_fee_and_interest_leaves_principal_untouched():
    result = apply_payment(
        {"fee_owed": 2.00, "interest_owed": 3.00, "principal_owed": 25.00}, 5.00
    )
    assert result["fee_owed"] == 0.0
    assert result["interest_owed"] == 0.0
    assert result["principal_owed"] == 25.00
    assert result["credit"] == 0.0


def test_promo_from_earlier_parts_still_works():
    result = apply_promo(80.00, [{"code": "S", "type": "amount_off", "value": 10.00}])
    assert result["final_amount"] == 70.00


@pytest.mark.trap("float-precision")
def test_waterfall_leaves_exact_cents_not_float_epsilon():
    # 0.35 - 0.10 - 0.20 = 0.05 exactly. Naive float subtraction leaves
    # 0.04999999999999999, which then corrupts principal_owed and makes an
    # `if remaining > 0` style check misbehave.
    result = apply_payment(
        {"fee_owed": 0.10, "interest_owed": 0.20, "principal_owed": 5.00}, 0.35
    )
    assert result["fee_owed"] == 0.0
    assert result["interest_owed"] == 0.0
    assert result["principal_owed"] == 4.95
    assert result["credit"] == 0.0
