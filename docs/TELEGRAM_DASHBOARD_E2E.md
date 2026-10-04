# Telegram → saved dashboard evidence verification

Executed 4 October 2026 against an isolated local PostgreSQL 15.12 cluster.
This is a **synthetic integration test**, not a real Telegram-client or hosted
Render/Vercel test. The model and Telegram delivery adapter are deterministic
fixtures; no real payment, booking, call, or third-party message was sent.

## Executed coverage

`tests/test_telegram_dashboard_e2e.py` sends updates through the authenticated
FastAPI Telegram webhook, configures a budget through the operator API, processes
model proposals, dispatches replies to the fake Telegram adapter, and reads the
saved dashboard API at each stage:

1. Reject missing webhook/operator credentials; accept one message and deduplicate
   its repeated delivery.
2. Persist an exact-action approval proposal and outgoing approval card.
3. Reject a different chat's approval; accept the owner once; deduplicate callbacks.
4. Persist Telegram `/pause` and `/resume` state.
5. Save labelled operation-result evidence through `/api/evidence`; keep the
   overall outcome open after payment reconciliation.
6. Save separately labelled physical-outcome evidence, then close as a rehearsal
   only when the deterministic model requests closure against that evidence.
7. Reload the app and Store from the same database and compare messages,
   operations, decisions, evidence, delivery, and commitment state exactly.
8. Check selected-chat isolation, dashboard authentication and no-store responses.

The PostgreSQL run explicitly asserts `Store.postgres`, checks `SELECT version()`
and a unique `tarang_test_*` schema. There is no SQLite fallback in that run.
Each fixture schema is removed after its test. Normal runs also exercise the same
journey on SQLite.

The new journey and existing dashboard, public-demo, and intake tests passed:
**31 passed**, with one pre-existing Starlette/httpx deprecation warning. Public
visitors' demo sessions, conversation isolation, capture, reset/deletion and intake
state were included through the existing suites; these remain simulated sessions.

## Failure discovered and fixed

The first PostgreSQL run failed 2 tests (29 passed). PostgreSQL rejected Python
booleans bound to the schema's BIGINT flags (`budgets.delegated`). The same binding
also affects evidence verification and Telegram pause/resume. SQLite accepts these
implicitly and had hidden the defect. `PostgresConnection.execute` now binds Python
bool values as integer 0/1, matching the existing schema; no migration is required.
The journey now tests all three paths, including false and true values. A small
adapter regression checks parameter types during the standard no-server test run.

## Reproduce and inspect

Start an isolated, disposable PostgreSQL database using your normal local setup.
Never point this test at the hosted private database. Set `TARANG_TEST_POSTGRES` to
that database's connection URL, then run:

```bash
.venv/bin/python -m pytest -q tests/test_telegram_dashboard_e2e.py tests/test_dashboard.py tests/test_public_demo.py tests/test_intake.py
```

Optionally set `TARANG_E2E_ARTIFACT` to a local JSON output path to capture the new
journey. Artifact generation requires PostgreSQL and occurs only after all journey
assertions pass. A sanitized fixture-only run is retained at
[testing/telegram-dashboard-postgres-e2e.json](testing/telegram-dashboard-postgres-e2e.json).
Its `sent` states mean the fake adapter returned successfully, not Telegram service
delivery. All evidence has `illustrative-fixture` provenance. Timestamps are actual
local execution timestamps; dialogue and operation outcomes are fixtures.

## Gate before the final demo

This test does not verify live OpenRouter decisions, a Telegram-origin message,
Telegram-client delivery, Render deployment, Vercel API proxying, or browser polling.
After the approved GitHub release updates both frontend and backend, send one
consented rehearsal message from the actual Telegram client, retain its update and
chat correlation privately, verify its reply and matching saved dashboard evidence,
then reload the production dashboard to verify persistence. Record the final demo
only after that hosted round trip passes. Do not relabel these fixture artifacts as
live integration proof.
