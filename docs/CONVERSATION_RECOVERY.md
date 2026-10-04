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

Normal free-text replies after intake now contain only the model's concise answer,
without appending the full saved plan or review/change/pause controls. During
collection, only the next missing question and its buttons accompany the answer.
The repeated numbered menu and /choose tutorial have been removed from all intake
messages; /choose remains supported. Explicit guided button interactions retain
their controls. The prompt requests a direct answer and one necessary next decision,
with separate quoted, approved and paid amounts.

The button-driven review step also uses a short next-action message rather than
automatically dumping all stored fields. Full summaries are requested explicitly
in conversation. See [repeatable conversation cases](CONVERSATION_TEST_RUNBOOK.md)
for exact inputs, expected checks and outstanding live integration gates.
