### Part 2 — Per-transaction fee ledger

Finance needs to reconcile fees down to the transaction, not just the
merchant total. Extend `compute_merchant_payouts` so each entry in
`"payouts"` also carries a `"fee_breakdown"`: one entry per transaction
that merchant had, in the order it appeared, `{"transaction_id": ...,
"fee": ...}`.

- Each transaction's "raw" fee share is `transaction_amount * fee_rate`.
  That raw share almost never lands on a whole cent.
- The `fee_breakdown` entries **must sum to exactly** the merchant's
  `"fee"` (the same rounded total from Part 1 — that figure doesn't
  change).
- Rule for who gets the leftover cent(s): give each transaction its raw
  fee **rounded down** to the cent, then hand out the remaining cents one
  at a time to the transactions with the **largest fractional remainder
  first**. If two transactions tie on remainder, the one that appears
  first for that merchant gets the cent.

`"payouts"` keeps its existing keys (`gross`, `fee`, `net`) with the same
values as Part 1 — that behavior must not change.

### Example

    compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-1", "amount": 1.00},
            {"id": "t2", "merchant_id": "merchant-1", "amount": 1.00},
            {"id": "t3", "merchant_id": "merchant-1", "amount": 1.00},
        ],
        0.0033,
    )
    # merchant fee rounds to 1 cent total; each transaction's raw share is
    # 0.33 cents (a three-way tie) — the leftover cent goes to t1, the
    # first transaction for that merchant.
    == {
        "payouts": [
            {
                "merchant_id": "merchant-1",
                "gross": 3.00,
                "fee": 0.01,
                "net": 2.99,
                "fee_breakdown": [
                    {"transaction_id": "t1", "fee": 0.01},
                    {"transaction_id": "t2", "fee": 0.0},
                    {"transaction_id": "t3", "fee": 0.0},
                ],
            },
        ]
    }
