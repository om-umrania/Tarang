# Conversation reply recovery

4 October 2026: the live Jaipur case produced two failed model turns. The prior
worker discarded exception details and immediately sent the generic AI-unavailable
message followed by an unchanged intake summary. Historical error causes cannot
be recovered from those rows.

The isolated conversation worker now retries a transient timeout, transport error,
429, selected 5xx response or schema-validation error once, after one second.
Each attempt is limited to 40 seconds; the processing lease lasts 100 seconds.
Retries are generation requests only, never vendor, booking or payment actions.
Reset/deletion is checked before retry and before delivery. Authentication and
unknown errors are not automatically retried.

Successful recovery sends only the successful answer. Exhausted failures retain
the input and unchanged facts, mark the turn failed, and briefly explain that the
latest update was not applied. They do not repeat the stale summary or promote a
guided scenario. A crashed request is not replayed. Logs contain exception class,
attempt number and retry eligibility, never raw provider bodies or message text.

This reduces transient interruptions; it does not guarantee provider availability.
Live verification after release is required before recording the final scenario.

All successful free-text replies now contain only the model's answer, even while
intake fields remain empty. No missing-field question or options are appended.
This prevents the generic trade-off question from reappearing after a delivery
update or closure. Initial entry and explicitly chosen guided buttons retain
their controls; old buttons are still invalidated when a free-text turn starts.
The repeated numbered menu and /choose tutorial have been removed from all intake
messages; /choose remains supported. Explicit guided button interactions retain
their controls. The prompt requests a direct answer and one necessary next decision,
with separate quoted, approved and paid amounts.

The prompt treats missing fields as optional hints, asks only for information
that blocks the next decision, and tracks the supplied case toward verification
and closure. Updated fields should preserve still-valid constraints and supersede
stale statuses. This is model guidance, not a deterministic guarantee of correct
fact extraction or operational closure. Scenario 2's courier-unavailable cause,
venue quantity/condition check and payment reconciliation are explicit examples.

Local regressions cover partial intake, carrier-only status and a closure reply
without priority filled in, plus stale buttons and absence of operational effects.
Live model replay of saved Telegram history was blocked by approval review; no
such transcript was sent for evaluation. Hosted verification remains pending.

The button-driven review step also uses a short next-action message rather than
automatically dumping all stored fields. Full summaries are requested explicitly
in conversation. See [repeatable conversation cases](CONVERSATION_TEST_RUNBOOK.md)
for exact inputs, expected checks and outstanding live integration gates.
