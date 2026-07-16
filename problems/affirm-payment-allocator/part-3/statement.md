### Part 3 — Fees and principal

Finance now splits each installment into a **fee** and **principal**.
Within an installment, money pays the fee first, then principal.

- New installment shape: `{"id": "a", "fee": 2.00, "principal": 23.00}`
- The old billing service still sends `{"id": "a", "due": 25.00}` — treat
  those as principal-only (`fee = 0`). Both shapes can appear in one call.
- Each balance entry now also reports `"fee_remaining"` and
  `"principal_remaining"`. Keep `"remaining"` (their sum) — dashboards
  depend on it. Keep `"credit"`.

Parts 1 and 2 must keep passing.

### Example

    allocate_payment([{"id": "a", "fee": 2.00, "principal": 8.00}], 5.00)
    == {
        "balances": [
            {"id": "a", "fee_remaining": 0.0, "principal_remaining": 5.0, "remaining": 5.0}
        ],
        "credit": 0.0,
    }
