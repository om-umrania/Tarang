# Tarang — Single Source of Truth (SSOT)

**Project:** Tarang, a proactive wedding-operations agent
**Competition:** The Ken's Case-Build Competition 2026 ("The Great Rewiring") — Round 3
**Opening:** "Running your wedding" · Track: Product Strategy
**Round 3 deadline:** Sunday, 4 October 2026, 11:59 PM IST
**Document status:** v0.1 — reconstruction from conversation + attached files. NOT yet validated by the team.
**Last updated:** 30 September 2026

> **How to read this file:** Every item is tagged with its epistemic status:
> `[CONFIRMED]` = explicitly decided by the team in this conversation or a submitted round.
> `[ASSUMPTION]` = used in the work but never explicitly ratified — do not treat as a requirement.
> `[IDEA]` = discussed, not accepted or rejected.
> `[REJECTED/OOS]` = explicitly set aside or out of scope.
> `[OPEN]` = unanswered question.
> Assumptions have NOT been silently promoted to requirements.

---

## 0. The single most important open item

**[OPEN-0] Interface for the simulation: WhatsApp or Telegram?**
The product concept, both submitted rounds, and every scenario use **WhatsApp** as Tarang's primary human interface. The Round 3 prompt introduced the word **"Telegram"** for the first time. These are not reconciled. Likely interpretation: WhatsApp is the *product* interface; Telegram is a practical *simulation* stand-in (free Bot API, no gating). This must be decided explicitly before any build, because it changes the entire ingestion + messaging architecture of the recorded demo.

---

## 1. Problem & desired outcomes

- `[CONFIRMED]` **Core problem:** The person running a wedding is also its overworked project manager. Coordination chaos — vendor discovery, follow-ups, chasing, payments, logistics, and unexpected failures — falls on one person, fragmented across calls, WhatsApp groups, notes, and invoices.
- `[CONFIRMED]` **Tarang's accountability:** absorb the organisational and coordination load of a wedding by managing vendors, handling follow-ups and payments, taking care of logistical and unexpected issues, **while keeping the family involved only when their decision is genuinely needed.**
- `[CONFIRMED]` **Emotional job-to-be-done (own-wedding framing):** give the couple their own wedding back — let them be participants at their event, not operators of it.
- `[ASSUMPTION]` Success = the wedding's operational threads all reach verified closure with minimal, well-timed human interruption. (Implied throughout; never stated as the metric.)

---

## 2. Target user (ICP)

- `[CONFIRMED]` **Primary ICP = the couple running their own wedding.** In the canonical scenario: **Meera & Rohan**, Bengaluru-based, hosting a **destination wedding in Jaipur on 14 December 2026.**
- `[CONFIRMED]` **The couple themselves set Tarang's budgets and authority** (they are the hosts/decision-makers — no parent intermediary in the canonical version).
- `[IDEA]` A secondary ICP — a daughter/family member running *parents'* wedding — was explored (persona "Radha") and its buyer-vs-user split noted, but the team chose the own-wedding couple as canonical. Radha is retired from the scenarios.
- `[CONFIRMED — orbit characters]` Vendors (Suresh/decorator, Petal Inn/backup décor, Anand Gifts/return gifts); out-of-town relatives (guest-transport situations). These generate situations; they are not users.
- `[OPEN-1]` Is the *buyer* always the same as the *user*? For monetisation (Part 2), does the couple pay, a parent pay, or the platform earn indirectly? Unresolved.

---

## 3. Agent architecture — the 10-stage lifecycle

`[CONFIRMED]` Tarang is described as a **10-stage operating system with continuous monitoring and conditional escalation**, not a linear flow:

1. **Connect** — establish context (voice briefing).
2. **Map** — build the plan: vendors, budgets, backup shortlist, guest list, hierarchy.
3. **Set Authority** — couple defines spending limits, negotiable categories, approval rules.
4. **Execute** — act on vendors: call, negotiate, confirm, pay.
5. **Monitor** — watch every open thread; scheduled check-ins.
6. **Resolve** — handle problems within authority.
7. **Escalate** — hand decisions outside authority to the couple.
8. **Verify** — confirm the outcome actually happened before closing.
9. **Event-Day** — heightened real-time operation on the wedding day.
10. **Close** — reconcile and summarise; end the thread.

