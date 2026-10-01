# Tarang hosting recommendation — 1 October 2026

Recommendation, pending cost approval: retain the deployed Python/FastAPI service,
Telegram webhook and PostgreSQL on Render. Use always-on paid compute for dependable
scheduled follow-up. Do not migrate merely to change platforms.

Telegram/BotFather creates the bot identity and credentials; it does not host Python.
The working route is Telegram -> HTTPS webhook -> durable inbox -> persona and runtime
policy -> OpenRouter -> validated decision -> Telegram reply. PostgreSQL holds memory
and scheduled work. The persona is already loaded by tarang/adapters.py from the full
prompt in prompts/tarang-persona.md on each decision.

Verified this turn: bot username tarang_wedding_bot, registered Render webhook, zero
pending updates, no reported webhook error, HTTP 200 health, successful hosted fixed
synthetic model/schema check using the configured free Nemotron model. This does not
substitute for a new user-authored Telegram conversation or an unattended long-run test.

## Options assessed

- Existing free Render: keep for conversational prototype testing. Sleeps after idle;
  proactive checks can run late. Already deployed, no migration required.
- Paid Render: recommended next step for this architecture. Upgrade existing compute
  and replace/upgrade the expiring free database. Preserve webhook and state. Model
  availability is separate; a free OpenRouter model is not a reliability guarantee.
- Railway: viable alternative; Hobby has a $5 monthly minimum with usage-based billing.
  Migration introduces configuration and state-transfer work without a demonstrated
  benefit for the current prototype.
- Vercel Functions: supports Python, but function lifetimes are bounded. The current
  continuous worker/scheduler would require a queue/workflow redesign. It is not a
  direct deployment target for the current process design.

## Concrete next steps

1. Keep current free service and Telegram webhook working while budget is decided.
2. With approval, upgrade the existing Render web service to Starter (listed $7/month).
3. Upgrade/migrate PostgreSQL before the recorded 31 October expiry. Confirm the exact
   database/storage cost before purchase; web compute price is not the total budget.
4. Set an explicit model-credit budget and use a tested provider route. Existing free
   model remains provisional; credits are billed separately from hosting.
5. Send a real greeting and a wedding commitment to the bot; inspect delivery and voice.
   Verify a scheduled follow-up after >15 minutes idle and across a restart before
   describing it as dependable unattended operation.

No paid plan, new hosting account, model purchase or migration was executed. Earlier
user instruction was existing/free resources first; a recurring charge needs approval.
WhatsApp remains disabled pending its separate source/configuration decision.

Sources checked 1 October 2026:
- https://core.telegram.org/bots/webhooks
- https://render.com/docs/free
- https://render.com/pricing
- https://docs.railway.com/pricing/plans
- https://vercel.com/docs/functions/limitations
