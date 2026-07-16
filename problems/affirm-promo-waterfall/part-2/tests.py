import pytest
from solution import apply_promo


@pytest.mark.sample
def test_stacked_promos_apply_in_order_against_remaining_balance():
    result = apply_promo(
        50.00,
        [
            {"code": "HALF", "type": "percent_off", "value": 50},
            {"code": "FLAT30", "type": "amount_off", "value": 30.00},
        ],
    )
    assert result["final_amount"] == 0.00
    assert result["discount_amount"] == 50.00
    assert result["breakdown"] == [
        {"code": "HALF", "discount_amount": 25.00},
        {"code": "FLAT30", "discount_amount": 25.00},
    ]


@pytest.mark.sample
def test_second_promo_applies_to_post_discount_balance():
    result = apply_promo(
        100.00,
        [
            {"code": "TEN", "type": "percent_off", "value": 10},
            {"code": "TEN2", "type": "percent_off", "value": 10},
        ],
    )
    # 100 -> 90 (10% of 100) -> 81 (10% of 90), not 80 (10%+10% of the
    # original 100).
    assert result["final_amount"] == 81.00
    assert result["discount_amount"] == 19.00


def test_promo_after_balance_hits_zero_contributes_nothing():
    result = apply_promo(
        20.00,
        [
            {"code": "FULL", "type": "amount_off", "value": 20.00},
            {"code": "EXTRA", "type": "percent_off", "value": 50},
        ],
    )
    assert result["final_amount"] == 0.00
    assert result["breakdown"][1] == {"code": "EXTRA", "discount_amount": 0.00}


def test_single_promo_list_still_matches_part_one():
    result = apply_promo(
        199.99, [{"code": "SAVE10", "type": "percent_off", "value": 10}]
    )
    assert result["final_amount"] == 179.99


def test_empty_promo_list_still_matches_part_one():
    result = apply_promo(30.00, [])
    assert result["final_amount"] == 30.00
    assert result["breakdown"] == []


@pytest.mark.trap("remainder-distribution")
def test_stacked_rounding_stays_exact_across_cascades():
    # Each 15% cut lands exactly on a half-cent boundary. Rounding (or
    # subtracting) with naive floats after each step drifts the final
    # answer to 9.76; exact cent math across both cascades gives 9.75.
    result = apply_promo(
        13.50,
        [
            {"code": "A", "type": "percent_off", "value": 15},
            {"code": "B", "type": "percent_off", "value": 15},
        ],
    )
    assert result["final_amount"] == 9.75
    assert result["discount_amount"] == 3.75
    assert result["breakdown"][0]["discount_amount"] == 2.03
    assert result["breakdown"][1]["discount_amount"] == 1.72