`[CONFIRMED]` When something goes off-track, it branches into **Resolve** (in authority) or **Escalate** (outside authority), depending on the boundary.
`[CONFIRMED]` **Day-One onboarding (Connect/Map/Set Authority) happens BEFORE the recorded simulation** and is answered in writing, not re-enacted on camera, to keep the recording tight.

---

## 4. Authority model (spending boundaries)

- `[ASSUMPTION — proposed by Claude, tacitly used]` **Two-rule authority model:**
  - **Rule A (amount):** Tarang can auto-pay up to a **per-transaction cap** within any category that has a budget with remaining room.
  - **Rule B (category):** any spend in a category with **no** budget set requires approval, regardless of size.
- `[ASSUMPTION]` **Per-transaction cap = ₹5,000.** This specific number was proposed by Claude ("say ₹5,000") and used in scenarios; it was never explicitly ratified by the team.
- `[CONFIRMED]` Autonomy level = **L3** — acts autonomously within predefined limits; asks the couple to step in beyond them.
- `[CONFIRMED]` The couple can define: max spend without approval; vendors/categories Tarang may negotiate with; what it can confirm directly; which decisions need approval; what changes it may make.
- `[CONFLICT — needs resolution]` After the latest edit, **Scenario 2's ₹1,200 courier cost was moved to "within the ad-hoc courier budget," so it is now paid autonomously, not escalated.** This means an "ad-hoc courier" category budget now exists, AND the earlier "two different escalation reasons" standout (amount vs category) is weakened — only Scenario 1 now shows an escalation. See [OPEN-6].

---

## 5. External tools / rails

### Rail status legend: Confirmed (documented) / Gated (exists but access unclear) / Must-Build (capability gap)

**VOICE — Gnani**
- `[Confirmed]` Start Voice Briefing — real-time STT, 10+ Indian languages + native script. (State 1)
- `[Gated]` Call Vendor — Gnani references outbound voice agents on its enterprise page, **no public API spec found; access/implementation gated.** (States 4, 6)
- `[Must-Build]` Detect Call Urgency — real-time urgency scoring not found (only post-call sentiment via Call Analytics). (States 5, 6)
- `[Must-Build]` Schedule Next Call — task-based scheduling, retry limits, stopping logic; no documented orchestration layer. (States 5, 6)

**PAYMENTS — Pine Labs**
- `[Confirmed]` Confirm Permission Status — mandates & recurring permissions documented. (State 3)
- `[Confirmed]` Submit Payout — Instant Payouts, maker-checker approval, custom roles. Failure path: bank rejects. (States 4, 6)
- `[Must-Build]` Check Category Ceiling — Pine Labs enforces a rule handed to it but does not define Tarang's category-specific limits. (State 6)
- `[Must-Build]` Release on Delivery — no escrow/milestone-based release found. (State 8)

**LOGISTICS — Delhivery**
- `[Confirmed]` Get Route ETA — routing/distance-matrix via Maps. (States 2, 5)
- `[Confirmed]` Track Shipment — pull or webhook; corroborated via third-party guides (dev portal is JS-rendered, not readable). Failure path: shipment stalls. (State 5)
- `[Confirmed/corroborated]` Request Pickup — corroborated via third-party sources, not directly confirmed from primary docs. (States 4, 10)
- `[Must-Build]` Book Guest Transport — **confirmed capability gap**; no passenger-transport booking surface in Delhivery's API. (States 4, 9)

**PROPOSED 4th RAIL — Hyperlocal Quick-Commerce (Blinkit)**
- `[IDEA]` "Agentic Event Procurement API" — Tarang places short-notice orders (puja items, snacks, décor supplies, D-day emergencies) within family-set budget/rules, pre/during/post wedding. Proposed, not built; depends on a capability Blinkit does not currently expose.

> `[OPEN-2]` Every "Confirmed" above still needs the **exact endpoint name + request/response** pulled from live docs for Part 1 Q4. Corroborated-via-third-party items (Delhivery Track/Pickup) especially need primary-source verification or an explicit caveat in the submission.

---

## 6. Human interface & data ingestion

