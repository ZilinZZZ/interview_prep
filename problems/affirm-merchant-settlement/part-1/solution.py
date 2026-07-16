def _to_cents(dollars):
    return round(dollars * 100)


def compute_merchant_payouts(transactions, fee_rate):
    """Aggregate captures per merchant and net out the processing fee.

    All arithmetic in integer cents; merchants ordered by first appearance.
    """
    order = []
    gross_cents_by_merchant = {}
    for txn in transactions:
        mid = txn["merchant_id"]
        if mid not in gross_cents_by_merchant:
            gross_cents_by_merchant[mid] = 0
            order.append(mid)
        gross_cents_by_merchant[mid] += _to_cents(txn["amount"])

    payouts = []
    for mid in order:
        gross_cents = gross_cents_by_merchant[mid]
        fee_cents = round(gross_cents * fee_rate)
        net_cents = gross_cents - fee_cents
        payouts.append({
            "merchant_id": mid,
            "gross": gross_cents / 100,
            "fee": fee_cents / 100,
            "net": net_cents / 100,
        })
    return {"payouts": payouts}
