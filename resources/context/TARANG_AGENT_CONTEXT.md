# TARANG --- Agent Build Context

## The Ken Case-Build Competition, Round 3

**Purpose:** Single source of truth for any coding agent, terminal
agent, teammate, or AI model continuing the Tarang build.

**Status:** Round 3 simulation/build context\
**Round 3 deadline:** 4 October 2026, 11:59 PM IST\
**Primary demo scenarios:** Décor collapse; return-gift courier failure

------------------------------------------------------------------------

## 0. Executive Context

Tarang is a proactive, policy-bounded wedding operations agent for Meera
and Rohan's Jaipur wedding on **14 December 2026**.

Tarang is not intended to be a chatbot that waits for instructions. It
owns operational outcomes within explicit authority limits. It monitors
commitments, detects deviations and missing expected events,
investigates problems, plans recovery, asks humans only when authority
requires it, executes through external rails, verifies the real-world
outcome, and keeps monitoring until the outcome is achieved.

The core invariant is:

> **Humans provide goals, constraints and approvals. They should not
> need to remember what Tarang needs to check next.**

Every unresolved thread must end in exactly one of:

-   `ACTION`
-   `WAITING_FOR_EVENT`
-   `SCHEDULED_CHECK`
-   `WAITING_FOR_APPROVAL`
-   `CLOSED`

**Never leave a thread in an undefined `IDLE` state.**

------------------------------------------------------------------------

# 1. Competition Constraints

## 1.1 Round 3 objective

Round 3 requires a **Wizard of Oz simulation** of the agent, followed by
a business case around it.

The agent itself must be an AI model such as Claude or Gemini following
a system prompt and making its own decisions.

Where direct connectors exist, connect them. Where a capability does not
currently exist, a teammate may play the outside world behind the
curtain.

The human Wizard may: - supply a real external event; - run a real API
manually and return exactly its response; - reproduce a response
documented by a rail where permitted by the brief.

The human Wizard may **not**: - reason for Tarang; - choose Tarang's
next action; - tell Tarang what decision to make; - silently alter
external data to make the demo work.

If Tarang needs a human to tell it what to do next, the agent design has
failed.

## 1.2 Recording requirements

The Round 3 recording must show: - every input arriving; - every
relevant call to Gnani, Pine Labs or Delhivery; - responses returned by
those rails; - every message Tarang sends to a person; - the journey
from initial trigger to achieved outcome.

Maximum recording length: **5 minutes**. Model-thinking periods may be
fast-forwarded.

The submission also requires the system prompt and model name.

## 1.3 Decision reconstruction requirement

For every decision made during the recording, preserve:

1.  When: date and time.
2.  What Tarang received.
3.  Where it came from: connector and real source.
4.  What Tarang decided.
5.  Why: the system-prompt/policy rule used.
6.  Exact action/message and recipient.
7.  Connector used.
8.  Result.
9.  Next state / next observation.

This requirement motivates the **Decision Ledger** described later.

## 1.4 Rail/API requirement

For calls involving Gnani, Pine Labs and Delhivery: - record the exact
documented endpoint used; - retain request and response payloads; -
distinguish real current capabilities from imagined capabilities.

Up to three capabilities that do not yet exist may be proposed
separately, with: - partner; - proposed endpoint; - data the partner
already possesses that would enable it.

Do not invent a capability and present it as a real API.

------------------------------------------------------------------------

# 2. Product Thesis

Tarang is an **outcome-owning wedding operations agent**.

A normal wedding assistant may remind users:

> "Call the decorator."

Tarang instead owns:

> "Mandap décor must be ready for the wedding."

A normal automation may complete:

> "Book Delhivery."

Tarang owns:

> "200 hampers must physically reach the venue."

This distinction drives the entire architecture.

Tarang closes a thread only after the **desired outcome is verified**,
not merely because an intermediate action or API call succeeded.

------------------------------------------------------------------------

# 3. Core Operating Framework --- MAP-RAV

Tarang follows:

## M --- Monitor

Observe commitments, deadlines, vendor responses, payments, shipments,
approvals, and expected events.

## A --- Assess

Determine: - current observed state; - expected state; - discrepancy; -
urgency; - risk; - available evidence.