- `[CONFIRMED]` **WhatsApp = primary interface.** Couple messages Tarang, sends voice notes, or calls; approves decisions there. Tarang proactively messages when input/approval is needed.
- `[CONFIRMED]` **Tarang app = secondary interface** — dashboard for overall status, task/vendor progress, timelines, payments, upcoming decisions. (Expected to be opened rarely — mainly at setup and post-event reconciliation.)
- `[CONFIRMED — customer assets to ingest]` WhatsApp coordination chats; planning documents (Excel/Google Docs); vendor invoices. Together these carry budget, vendor list, timeline, decisions-to-date.
- `[OPEN-3]` **Exact day-one ingestion mechanism is undesigned.** How do the WhatsApp chats / planning docs / invoices actually get into Tarang? Voice briefing (Start Voice Briefing) + manual upload? A dedicated onboarding WhatsApp number that scans a wedding-specific chat? (A "fresh WhatsApp account that scans only the wedding chat" was floated in Round 2 discussion — `[IDEA]`, not decided.)
- `[OPEN-0/OPEN-1]` See interface question (Telegram vs WhatsApp) above.

---

## 7. Canonical scenarios (simulation content)

### Shared context `[CONFIRMED]`
Couple Meera & Rohan (Bengaluru); destination wedding, Jaipur, 14 Dec 2026. Tarang onboarded ~early Nov; couple set budgets, backup shortlist, authority at Day One. WhatsApp = approval channel.

### Scenario 1 — Décor collapse (Voice + Payments) `[CONFIRMED]`
- **Trigger: human-initiated** — 11 Dec, Rohan asks if mandap décor is on track.
- Tarang calls Suresh (Gnani) → silence → retry w/ backoff → reaches assistant → Suresh hospitalised, can't deliver.
- Does not wake couple. Goes to Day-One backup shortlist → calls Petal Inn → sends plan/specs → quote **₹40,000**.
- ₹40,000 > per-transaction cap → **escalates on amount (Rule A)** → WhatsApp to couple → yes.
- Petal Inn flags **₹3,000** delivery surcharge → Tarang negotiates to **₹2,500** → within authority → pays via Pine Labs, **no second escalation.**
- Closes with WhatsApp summary.

