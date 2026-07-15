# Affirm — Practical Coding (Backend)

## Logistics
- **Duration:** 60 min
- **Format:** Live coding with another engineer
- **Tooling:** HackerRank
- **Language:** Python (candidate's choice; kotlin/java/C++/js/go/ts also offered)
- **Starter code provided:** Y — interviewer presents it, candidate builds on it

## What it covers
Per the recruiter: an "Affirm flavored question that tests real-world coding skills," similar to day-to-day work at Affirm. Tests "commonly-used data structures, control statements, and coding fundamentals." Designed to get signal on "more than just coding, including debugging, code design, testing, communication & collaboration."

## Domain flavor
Consumer lending / payments. Installment loans, payment allocation, refunds, ledgers, merchant settlement, credit limits, fee & interest waterfalls, chargebacks, disbursement scheduling, promo/discount application.

Canonical archetype: **installment loan payment allocator** — allocate a payment across N installments oldest-first, then extend to partial payments, overpayment, fees-before-principal, out-of-order/multi-loan.

Every problem in this round is: model an entity, mutate it correctly under a sequence of events, get the arithmetic exactly right.

## Structure
Multi-part. "Questions may consist of multiple parts, so allocating your time wisely is important." 3–4 parts, strictly increasing.

- Part 1 (~15 min): trivially achievable. Establishes the model.
- Part 2 (~15 min): a rule that breaks the naive Part 1 shape.
- Part 3 (~15 min): a new dimension.
- Part 4 (stretch): scale, concurrency, or a planted bug.

## Explicitly graded
Debugging. Code design. Testing. Communication & collaboration. Thought process. **Responsiveness to interviewer feedback** — the description calls out "your ability to collaborate with them taking into account their feedback."

## Out of scope
Not a LeetCode round. No DP, tries, graph algorithms, DSU, backtracking. "Commonly-used data structures" is deliberately unambitious language: dicts, lists, sorting, grouping, deques. Algorithmic screening happens earlier in the loop.

Keep data-structure reflexes warm (`defaultdict`, `sorted(key=)`, `deque`, `dataclass`) but do not grind problems.

## Traps
- **Money as floats.** `0.1 + 0.2 != 0.3`. A `-1e-09` remaining balance silently corrupts an `if balance > 0` branch. The candidate should say "integer cents, unless the starter code dictates otherwise" within the first two minutes. Failing to raise this unprompted is the headline finding.
- **Remainder distribution.** $10.00 / 3 → 333/333/334. Which installment eats the extra cent? The rule must be stated, not stumbled into.
- **Starter code is imperfect on purpose.** May contain a bug, or floats where cents belong. Do not assume the scaffold is correct.
- **Gold-plating Part 1.** 25 minutes on Part 1 is a fail regardless of code quality.
- **Ignoring nudges.** The interviewer will interject. Stopping mid-thought to engage is the graded behavior.

## Anti-patterns for this round
- Reaching for pandas, numpy, or a Spark-shaped mental model. This is a dict-and-a-loop round.
- Building the streaming/distributed/threadsafe version before asked.
- `time.time()` inside business logic instead of injecting `now`.
- Rewriting the interviewer's scaffold into a preferred architecture.
- Generic naming — `arr`, `x`, `tmp` — instead of `installment`, `principal_cents`, `outstanding`.

## Time budget
| Phase | Minutes |
|---|---|
| Read + clarify + state assumptions | 5 |
| Part 1 working + 1–2 tests | 15 |
| Part 2 | 15 |
| Part 3 | 15 |
| Buffer / cleanup / edge cases | 10 |

## Prep drills
1. Payment allocator from a blank file, integer cents, oldest-first, 20 min timed. Extend twice without rewriting.
2. Ledger with refunds — apply, reverse, query balance at a point in time.
3. Read code aloud while writing it. Literally out loud.
4. Warm-up only: `defaultdict`, `sorted(key=lambda)`, `deque`, `dataclass`, `enumerate`, `zip`.

## Unknowns
- Does the starter code use floats, `Decimal`, or ints? (Ask the recruiter — they're generally forthcoming about round format.)
- Is there a planted bug in the scaffold?
