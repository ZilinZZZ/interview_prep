def _to_cents(dollars):
    return round(dollars * 100)


def allocate_payment(installments, payment):
    """Oldest-first; within an installment fees before principal.

    Accepts {"fee", "principal"} or legacy {"due"} (principal-only).
    All arithmetic in integer cents.
    """
    remaining_cents = _to_cents(payment)
    balances = []
    for installment in installments:
        fee_cents = _to_cents(installment.get("fee", 0.0))
        if "principal" in installment:
            principal_cents = _to_cents(installment["principal"])
        else:
            principal_cents = _to_cents(installment["due"])

        fee_paid = min(fee_cents, remaining_cents)
        remaining_cents -= fee_paid
        principal_paid = min(principal_cents, remaining_cents)
        remaining_cents -= principal_paid

        fee_left = fee_cents - fee_paid
        principal_left = principal_cents - principal_paid
        balances.append({
            "id": installment["id"],
            "fee_remaining": fee_left / 100,
            "principal_remaining": principal_left / 100,
            "remaining": (fee_left + principal_left) / 100,
        })
    return {"balances": balances, "credit": remaining_cents / 100}
