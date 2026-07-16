def _to_cents(dollars):
    return round(dollars * 100)


def outstanding_balance(principal, events):
    """Apply payments oldest-first; return the balance still owed.

    All arithmetic in integer cents to avoid float drift.
    """
    outstanding_cents = _to_cents(principal)
    for event in events:
        if event["type"] == "payment":
            outstanding_cents -= _to_cents(event["amount"])
    return {"outstanding": outstanding_cents / 100}