## P --- Plan

Choose a recovery or fulfilment plan using current context, available
vendors, dependencies and tools.

## R --- Resolve

Take the necessary operational action: call, negotiate, book, message,
pay, re-route, etc.

## A --- Authorise

Before consequential actions, pass through the deterministic Authority
Gate.

## V --- Verify

Verify that the actual outcome occurred.

After verification:

``` text
Outcome achieved?
    YES -> CLOSE
    NO  -> schedule next observation -> MONITOR
```

A critical addition to MAP-RAV is:

> **Every action must answer: "When and how should Tarang observe this
> again?"**

------------------------------------------------------------------------

# 4. High-Level Architecture

``` text
                         WEDDING STATE
          deadlines | vendors | budgets | dependencies
          approvals | expected events | commitments
                               |
              +----------------+----------------+
              |                                 |
        EVENT TRIGGERS                    TIME TRIGGERS
        human messages                    heartbeat
        vendor response                   deadlines
        shipment webhook                  next_check_at
        payment event                     watchdog expiry
              |                                 |
              +----------------+----------------+
                               |
                          EVENT QUEUE
                               |
                         TARANG AGENT
                               |
             Observe -> Assess -> Plan -> Decide
                               |
                        AUTHORITY GATE
                         /           \
                 authorised       approval needed
                      |                 |
                      |            Human approval
                      +--------+--------+
                               |
                              ACT
                               |
          +--------------------+---------------------+
          |                    |                     |
        Gnani              Pine Labs             Delhivery
        voice               payments              logistics
          |                    |                     |
          +--------------------+---------------------+
                               |
                            VERIFY
                               |
                      outcome achieved?
                        /             \
                      YES              NO
                       |                |
                     CLOSE      schedule next check
                                        |
                                      MONITOR
```

------------------------------------------------------------------------

# 5. Recommended Technical Stack

The precise implementation can change, but the architectural roles
should remain stable.

  Layer                       Recommended implementation
  --------------------------- ------------------------------------------------
  Human prototype interface   Telegram Bot
  Telegram bot provisioning   BotFather
  Agent orchestration         LangGraph or equivalent explicit state machine
  Reasoning model             Claude or Gemini
  Persistent state            Supabase/Postgres
  Voice rail                  Gnani
  Payment rail                Pine Labs
  Logistics rail              Delhivery
  Scheduled work              Cron + dynamic job queue
  External events             Webhooks where supported
  Human approval              Telegram messages / inline approval controls
  Hard authority rules        Deterministic policy engine
  Auditability                Decision Ledger
  Missing integrations        Explicit Wizard-of-Oz adapters

### Architectural rule

**LLM = judgement**\
**Code = authority**\
**Tools = action**\
**State = memory**\
**Scheduler = persistence**\
**Verification = accountability**

Do not delegate arithmetic authority checks or hard policy boundaries to
probabilistic model reasoning.

------------------------------------------------------------------------

# 6. Telegram and WhatsApp

## 6.1 Telegram

For the prototype, Telegram is Tarang's primary live human interface.

Telegram is a connector/UI, not Tarang's brain.

``` text
Telegram -> Tarang -> State -> Tools
```

## 6.2 WhatsApp

Do not assume a Telegram bot can directly read arbitrary WhatsApp
conversations.

Do not make unofficial WhatsApp Web scraping a core dependency of the
Round 3 simulation.

Possible WhatsApp roles:

### Supported business-message path

Where an official supported WhatsApp business integration can provide
events, normalize those events into Tarang's event format.

### Historical context

An exported WhatsApp conversation can be parsed and ingested as
historical context if needed.

### Round 3 Wizard-of-Oz input

When a direct WhatsApp connector is unavailable, a teammate may feed the
exact real WhatsApp event into the simulation without interpreting it or
telling Tarang what to do.

Example normalized event:

``` json
{
  "source": "whatsapp",
  "source_type": "group",
  "sender": "Rohan",
  "timestamp": "2026-12-11T10:00:00+05:30",
  "content": "Is the mandap decor moving smoothly?"
}
```

The provenance must remain visible.

------------------------------------------------------------------------

# 7. Core Data Model

