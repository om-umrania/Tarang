# Rail contracts and source reconciliation

Read on 1 October 2026: the two original PDFs in `resources/mails/`, dated
18 September (forwarded 30 September) and 22 September. They describe **Round 2**:
no running build then; specific endpoint and response knowledge required; Gnani
sandbox exploration was the exception. They are not an instruction to stop the
now-requested Round 3 prototype. The supplied Round 3 brief remains authoritative
for the actual simulation and evidence requirements.

| Surface | Implemented path | Evidence still needed |
|---|---|---|
| Telegram | Live Bot API ingestion, private-chat allowlist, replies, exact approval callbacks | Hosted round trip and redeploy persistence verified; see handoff |
| Model | OpenRouter structured JSON; Gemini Flash candidate plus tested temporary free Nemotron default | Scenario evaluations, not just greeting smoke |
| Gnani | Runnable STT adapter: `python -m tarang.gnani`; exact request metadata, audio hash, HTTP status and response saved to operator evidence | GNANI_API_KEY and an authorised ≤60-second source audio clip; no live Gnani call completed yet |
| Pine Labs | Exact documented bank-payout request preparation and correlated documented-response ingestion | Sandbox Payouts entitlement, credentials, funding and test beneficiary; live dispatch/reconciliation not enabled |
| Delhivery | Operator shipment/tracking request and provenance-labelled result ingestion | Serviceability, origin, package count/dimensions, SLA, exact shipment/pickup/tracking contract |

Gnani's documented speech endpoint is `POST https://api.vachana.ai/stt/v3` with
`X-API-Key-ID`, multipart `audio_file` and `language_code`. The adapter uses
`format=verbatim` and preserves the response without substituting amounts or
names. This transcribes a recording; it does **not** place a phone call.
[Gnani STT contract](https://docs.gnani.ai/api/STT/speech-to-text).

Pine Labs now has verified public bank-payout contracts: POST `/payouts/v3/payments/banks`, GET `/payouts/v3/payments` and funding-account lookup. The prototype prepares these requests and ingests labelled documented responses; no payment is executed. See [payment integration](PAYMENTS.md) for exact source contracts, authority checks and sandbox requirements.

Delhivery's [developer portal](https://one.delhivery.com/developer-portal/documents)
and [Maps reference](https://www.delhivery.com/maps/reference) were the links in
the mail. Maps and serviceability do not guarantee same-day delivery of 200
hampers. Those operational facts remain source inputs before a booking request.

Missing capability register: authorised outbound vendor calling, payout authority
matching the couple's limits, and capacity/SLA-backed urgent local delivery remain
unverified in the needed form. Keep them explicit in the competition submission;
operator assistance is not evidence that a rail supplies those capabilities.
