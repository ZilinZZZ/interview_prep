## Promo Discount & Payment Waterfall

Affirm approves a purchase, but checkout may attach a promo code before the
loan is created, and Finance layers a fee and interest onto whatever ends up
financed. Today you're building the promo step.

### Part 1

Implement `apply_promo(purchase_amount, promos)`.

- `purchase_amount`: dollars, e.g. `199.99`.
- `promos`: a list of promo dicts. **In this part, checkout only ever attaches
  at most one active promo code** — the list has length 0 or 1. Don't defend
  against more than one; that's guaranteed for now.
  - `{"code": "SAVE10", "type": "percent_off", "value": 10}` — `value` is a
    whole-number percent, `0`-`100`.
  - `{"code": "FLAT20", "type": "amount_off", "value": 20.00}` — `value` is a
    dollar amount. Guaranteed to be no larger than `purchase_amount`.
- Round every discount to the nearest cent, **half up** (a computed discount
  of `$2.025` rounds to `$2.03`, not `$2.02`).
- Return:
  ```
  {
      "purchase_amount": ...,
      "discount_amount": ...,   # total discount, dollars
      "final_amount": ...,      # purchase_amount - discount_amount
      "breakdown": [{"code": ..., "discount_amount": ...}, ...],
  }
  ```
  `breakdown` has one entry per promo applied, in order (empty list if no
  promo). Dashboards read `breakdown` directly; keep it even though right now
  it's redundant with `discount_amount`.

### Example

    apply_promo(199.99, [{"code": "SAVE10", "type": "percent_off", "value": 10}])
    == {
        "purchase_amount": 199.99,
        "discount_amount": 20.00,
        "final_amount": 179.99,
        "breakdown": [{"code": "SAVE10", "discount_amount": 20.00}],
    }