Tarang should maintain a persistent **Wedding State**, not merely a
conversation transcript.

Illustrative structure:

``` json
{
  "wedding": {
    "couple": ["Meera", "Rohan"],
    "date": "2026-12-14",
    "location": "Jaipur"
  },
  "authority": {
    "transaction_limit": 5000,
    "approved_categories": []
  },
  "vendors": {},
  "commitments": {},
  "approvals": {},
  "payments": {},
  "shipments": {},
  "expected_events": {},
  "open_issues": {},
  "scheduled_jobs": {}
}
```

------------------------------------------------------------------------

# 8. Commitments, Not Tasks

Tarang should model operational promises as **commitments**.

Example:

``` json
{
  "id": "mandap_ready",
  "outcome": "Mandap decor ready",
  "deadline": "2026-12-14T08:00:00+05:30",
  "owner": "Suresh",
  "status": "confirmed",
  "dependencies": [
    "decorator_available",
    "materials_ready",
    "transport_confirmed",
    "venue_access"
  ],
  "risk": "low",
  "next_check_at": "2026-12-11T10:00:00+05:30"
}
```

Return-gift example:

``` json
{
  "id": "return_gifts_at_venue",
  "outcome": "200 return-gift hampers delivered to venue",
  "deadline": "2026-12-12T18:00:00+05:30",
  "owner": "Anand Gifts",
  "status": "confirmed",
  "dependencies": [
    "hampers_ready",
    "courier_assigned",
    "shipment_dispatched",
    "shipment_delivered"
  ],
  "risk": "medium",
  "next_check_at": "2026-12-12T11:30:00+05:30"
}
```

------------------------------------------------------------------------

# 9. Expected Events

This is the core primitive for proactivity.

Whenever something is expected to happen, Tarang stores:

``` json
{
  "event": "hampers_dispatched",
  "expected_by": "2026-12-12T11:00:00+05:30",
  "grace_period_minutes": 15,
  "observed": false
}
```

If the event has not been observed after its deadline plus grace period:

``` text
EXPECTED EVENT MISSING
        ->
EXPECTATION VIOLATION
        ->
wake Tarang
        ->
investigate
```

Tarang therefore responds not only to **events**, but also to **missing
events**.

This is a defining proactive-agent capability.

------------------------------------------------------------------------

# 10. Trigger Taxonomy

Tarang must support five trigger classes.

## 10.1 Human trigger

Example: - Rohan asks whether décor is on track.

Source: - Telegram / supported messaging connector / WoZ event adapter.

## 10.2 External event trigger

Examples: - shipment status changes; - payment succeeds/fails; - vendor
replies.

Source: - webhook or external connector.

## 10.3 Temporal trigger

Examples: - T-48 hours before delivery; - scheduled follow-up; -
deadline approaching.

Source: - scheduler.

## 10.4 Missing-event trigger

Examples: - vendor promised confirmation by 2 PM and no confirmation
arrived; - shipment should have dispatched but no dispatch event exists.

Source: - expectation watchdog.

## 10.5 Derived/risk trigger

Examples: - wedding is T-2 days and shipment has not moved; - primary
decorator is unreachable while dependency criticality is high.

Source: - reconciliation/risk engine.

------------------------------------------------------------------------

# 11. Scheduler and Automation Architecture

## 11.1 Heartbeat

Do not encode the whole business as dozens of static cron jobs.

Use a general heartbeat such as:

``` text
*/15 * * * *
```

Production cadence is configurable.

Heartbeat responsibility:

``` text
wake Tarang
   ->
query unresolved commitments
   ->
find due next_check_at values
   ->
detect overdue expected events
   ->
recalculate risk
   ->
identify commitments requiring attention
   ->
enqueue relevant agent events
```

The heartbeat wakes the agent. It does **not** make business decisions.

## 11.2 Dynamic job queue

Tarang creates scheduled jobs from events and decisions.

Examples:

``` text
call_vendor at +5m
check_shipment at 14:00
approval_reminder at +30m
verify_payment at +2m
reconcile_commitment at 17:00
```

## 11.3 Self-scheduling follow-ups

Every non-terminal action should create the next observation.

Example:

``` text
Call Suresh
-> no answer
-> schedule retry +5m
```