### Scenario 2 — Vendor's courier falls through (Voice + Logistics + Payments) `[CONFIRMED, with conflict]`
- **Trigger: agent-initiated** — 12 Dec 11:40 AM, routine Monitor check-in.
- Couple ordered 200 return-gift hampers from Anand Gifts (`[ASSUMPTION]` a local **Jaipur** shop — Claude's choice; Bengaluru-origin shipping was offered as an alternative and is unanswered, see [OPEN-7]). Shop had committed to courier them itself by 12 Dec — not Tarang-tracked.
- Tarang follows up (Gnani) → shopkeeper: regular courier unavailable, nothing shipped.
- Resolve (in authority): tells shop to keep hampers ready; places Delhivery pickup shop→venue.
- Delhivery: same-day priority pickup for **₹1,200**.
- `[CONFLICT]` Latest edit: ₹1,200 is **within the ad-hoc courier budget → Tarang pays autonomously**, no escalation. (Bullet still mislabeled "Escalate — on category"; this is a leftover and should be corrected.)
- Pays ₹1,200 via Pine Labs, confirms pickup.
- Verify: tracks shipment; closes only once delivered at venue.
- Closes with WhatsApp summary.

---

## 8. Micro-interaction inventory (from scenarios)

| Interaction | Where it appears | Status |
|---|---|---|
| Proactive status question answered | S1 (Rohan asks) | `[CONFIRMED]` |
| Outbound vendor call | S1, S2 (Gnani) | `[CONFIRMED]` |
| No-answer → retry with backoff | S1 | `[CONFIRMED]` |
| Reaching an alternate contact (assistant) | S1 | `[CONFIRMED]` |
| Fallback to Day-One backup vendor | S1 | `[CONFIRMED]` |
| Sending plan/specs to a new vendor | S1 | `[CONFIRMED]` |
| Quote capture | S1 | `[CONFIRMED]` |
| Escalation (amount) → WhatsApp yes/no | S1 | `[CONFIRMED]` |
| Negotiation (₹3,000 → ₹2,500) | S1 | `[CONFIRMED]` |
| Autonomous payment within authority | S1, S2 | `[CONFIRMED]` |
| Routine Monitor check-in | S2 | `[CONFIRMED]` |
| Direct logistics booking (pickup) | S2 | `[CONFIRMED]` |
| Shipment tracking | S2 | `[CONFIRMED]` |
| Verify-before-close (release only on delivered) | S2 | `[CONFIRMED]` |
| Closure summary message | S1, S2 | `[CONFIRMED]` |
| Discretion (withhold Suresh's medical detail) | Nuance turn | `[IDEA]` |
| "Must inform" FYI vs "must ask" (style change flag) | Nuance turn | `[IDEA]` |
| On-screen rule-check log lines | Nuance turn | `[IDEA]` (offered, unanswered) |
| Urgency near-misfire → correctly not acting | Nuance turn | `[IDEA]` |
| Reconciliation close w/ running totals | Nuance turn | `[IDEA]` |
| Multilingual Hindi-English vendor reply | Nuance turn | `[IDEA]` |

---

## 9. Trigger & proactive-behavior map

> This is the heart of "not a reactive chatbot." Each open commitment must own a next action / expected event / scheduled observation / approval wait / verified closure.

**Temporal / scheduled triggers**
- `[CONFIRMED-in-scenario]` Pre-agreed vendor check-in (Suresh had a scheduled check-in).
- `[CONFIRMED-in-scenario]` Routine Monitor follow-up at a set time (Anand Gifts, 12 Dec 11:40).
- `[ASSUMPTION]` Countdown triggers as the date nears (T-3, T-2 days heighten monitoring).
- `[CONFIRMED-in-design]` Event-Day (State 9) = elevated real-time mode.

**Missing-event / watchdog triggers**
- `[CONFIRMED-in-scenario]` Expected check-in missed → silence watchdog fires (Suresh went silent).
- `[Must-Build]` Response/silence watchdog on calls → retry with backoff, capped (Schedule Next Call).

**Approval / payment / logistics watchdogs**
- `[OPEN-4]` **Approval-wait watchdog:** after an escalation, what happens if the couple doesn't reply? No timeout, reminder cadence, or fallback is defined.
- `[Must-Build / OPEN]` Payment watchdog: on Submit Payout failure (bank rejects) — recovery path undesigned.
- `[CONFIRMED-in-design]` Logistics watchdog: track until delivered; release payment only on delivered (Release on Delivery, Must-Build).
- `[OPEN]` Shipment-stall path (Track Shipment failure) — undesigned.

**Risk triggers**
- `[Must-Build]` Urgency detection on live calls.
- `[Must-Build]` Category-ceiling breach detection.

**Cron / heartbeat / dynamic jobs**
- `[ASSUMPTION]` A continuous monitoring loop watches all active threads; each open commitment schedules its own next-observation time (dynamic jobs). Not architected yet.

**Retry / backoff**
- `[CONFIRMED-in-scenario]` Call retry with backoff, finite cap ("never redial indefinitely").
- `[OPEN]` Exact retry count, backoff interval, and stop-condition values (illustrative "Retry 1/3, next in 20 min" was an `[IDEA]`, not set).

---

## 10. Unresolved workflows (the 7-question treatment)

For each: **accountable outcome / info needed / start event / autonomous decisions / needs approval / tools / verify / re-observe.** All currently `[OPEN]`.

**W1 — Approval never comes.** Couple doesn't answer an escalation before a hard deadline.
- Accountable for: getting a decision in time OR failing safe. Start: escalation sent, no reply within X. Re-observe: reminder cadence? Autonomous fallback if T-minus critical? Undesigned.

**W2 — Payment rejected.** Pine Labs payout fails (bank rejection).
- Retry? Alternate method? Escalate to couple? Undesigned.

**W3 — Shipment stalls in transit.** Delhivery status not progressing.
- When does Tarang act, re-observe, or escalate? Does it hold vs chase the carrier? Undesigned.

**W4 — Vendor unreachable past retry cap.** All backoff attempts exhausted.
- Move to next backup automatically? Escalate? Undesigned.

**W5 — Conflicting information.** Vendor claims done; tracking/verification disagrees.
- Which source wins? Does Tarang re-verify, hold payment, or flag? Undesigned.

**W6 — Agent restart / state recovery.** After a crash or downtime, how does Tarang re-hydrate its open commitments and resume watchdogs? Undesigned.

**W7 — Day-one knowledge bootstrap.** Precisely who supplies guest list, budget, vendors, hierarchy, and how it's ingested/verified. Undesigned (see [OPEN-3]).

---

## 11. Round 3 deliverables (from the brief) — status

- `[OPEN]` Working agent (AI model + system prompt, makes own decisions). Model unchosen; system prompt unwritten.
- `[OPEN]` Screen recording ≤5 min showing every input, connector call+response, message.
- `[OPEN]` System prompt + model name shared.
- `[PARTIAL]` Part 1 Q1 (100-word story) — drafted for both scenarios. `[OPEN]` whether the recording shows one scenario or both. See [OPEN-5].
- `[OPEN]` Part 1 Q2 (decision log), Q3 (day-one knowledge), Q4 (endpoints + ≤3 imagined capabilities), Q5 (mockups), Q6 (rail scores /10).
- `[OPEN]` Part 2 Q1–Q6 (where it lives, who builds it, who pays, first 1,000 users, landing page, what kills it). Only "who builds it = WedMeGood" `[CONFIRMED from Round 2]`.

---

## 12. Confirmed / Assumption / Idea / Rejected / Open — consolidated register

### (a) Confirmed decisions
- Agent name **Tarang**; accountability; L3 autonomy; 10-stage lifecycle.
- Canonical ICP = own-wedding couple **Meera & Rohan**, Jaipur, 14 Dec 2026; couple set authority.
- Three rails: Voice/Gnani, Payments/Pine Labs, Logistics/Delhivery.
- WhatsApp primary interface; Tarang app secondary; customer assets = WhatsApp chats + planning docs + invoices.
- Day-One onboarding precedes and is excluded from the recording.
- Both canonical scenarios (S1 décor, S2 courier) as written.
- WedMeGood = company that should build it (Round 2).
- Track = Product Strategy; deadline 4 Oct.

### (b) Assumptions (NOT requirements)
- ₹5,000 per-transaction cap (specific number).
- Two-rule authority model (amount + category).
- Anand Gifts = Jaipur-local shop.
- Continuous monitoring loop / dynamic per-commitment jobs.
- Countdown-based escalation of monitoring near the date.
- "Success = all threads verified-closed with minimal interruption."

### (c) Ideas discussed, not accepted
- Discretion/withholding medical detail; must-inform-vs-must-ask FYIs; on-screen rule-check logs; urgency near-misfire beat; reconciliation running totals; multilingual texture.
- 4th rail (Blinkit quick-commerce).
- "Fresh WhatsApp number that scans only the wedding chat" ingestion idea.
- Secondary ICP (daughter running parents' wedding / "Radha").

### (d) Explicitly out of scope / set aside
- `[REJECTED/OOS]` Alternate "two vendors fail simultaneously on event day" scenario — set aside (concurrency too risky for a ≤5-min recording).
- `[REJECTED earlier in project]` Fabricated WhatsApp screenshots / invented research as evidence.
- Full product build — Round 3 is strategy + simulation, not shipping a real product (Product Strategy track).

### (e) Unanswered questions (master list)
- OPEN-0: WhatsApp vs Telegram for the simulation.
- OPEN-1: Buyer vs user (monetisation).
- OPEN-2: Exact endpoints + request/response for every rail call; primary-source verification for corroborated-only items.
- OPEN-3: Day-one ingestion mechanism.
- OPEN-4: Approval-wait timeout / reminder / fallback.
- OPEN-5: Does the recording show one scenario or both?
- OPEN-6: Resolve the S2 escalation/no-escalation conflict; is the "two escalation reasons" standout being kept?
- OPEN-7: Anand Gifts — Jaipur-local or Bengaluru-origin shipping?
- OPEN-8: Which AI model (Claude/Gemini) runs the agent?
- OPEN-9: Retry count / backoff interval / stop-condition values.
- W1–W7 (Section 10) failure/recovery workflows.

---

*End of v0.1. This file is the working SSOT; it will be revised as discovery answers land, and re-issued as the final consolidated context file at the end of the process.*
