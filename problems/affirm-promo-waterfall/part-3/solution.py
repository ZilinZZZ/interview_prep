def _dollars_to_cents(amount):
    """Exact cents from a dollar amount that already has <= 2 decimal places."""
    return round(amount * 100)


def _round_half_up(numerator, denominator):
    """Integer division rounding .5 up, e.g. round_half_up(20250, 100) == 203."""
    return (numerator + denominator // 2) // denominator


def apply_promo(purchase_amount, promos):
    """Apply promo(s) to a purchase, in list order, cascading off the
    remaining balance. A promo's discount clamps to whatever remains so the
    running total never goes negative. All arithmetic in integer cents;
    discounts round half up to the cent.
    """
    purchase_cents = _dollars_to_cents(purchase_amount)
    remaining_cents = purchase_cents
    breakdown = []
    for promo in promos:
        if promo["type"] == "percent_off":
            discount_cents = _round_half_up(remaining_cents * promo["value"], 100)
        else:
            discount_cents = _dollars_to_cents(promo["value"])
        discount_cents = min(discount_cents, remaining_cents)
        remaining_cents -= discount_cents
        breakdown.append(
            {"code": promo["code"], "discount_amount": discount_cents / 100}
        )
    return {
        "purchase_amount": purchase_cents / 100,
        "discount_amount": (purchase_cents - remaining_cents) / 100,
        "final_amount": remaining_cents / 100,
        "breakdown": breakdown,
    }


def apply_payment(account, payment):
    """Apply a payment fee-first, then interest, then principal; leftover
    after principal is fully paid comes back as credit. All arithmetic in
    integer cents.
    """
    fee_cents = _dollars_to_cents(account["fee_owed"])
    interest_cents = _dollars_to_cents(account["interest_owed"])
    principal_cents = _dollars_to_cents(account["principal_owed"])
    remaining_cents = _dollars_to_cents(payment)

    fee_paid = min(fee_cents, remaining_cents)
    remaining_cents -= fee_paid
    interest_paid = min(interest_cents, remaining_cents)
    remaining_cents -= interest_paid
    principal_paid = min(principal_cents, remaining_cents)
    remaining_cents -= principal_paid

    return {
        "fee_owed": (fee_cents - fee_paid) / 100,
        "interest_owed": (interest_cents - interest_paid) / 100,
        "principal_owed": (principal_cents - principal_paid) / 100,
        "credit": remaining_cents / 100,
    }
