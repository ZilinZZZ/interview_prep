## Loan Refund & Chargeback Ledger

You're on the servicing team. Each loan has a principal balance. As payments
come in, the ledger's outstanding balance goes down. Later parts add refunds,
chargebacks, and point-in-time queries — for now, just payments.

### Part 1

Implement `outstanding_balance(principal, events)`.

- `principal`: the loan's original principal, in dollars, e.g. `500.00`.
- `events`: list of dicts, given **oldest first**. In this part every event
  is a payment: `{"id": "pay-1", "type": "payment", "amount": 25.00, "at": "2026-01-05"}`.
  Upstream billing guarantees payments never exceed the remaining balance;
  don't validate that, it's guaranteed.
- Return `{"outstanding": ...}` — the dollars still owed after applying every
  event. (The servicing API returns an object so we can extend it later.)

### Example

    outstanding_balance(500.00, [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "pay-2", "type": "payment", "amount": 50.00, "at": "2026-01-10"},
    ])
    == {"outstanding": 350.00}
