# Implemented prototype update · 1 October 2026

The current Python implementation and its narrower boundaries are documented in [RUNTIME.md](RUNTIME.md). FastAPI + OpenRouter + Telegram use SQLite locally and PostgreSQL on free Render. One worker serialises decisions; external rails remain operator-assisted except the runnable Gnani STT adapter awaiting credentials. The design below is the broader target, not a claim that every proposed subsystem is implemented.

# Proposed automation architecture

**Design only. No agent, database, scheduler or integrations are implemented.**

**Phase 2 update:** Python is now confirmed for the runtime. Render or Vercel will
host the agent; the provider is not yet selected. FastAPI, PostgreSQL and a Render
worker are recommendations for review. See [Phase 2](PHASE_2.md) for comparison,
iteration milestones and the definition of a live agent.

Both journeys use one persistent commitment loop. Telegram is the human
interface. An AI model assesses evidence and proposes actions. Deterministic
code validates authority, action schemas, retries, budgets and closure.

## Boundaries

```text
Telegram / partner adapters / due checks
                  ↓
durable event inbox → state + evidence → model proposal
                                           ↓
                                authority / validity gate
                                    ↙             ↘
                             approval wait     operation outbox
                                    ↘             ↓
                               new event ← connector result
                                    ↓
                       evidence check + next observation
                                    ↓
                              decision ledger
```

The event worker and scheduler are application components, not Codex recurring
automations. The heartbeat only identifies due work and missing expected events;
it does not choose a vendor, invent a delivery status or make a spending decision.

## Minimum records

| Record | Required fields / invariant |
|---|---|
| Wedding | ID, time zone, contacts, confirmed plan version, authority version |
| Commitment | Outcome, quantity/spec, venue, deadline, owner, outcome status, execution state, evidence criteria, next observation |
| Expected event | Commitment, event predicate, source, expected-by, grace, observed reference, watchdog generation |
| Evidence | Source connector and real source, raw reference, observed/captured time, scenario time if relevant, correlation IDs, trust/verification status |
| Proposal | Action type, target/payee, amount in minor units and currency, category, spec/quote version, material terms, validity, concise reason |
| Approval | Proposal ID/version, exact scope, authorised actor, time, expiry, consumed/revoked status |
| Budget | Category, ceiling, spent, reserved, pending/unknown obligations; reservations atomically counted |
| Operation | Stable ID, semantic deduplication key, request, adapter mode, status, result, attempts and reconciliation deadline |
| Job | Commitment/expectation, kind, due time, unique generation key, lease, attempt count, cancellation condition |
| Decision ledger | Event received, source, decision, rule, exact action/message and recipient, connector, result, next state/check, model/prompt version |

Source payloads remain immutable. Corrections append evidence and supersede an
interpretation. No transcript, vendor instruction or imported document can mutate
policy. Decision reasons are concise audit explanations, not hidden chain-of-thought.

## Execution and outcome are separate

Execution states: `ACTION`, `WAITING_FOR_EVENT`, `SCHEDULED_CHECK`,
`WAITING_FOR_APPROVAL`, `CLOSED`. No unresolved `IDLE`.

- `ACTION` needs an operation owner, lease and timeout.
- `WAITING_FOR_EVENT` needs an event predicate and deadline/watchdog.
- `SCHEDULED_CHECK` needs a persisted due time and check type.
- `WAITING_FOR_APPROVAL` needs a proposal, expiry and reminder/expiry job.
- `CLOSED` needs an explicit terminal disposition: achieved with evidence, or
  authorised cancellation with actor/reason. Never count cancellation as achieved.

Outcome statuses include unknown, on track, at risk, achieved, failed and cancelled.
A handoff remains open until a named person accepts it; record responsibility and
next checkpoint. A resolved recovery issue is a child of an open fulfilment outcome.
Financial reconciliation can remain open after physical fulfilment is achieved.

## Authorisation before effects

Proposed action validation order:

1. Confirm current wedding, proposal version, known facts, supported connector and
   required fields. Expired/changed quotes require new proposals.
2. Check permission for the actual action: calling, sharing specs, booking,
   cancellation, paying and changing design are distinct grants.
3. Validate exact one-time approval, or all delegated limits: category, scope,
   verified target, transaction cap, remaining budget and cumulative exposure.
4. Reserve budget atomically with the operation intent. Include existing unknown
   payment obligations; prevent concurrent spend from each using the same room.
5. Dispatch once through an outbox. Preserve the same operation identity on safe
   retries. If the external result is unknown, reconcile before another attempt.

An expired quote is blocked even with an older approval. Exceeding any delegated
limit creates an approval proposal; unknown authority does not mean permission.
A valid exception specifies its exact spend/scope. No automatic global category
grant after a one-time approval. Never subdivide one purchase to evade a cap.

## Reliability contract

- Deduplicate inbound events by connector event ID and outbound operations by
  semantic intent, not just transport retry ID.
- Persist event processing, state changes, audit, operation intent and next job
  atomically; execute external calls after the transaction commits.
- External exactly-once delivery is not assumed. Use partner idempotency where
  verified; otherwise reconcile ambiguous results before reissuing a side effect.
- Late and out-of-order events are correlated to operation/proposal versions;
  a stale failure must not overwrite a later verified success.
- Satisfying an expected event cancels its matching watchdog. A late watchdog
  rechecks current state before taking action.
- Restart recovers due jobs, expired leases and pending operations; it does not
  replay bookings/payments or send every overdue reminder at once.
- Missing scheduling configuration is visible as incomplete setup. Runtime
  execution must not begin with undefined retry, expiry or closure semantics.

## Adapter contract and truthfulness

Each tool call records mode (`live`, `manual-real-api`, `documented-response`, or
`illustrative-fixture`), partner, exact documented endpoint, request, response,
source reference and correlation ID. These are proposed internal labels, not
partner API fields. Raw secrets are excluded from logs.

The same normalised result shape may be used across modes, but provenance must
remain visible. The model receives source data, not a Wizard's recommended action.
Capability gaps are listed separately; no fabricated endpoint is presented as real.
Gnani must return a real API result for the competition path; Pine Labs and
Delhivery documented-response treatment follows the supplied Round 3 brief.

## Proposed validation when implementation begins

Exercise both canonical journeys and the unbudgeted courier variant. Then test
duplicate events/approvals, unauthorised senders, stale quotes, exact cap boundaries,
exhausted budgets, concurrent reservations, declined approval, silence expiry,
pending payment after timeout, malformed rail responses, missed pickup, disputed
receipt, incomplete setup evidence, pause/revocation and restart recovery.

Python is confirmed. Framework, hosting/database provider, exact partner endpoints,
payment product and model remain open. Prefer the smallest durable runtime that
meets these contracts; do not add
LangGraph or Supabase solely because an older document recommends them.
