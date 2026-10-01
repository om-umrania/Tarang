# Python prototype: run and verify

Implemented 1 October 2026. Local contract tests are distinct from a live OpenRouter model,
Telegram connection and deployed service. Current setup status is in HANDOFF.md.

## Start locally

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m tarang.setup
.venv/bin/python -m uvicorn tarang.app:app --host 127.0.0.1 --port 8766 --workers 1
```

Setup prompts hide credentials, validate the bot and model, then bind your numeric
Telegram ID from a real private `/start` update. Alternatively edit ignored `.env`
using [.env.example](../.env.example). The local `.env` overrides stale shell keys.
Never put tokens in chat, Git, a URL, shell command arguments or screen recordings.
Generate OPERATOR_TOKEN and TELEGRAM_WEBHOOK_SECRET as random 32-byte secrets if
setting up on a new machine. The current workspace has generated local values.

Open the operator console at `http://127.0.0.1:8766/`; enter OPERATOR_TOKEN from
`.env`. It is held only in the page, never persisted in browser storage. All data
endpoints require a bearer token. Telegram only accepts allowlisted private chats;
no first-message auto-enrolment. `/pause` immediately holds model-generated effects;
`/resume` resumes observations; `/status` displays persistent state. A single
commitment is tracked per chat in this first slice; group/multi-wedding support
and opening a second outcome in the same chat need a later data-model iteration.

## What runs

FastAPI accepts authenticated Telegram webhooks or uses long polling (default).
Updates are durably deduplicated. A single process runs model decision jobs,
clock-derived due checks and a message outbox. The selected model through OpenRouter receives persona, policy,
schema and structured state. Pydantic validates every proposal. Monetary values
are INR paise. The operator console configures actual rehearsal authority; no
scenario budget is silently installed.

SQLite uses transactions and WAL. A process lock prevents concurrent workers on
one database. Every unresolved outcome gets a persisted next check, including
failures and waiting approvals. Restart recovers interrupted model decisions;
sending Telegram messages interrupted by a crash become **unknown**, not blindly
resent (Telegram sendMessage has no caller-supplied idempotency key). Unknown
messages currently require operator investigation in the ledger; there is no
automatic resend button. Back up the database using SQLite's backup API, not a
copy of just the main file while WAL is active.

## Authority and evidence

Payment, booking and shipment requests require a positive total exposure and a
configured category ceiling. Approval, queued, unknown and successful obligations
all count against available room. Autonomous dispatch additionally requires exact
recipient, action kind and specification equality with the delegated scope and an
amount within its cap. Otherwise the runtime sends an exact approval card, valid
until the proposal expiry and consumable only once by that private chat's owner.
No blanket authority is inferred from prose. Scope matching is intentionally
conservative; changed specifications ask again.

An unresolved financial operation blocks another financial operation on the same
commitment. A booking and later payment must not double-charge or double-reserve:
this slice treats the original operation as the obligation and records its result;
it does not implement a full payable/payment allocation model.

All partner operations stop in **operator_pending**. The operator executes the
approved request through a supported rail, then records exact response + source:
`manual-real-api`, `documented-response`, `illustrative-fixture`, or
`human-verification`. These labels do not certify a vendor's API; the operator is
responsible for truthful provenance. Real payment/call/shipment adapters are not
connected. For Gnani competition evidence, a fixture is insufficient: run its
actual API and retain the exact response. No endpoints are invented here.

Only operator-attested outcome evidence can close a commitment, and only once
pending/unknown financial operations are reconciled. Illustrative or documented
response closure is labelled rehearsal closure. Runtime status cards replace model
copy for operational proposals/closure; ordinary conversational model copy still
needs persona and factuality evaluation with a working model credential.

## Rehearse both journeys

1. Talk to the bot about one concrete outcome, deadline and designated verifier.
2. Configure a category budget and delegation only where approved. For courier,
   use the agreed exact ₹1,200 scope and recipient; the ₹5,000 cap remains a demo
   choice, not a global default. For décor, do not enable blanket delegation.
3. Let the model request investigation. Record real or explicitly labelled source
   evidence through the console. The operator supplies events, not the decision.
4. Inspect the generated proposal: décor should ask for ₹40,000 authority;
   an exact delegated ₹1,200 courier request should enter the operator queue.
   No configured courier budget means spending is blocked until a budget exists.
5. Record operation results; unknown results remain reserved. Provide physical
   outcome evidence separately (all 200 undamaged hampers / approved décor on time).
6. Verify ledger, approval expiry, pause, duplicate input and restart. Leave one
   due check unattended and verify the clock event without messaging the bot.

Tests use a deterministic fake model and fake Telegram adapter; they prove policy
and persistence contracts, not model intelligence or actual partner connectivity.
Run `python3 -m pytest -q` and `./scripts/check.sh`.

## Free Render deployment

Om chose existing/free resources first. [render.yaml](../render.yaml) specifies a
free Python web service and free PostgreSQL database. The deployed app uses
`DATABASE_URL`; local use defaults to SQLite. Short database transactions use an
advisory lock, and a separate lifetime advisory lock prevents multiple workers.
Run one process. This is a prototype, not a horizontally scaled queue system.

Use Telegram webhooks on the free host: messages wake the service. Free compute
can sleep after 15 minutes without inbound traffic; due checks stay persisted but
execute late on the next wake. No artificial keepalive service is configured.
Always-on monitoring needs a later hosting decision. The free database created
for this prototype expires **31 October 2026**; export/migrate it before then.
[Render free limits](https://render.com/docs/free).

Render secrets are loaded from `/etc/secrets/tarang.env` when using CLI secret-file
deployment, or normal environment variables with the Blueprint. Never use a free
service's filesystem for persistent state. The database disallows public inbound
connections; hosted services access it on Render's private network.

Telegram webhook verification uses a separate secret header. Do not run local
polling while the webhook is active. Hosting costs are free for the selected tier;
OpenRouter token usage is separate. Gemini 3.8 Flash was the selected starting
model after a successful structured-output and incomplete-delivery smoke test;
this is a candidate choice, not a completed comparative benchmark. Subsequent
hosted calls returned HTTP 402: model credits/fallback selection need resolution
(see handoff), even though the key itself validates. A tested free Nemotron
candidate is the temporary MODEL default and its hosted synthetic check passed; free provider capacity/rate limits
can still interrupt requests.

After deployment, verify health, a real Telegram turn, an unattended due check
while the service is awake and restart persistence. Operator evidence and all
state APIs require the bearer token. Retention, key rotation, migrations,
production backup/restore and proactive alerting are follow-up work.

API contracts referenced: [Telegram Bot API](https://core.telegram.org/bots/api),
[OpenRouter structured outputs](https://openrouter.ai/docs/guides/features/structured-outputs).

## WhatsApp conflict inbox

See [WHATSAPP.md](WHATSAPP.md) for the receive-only adapter, scoped routes, webhook
configuration and limitations. Intake defaults to disabled. Existing groups, voice
notes and historical chats are not connected. Source-quoted possible conflicts appear
in the operator console; live WhatsApp delivery remains unverified.
