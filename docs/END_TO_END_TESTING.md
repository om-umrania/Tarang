# End-to-end testing and WhatsApp dates — 1 October 2026

## Scope and evidence

- 27 local contract tests pass, including authentication, duplicate intake, isolated
  wedding scopes, grounding checks, spending authority, pause and restart recovery.
- Live Render health returned HTTP 200. Persisted Telegram events 1, 2 and 4 are done
  and outbox records 1–5 are sent. Hosted clock event 5 completed in one attempt.
  Older clock event 3 failed after three attempts; preserve that failure evidence.
- These records prove prior processing and delivery acknowledgement, not a newly
  completed user-client test or that a recipient read a message.
- The Mac Telegram UI could be inspected but input failed with no available window.
  Om subsequently sent the requested synthetic date scenario.
  Do not simulate an inbound webhook and describe it as a real Telegram-origin message.

Run `scripts/evaluate_dates.py` for four synthetic date scenarios through a local
signed Telegram webhook, live model, isolated SQLite databases, and a captured
Telegram adapter. It checks durable deduplication, a completed event, a captured
reply and absence of operations/closure. Responses still require semantic review.
Receipt: `.runtime/date-integration-evaluation.json` (ignored). This is integration
testing, not actual Telegram or WhatsApp transport proof.

## Actual remaining acceptance test

1. Om sends the labelled synthetic date message to @tarang_wedding_bot.
2. Correlate its real inbound event with model decision and Telegram-acknowledged reply.
3. Check wording: neither proposed date is called confirmed; no vendor operation or
   real deadline is created from the test. Existing wedding state should remain intact.
4. Verify the actual conversation response in Telegram and record evidence accurately.
5. For WhatsApp, identify the exact group and authorised sample; verify ingestion,
   date extraction and human confirmation before testing automatic follow-ups.

No paid hosting change was made. Free Render can sleep, so a successful short awake
scheduler test does not establish continuously available background monitoring.

## Recommended WhatsApp first slice

The user has now identified the desired source as their existing wedding group;
the exact group has been identified privately. Start with an exported chat or selected text
messages, not an assumed Cloud API connection to the group. WhatsApp documents chat
export: https://faq.whatsapp.com/1180414079177245/ . Exports are snapshots, not live sync.

The current webhook supports only explicitly routed direct text messages. It has no
chat-export parser or structured date registry yet. Ordinary Telegram text can be
used for a small reviewed prototype sample, but should not be described as a durable
calendar ingestion feature. Source author/time and message quotes must be retained.
Current official Groups API documentation could not be retrieved (HTTP 429), so
eligibility and access to the existing group remain unverified. Do not infer that
registering a Business number allows it to read arbitrary existing groups or history.

Extract a reviewable timeline with:
- Event/task (wedding ceremony, mehendi, sangeet, setup, delivery, guest arrival).
- Date, year, local time and timezone; keep missing components unknown.
- Location, owner/vendor and completion deadline, if explicitly stated.
- Status: proposed, confirmed by a named source, changed/cancelled, conflicting, unknown.
- Original author, message timestamp, verbatim quote and source reference.
- Superseding message reference when a change is explicitly accepted.

Relative dates need the original message timestamp/timezone; '04/05' needs the date
format; 'at 7' needs AM/PM. Two different dates are not automatically a conflict if
one is a clearly accepted revision. Vendor claims are not couple approval. Never
create bookings, calendar events or payment authority merely from extracted text.
Keep the group's export out of Git and restrict any model processing to the agreed
source. No unrelated private WhatsApp archive or session credentials were accessed.

## Completed real Telegram test

Om sent the Mehendi proposal scenario through Telegram. Inbound event 6 completed in
one model attempt; its corresponding outbox record is `sent`. Telegram reported zero
pending updates and no webhook error. The reply asked which date was confirmed and
created no operation or closure. It also asked unrelated onboarding questions: this
copy issue prompted a focused-date clarification rule in prompts/runtime.md. No claim
of perfect persona compliance is made from transport success.

All four live-model synthetic integration scenarios passed; responses were reviewed:
proposals stayed tentative, missing year/timezone were queried, an accepted revision
superseded the old date, and ambiguous numeric dates/time were queried. No operations
were created. Test receipt remains local and ignored.

The authorised group was opened read-only in the Mac app. Only a newly created group
and no date messages were visible, with a syncing-paused notice requiring WhatsApp to
be opened on the phone. This is an incomplete local view, not proof the full group has
no dates. No group messages were sent or exported to OpenRouter.

## Fixes from testing

Focused date questions now explicitly request a direct confirmation-status answer
without unrelated onboarding questions. A subsequent synthetic live-model probe
correctly said neither date was confirmed, but still proposed changing the outcome.
Therefore runtime code now enforces read-only commitment handling for Telegram text
starting `TEST ONLY:` or `E2E TEST`: no outcome/owner/deadline changes, operations or
closure; only an audit record and labelled test reply. Two adversarial contract tests
pass even when the model proposes spending and closure. The user-authored transport
test omitted the label; this new guard did not apply to that earlier message.

The 27-test suite and static checks pass. The full Telegram transport check predates
the prompt/guard refinement; those refinements are separately validated by the
synthetic model probe and deterministic contract tests.
