## Installment Payment Allocator

You're on the servicing team. A customer's purchase is split into fixed
installments. When a payment arrives, apply it to installments **oldest
first** and report what's still owed.

### Part 1

Implement `allocate_payment(installments, payment)`.

- `installments`: list of dicts, oldest first. Each has an `"id"` (string)
  and `"due"` (dollars): `{"id": "inst-1", "due": 25.00}`
- `payment`: dollars. In this part, upstream billing guarantees every payment
  exactly covers a whole number of installments, oldest first. Don't validate
  that; it's guaranteed.
- Return `{"balances": [...]}` — one entry per installment, **original
  order**, each `{"id": ..., "remaining": ...}`. (The servicing API returns
  an object so we can extend it later.)

### Example

    allocate_payment(
        [{"id": "a", "due": 25.00}, {"id": "b", "due": 25.00}],
        25.00,
    )
    == {"balances": [{"id": "a", "remaining": 0.0}, {"id": "b", "remaining": 25.0}]}
