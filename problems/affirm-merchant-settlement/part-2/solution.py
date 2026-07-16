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
