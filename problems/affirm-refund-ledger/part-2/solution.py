def _to_cents(dollars):
    return round(dollars * 100)


def outstanding_balance(principal, events):
    """Apply payments and reversals oldest-first; return balance still owed.

    Refunds/chargebacks add back onto the balance, capped so the lifetime
    total reversed against one payment never exceeds what it originally paid.
    All arithmetic in integer cents to avoid float drift.
    """
    outstanding_cents = _to_cents(principal)
    paid_cents = {}
    reversed_cents = {}
    for event in events:
        kind = event["type"]
        if kind == "payment":
            amount_cents = _to_cents(event["amount"])
            paid_cents[event["id"]] = amount_cents
            outstanding_cents -= amount_cents
        elif kind in ("refund", "chargeback"):
            ref = event["ref"]
            already = reversed_cents.get(ref, 0)
            headroom = paid_cents[ref] - already
            reverse_cents = min(_to_cents(event["amount"]), headroom)
            reversed_cents[ref] = already + reverse_cents
            outstanding_cents += reverse_cents
    return {"outstanding": outstanding_cents / 100}
