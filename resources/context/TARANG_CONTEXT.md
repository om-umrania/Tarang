# Tarang — Context File (DRAFT v0)

> Status: **draft, pre-discovery**. Built only from this conversation (one scenario + one Q&A set).
> Nothing below is a requirement unless it sits in §1 Confirmed.
> Last updated: 2026-09-30

---

## 0. Source inventory

| # | Source | What it contains |
|---|---|---|
| S1 | User paste: "Scenario 1 — Décor collapse (Voice + Payments)" | Trigger, flow, ₹5,000 limit, Rule A, Petal Inn, Pine Labs payment, WhatsApp summary, 100-word story |
| S2 | User paste: "Part 1: Your agent" questions | Deliverable format: story, decision log, day-one knowledge, endpoints for Pine Labs / Delhivery / Gnani, ≤3 imagined capabilities, mockups, rail scores |
| S3 | Claude's answer + Claude Doc "Tarang — Scenario 1: Décor Collapse" | Mostly **Claude-invented** detail (rules R1–R8, timings, names). Treat as proposals, not decisions. |
| S4 | User paste: discovery brief (this file's mandate) | Mentions **Telegram interaction model** and **WhatsApp/data-ingestion** — neither is described anywhere else yet |

**Not yet seen:** any other scenarios, a product brief, a system prompt, Telegram/WhatsApp design notes, attached files.

---

## 1. Confirmed (stated by the user in S1/S2)

- **C1** Tarang is a proactive wedding-operations agent.
- **C2** Example couple: Meera & Rohan. Wedding 14 Dec 2026. Jaipur (from the 100-word story).
- **C3** Rails in the exercise: **Pine Labs** (payments), **Delhivery** (logistics), **Gnani** (voice).
- **C4** Triggers can be **human-initiated** (Scenario 1 is labelled "Trigger type: human-initiated"). This implies other trigger types exist.
- **C5** Tarang has a **₹5,000 per-transaction autonomous limit**.
- **C6** **Rule A:** amount above the limit → escalate to the couple.
- **C7** After a category spend is approved, a follow-on charge **within ₹5,000 and inside the approved category** is paid without a second escalation.
- **C8** A **Day-One backup shortlist** exists, produced at a **"Map" stage**.
- **C9** Tarang retries unanswered vendor calls **with backoff**, then tries an alternate contact.
- **C10** Tarang handles real problems without "waking the couple" until a decision needs them; it brings a solution, not a problem.
- **C11** Tarang **negotiates** add-on fees (₹3,000 → ₹2,500).
- **C12** Closure = short summary to the couple: **problem, fix, spend, done**. S1 says this goes over **WhatsApp**.
- **C13** "Real problem, not a checklist beat" implies Tarang also runs **checklist beats** (routine scheduled checks).

## 2. Assumptions (unconfirmed — do not build on these without sign-off)

| ID | Assumption | Origin | Risk if wrong |
|---|---|---|---|
| A1 | The couple talks to Tarang on WhatsApp | S1 closing line + Claude's mockups | **High.** S4 says "Telegram interaction model" — the couple channel may be Telegram, with WhatsApp only for ingestion or vendors |
| A2 | Vendors are contacted via WhatsApp Business API + Gnani voice | Claude | Medium |
| A3 | Rules R1–R8 (freshness, contact ladder 3× at 0/+2/+5 min, severity, solutions-first 60 min, backup rank order, negotiation once, summary ≤5 lines, balance check) | Claude | Medium — these are plausible but invented |
| A4 | Either partner approves ≤₹50,000; both above | Claude | High (authority) |
| A5 | Vendor calling hours 08:00–21:00 | Claude | Low |
| A6 | Pine Labs Payouts (IMPS to bank account) is the payment path; couple pre-funds a Pine Labs funding account | Claude | **High.** Could instead be payment links, UPI collect, or cards |
| A7 | Payee bank details verified at Map stage | Claude | High (fraud) |
| A8 | Two separate payouts (approved + autonomous) for audit clarity | Claude | Low |
| A9 | Names/details: Kavita, Rang Décor, Gulmohar Events, specs, timestamps, pay-on-delivery for Suresh | Claude | Low (illustrative) |
| A10 | Onboarding happens in a chat; Hinglish language preference | Claude | Medium |

## 3. Ideas discussed, not accepted

- **I1** Gnani `call_sequences` endpoint (contact ladder + structured extraction + webhook) — imagined.
- **I2** Pine Labs `spend-policies` (rail-enforced limits) — imagined.
- **I3** Pine Labs `payees/verify` (KYC'd merchant match) — imagined.
- **I4** A "commitment ledger" where every open item has a next action / expected event / observation time — proposed in this draft (§7), not agreed.

## 4. Out of scope / rejected

- Nothing explicitly rejected yet.
- Scenario 1 alone does not use Delhivery (Claude's reading; not a product decision).

## 5. Integration capability status

| Integration | Verified against public docs | Proposed use | Needs verification |
|---|---|---|---|
| Gnani Inya | `POST /platform/v1/agents/{botId}/trigger_call`; `POST /platform/v1/conversations/logs`; `GET /v1/conversations/{id}/stats` | Vendor calls, outcome detection | Production (non-whitelisted) outbound; webhooks for call completion; passing per-call context; inbound calls; Hindi/Hinglish |
| Pine Labs | `POST /api/auth/v1/token`; `POST /payouts/v3/payments/banks`; `GET /payouts/v3/payments`; `GET /payouts/v3/payments/funding-account`; scheduled payout update/cancel | Vendor payouts | Amount units (paise?); payout webhooks; UPI payouts; account-holder verification; refunds/recovery |
| Delhivery | Not checked | Unknown — no logistics flow defined yet | Everything |
| Telegram | Not checked | Unknown — named in S4 only | Bot API: inline-button approvals, groups, webhooks |
| WhatsApp | Not checked | Unknown — "data ingestion" in S4 | Business Cloud API vs. chat export vs. other; consent; group access (the Cloud API cannot read personal groups) |
| Scheduler / cron | — | Not designed | — |

## 6. Trigger taxonomy (skeleton; only T-H1 is confirmed)

| Type | Example | Status |
|---|---|---|
| Human-initiated | Rohan asks "is décor on track?" | **Confirmed (S1)** |
| Temporal / checklist beat | T-3 days: confirm every vendor | Implied by C13; not specified |
| Expected-event | Vendor sends confirmation / invoice by date X | Not specified |
| Missing-event / silence watchdog | Vendor unreachable; couple hasn't approved | Partly (C9 retries); no timeouts defined |
| Approval watchdog | Rule A escalation unanswered | Not specified |
| Payment watchdog | Payout not SUCCESS by T+N | Not specified |
| Logistics watchdog | Delhivery shipment stuck | Not specified |
| Risk trigger | Weather, venue change, vendor bad news in chat | Not specified |
| Heartbeat / restart recovery | Re-read open commitments after downtime | Not specified |

## 7. Proposed operating principle (NOT agreed — I4)

Every open commitment carries: `outcome`, `owner`, `state`, `next_action`, `expected_event` (+ deadline), `observe_at`, `approval_pending?`, `escalation_path`, and `closure_evidence`. The scheduler wakes Tarang at `min(observe_at)`. Nothing closes without evidence.

## 8. Open questions register

Tracked in discovery; see the Q&A log (to be appended).

## 9. Q&A log

_(empty — discovery not started)_