Second failure:

``` text
retry fails
-> depending on urgency:
   retry later OR
   call secondary contact OR
   move to backup vendor
```

## 11.4 Deadline-sensitive backoff

Backoff should reflect urgency.

Conceptually:

``` text
T-30 days -> retry tomorrow
T-7 days  -> retry in hours
T-2 days  -> retry in minutes
T-6 hours -> seek alternative immediately
```

Exact values belong in policy/configuration rather than being improvised
by the model.

------------------------------------------------------------------------

# 12. Watchdogs Required

## 12.1 Expectation watchdog

Detects expected events that fail to occur.

## 12.2 Response/silence watchdog

If Tarang requests a response and none arrives by
`expected_response_by`, wake the agent.

## 12.3 Approval watchdog

For pending approvals: - remind; - increase urgency as decision deadline
approaches; - escalate to another authorised approver only if predefined
policy allows it.

The model must never invent approval authority.

## 12.4 Payment watchdog

Track: - requested; - pending; - success; - failed.

An API call is not equivalent to successful payment.

## 12.5 Logistics watchdog

Track: - pickup requested; - pickup confirmed; - in transit; - out for
delivery; - delivered.

Do not close a delivery outcome at "booking successful."

## 12.6 Closure watchdog

Before closing an issue, test whether the actual target outcome has been
verified.

------------------------------------------------------------------------

# 13. Reconciliation Engine

Periodically compare:

``` text
EXPECTED STATE
      vs
OBSERVED STATE
```

For every commitment.

Example:

``` text
Expected:
hampers_dispatched = true

Observed:
hampers_dispatched = unknown

Difference:
YES

Action:
create issue -> Tarang investigates
```

This is the generic mechanism by which Tarang discovers operational
failures that nobody explicitly told it to look for.

------------------------------------------------------------------------

# 14. Risk Engine

A simple heuristic is sufficient.

Conceptual risk:

``` text
Risk =
deadline proximity
x consequence
x uncertainty
x dependency importance
x replacement difficulty
```

Risk affects monitoring cadence and recovery urgency.

Example mapping:

``` text
LOW      -> check approximately daily
MEDIUM   -> check several times per day
HIGH     -> check approximately hourly
CRITICAL -> active resolution loop
```

The exact thresholds should be deterministic/configurable.

------------------------------------------------------------------------

# 15. Authority Engine

Authority is enforced by code, not left solely to the LLM.

Current core rules:

## Rule A --- Amount

If a transaction exceeds **₹5,000**, Tarang requires approval.

``` python
if transaction.amount > 5000:
    require_approval()
```

## Rule B --- Category

If spending belongs to a category the couple has not
authorised/budgeted, Tarang requires approval even if the amount is
below ₹5,000.

``` python
if transaction.category not in approved_categories:
    require_approval()
```

## Contextual authority

Once humans approve a category/action context, subsequent actions may
occur autonomously only if they fall inside the delegated scope and
transaction limit.

Approval should become structured state:

``` json
{
  "category": "decor",
  "vendor": "Petal Inn",
  "approved_amount": 40000,
  "approved_by": "Rohan",
  "status": "approved"
}
```

Do not treat a vague conversational "yes" as universal future spending
authority.

------------------------------------------------------------------------

# 16. Decision Ledger

Every reasoning/action cycle should create an audit record.

Example:

``` json
{
  "timestamp": "2026-12-11T13:05:00+05:30",
  "commitment_id": "mandap_ready",
  "state": "PRIMARY_VENDOR_UNAVAILABLE",
  "received": "Suresh is hospitalised and cannot deliver",
  "source": {
    "connector": "Gnani",
    "real_source": "Suresh's assistant"
  },
  "decision": "Contact first approved backup decorator",
  "rule": "VENDOR_FAILURE_RECOVERY",
  "action": "call_vendor",
  "recipient": "Petal Inn",
  "connector": "Gnani",
  "result": "Quote received: ₹40,000",
  "next_state": "QUOTE_REQUIRES_AUTHORITY_CHECK"
}
```

The Decision Ledger should power: - competition answers; - demo
observability; - debugging; - auditability; - post-run reconstruction.

Ideally show it beside the human UI during the demo.

