### Part 3 — Point-in-time balance

Auditors want to know what a loan's balance was on a given date, and the
event feed isn't reliable about ordering — retries and backfills mean events
can arrive **out of chronological order** in the list you're handed.

- Add an optional `as_of` parameter: `outstanding_balance(principal, events, as_of=None)`.
- When `as_of` is given (an `"at"`-format date string), only events with
  `"at" <= as_of` count toward the balance — as if later events hadn't
  happened yet.
- When `as_of` is omitted, behavior is unchanged (every event counts).
- `events` may now be given in **any order** — sort by `"at"` yourself
  before applying the Part 1/2 rules. (A payment can still appear after its
  own reversal in the list you're handed, even though it happened first.)
- Parts 1 and 2 must keep passing (those tests call you with no `as_of`,
  using chronologically-sorted lists, same as before).

### Example

    events = [
        {"id": "pay-1", "type": "payment", "amount": 100.00, "at": "2026-01-05"},
        {"id": "refund-1", "type": "refund", "ref": "pay-1", "amount": 40.00, "at": "2026-01-10"},
    ]
    outstanding_balance(500.00, events, as_of="2026-01-07") == {"outstanding": 400.00}
    outstanding_balance(500.00, events, as_of="2026-01-10") == {"outstanding": 440.00}
