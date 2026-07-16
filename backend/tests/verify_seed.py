"""Verify the seed problem: solutions pass, starter fails ONLY the traps,
and every part-N solution still passes parts 1..N (forward compatibility)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
from app import runner  # noqa: E402

SEED = Path(__file__).parent.parent.parent / "problems" / "affirm-payment-allocator"


def check(label, ok):
    print(("PASS " if ok else "FAIL ") + label)
    return ok


def outcomes(result):
    return {t["name"]: t["outcome"] for t in result["tests"]}


def main():
    all_ok = True

    # 1. Each part's solution passes ALL tests up to and including its part.
    for n in (1, 2, 3):
        code = (SEED / f"part-{n}" / "solution.py").read_text(encoding="utf-8")
        result = runner.run_tests(SEED, code, part=n, mode="submit")
        ok = result["exit_code"] == 0 and all(
            o == "passed" for o in outcomes(result).values()
        )
        all_ok &= check(f"part-{n} solution green through part {n}", ok)

    # 2. Final solution passes EVERYTHING (the abstraction survived).
    final = (SEED / "part-3" / "solution.py").read_text(encoding="utf-8")
    result = runner.run_tests(SEED, final, part=3, mode="submit")
    all_ok &= check(
        "part-3 solution green on all parts",
        all(o == "passed" for o in outcomes(result).values()),
    )

    # 3. Starter passes both part-1 samples but fails the part-1 trap.
    starter = (SEED / "part-1" / "starter.py").read_text(encoding="utf-8")
    result = runner.run_tests(SEED, starter, part=1, mode="submit")
    out = outcomes(result)
    all_ok &= check(
        "starter passes samples",
        out["test_payment_clears_oldest_installment"] == "passed"
        and out["test_zero_payment_changes_nothing"] == "passed",
    )
    all_ok &= check(
        "starter FAILS float-precision trap",
        out["test_dime_installments_leave_exact_zero"] == "failed",
    )
    trap = [t for t in result["tests"] if t["name"] == "test_dime_installments_leave_exact_zero"][0]
    all_ok &= check("trap carries its label", trap["trap"] == "float-precision")

    # 4. A float-based part-2 attempt trips the remainder-distribution traps.
    float_v2 = '''
def allocate_payment(installments, payment):
    balances = []
    for item in installments:
        pay = min(item["due"], payment)
        payment = payment - pay
        balances.append({"id": item["id"], "remaining": item["due"] - pay})
    return {"balances": balances, "credit": payment}
'''
    result = runner.run_tests(SEED, float_v2, part=2, mode="submit")
    out = outcomes(result)
    all_ok &= check(
        "float part-2 impl FAILS credit-exactness trap",
        out["test_credit_is_exact_after_cascading"] == "failed",
    )
    all_ok &= check(
        "float part-2 impl FAILS boundary-balance trap",
        out["test_boundary_installment_balance_is_exact"] == "failed",
    )

    # 5. A float-based part-3 attempt trips the fee-split trap.
    float_v3 = '''
def allocate_payment(installments, payment):
    balances = []
    for item in installments:
        fee = item.get("fee", 0.0)
        principal = item.get("principal", item.get("due", 0.0))
        fee_paid = min(fee, payment)
        payment -= fee_paid
        pr_paid = min(principal, payment)
        payment -= pr_paid
        balances.append({
            "id": item["id"],
            "fee_remaining": fee - fee_paid,
            "principal_remaining": principal - pr_paid,
            "remaining": (fee - fee_paid) + (principal - pr_paid),
        })
    return {"balances": balances, "credit": payment}
'''
    result = runner.run_tests(SEED, float_v3, part=3, mode="submit")
    out = outcomes(result)
    all_ok &= check(
        "float part-3 impl FAILS fee-split trap",
        out["test_fee_principal_split_is_exact"] == "failed",
    )

    print("\nALL CHECKS PASSED" if all_ok else "\nSOME CHECKS FAILED")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
