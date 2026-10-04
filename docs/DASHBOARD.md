# Telegram and decision dashboard

Implemented locally on 4 October 2026. Intended public website:
[Tarang](https://tarang-virid.vercel.app/), with the authenticated dashboard at
`/dashboard`. Local verification is distinct from a deployed live Telegram round trip.

## Data and access

The dashboard reads `/api/dashboard` on the bot's existing FastAPI backend and
refreshes every five seconds while visible. `vercel.json` serves `docs/` and
rewrites only that API path to the existing Render service. Requests carry the
operator's bearer token; the website contains no embedded secrets. The same page
is served locally and on Render at `/dashboard`.

Use the existing OPERATOR_TOKEN privately. It grants operator access to all stored
conversations; this is not a visitor/couple login. Do not share it with demo visitors.
The page keeps it only in memory, clears the input immediately and removes loaded
data on disconnect or rejected authentication. Responses and the Vercel proxy are
marked `private, no-store`; no conversation data goes into static build output.
Dynamic text is rendered with DOM textContent and the dashboard restricts script,
style and network access to its own origin.

Select a wedding workspace or an isolated fictional rehearsal. The view includes:

- Recorded Telegram input, button labels, outgoing text/voice reply text and outbox status.
- Model processing counts, pending or uncertain delivery and explicit last-sync age.
- Current outcome, responsible owner, pause state and saved next observation.
- Exact operation proposals and approval/expiry/operator/result states.
- Decision ledger and source-labelled outcome evidence.
- Demo intake facts, current phase, latest preference and voice transcript review status.

A connected badge proves the dashboard fetched a database snapshot. It does not
prove worker health, Telegram delivery, message reading or vendor completion.
Configuration indicators describe configured access, not successful provider calls.
Sent means Telegram accepted the request. Unknown requires reconciliation. Approval
and operation success do not by themselves prove physical fulfilment. Rehearsals
remain explicitly fictional and never appear as real operations.

The page pauses polling when hidden, retries failed requests after 15 seconds,
times out requests after 25 seconds and retains a visibly stale last-known view on
network/server failure. It aborts old requests on chat switches and disconnect.
Free Render sleep can delay the first request and scheduled work.

## Persistence and history

An additive migration creates `demo_messages` for bounded display text and adds
`outbox.created` for newly queued messages. Existing outbox records retain zero,
rendered as **Time not recorded**, rather than a fabricated timestamp. No existing
records are removed by this migration. New demo input is recorded in the same
transaction as the existing demo handling, using the deduplicated Telegram update.
Demo `/reset`, `/delete`, `/live` and seven-day inactivity cleanup remove this
additional history along with existing demo data. No audio files or Telegram file
IDs are exposed by this view.

Historical demo free-text turns are reconstructed from existing `demo_turns` when
available. Old button events and deleted records cannot be reconstructed. History
is bounded to the latest 100 rows per type/direction; a banner indicates truncation.
The conversation picker is bounded to 1,200 records and signals truncation. This
is an operational status view, not an archival export. No new public access or
real booking/payment authority is introduced.

## Validation and release

Run `./scripts/check.sh`. Dashboard tests cover authentication, webhook-to-decision
projection, approval updates, labelled evidence, uncertain delivery, demo/workspace
isolation, reset/delete/retention, history bounds and upgrading an existing SQLite
outbox. The shared `demo_database` fixture can use an explicitly isolated PostgreSQL
test schema when TARANG_TEST_POSTGRES is supplied; PostgreSQL execution is not
implied by a normal SQLite run.

Local browser verification uses a separate synthetic database and no bot worker.
Check desktop and narrow widths, connect/disconnect, invalid token, conversation
switching and automatic refresh. Do not describe synthetic checks as live Telegram
or model evidence.

Release through the repository's normal GitHub branch/PR workflow. Do not directly
deploy or promote on Vercel. After an authorised merge, the existing GitHub-to-Vercel
integration must build the website, and Render must receive the matching backend
revision through its normal deployment path. Until both have the change, the UI
reports unavailable API instead of claiming a live connection. No hosting setting
or webhook change is required by the application; actual integration readiness still
needs verification. The source routing uses Vercel's documented
[external rewrites](https://vercel.com/docs/routing/rewrites).

After release, verify `/` and `/dashboard`, confirm unauthenticated API access is
rejected, connect privately with the operator token, and check an authorised
Telegram message and reply appear in the selected conversation. Verify cache headers
and refresh across both Vercel and Render. Never paste tokens into URLs or reports.
