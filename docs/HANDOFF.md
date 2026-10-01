# Tarang handoff · 1 October 2026

## Live prototype

- Bot: https://t.me/tarang_wedding_bot (allowlisted private chat only).
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
- Four additional synthetic model probes passed: short delivery, vendor injection,
  first greeting and payment timeout. Outputs are saved privately in
  `.runtime/model-evaluation.json`; they are not real rail evidence or the full
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
  succeeds; the free Nemotron candidate is being configured as the temporary route.

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
