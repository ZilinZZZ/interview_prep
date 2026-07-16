### Part 2 — Partial payments and overpayment

The exact-cover guarantee is gone. Real payments are any amount.

- A payment may **partially** cover an installment: pay it down, and any
  leftover cascades to the next-oldest installment.
- A payment may exceed everything owed. Whatever is left after all
  installments are cleared is returned to the customer as **credit**.
- Add a `"credit"` key to the result: dollars left over (`0.0` when the
  payment was fully absorbed).

Part 1 behavior must not change — those tests still run.

### Example

    allocate_payment([{"id": "a", "due": 10.00}], 12.50)
    == {"balances": [{"id": "a", "remaining": 0.0}], "credit": 2.50}
