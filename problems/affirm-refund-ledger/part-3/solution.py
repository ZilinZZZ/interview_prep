def _to_cents(dollars):
    return round(dollars * 100)


def outstanding_balance(principal, events, as_of=None):
    """Apply payments and reversals in chronological order; optionally as of a date.

    `events` may arrive in any order (retries/backfills) — sort by `"at"`
    before applying the Part 1/2 rules. When `as_of` is given, only events
    at or before that date count toward the balance.
    All arithmetic in integer cents to avoid float drift.
    """
    ordered = sorted(events, key=lambda event: event["at"])
    if as_of is not None:
        ordered = [event for event in ordered if event["at"] <= as_of]

    outstanding_cents = _to_cents(principal)
    paid_cents = {}
    reversed_cents = {}
    for event in ordered:
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
