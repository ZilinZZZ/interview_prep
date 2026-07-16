def allocate_payment(installments, payment):
    """Allocate oldest-first. All arithmetic in integer cents."""
    remaining_cents = round(payment * 100)
    balances = []
    for installment in installments:
        due_cents = round(installment["due"] * 100)
        paid = min(due_cents, remaining_cents)
        remaining_cents -= paid
        balances.append({"id": installment["id"], "remaining": (due_cents - paid) / 100})
    return {"balances": balances}
