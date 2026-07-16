def compute_merchant_payouts(transactions, fee_rate):
    totals = {}
    for txn in transactions:
        mid = txn["merchant_id"]
        if mid not in totals:
            totals[mid] = 0
        totals[mid] += txn["amount"]

    payouts = []
    for mid, gross in totals.items():
        fee = gross * fee_rate
        payouts.append({
            "merchant_id": mid,
            "gross": gross,
            "fee": fee,
            "net": gross - fee,
        })
    return {"payouts": payouts}
