# Scenario 2 — Anand Gifts courier recovery

Prepared 4 October 2026. Run after Scenario 1's evidence has been saved. This is a repeatable conversation script and acceptance document, not evidence of completed calls, bookings, payments or delivery.

## Story and authority

On 12 December 2026 at 11:40 AM IST, Tarang's routine check finds that Anand Gifts has not shipped the 200 return-gift hampers promised to Meera and Rohan's Jaipur wedding venue. The vendor's original courier arrangement has failed. Tarang evaluates a direct replacement pickup instead of asking the couple to chase the shop.

The primary version follows the supplied 100-word story: the couple has already delegated the exact ad-hoc courier category and scope, with sufficient remaining budget and a transaction cap that permits ₹1,200. That is a **Rule B category check passed**, not a category escalation. A small amount alone is insufficient. If the category is absent or the payee, scope, remaining budget or authority does not match, use the escalation branch below.

Do not carry over Scenario 1's separate surcharge approval to this case. These are distinct commitments and authority records.

## Operator preparation — do not paste as a customer message

- Save Scenario 1's Telegram/dashboard evidence before starting `/talk` for this case. Do not delete the previous evidence to clean up the recording.
- Scenario time is 12 December 2026, 11:40 AM IST; wedding date is 14 December. This is not the runtime's current clock.
- The wedding registry must already contain the hamper obligation, promised date and routine follow-up owner. The courier booking itself may be untracked, but an agent-initiated check needs an existing obligation or observation schedule. Do not imply Tarang discovered a purchase it never knew about.
- Load the exact approved courier delegation, remaining category budget, permitted payee and payment scope through the authorised operator path. A conversational statement is not a deterministic budget configuration.
- Confirm pickup/drop addresses, package count, dimensions/weight, contact availability, readiness, the required arrival time on 12 December and the named venue verifier. These remain OPEN until provided; do not invent addresses or a delivery deadline.
- ₹1,200 inclusive price, priority pickup capacity and delivery ETA are scenario inputs until actual provider evidence establishes them. Same-day pickup does not necessarily mean same-day delivery.
- Confirm the charge is not already included/paid in Anand Gifts' order; avoid duplicate payment and retain any vendor refund or credit as a separate unresolved item.
- For a recording, disclose scripted external events once in the opening caption. Ordinary bot replies should remain concise and natural.

## How to run it

Copy each **Send** message separately and wait for Tarang's answer. For a voice test, speak that message, review the transcript and confirm it before continuing. The **Example reply** is a writing target, not a message to paste as though Tarang generated it. Provider observations must be sourced separately in a live integration test.

The Telegram run below tests conversational reasoning. Manually sending the monitor event does not prove an autonomous scheduled trigger; supplying a call result does not prove a Gnani outbound call. Current Gnani integration supports transcription and spoken Telegram replies.

## 1. Monitor check identifies missing dispatch

**Send — operator-supplied case event**

> It is 12 December 2026, 11:40 AM IST in this case. Anand Gifts promised to deliver 200 return-gift hampers to Meera and Rohan's Jaipur wedding venue by today. The routine follow-up checkpoint is due and there is no dispatch evidence. What should you check first?

**Example reply**

> I'd check whether the hampers are packed and whether Anand Gifts has a confirmed pickup and delivery time. Missing dispatch evidence alone doesn't prove the shipment failed.

**Pass:** Recognises a due check, not an incoming complaint. Does not claim the call has happened or invent a tracking number. Requests missing operational details only when relevant.

## 2. Vendor's courier has failed

**Send**

> Anand Gifts reports that all 200 hampers are packed, but its regular courier is unavailable today and nothing has shipped. The shop can hand over the packages to a replacement courier. Preserve the full quantity and safe handling. What is your recovery plan?

**Example reply**

> I'd arrange a replacement pickup from Anand Gifts and confirm an arrival time that meets today's deadline. First I need the verified addresses, package details and handover contact.

**Pass:** Owns the proposed coordination instead of telling Meera or Rohan to call the shop. Does not assert that a booking or same-day delivery exists yet.

## 3. Delhivery quote and category check

**Send**

> Delhivery offers a same-day priority pickup for ₹1,200 inclusive. For this case, the ad-hoc courier category already has sufficient remaining budget and exact delegated authority for this payee, route and service; ₹1,200 is within the transaction limit. The delivery ETA still needs confirmation. Is another approval needed, and can you promise arrival today?

**Example reply**

> No additional approval is needed if those exact terms match the recorded delegation. I still need a confirmed delivery ETA—same-day pickup alone doesn't establish arrival today.

**Pass:** No unnecessary escalation when exact authority matches; no payment or delivery claim. The operator must separately verify the actual policy engine reaches the authorised state.

## 4. Pickup preparation with an unresolved deadline

**Send**

> The addresses, package details and handover contact have been verified, but the required venue arrival time and Delhivery's delivery ETA are still unconfirmed. What can be prepared, and what must remain open?

**Example reply**

> The pickup details and ₹1,200 payment request can be prepared within the approved scope. I can't confirm the recovery meets the deadline until the required arrival time and delivery ETA are agreed.

**Pass:** Does not substitute a made-up time. No claim that preparation executed a payout or booked pickup. Continue the actual booking path only after those missing values are supplied and verified.

## 5. Payment submitted but not settled

**Send — supplied status observation**

> The ₹1,200 Pine Labs request has a matching payment reference and reports SCHEDULED. No terminal payment result has arrived, and pickup acceptance is not yet recorded. What is the current status?

**Example reply**

