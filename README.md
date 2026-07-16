# Interview Practice Platform

Local practice harness for multi-part practical-coding interview rounds.
Statement left, Monaco editor right, pytest results below. Localhost only.

## Setup (once)

    npm run setup

## Run

    npm run dev        # or: make dev

Backend: http://127.0.0.1:8000 · Frontend: http://localhost:5173

## Adding a problem

Make a folder under `problems/` — see
`docs/superpowers/specs/2026-07-15-interview-platform-design.md` for the format.
No registration step; it appears in the list on refresh.

To have Claude Code write one for you: `/generate-problem <interview>`
(e.g. `/generate-problem affirm-practical-coding`). Check any problem folder,
hand-written or generated, with
`backend\.venv\Scripts\python scripts\validate_problem.py <id>`.

## Tests

    npm run test:api   # backend (pytest)
    npm run test:web   # frontend logic (vitest)
