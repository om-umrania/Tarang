# Tarang handoff · updated 3 October 2026

## Interactive Telegram prototype

The public fictional conversation is live at
[Tarang demo](https://t.me/tarang_wedding_bot?start=demo). Send `/start demo`, then
choose **Start a conversation** or send `/talk`. Answer with buttons, `/choose N`,
or fictional free text. Intake asks for problem, deadline, contact, decision maker,
verifier, constraints and priority, then reviews the plan before simulated action
and feedback. The operational wedding workspace remains allowlisted.

Actual Mac Telegram verification covered welcome, real button callbacks, typed
details, a deadline correction preserving other facts, contact rehearsal, feedback
and keyboard pause/resume. 58 runtime tests and static checks passed; all 23
public-demo/intake tests also passed against disposable PostgreSQL. The real-client
test exposed and repaired a PostgreSQL percent-placeholder webhook failure.

Runtime commit `6714a273d8e987b14d26e655de7f1998806a17b2` is deployed. See
[INTERACTIVE_TESTING.md](INTERACTIVE_TESTING.md) for evidence, private receipt
pointers and limits. The full persona rubric remains unexecuted and vendor actions
remain fictional; this is not production fulfilment evidence.

## Live prototype

- Bot: https://t.me/tarang_wedding_bot (public fictional demo; allowlisted operations).
- App/operator workspace: https://tarang-prototype.onrender.com.
- Render web service: `srv-dav71cvpn0mc73affks0`, free, Singapore.
- PostgreSQL: `dpg-dav6ujp42hec73d8bll0-a`, free, private-network access only;
  expires **31 October 2026**. No paid resources were created.
- Temporary model: `nvidia/nemotron-3-super-120b-a12b:free` through OpenRouter.
  Gemini 3.8 Flash remains the paid candidate once credit access is restored.
- Telegram webhook registered with a secret header; commands start/status/pause/resume.
- Credentials are in ignored `.env` locally and Render's secret file. Never print
  them. Original PDFs and unrelated `.DS_Store` changes remain untouched.

## Verified evidence

- 16 runtime contract tests pass in `.venv`: duplicate inputs/intents, budgets,
  exact authority, expiry, single-use approval, refusal of unauthorised results,
  pause, physical-outcome closure, unknown sends and restart.
- Static review JS/local links and whitespace checks pass.
- OpenRouter live greeting and incomplete-delivery probes worked.
- Four additional synthetic Gemini model probes passed: short delivery, vendor injection,
  first greeting and payment timeout. Outputs are saved privately in
  `.runtime/model-evaluation-gemini.json`. The same four probes also passed on
  the temporary free Nemotron model, in `.runtime/model-evaluation.json`.
  These are not real rail evidence or the full
  15-case persona evaluation. Transient local transport failures needed retries.
- Real Telegram `/start` updates reached the deployed model; two replies were
  acknowledged by Telegram and recorded as sent. Webhook queue was zero with no
  reported Telegram error. This is transport proof, not proof Om read the messages.
- PostgreSQL commitment, events and sent-message records survived redeployment.
- Authenticated operator console loaded live records; unauthenticated state access
  is rejected. A screenshot is saved in this chat's visualization directory.
- Real scheduled clock event fired about one second after its requested due time.
  Its model call failed three times and reached the bounded failed state. Timer
  dispatch and retry persistence are verified; successful scheduled model follow-up
  is **not yet verified**. The fixed-synthetic hosted diagnostic identifies **model_http_402**: OpenRouter
  currently blocks the paid model for credit/payment reasons. Key validation
  succeeds; the temporary free Nemotron route is now deployed. Its hosted fixed-synthetic
  diagnostic returned `ok: true` and `schema_valid: true`. A successful unattended
  model-driven follow-up on that route still needs its own hosted verification.
- An isolated local synthetic commitment completed a real 30-second clock → live
  free-model → persisted decision cycle without user input. No Telegram messages
  were sent by this test. Result: `.runtime/live-clock-test.json`. This closes the
  local scheduler/model integration check, not the full hosted unattended test.

## Boundaries and remaining work

Free compute sleeps, so scheduled checks can run late until inbound traffic wakes
it. Do not describe this host as always-on. Free PostgreSQL also needs migration
or export before expiry. One active commitment per private chat; no group or
multi-wedding support yet. One worker leader; no horizontally scaled queue.

Financial intents become operator requests only. No actual payment, vendor call,
booking or courier API is connected. [RAILS.md](RAILS.md) reconciles the new mails
and explains each gap. The Gnani STT adapter is implemented from current docs;
Om said they will supply GNANI_API_KEY and an authorised audio path. No live Gnani
response has been recorded. Pine Labs product contracts and Delhivery feasibility
remain unverified in the specific required form.

Category budgets are deliberately not installed from storyboard fixtures. The
₹5,000 cap remains illustrative. Approval for a ₹40,000 booking does not delegate
future surcharges. Unknown obligations stay reserved. A model-generated new key
cannot duplicate an identical financial intent.

General conversational copy remains model-generated and needs broader evaluation.
The runtime replaces model wording for proposed actions and closure with precise
execution facts. Do not promote rehearsal evidence to actual fulfilment.

## Continue

Read [RUNTIME.md](RUNTIME.md), then [RAILS.md](RAILS.md). The API, engine, store and
schemas are under `tarang/`; actual prompt assembly uses `prompts/runtime.md` plus
the full persona section. `scripts/evaluate_model.py` uses synthetic inputs only.
The authenticated `/api/model-check` diagnostic also uses fixed synthetic input;
it must not replay private Telegram histories for debugging without permission.

Use `.venv/bin/python -m pytest -q` and `PATH="$PWD/.venv/bin:$PATH" ./scripts/check.sh`.
Render auto-deploy is off; push does not change the live service until an explicit
`render deploys create` succeeds. Preserve free plans unless Om changes the budget.

## Design history

The standalone storyboard `docs/index.html` contains both designed journeys,
onboarding proposals and failure branches. Earlier design publication was
`4acfd5f`; user commit `2fe600f` renamed the review to `index.html`. The submitted
competition resources remain authoritative over invented capabilities.

## WhatsApp conflict foundation — 1 October 2026

Added a disabled-by-default, receive-only Cloud API webhook, durable scoped text inbox,
source-checked conflict detector, bounded retries and authenticated operator review.
25 local contract tests pass. See WHATSAPP.md for configuration and pending live checks.
No WhatsApp credentials configured or actual WhatsApp conversation connected yet.

Two synthetic live OpenRouter conflict probes passed: contradictory setup times flagged
with source quotes; agreeing times produced no conflict. This is model evidence, not
a live WhatsApp delivery test. Local receipt: `.runtime/whatsapp-synthetic-eval.json`.

## Telegram voice implementation — 3 October 2026

Voice-note input, transcript confirmation/correction and spoken replies are implemented
for the fictional conversation. `/talk` then `/voice` opts in; `/heard` confirms,
`/discard` rejects, `/voice off` returns to text. 72 runtime checks and 37 PostgreSQL
public-demo/intake/voice checks pass. Live speech and actual Telegram audio remain
blocked on missing GNANI_API_KEY. See [VOICE_TELEGRAM.md](VOICE_TELEGRAM.md).

### Voice-first follow-up

Om supplied the Gnani key privately in local `.env`; a real synthetic TTS/STT test
and an isolated live STT/review/OpenRouter/TTS pipeline passed. The welcome now
puts **Start with voice** first; `/voice` starts directly after the welcome and
preserves existing text-conversation facts. 74 runtime tests pass. Hosted key
configuration is awaiting explicit permission to copy the credential to Render.
See [voice evidence](VOICE_TELEGRAM.md); the real Telegram audio round trip is pending.


Voice evidence update (3 October, 12:37 IST): the live synthetic probe in
`scripts/verify_telegram_voice.py` passed Gnani STT/TTS, OpenRouter intake and
actual Telegram media transport, with input and spoken follow-up visible in the
Mac client. Updates and confirmation were synthetic/local; human recording,
playback quality, hosted activation and calling remain pending. See
[voice verification](VOICE_TELEGRAM.md). Explicit permission to store the Gnani key
in Render remains pending following the prior automatic approval rejection.


Payment iteration — 3 October: [Pine Labs contracts and setup](PAYMENTS.md) are
reconciled against Muskan's email/attachments and official OpenAPI. Operator-only
request preparation and documented-result ingestion are implemented. They retain
existing exact approvals/delegation, bind beneficiary/reference/amount, preserve
unknown obligations and never verify fulfilment from a payout. No live financial
dispatch, sandbox transaction, hosting secret transfer or phone call occurred.

## Dashboard addition — 4 October 2026

The new [dashboard](DASHBOARD.md) reads Telegram conversations and decision status
from the existing backend. Source routing targets the user-supplied
https://tarang-virid.vercel.app/ (which returned 404 before these changes).
Both the website and backend must receive the new revision before live verification.
The page is operator-only; the operator token is entered privately, never embedded.
See the dashboard guide for migration, limits, release and acceptance checks.
