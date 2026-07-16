### Part 3 — Settlement-day scheduling and refunds

Now transactions carry a date, and can be refunds. We don't disburse
same-day — money settles a fixed number of **business days** later, and
refunds must net against whatever bucket they land in.

Implement `schedule_disbursements(transactions, fee_rate, settlement_delay_days)`.

- Each transaction now has a `"type"`, either `"capture"` or `"refund"`,
  and a `"captured_at"` date (`"YYYY-MM-DD"`, the date it posted).
- A transaction's **settlement date** is its `captured_at` date advanced
  by `settlement_delay_days` **business days** (Mon–Fri; weekends don't
  count and are skipped entirely — landing on a weekend is impossible).
- Group transactions into buckets by `(merchant_id, settlement_date)`.
  For each bucket:
  - `gross`: sum of `"capture"` amounts in the bucket.
  - `refunds`: sum of `"refund"` amounts in the bucket.
  - `fee`: `gross * fee_rate`, rounded to the nearest cent. Fees are
    **not refunded** — a refund reduces what's disbursed, but the fee
    already earned on the original capture stays earned.
  - `net`: `gross - refunds - fee`.
- Return `{"disbursements": [...]}`, one entry per bucket:
  `{"merchant_id": ..., "settlement_date": ..., "gross": ..., "refunds":
  ..., "fee": ..., "net": ...}`, sorted by `settlement_date` then
  `merchant_id`.

Parts 1 and 2 (`compute_merchant_payouts`) must keep passing unchanged.

### Example

Assume `settlement_delay_days=2` and `2026-07-13` is a Monday (so it
settles Wednesday `2026-07-15`), `2026-07-16` is a Thursday (skips the
weekend, settling Monday `2026-07-20`).

    schedule_disbursements(
        [
            {"id": "t1", "merchant_id": "m1", "type": "capture", "amount": 100.00, "captured_at": "2026-07-13"},
            {"id": "t2", "merchant_id": "m1", "type": "capture", "amount": 50.00, "captured_at": "2026-07-13"},
            {"id": "t3", "merchant_id": "m1", "type": "capture", "amount": 20.00, "captured_at": "2026-07-16"},
            {"id": "t4", "merchant_id": "m1", "type": "refund", "amount": 10.00, "captured_at": "2026-07-16"},
        ],
        0.03,
        2,
    )
    == {
        "disbursements": [
            {"merchant_id": "m1", "settlement_date": "2026-07-15", "gross": 150.00, "refunds": 0.0, "fee": 4.50, "net": 145.50},
            {"merchant_id": "m1", "settlement_date": "2026-07-20", "gross": 20.00, "refunds": 10.00, "fee": 0.60, "net": 9.40},
        ]
    }
