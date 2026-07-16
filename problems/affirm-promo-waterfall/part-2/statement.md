### Part 2 — Stacked promo codes

Marketing wants stacking. `promos` may now contain more than one entry.

- Apply promos **in list order**. Each promo's discount is computed against
  whatever amount remains *after* the promos before it — not the original
  `purchase_amount`.
- A promo can't push the running total below zero. If a promo's computed
  discount would exceed what's left, clamp it to exactly what's left (the
  remaining amount becomes `$0.00`). Any promo applied after the balance
  hits zero contributes `$0.00` and still gets a `breakdown` entry.
- `discount_amount` is still the total across all promos, and it must equal
  `purchase_amount - final_amount` exactly, cent for cent — no drift from
  rounding at each step.

Part 1 behavior is unchanged (a single-promo or empty list) — those tests
still run.

### Example

    apply_promo(
        50.00,
        [
            {"code": "HALF", "type": "percent_off", "value": 50},
            {"code": "FLAT30", "type": "amount_off", "value": 30.00},
        ],
    )
    == {
        "purchase_amount": 50.00,
        "discount_amount": 50.00,
        "final_amount": 0.00,
        "breakdown": [
            {"code": "HALF", "discount_amount": 25.00},
            {"code": "FLAT30", "discount_amount": 25.00},
        ],
    }
