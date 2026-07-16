### Part 3 — The fee-interest-principal waterfall

Once financed, the promo-adjusted `final_amount` becomes principal on the
loan. Finance also attaches an origination fee and accrued interest. When a
payment comes in, apply it in a strict order: **fees first, then interest,
then principal.** Anything left over after principal is fully paid is
returned as credit.

Implement `apply_payment(account, payment)`.

- `account`: `{"fee_owed": ..., "interest_owed": ..., "principal_owed": ...}`
  — dollars, each `>= 0`.
- `payment`: dollars, `>= 0`.
- Return the updated account with all four keys: `"fee_owed"`,
  `"interest_owed"`, `"principal_owed"`, `"credit"` (dollars, exact to the
  cent).

`apply_promo` from Parts 1-2 is unchanged and those tests still run.

### Example

    apply_payment(
        {"fee_owed": 5.00, "interest_owed": 12.00, "principal_owed": 100.00},
        20.00,
    )
    == {"fee_owed": 0.0, "interest_owed": 0.0, "principal_owed": 97.0, "credit": 0.0}
