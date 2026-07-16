def allocate_payment(installments, payment):
    # apply oldest first
    balances = []
    for item in installments:
        pay = min(item["due"], payment)
        payment = payment - pay
        balances.append({"id": item["id"], "remaining": item["due"] - pay})
    return {"balances": balances}