------------------------------------------------------------------------

# 17. Scenario 1 --- Décor Collapse

## 17.1 Setup

**Date:** 11 December 2026\
**Wedding:** 14 December 2026\
**Trigger:** human initiated\
**Human:** Rohan

Rohan asks Tarang whether the mandap décor is moving smoothly.

## 17.2 Intended sequence

1.  Rohan asks for décor status.
2.  Tarang identifies the unresolved objective: ensure mandap décor is
    confirmed.
3.  Tarang retrieves primary vendor Suresh and backup shortlist.
4.  Tarang calls Suresh through Gnani.
5.  No answer.
6.  Tarang retries using deadline-sensitive backoff.
7.  Tarang reaches Suresh's assistant.
8.  Assistant reports Suresh is hospitalised and cannot deliver.
9.  Tarang updates primary vendor availability and décor commitment
    risk.
10. Tarang chooses a Day-One backup, Petal Inn.
11. Tarang sends/shares existing décor plan and specifications.
12. Petal Inn confirms availability and quotes **₹40,000**.
13. Authority Gate applies Rule A: ₹40,000 \> ₹5,000.
14. Tarang asks Meera/Rohan to approve.
15. They approve.
16. Tarang records structured approval.
17. Tarang confirms Petal Inn.
18. Petal Inn flags a **₹3,000 last-minute delivery surcharge**.
19. Tarang negotiates it to **₹2,500**.
20. Authority Gate evaluates:
    -   ₹2,500 \<= ₹5,000;
    -   décor is now an approved context/category.
21. No second escalation.
22. Tarang pays ₹2,500 through Pine Labs.
23. Tarang verifies payment success and vendor confirmation.
24. Tarang sends a concise closure summary.
25. Tarang schedules any subsequent fulfilment verification needed to
    ensure the décor is actually delivered/set up.

## 17.3 Important design lesson

The ₹2,500 payment demonstrates **bounded contextual autonomy**.

Tarang should neither: - ask humans about every minor action; nor -
spend without constraints.

------------------------------------------------------------------------

# 18. Scenario 1 --- 100-Word Story

On 11 December 2026, three days before Meera and Rohan's Jaipur wedding,
Rohan asks Tarang if the mandap décor is on track. Tarang calls
decorator Suresh --- silence. It retries, then reaches his assistant:
Suresh is hospitalised, can't deliver. Tarang doesn't wake the couple.
It pulls its Day-One backup list, calls Petal Inn, shares the specs,
gets a ₹40,000 quote. That exceeds its autonomous limit, so it messages
Meera and Rohan: old vendor's out, Petal Inn confirmed at ₹40,000 ---
proceed? They say yes. A ₹2,500 delivery surcharge surfaces; within
authority, Tarang negotiates it down, pays via Pine Labs. Done.

------------------------------------------------------------------------

# 19. Scenario 2 --- Vendor Courier Falls Through

## 19.1 Setup

**Date:** 12 December 2026\
**Wedding:** 14 December 2026\
**Trigger:** agent initiated\
**Commitment:** 200 return-gift hampers must reach the venue.

Meera and Rohan ordered 200 hampers from **Anand Gifts**, which had
committed to arrange its own courier and deliver them by 12 December.

## 19.2 Critical product behaviour

Tarang should not require Rohan to ask whether the hampers shipped.

Tarang already knows: - the delivery commitment; - due date; - expected
dispatch; - lack of verified shipment state; - shrinking time to
wedding.

Its Monitor/Reconciliation loop should wake it proactively.

## 19.3 Intended sequence

1.  Scheduler/heartbeat identifies the return-gift commitment as
    requiring verification.
2.  Tarang sees dispatch has not been verified.
3.  Tarang calls Anand Gifts via Gnani.
4.  Tarang asks whether the package has shipped.
5.  Shopkeeper says his regular courier is unavailable and nothing has
    shipped.
6.  Tarang marks the commitment `AT_RISK`.
7.  Tarang identifies the objective: 200 hampers must reach the venue.
8.  Tarang chooses alternative logistics rather than waiting for the
    failed vendor arrangement.
