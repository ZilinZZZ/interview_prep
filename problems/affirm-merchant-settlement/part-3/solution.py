from datetime import date, timedelta


def _to_cents(dollars):
    return round(dollars * 100)


def _apportion_fee_cents(amounts_cents, fee_rate, target_cents):
    """Largest-remainder apportionment: split target_cents across
    amounts_cents (in order) so the parts sum to exactly target_cents,
    keeping each part close to its raw (amount * fee_rate) share.
    """
    raw_shares = [amount_cents * fee_rate for amount_cents in amounts_cents]
    floors = [int(share) for share in raw_shares]
    remainders = [share - floor for share, floor in zip(raw_shares, floors)]

    leftover = target_cents - sum(floors)
    order_by_remainder = sorted(
        range(len(amounts_cents)), key=lambda i: (-remainders[i], i)
    )
    fee_cents = list(floors)
    for i in order_by_remainder[:leftover]:
        fee_cents[i] += 1
    return fee_cents


def compute_merchant_payouts(transactions, fee_rate):
    """Aggregate captures per merchant and net out the processing fee.

    All arithmetic in integer cents; merchants ordered by first appearance.
    Also returns a per-transaction fee_breakdown per merchant that sums
    exactly to that merchant's rounded fee total.
    """
    order = []
    txn_ids_by_merchant = {}
    amounts_cents_by_merchant = {}
    for txn in transactions:
        mid = txn["merchant_id"]
        if mid not in amounts_cents_by_merchant:
            amounts_cents_by_merchant[mid] = []
            txn_ids_by_merchant[mid] = []
            order.append(mid)
        amounts_cents_by_merchant[mid].append(_to_cents(txn["amount"]))
        txn_ids_by_merchant[mid].append(txn["id"])

    payouts = []
    for mid in order:
        amounts_cents = amounts_cents_by_merchant[mid]
        gross_cents = sum(amounts_cents)
        fee_cents = round(gross_cents * fee_rate)
        net_cents = gross_cents - fee_cents

        per_txn_fee_cents = _apportion_fee_cents(amounts_cents, fee_rate, fee_cents)
        fee_breakdown = [
            {"transaction_id": txn_id, "fee": fee_c / 100}
            for txn_id, fee_c in zip(txn_ids_by_merchant[mid], per_txn_fee_cents)
        ]

        payouts.append({
            "merchant_id": mid,
            "gross": gross_cents / 100,
            "fee": fee_cents / 100,
            "net": net_cents / 100,
            "fee_breakdown": fee_breakdown,
        })
    return {"payouts": payouts}


def _add_business_days(start, n):
    current = start
    added = 0
    while added < n:
        current = current + timedelta(days=1)
        if current.weekday() < 5:  # Mon-Fri
            added += 1
    return current


def schedule_disbursements(transactions, fee_rate, settlement_delay_days):
    """Bucket transactions by (merchant, settlement date) and net them out.

    Fees apply only to captures and are never refunded. All arithmetic in
    integer cents.
    """
    order = []
    gross_cents = {}
    refund_cents = {}
    for txn in transactions:
        captured_at = date.fromisoformat(txn["captured_at"])
        settlement_date = _add_business_days(captured_at, settlement_delay_days)
        key = (txn["merchant_id"], settlement_date.isoformat())
        if key not in gross_cents:
            gross_cents[key] = 0
            refund_cents[key] = 0
            order.append(key)

        amount_cents = _to_cents(txn["amount"])
        if txn["type"] == "capture":
            gross_cents[key] += amount_cents
        else:
            refund_cents[key] += amount_cents

    disbursements = []
    for key in sorted(order, key=lambda k: (k[1], k[0])):
        merchant_id, settlement_date = key
        gross = gross_cents[key]
        refunds = refund_cents[key]
        fee = round(gross * fee_rate)
        net = gross - refunds - fee
        disbursements.append({
            "merchant_id": merchant_id,
            "settlement_date": settlement_date,
            "gross": gross / 100,
            "refunds": refunds / 100,
            "fee": fee / 100,
            "net": net / 100,
        })
    return {"disbursements": disbursements}
