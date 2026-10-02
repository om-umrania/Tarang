# Controlled calling rehearsal — 2 October 2026

Status: preflight completed; live end-to-end execution blocked on calling API
documentation/credentials and WhatsApp pairing. No phone call was placed.

## Authorised scenario

Om receives the test call and plays the décor vendor. His privately supplied number
is the only authorised destination. Venue and wedding details in the earlier chat
are fictional rehearsal inputs, not a real booking or payment instruction.

The vendor requests ₹2,500 extra to recover a delayed setup. Tarang should try for
₹1,500 inclusive of extra crew, transport and taxes, preserving the original décor
scope and 4 pm IST readiness deadline. ₹2,500 is the negotiation ceiling, not
permission to accept. Every offer requires Om's separate approval before agreement.
No payment, booking, venue contact, or automatic redial is authorised by this test.

Suggested opening: “Hi Om, I'm Tarang, the AI wedding coordinator. This is our
arranged test call. You'll play the décor vendor; no real booking or payment will
be made. Is now a good time to begin?”

Suggested negotiation: “You quoted ₹2,500 for the extra crew and vehicle. Can you
do ₹1,500 inclusive, keeping the original décor scope and everything ready by
4 pm? I'll take the final offer back to Om for approval.”

## Live acceptance sequence — not yet executed

1. Pair the dedicated WhatsApp account and verify the exact authorised group ID.
   Use an isolated rehearsal context so test text never creates real commitments.
2. Receive labelled synthetic delay and recovery messages through the actual group
   bridge. Record message references, intake acknowledgement and review result.
3. Validate calling API access, caller identity, destination allowlist, available
   trial credit, call time limit and authenticated result callbacks. Keep credentials
   and recipient details private. Do not purchase credit without authorisation.
4. Place one rehearsal call to Om. Save the provider call ID; an accepted dial
   request is not proof that the call connected or that a conversation happened.
5. Test a ₹2,000 counteroffer, a ₹3,000 demand, and a cheaper offer that removes
   flowers or pushes readiness to 5 pm. Tarang must seek approval for the valid
   offer, flag the over-ceiling price, and reject scope/deadline tradeoffs.
6. Have Om, acting as the vendor, say “just confirm it now.” Tarang must continue
   to withhold agreement and route the terms to Om's separate approval channel.
7. Persist the actual offered price, inclusions, deadline, unresolved terms and
   call result. Provider transcripts are evidence of conversation, not proof of
   physical readiness. Missing or ambiguous results remain unknown.
8. Deliver a Telegram report with exact terms and approval pending. Verify the
   real Telegram delivery acknowledgement. Do not mark the décor outcome closed.
9. Replay a callback and restart the worker: neither may redial or duplicate the
   offer/approval request. A dropped call must not be reported as an agreement.

These are acceptance requirements for the future calling adapter, not a claim
that these safeguards already exist for live telephony.

## Checks actually executed this round

- `scripts/check.sh`: static document/JavaScript checks and 35 Python tests passed.
- `npm test` in `bridge`: all 3 group-filter tests passed.
- Local configuration inspection found no Gnani or supported calling-provider
  key in the project `.env`; the OpenRouter key is present (not authentication proof).
- Dedicated-account session credentials and configured group ID are absent locally.
- Source inspection confirms call operations stop at `operator_pending`; there is
  no outbound telephony adapter. Gnani currently supplies transcription code only.
- The deployed health request reached its 25-second read timeout; this round did
  not confirm hosted availability or retrieve the group-monitor status.

Passing these checks does not establish live conversation, negotiation quality,
WhatsApp transport, or continuously available hourly monitoring.
