> Superseded status: implementation is now authorised and underway. See [runtime](RUNTIME.md), [rails](RAILS.md) and [handoff](HANDOFF.md) for current evidence. This page records the earlier planning stage.

# Phase 2: persona and Python agent foundation

**1 October 2026. Python confirmed; hosting candidate set: Render or Vercel.**
Persona v0.1 is drafted for review. No backend, model connection or cloud service
has been created. This phase begins with behaviour and prompt iteration; deployment
follows a working, validated vertical slice.

## Architecture recommendation for review

Use Python for the agent runtime, tool adapters, authority checks and scheduling.
FastAPI is a proposed HTTP layer for Telegram/partner webhooks and health endpoints.
A durable relational database stores commitments, events, approvals, jobs, operation
intents and the ledger. PostgreSQL is proposed; provider is unselected.

```text
Telegram webhook → Python API → durable event inbox
                                      ↓
                             Python agent worker
                         persona + model + policy gate
                                      ↓
                           operation outbox → tools
                                      ↓
                           evidence + persisted next job
```

Return webhook acknowledgements after durable acceptance. Process model calls and
slow tools outside that request. Persist due jobs and use leases/deduplication so
restart or multiple workers cannot double-execute. No in-memory timer is the sole
record of an approval reminder. A worker can claim database-backed jobs initially;
a separate queue is optional once load or reliability requirements justify it.

Separate prompt layers: application policy and tool/output schema → persona →
structured wedding context and evidence → untrusted incoming message. Version the
prompt components. Trusted runtime policy results must not be forgeable by source
documents. The persona does not contain credentials or enforce permissions itself.

## Hosting comparison

Official documentation checked 1 October 2026; service choice and pricing not approved.

| Option | Fit for the proposed design | What must be addressed |
|---|---|---|
| Render | Python web service plus a continuously running background worker maps directly to API + agent jobs | Select suitable compute and durable storage; configure secrets, health checks and worker recovery |
| Vercel | Python/FastAPI can run as Functions for webhooks/API | Break work into bounded invocations; select and verify durable job delivery/orchestration and Python compatibility; do not rely on a forever-running loop inside a request |

**Recommendation, not a decision:** start with Render for the Python agent and
its worker. It matches the existing persistent-monitoring design with fewer
execution-model changes. Vercel remains viable if its selected workflow/queue
arrangement meets the same contracts. A separate Vercel frontend is optional,
not required: Telegram already supplies the prototype's human interface.

Render's free web services spin down after 15 minutes without inbound traffic;
background workers are not among its free service types. A free web service alone
must not be presented as always-on monitoring. Local filesystem state is not
durable across service restarts/redeploys without an appropriate storage setup.
Budget, account access and service tier remain open; no cost is incurred here.
[Render free service limits](https://render.com/docs/free).

Vercel supports Python ASGI/WSGI apps including FastAPI as Functions. Its function
duration limits depend on configuration/plan. Validate the chosen execution path
against tool latency, retries and due-check requirements before committing to it.
[Vercel Python](https://vercel.com/docs/functions/runtimes/python),
[function limits](https://vercel.com/docs/functions/limitations).

Reference: [Render FastAPI deployment](https://render.com/docs/deploy-fastapi),
[Render background workers](https://render.com/docs/background-workers).
The platform comparison is an architectural inference from these documented
execution models, not a deployed benchmark or a claim that either account is ready.

## Iterations with visible acceptance criteria

| Iteration | Deliverable | Exit condition |
|---|---|---|
| 1 · Persona | Persona v0.1, prompt and review fixtures | Om chooses relationship/language direction and approves representative responses |
| 2 · Model rehearsal | Selected model runs fixed persona cases with labelled fixtures | Recorded outputs satisfy review rubric; no fabricated action or authority claims |
| 3 · Python vertical slice | API, persisted event, model proposal, authority gate, adapter result, next job and ledger | One commitment resumes after restart; duplicate event does not duplicate an operation |
| 4 · Telegram | Verified identities, status and scoped approval interactions | Exact proposal accepted once; stale/unauthorised responses cannot act |
| 5 · Hosted staging | Selected host, managed secrets, database, worker and HTTPS webhooks | Receives an event; acts through labelled adapters; due check fires without a user prompt; restart verified |
| 6 · Scenario rehearsal | Both journeys and authority variant | Verified closure only with evidence; full decision and tool provenance retained |

## What remains to choose

- Personality warmth and default language; no gender/voice identity implied.
- Model/provider and available access for actual prompt evaluations.
- Render versus Vercel, acceptable hosting spend and database provider.
- Existing open operational configuration: cap, budgets, approvers, exact rail
  support, timings and receipt/verification requirements.

## What proves “live”

A published URL alone is not a live agent. Require a reachable webhook, durable
event ingestion, a model-generated proposal, validated authority, observable tool
result, persisted next check, and successful unattended execution of that check.
Also verify pause, unknown-result reconciliation and restart before relying on
the agent. Label any Wizard/documented responses visibly. Publish only the minimum
HTTP surface; operator evidence views need access control before live data is used.
