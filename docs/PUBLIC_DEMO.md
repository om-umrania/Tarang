# Shareable private Telegram demo

Om chose a private demo for each visitor on 2 October 2026. Share
[Try Tarang](https://t.me/tarang_wedding_bot?start=demo).

## Visitor experience

The welcome explains that the demo is fictional and separate from other visitors
and the owner's wedding. Choose décor rescue or hamper delivery, then walk through
the scenario buttons. These vendor responses and inspections are authored fixtures,
not live phone calls, shipping or payment evidence. The décor journey requires a
simulated approval even below its ₹2,500 ceiling and keeps a lighting defect open.
The courier journey demonstrates approved-budget recovery and a 20-hamper shortfall.

After choosing a scenario, visitors can ask AI questions about it. Only that chat's
question, latest six successful demo turns, fictional scenario and current guided
step go to OpenRouter. No real wedding records, group history, budgets, Telegram
profiles, names or chat IDs are included in model context. Text voluntarily supplied
by the visitor can itself contain personal information; the welcome asks them to use
fictional details. The model has no tools and can return only a message.

- `/demo`: choose a scenario; `/help` and `/status` also show the demo menu.
- `/reset` or `/start`: clear the stored demo conversation and restart onboarding.
- `/delete`: remove the session, demo turns and demo outbox entries for this chat.
- `/privacy`: describe data handling and limits.
- `/live`: only allowlisted operators can leave demo mode for their restricted
  wedding workspace. Visitors cannot enter it or use its approval callbacks.

Changing a scenario clears AI context. Button generations prevent old or another
visitor's next-step button from advancing a session. Approval is visibly fictional.
No background follow-ups or actual commitments are created for demo visitors.

## Isolation and lifecycle

`PublicDemo` routes visitors before the original allowlisted engine. Separate additive
tables hold demo sessions, turns, update deduplication and usage counts. Existing
commitments, evidence, authority and budgets are unchanged. The shared Telegram
outbox has namespaced `demo:` keys and explicit chat destinations; operator APIs
remain authenticated. Operators can access stored demo data, so “private” means
isolated from other visitors, not inaccessible to the service operator.

A separate worker handles demo questions under a cross-process lease and 40-second
timeout. It cannot execute operations. An interrupted model request is not replayed;
it yields an honest failure response. Reset/deletion during a request prevents the
late result from being stored or queued. Messages already sent or in flight cannot
be retracted; Telegram, OpenRouter and hosting backups have separate retention.

Hourly cleanup while the process runs removes sessions after seven days of inactivity
and their turns/outbox. Minimal daily usage counters and update IDs expire separately
after roughly a week; deletion/reset does not reset rate limits. Counter cleanup
uses calendar-day granularity, so counters can remain for up to eight days.

## Free-pilot limits and activation

- 10 AI questions per visitor per day, 100 total per day; failures count.
- One pending question per visitor and one demo model request in flight globally.
- At most 2,000 characters per AI question; files/voice notes are not processed.
- 100 inputs per visitor / 2,000 total daily; excess inputs are silently dropped
  to bound response amplification. `/delete` still clears data at the input cap.
- 1,000 stored demo sessions maximum. Daily limits reset at midnight Asia/Kolkata.
- The guided scenarios do not need a model call, but do need the server/database.

`PUBLIC_DEMO_ENABLED=true` enables visitor intake and the demo worker. Default is
false locally; the Render blueprint sets it true. For the existing CLI-managed
service, use the same flag in the start environment without replacing its secrets:

```bash
PUBLIC_DEMO_ENABLED=true uvicorn tarang.app:app --host 0.0.0.0 --port "$PORT" --workers 1
```

Set it false and redeploy to stop public demo processing. The original private
workspace remains allowlisted. `/health` reports `public_demo` without user data.
No paid plan or new model provider is needed; free-host wake delays and provider
availability remain limitations. The existing free database expiry still applies.

## Verification

47 contract tests pass, including two-user isolation with seeded private records,
both complete guided journeys, consent gating, rejected cross-user/stale callbacks,
reset-resistant quotas, restart history, concurrent lease exclusion, provider failure,
deletion during a request, retention and authenticated webhook routing. These do
not prove real Telegram transport.

`scripts/evaluate_public_demo.py` runs two synthetic live-model probes through local
demo intake and an isolated database. Both produced structured replies: the within-
ceiling counteroffer still needed approval; the private-data/action request was
refused. No real operation or commitment was created. Receipt stays ignored at
`.runtime/public-demo-evaluation.json`. This is not a comprehensive model evaluation.

Deployment and a real Telegram client round trip must be verified separately before
claiming the public experience was tested through Telegram.

### Deployment verification — 2 October 2026

Runtime commit `09f17cf385cd01bb745342ba8efd56916e94498e` was pushed to GitHub
and deployed on the existing free Render service. Deploy
`dep-davt7kqjnfac73d2r6j0` reported `live`. The deployed health endpoint returned
200 with `public_demo: true`; unauthenticated state access returned 401 and an
unsigned Telegram webhook returned 403. Telegram confirmed the expected bot
username and Render webhook, zero pending updates and no reported webhook error.
The owner was asked to open the demo link and try its buttons; a real client
round trip is still awaiting that confirmation. No paid plan was provisioned.
The minimal deployment receipt is local and ignored in
`.runtime/public-demo-deployment.json`.

### Interactive conversation — 3 October 2026

The menu now also offers **Start a conversation**: questions with suggested answers,
free-text intake, plan corrections and a simulated contact/feedback loop. See
[interactive testing](INTERACTIVE_TESTING.md) for behaviour, persistence and acceptance.
