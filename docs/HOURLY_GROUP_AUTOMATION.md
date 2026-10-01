# Hourly wedding-group automation

This is application backend code, not a Codex automation or manual UI-reading loop.
The user chose a dedicated WhatsApp account for the existing wedding group.

## Data path

1. An isolated Node linked-device bridge continuously receives WhatsApp events.
2. It discards messages outside the exact configured group ID before persistence.
3. Selected-group text, unsupported-media markers and observed edits/deletions enter
   a durable local SQLite queue. Credentials use a separate private auth directory.
4. Every minute it delivers queued observations and connection health to the Python
   service. Acknowledged deliveries are removed from the queue; failures remain queued.
5. Python persists source revisions and checks its durable schedule. Every hour it
   reviews new messages, plus source references from the previous review, with the
   configured OpenRouter model. It makes no model call when no new messages exist.
6. A successful review advances the cursor atomically with the new review. Failed
   calls retain the cursor and use capped retry delays. A restarted worker resumes
   from persisted state. Large backlogs drain in bounded chunks before the next hour.
7. The operator console displays source health, last success, next run and the review.
   Telegram decisions receive this review as untrusted source context, including its
   age and freshness. It never grants spending authority or verifies physical outcomes.

The review distinguishes proposed dates, source-confirmed dates, cancellations,
contradictions and unknowns. It asks for the wedding ceremony date if missing or past;
it must not assume an upcoming wedding date from a mehendi date or silently shift years.
Message IDs and exact quotes are checked in code. Semantic extraction is model-generated
and still needs human review before consequential action. No automated group replies or
new Telegram push alerts are implemented by this monitor.

## Current readiness

Backend scheduler, authenticated intake, bridge queue, group filtering and status UI
are implemented. Dedicated-account pairing and real group delivery are NOT verified.
The bridge has not been started or linked. The server defaults to group monitoring off.
Local bridge configuration is ignored and private. No personal WhatsApp archive/session
was reused. Baileys 7.0.0-rc14 is pinned with a lockfile; its dependencies load locally.
It is an unofficial release-candidate client, not a WhatsApp-supported group API.
Re-pairing/protocol changes and account restrictions remain operational risks.

## Pair the dedicated account

1. Add that account to the intended wedding group using WhatsApp normally.
2. From the repository's `bridge` directory, run `npm run pair` in your own terminal.
   The private `bridge/.env` has the exact group name already prepared locally.
3. Scan the QR with **that dedicated account**, using WhatsApp → Linked devices.
   Pairing grants account-level device access. Only the selected group's content is
   retained/forwarded by this code. Do not pair a personal account inadvertently.
4. After connection, the exact group name must resolve to one group. The pairing
   command prints only its ID, saves credentials, and exits. Review that ID.
5. Set WHATSAPP_GROUP_ID in bridge/.env and on the Python service. Set the same
   WHATSAPP_BRIDGE_TOKEN on both; transfer it through secret configuration, not chat.
   Set WHATSAPP_GROUP_ENABLED=true on Python only after checking the target.
6. Run `npm start` under a persistent service manager. Pairing alone does not start
   hourly monitoring. For a hosted worker, transfer its private auth state securely
   to persistent encrypted storage. Never put credentials or the SQLite queue in Git.

Only selected-group messages go to the Python server and its configured OpenRouter
model for review. History supplied by the linked-device protocol is partial; it does
not guarantee complete history or messages missed during an outage. Full-account
history sync is disabled. Media is not transcribed. Observed unsupported edits remain
explicit evidence gaps; review source-health timestamps before relying on a snapshot.

## Hosting requirement

The bridge is a continuously running process and needs durable storage for credentials
and its queue. The Python scheduler also needs awake compute for timely hourly runs.
Existing free Render compute sleeps; a minute heartbeat is for source health, not a
promise or substitute for always-on hosting. No paid resources were provisioned.

For a free pilot, both processes can run on an existing machine that remains awake,
with a service manager restarting failures. Closing a terminal or sleeping the Mac
without supervision stops that process. For autonomous operation when the Mac is off,
use an always-on host and durable storage after approving the hosting budget.
Do not deploy this bridge to Vercel Functions or an ephemeral free filesystem.

## Verification

Run Python contract tests and `npm test` in bridge/. Tests cover authentication,
wrong-group rejection, duplicate batches, hourly gating, restart cursor preservation,
no model call without changes, failure without cursor advancement, invalid source IDs,
source staleness, and no financial or chat effects. Bridge filters reject unrelated
DMs/groups and retain unsupported media as such. These are not live pairing tests.

Live acceptance: pair the dedicated account, send authorised synthetic messages to
the group, observe bridge queue acknowledgement and the hourly review. Verify a
contradiction, then an accepted revision, then disconnect the bridge and confirm stale
status. Restart both processes and verify no duplicates or skipped pending messages.
Also verify the Telegram bot can answer from the latest review without claiming that
proposed dates are confirmed. These steps remain pending until pairing and hosting.

Sources: https://github.com/WhiskeySockets/Baileys and
https://github.com/WhiskeySockets/baileys.wiki-site/blob/main/docs/socket/receiving-updates.md

A Linux supervisor template is in `bridge/tarang-group-bridge.service.example`;
review paths and user before installing it on the chosen host. It has not been
installed on this Mac or any server. Pairing is an interactive one-time setup;
after activation the bridge and hourly Python job do not need ChatGPT running.

Verification on 1 October: 35 Python tests and 3 Node filter tests pass. The first
synthetic live-model review contradicted its structured fields. Added validation
rejects conflicting facts without supporting conflict citations; displayed summaries
are now derived from the validated structured counts. Model accuracy remains a
separate concern from scheduler reliability. `scripts/evaluate_group.py` is a
repeatable synthetic ceremony/setup dependency probe, with an ignored local receipt.

The new persistence is additive: separate `group_messages` and `group_runs` tables,
a source index, and one metadata schedule record. Existing Telegram commitments and
financial authority are not migrated or overwritten. Runtime startup creates these
tables; group intake stays disabled without explicit matching ID/token configuration.

Live model limitation: the new group-review probe has NOT passed end to end on the
configured free model. Observed inconsistent fields and schema validation failures;
a longer request stalled and was interrupted. The group job now has a 75-second
wall-clock timeout (in addition to HTTP timeouts), and runs separately from Telegram
processing. Cursor state remains unchanged on failure. Resolve the model-quality/
availability gate before activating on real group content. Do not describe the hourly
monitor as live, paired or semantically verified based on the passing contract tests.

Additional synthetic candidate checks: Qwen's free route reached the 75-second timeout;
Gemma's free route returned a provider error. Neither is promoted to the live model.
The group review acceptance test remains failed; supplying credits for a dependable
compatible model, or finding a passing existing provider route, is an activation gate.
The live server status confirms enabled=false, source_status=not_connected and
interval_seconds=3600. No live group messages or credentials were transmitted.