9.  Tarang tells Anand Gifts to keep the hampers ready.
10. Tarang requests Delhivery pickup from the shop to the venue.
11. Delhivery returns same-day priority availability at **₹1,200**.
12. Rule A passes because ₹1,200 \<= ₹5,000.
13. Rule B fails because ad-hoc courier/logistics is a new/unbudgeted
    category.
14. Tarang requests approval from Meera/Rohan.
15. They approve.
16. Tarang records the approval.
17. Tarang pays ₹1,200 through Pine Labs.
18. Tarang confirms priority pickup.
19. Tarang tracks logistics status.
20. Tarang does **not** close at booking or pickup.
21. Tarang closes only after `delivered` is verified at the venue.
22. Tarang sends one concise closure summary.

------------------------------------------------------------------------

# 20. Scenario 2 --- 100-Word Story

On 12 December 2026, two days before Meera and Rohan's Jaipur wedding,
Tarang runs a routine check-in with Anand Gifts about the 200
return-gift hampers the couple ordered. The shopkeeper says his courier
fell through --- nothing's shipped. Tarang doesn't wait: it books a
Delhivery pickup straight from the shop to the venue. The only same-day
slot costs ₹1,200 --- an ad-hoc cost the couple never budgeted, so
Tarang messages Meera and Rohan: here's what broke, the fix, the cost.
They say yes. Tarang pays via Pine Labs, then tracks the shipment,
closing only once it shows delivered.

------------------------------------------------------------------------

# 21. Scenario Comparison

  ------------------------------------------------------------------------
  Dimension               Scenario 1              Scenario 2
  ----------------------- ----------------------- ------------------------
  Trigger                 Human                   Agent

  Initial problem         Decorator unavailable   Vendor courier
                                                  unavailable

  Discovery               Rohan asks status       Monitor/reconciliation

  Voice                   Gnani                   Gnani

  Logistics               Not central             Delhivery

  Payment                 Pine Labs               Pine Labs

  Escalation              Rule A: amount          Rule B: category

  Verification            vendor/payment +        delivered at venue
                          eventual décor          
                          fulfilment              

  Agentic lesson          recovery + bounded      proactive monitoring +
                          spending                outcome ownership
  ------------------------------------------------------------------------

The two scenarios should use the **same core agent engine**, not two
separate scripted workflows.

------------------------------------------------------------------------

# 22. State Machine

Generic lifecycle:

``` text
MONITOR
   |
ISSUE DETECTED
   |
DIAGNOSE
   |
FIND OPTIONS
   |
SELECT ACTION
   |
AUTHORITY CHECK
   |----------------------|
authorised          not authorised
   |                      |
   |                  ESCALATE
   |                      |
   |                human approval
   |                      |
   +----------+-----------+
              |
             ACT
              |
           VERIFY
          /      \
      success    failure
         |          |
       CLOSE      RECOVER
                    |
                   PLAN
```

Possible explicit states include:

-   `MONITORING`
-   `INVESTIGATING`
-   `WAITING_FOR_VENDOR`
-   `RECOVERY_PLANNING`
-   `AUTHORITY_CHECK`
-   `WAITING_FOR_APPROVAL`
-   `EXECUTING`
-   `VERIFYING`
-   `AT_RISK`
-   `RECOVERING`
-   `CLOSED`

------------------------------------------------------------------------

# 23. Event Schema

All connectors should normalize incoming data into a shared event shape.

``` json
{
  "event_id": "evt_123",
  "event_type": "vendor_response",
  "timestamp": "2026-12-12T11:40:00+05:30",
  "source": {
    "connector": "gnani",
    "real_source": "Anand Gifts"
  },
  "entity_id": "return_gifts_at_venue",
  "payload": {
    "message": "Our regular courier is unavailable. Nothing has shipped."
  }
}
```

This allows Telegram, WhatsApp adapters, Gnani, Pine Labs, Delhivery,
scheduler and Wizard-of-Oz inputs to enter the same agent loop.

------------------------------------------------------------------------

# 24. Suggested Agent State

``` json
{
  "current_event": {},
  "active_commitment": {},
  "known_facts": [],
  "open_issues": [],
  "candidate_actions": [],
  "selected_action": {},
  "authority_result": {},
  "pending_approvals": [],
  "tool_results": [],
  "expected_events": [],
  "scheduled_jobs": [],
  "decision_log": [],
  "outcome_status": "unresolved"
}
```