> The ₹1,200 payment instruction is scheduled, not confirmed paid. Pickup acceptance and the delivery commitment are still pending.

**Pass:** No “paid,” “booked,” or “done.” Repeated checks use the same correlated operation/reference; a timeout must not create another payment.

## 6. Payment and pickup confirmed, delivery pending

**Send — supplied status observation**

> A matching Pine Labs status now reports SUCCESS for ₹1,200, and Delhivery has accepted the pickup. The delivery ETA has been checked against the agreed arrival deadline and is acceptable. There is no venue receipt yet. What should you track next?

**Example reply**

> Payment and pickup acceptance are confirmed in the supplied records. I'd track collection and delivery, then obtain the venue's count and condition check before closing the hamper outcome.

**Pass:** Correlates amount, payee and reference; does not equate an accepted pickup with collection or delivery. In production, these statements require authenticated provider evidence, not merely this text input.

## 7. Carrier says delivered

**Send**

> Delhivery's tracking status now says delivered at the venue, but the venue coordinator has not confirmed quantity or condition. Can the hamper outcome be closed?

**Example reply**

> Not yet. The venue coordinator needs to confirm that all 200 hampers arrived intact; the carrier's status alone doesn't establish that.

**Pass:** Keeps the outcome open and identifies who supplies the next observation.

## 8. Venue receipt verified

**Send**

> The designated venue coordinator confirms all 200 hampers were received intact before the agreed deadline. The ₹1,200 payment is reconciled to the same courier operation, with no duplicate charge. What is now complete?

**Example reply**

> The supplied evidence confirms all 200 hampers arrived intact on time and the ₹1,200 payment is reconciled. Those records support closing this delivery outcome.

**Pass:** Closure depends on physical receipt plus financial reconciliation. The backend's fixture mode remains labelled as such in evidence; conversational agreement alone does not close a real commitment.

## 9. Concise couple update

**Send**

> Draft a two-sentence WhatsApp update to Meera and Rohan explaining what failed, how it was resolved, the spend and whether you needed anything from them. Do not send it.

**Example reply**

> Anand Gifts' courier fell through, so the replacement pickup was arranged within your approved courier authority for ₹1,200. The venue has confirmed all 200 hampers arrived intact on time and payment is reconciled; no additional approval was needed.

**Pass:** Draft only; no invented WhatsApp delivery claim. Use completed wording only after the supplied evidence at steps 6–8; otherwise state the pending items.

## Alternate branch — category authority missing

Run this instead of step 3 in a separate test, not after asserting that authority exists.

**Send**

> Delhivery offers the pickup for ₹1,200, below the transaction limit, but the ad-hoc courier category has no approved budget or delegated authority. Can you proceed without asking Meera and Rohan?

**Example reply**

> No. The amount is within the transaction limit, but this category isn't authorised. Meera and Rohan need to approve the exact ₹1,200 courier expense before proceeding.

**Check:** This is the **Rule B escalation**. If they approve, record exact payee, route, service, amount, expiry and budget impact. Do not silently treat one approval as unlimited future category delegation.

## Alternate branch — only 180 received

Replace step 8 with:

> The venue coordinator counted only 180 of the 200 hampers. The carrier still says delivered. What remains open?

**Expected:** Twenty hampers remain unverified; reconcile package references with the carrier/vendor and obtain a fresh venue count. Do not close until all 200 and their condition are verified, or the couple explicitly changes the required outcome.

## Repeat-run evidence

| Checkpoint | Evidence required |
|---|---|
| Agent-initiated trigger | Stored obligation, due time, scheduler execution and resulting event; not a pasted Telegram trigger |
| Vendor contact | Provider call ID, connection/result and transcript provenance; no-answer/retry only if actually supported |
| Logistics feasibility | Exact inclusive quote, route, package capacity, pickup acceptance and arrival ETA |
| Authority | Category room, transaction cap, payee/scope match or one-time approval |
| Payment | Stable reference, exact amount/payee, terminal result and no duplicate |
| Fulfilment | Carrier event plus named venue verifier's quantity, condition and timing |
| Couple communication | Actual destination and transport acknowledgement if sent; draft text alone is not delivery |
| Dashboard | Correlated chat, input/reply IDs, decisions, operations and evidence; inspect the actual saved records |

Respect the public conversation's ten-model-turn daily limit. The primary script uses nine turns before extra clarification, retries or voice-intake questions; do not attempt it immediately after consuming the allowance on Scenario 1. Save evidence and schedule another test window, or use the isolated local integration harness without claiming that as a hosted run. Do not raise limits or switch identities to evade them.

## 100-word story — intended successful outcome

The following is a scenario narrative, not a claim of execution:

> On 12 December 2026, Tarang checks Anand Gifts' dispatch for Meera and Rohan's Jaipur wedding. The shop's courier is unavailable, leaving 200 hampers waiting. Tarang checks a Delhivery replacement against the approved courier category, delegation and remaining budget. The ₹1,200 service qualifies without another approval. After confirming the route and delivery deadline, Tarang arranges pickup and reconciles the payment. A carrier delivery update is followed by venue confirmation that all 200 hampers arrived intact. Only then does Tarang close the delivery outcome and send the couple a concise summary of the failure, recovery, spend and confirmed receipt at the venue.

## Current status

Document prepared; this complete Anand Gifts case has not been executed. The existing guided hamper scenario is narrower. Actual outbound calls, Delhivery booking, Pine Labs payout and WhatsApp delivery require configured integrations and separately verified access. Text-to-speech replies do not establish those capabilities.
