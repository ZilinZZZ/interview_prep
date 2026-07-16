import pytest
from solution import apply_promo


def slim(result):
    return (result["discount_amount"], result["final_amount"])


@pytest.mark.sample
def test_percent_off_discount():
    result = apply_promo(
        199.99, [{"code": "SAVE10", "type": "percent_off", "value": 10}]
    )
    assert result["discount_amount"] == 20.00
    assert result["final_amount"] == 179.99
    assert result["breakdown"] == [{"code": "SAVE10", "discount_amount": 20.00}]


@pytest.mark.sample
def test_amount_off_discount():
    result = apply_promo(50.00, [{"code": "FLAT5", "type": "amount_off", "value": 5.00}])
    assert slim(result) == (5.00, 45.00)


def test_no_promo_returns_full_price():
    result = apply_promo(30.00, [])
    assert result["discount_amount"] == 0.0
    assert result["final_amount"] == 30.00
    assert result["breakdown"] == []


def test_amount_off_exactly_covers_purchase():
    result = apply_promo(15.00, [{"code": "FREE", "type": "amount_off", "value": 15.00}])
    assert slim(result) == (15.00, 0.00)


def test_purchase_amount_echoed_back():
    result = apply_promo(88.88, [{"code": "P", "type": "percent_off", "value": 25}])
    assert result["purchase_amount"] == 88.88


@pytest.mark.trap("float-precision")
def test_percent_discount_rounds_half_up_at_cent_boundary():
    # 13.50 * 15% = $2.025 exactly, sitting on the half-cent boundary.
    # Naive float math (and round(x, 2)) gives 2.02 because 2.025 isn't
    # exactly representable in binary. The stated rule is round-half-up,
    # so the correct discount is 2.03.
    result = apply_promo(13.50, [{"code": "MID", "type": "percent_off", "value": 15}])
    assert result["discount_amount"] == 2.03
    assert result["final_amount"] == 11.47