------------------------------------------------------------------------

# 25. Separation of Responsibilities

## Agent / LLM should decide

-   what an ambiguous external event means operationally;
-   whether a commitment is at risk;
-   which recovery option is best among permitted options;
-   which vendor to contact;
-   what clarification is needed;
-   how to communicate/negoti­ate within permitted boundaries;
-   whether the objective remains unresolved;
-   what next observation is needed.

## Deterministic code should enforce

-   transaction thresholds;
-   approved spending categories;
-   authorised approvers;
-   maximum retry counts;
-   safety boundaries;
-   exact scheduler mechanics;
-   persistence;
-   idempotency;
-   tool schemas;
-   payment state;
-   job uniqueness;
-   deadline calculations where possible.

------------------------------------------------------------------------

# 26. Proactivity Requirements

Tarang is not proactive merely because a cron job calls a vendor.

True proactivity requires:

1.  Knowing the desired outcome.
2.  Knowing the deadline.
3.  Knowing expected intermediate events.
4.  Observing whether those events occurred.
5.  Detecting missing events.
6.  Assessing risk from the discrepancy.
7.  Choosing an investigation/recovery action.
8.  Scheduling its own next observation.
9.  Continuing until the outcome is verified.

The key loop is:

``` text
EXPECTED
   |
OBSERVE
   |
difference?
 /       \
NO       YES
|         |
wait    investigate
          |
         act
          |
       schedule
          |
       observe again
```

------------------------------------------------------------------------

# 27. Demo Observability

The demo should make Tarang's autonomy visible.

Recommended screen layout:

``` text
+----------------------+--------------------------+
| Telegram / Human UI  | Decision Ledger          |
|                      |                          |
| Rohan/Tarang chat    | Event received           |
| approvals            | Current state            |
| summaries            | Decision                 |
|                      | Rule                      |
|                      | Tool call                |
|                      | Result                   |
|                      | Next state/check         |
+----------------------+--------------------------+
```

Where useful, expose rail request/response payloads in a third panel or
developer console.

The audience should be able to see that: - the world supplied an
event; - Tarang independently decided what to do; - policy constrained
it; - a tool executed the action; - Tarang verified the result.

------------------------------------------------------------------------

# 28. Wizard-of-Oz Adapter Contract

A WoZ adapter must behave like a tool boundary.

Example:

``` text
Tarang -> delhivery_adapter.create_pickup(...)
                       |
              real API available?
                 /            \
               YES             NO
                |               |
          call real API     Wizard executes
                |           permitted simulation
                +-------+-------+
                        |
                 structured response
                        |
                     Tarang
```

Tarang should consume the same structured response shape regardless of
whether the current simulation used a real connector or a permitted
Wizard operation.

The Wizard must not alter Tarang's reasoning.

------------------------------------------------------------------------

# 29. Reliability Requirements

## Idempotency

Retries must not accidentally: - double-pay; - create duplicate
shipments; - send duplicate approvals; - create duplicate vendor
bookings.

Use idempotency keys / operation IDs where supported.

## Persistence

Agent state and scheduled work must survive process restarts.

## Tool failure handling

Every tool needs: - success state; - retryable failure; - non-retryable
failure; - timeout; - malformed response handling.

## Audit trail

Never overwrite decision history. Append new events.

------------------------------------------------------------------------

# 30. Suggested Build Order

## Phase 1 --- Core state

Implement: - wedding; - vendors; - commitments; - authority rules; -
approvals; - expected events.

## Phase 2 --- Event engine

Implement: - normalized event schema; - event queue; - state
transitions.

## Phase 3 --- Agent loop

Implement: - observe; - assess; - plan; - choose action; - verify; -
next observation.

## Phase 4 --- Policy engine

Implement Rule A and Rule B deterministically.

## Phase 5 --- Telegram

Implement: - user message; - approval request; - approval response; -
closure summary.

## Phase 6 --- Scheduler

Implement: - heartbeat; - `next_check_at`; - expectation watchdog; -
silence watchdog; - approval watchdog; - retry/backoff.

