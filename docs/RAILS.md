# Rail contracts and source reconciliation

Read on 1 October 2026: the two original PDFs in `resources/mails/`, dated
18 September (forwarded 30 September) and 22 September. They describe **Round 2**:
no running build then; specific endpoint and response knowledge required; Gnani
sandbox exploration was the exception. They are not an instruction to stop the
now-requested Round 3 prototype. The supplied Round 3 brief remains authoritative
for the actual simulation and evidence requirements.

| Surface | Implemented path | Evidence still needed |
|---|---|---|
| Telegram | Live Bot API ingestion, private-chat allowlist, replies, exact approval callbacks | Hosted round trip and restart check |
| Model | OpenRouter structured JSON with configurable Gemini Flash model | Scenario evaluations, not just greeting smoke |
| Gnani | Runnable STT adapter: `python -m tarang.gnani`; exact request metadata, audio hash, HTTP status and response saved to operator evidence | GNANI_API_KEY and an authorised ≤60-second source audio clip; no live Gnani call completed yet |
| Pine Labs | Operator-approved payment request and provenance-labelled result ingestion | Appropriate payout/authorisation product, exact API contract, supported beneficiary/funding and documented response |
| Delhivery | Operator shipment/tracking request and provenance-labelled result ingestion | Serviceability, origin, package count/dimensions, SLA, exact shipment/pickup/tracking contract |

Gnani's documented speech endpoint is `POST https://api.vachana.ai/stt/v3` with
`X-API-Key-ID`, multipart `audio_file` and `language_code`. The adapter uses
`format=verbatim` and preserves the response without substituting amounts or
names. This transcribes a recording; it does **not** place a phone call.
[Gnani STT contract](https://docs.gnani.ai/api/STT/speech-to-text).

The Pine Labs landing page lists distinct products. Its payment-collection sample
is not proof of a vendor payout capability. Do not swap collection for disbursement
or invent bank payout endpoints. [Pine Labs portal](https://www.pinelabs.com/docs).

Delhivery's [developer portal](https://one.delhivery.com/developer-portal/documents)
and [Maps reference](https://www.delhivery.com/maps/reference) were the links in
the mail. Maps and serviceability do not guarantee same-day delivery of 200
hampers. Those operational facts remain source inputs before a booking request.

Missing capability register: authorised outbound vendor calling, payout authority
matching the couple's limits, and capacity/SLA-backed urgent local delivery remain
unverified in the needed form. Keep them explicit in the competition submission;
operator assistance is not evidence that a rail supplies those capabilities.
