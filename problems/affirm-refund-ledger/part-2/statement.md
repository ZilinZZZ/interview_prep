### Part 2 — Refunds and chargebacks

Payments aren't always final. A refund (customer-initiated) or a chargeback
(card-network-forced) reverses some or all of an earlier payment — the
outstanding balance goes back up.

- New event types, each with a `"ref"` (the `"id"` of the payment being
  reversed) and an `"amount"` (dollars to reverse):
  `{"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-06"}`
  `{"id": "cb-1", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-07"}`
- Refunds and chargebacks affect the ledger identically: they add their
  `"amount"` back onto the outstanding balance.
- A single payment can be reversed more than once (a partial refund now, a
  chargeback later). The **total** ever reversed against one payment can
  never exceed that payment's original `"amount"` — cap it there, don't
  raise.
- `"ref"` always points at a payment earlier in the list. Part 1 behavior
  must not change.

### Example

    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "cb-1", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-06"},
        {"id": "cb-2", "type": "chargeback", "ref": "pay-1", "amount": 60.00, "at": "2026-01-07"},
    ]
    outstanding_balance(500.00, events) == {"outstanding": 500.00}
    # cb-1 and cb-2 together ask for 120.00 against a 100.00 payment; capped at 100.00
