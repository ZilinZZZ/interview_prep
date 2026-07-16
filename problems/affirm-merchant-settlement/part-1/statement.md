## Merchant Settlement & Disbursement Scheduler

You're on the merchant payouts team. Merchants run captures through Affirm
all day; at the end of the cycle we owe each merchant their money back,
minus our processing fee.

### Part 1

Implement `compute_merchant_payouts(transactions, fee_rate)`.

- `transactions`: list of dicts, each a captured charge:
  `{"id": "t1", "merchant_id": "merchant-42", "amount": 100.00}` (dollars).
  In this part every transaction is a successful capture — no refunds, no
  dates to worry about yet.
- `fee_rate`: our flat processing fee as a fraction, e.g. `0.03` for 3%.
- For each merchant, aggregate all of their transactions:
  - `gross`: sum of their transaction amounts.
  - `fee`: `gross * fee_rate`, rounded to the nearest cent.
  - `net`: `gross - fee` — what we actually disburse to the merchant.
- Return `{"payouts": [...]}`, one entry per merchant, `{"merchant_id":
  ..., "gross": ..., "fee": ..., "net": ...}`, in the order each
  merchant's first transaction appears in the input.

### Example

    compute_merchant_payouts(
        [
            {"id": "t1", "merchant_id": "merchant-42", "amount": 100.00},
            {"id": "t2", "merchant_id": "merchant-42", "amount": 50.00},
            {"id": "t3", "merchant_id": "merchant-7", "amount": 200.00},
        ],
        0.03,
    )
    == {
        "payouts": [
            {"merchant_id": "merchant-42", "gross": 150.00, "fee": 4.50, "net": 145.50},
            {"merchant_id": "merchant-7", "gross": 200.00, "fee": 6.00, "net": 194.00},
        ]
    }