## Phase 7 --- Rails

Implement adapters for: - Gnani; - Pine Labs; - Delhivery.

Use real endpoints where available and clearly separated WoZ adapters
where the competition permits simulation.

## Phase 8 --- Decision Ledger

Automatically persist every consequential decision.

## Phase 9 --- Scenario fixtures

Create deterministic test fixtures for Scenario 1 and Scenario 2.

## Phase 10 --- Demo harness

Make both scenarios reproducible within the 5-minute recording
constraint without changing the underlying agent logic.

------------------------------------------------------------------------

# 31. Test Cases

At minimum test:

### Authority

-   ₹4,999 approved category -\> autonomous.
-   ₹5,001 approved category -\> approval required.
-   ₹1,200 new category -\> approval required.
-   approved one-time action does not accidentally authorise unrelated
    future spending.

### Missing events

-   expected dispatch occurs -\> no issue.
-   expected dispatch absent -\> Tarang wakes.
-   vendor response arrives before timeout -\> watchdog cancelled.
-   no response -\> follow-up triggered.

### Payment

-   success -\> continue.
-   pending -\> verify later.
-   failure -\> recovery path.
-   retry -\> no double payment.

### Logistics

-   booking successful but not delivered -\> remain open.
-   delivered -\> close.
-   shipment delayed -\> re-assess risk.

### Voice

-   no answer -\> backoff.
-   repeated no answer -\> alternative contact/recovery.
-   meaningful negative response -\> update world state.

### Persistence

-   restart agent while waiting -\> scheduled follow-up survives.

------------------------------------------------------------------------

# 32. What Must NOT Happen

Do not: - turn the scenarios into hard-coded if/else scripts that only
work for the demo; - let the Wizard choose the next action; - claim
nonexistent APIs are real; - let the LLM bypass authority rules; -
equate tool invocation with outcome success; - close a logistics issue
when only pickup is booked; - leave unresolved threads without a next
observation; - require the couple to manually remember follow-ups; -
make Telegram the agent brain; - depend on arbitrary personal WhatsApp
scraping for the prototype.

------------------------------------------------------------------------

# 33. North-Star Behaviour

A successful Tarang interaction should feel like:

> "Tell Tarang what outcome matters and what authority it has. Tarang
> keeps watch, notices when reality drifts from the plan, fixes what it
> can, asks only when it must, and returns when the outcome is actually
> secure."

------------------------------------------------------------------------

# 34. Current Open Implementation Questions

These should be resolved against actual partner documentation before
final submission:

1.  Exact Gnani endpoints and payloads available for the required call
    flow.
2.  Exact Pine Labs payment/authorisation endpoints available to the
    simulation.
3.  Exact Delhivery pickup/tracking endpoints and status payloads.
4.  Which proposed capabilities, if any, must be classified as one of
    the permitted imagined capabilities.
5.  Exact Telegram interaction design for approvals.
6.  Final system prompt.
7.  Final model selection.
8.  Exact Day-One data ingestion process.
9.  Exact vendor backup-selection criteria.
10. Exact retry/backoff configuration.
11. Exact approval expiry/escalation policy.
12. Exact risk-score thresholds.

Do not silently invent answers to these. Verify them before
implementation/submission.

------------------------------------------------------------------------

# 35. Compact Mental Model for Future Agents

When continuing this project, reason in this order:

``` text
1. What outcome is Tarang accountable for?
2. What does Tarang currently know?
3. What should have happened by now?
4. What actually happened?
5. Is there a discrepancy or risk?
6. What options can restore the outcome?
7. Which action is best?
8. Does Tarang have authority?
9. Execute or ask.
10. Did the real-world outcome occur?
11. If not, when/how will Tarang observe it again?
12. Log everything.
```

If step 11 has no answer and the outcome is unresolved, the design is
incomplete.

------------------------------------------------------------------------

# 36. Source Basis

This context file combines: - the Round 2 and Round 3 competition
requirements supplied in the project materials; - the two Tarang
scenarios supplied by the team; - the architecture and proactive-agent
framework developed during planning.

Where exact partner API capabilities/endpoints have not yet been
verified, this document intentionally marks them as open implementation
questions rather than asserting unsupported details.
