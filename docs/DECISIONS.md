# Decisions and unresolved choices

## Confirmed by Om in this chat · 1 October 2026

| ID | Decision | Evidence |
|---|---|---|
| D01 | Design both journeys before implementing the agent | “Design both journeys before implementing” |
| D02 | Telegram is the working prototype's couple interface | “Yes—Telegram for the working prototype (Recommended)” |
| D03 | Canonical courier recovery pays ₹1,200 automatically from an approved courier budget | “Pay automatically from an approved courier budget” |
| D04 | Python is the base language for the agent architecture | “The base architecture would be based on Python” |
| D05 | Develop Tarang's persona in the next iteration; target a hosted agent on Render or Vercel | “make the persona of the tarang” and “using Render or Vercel to deploy it” |

The product's submitted WhatsApp concept remains historical context; D02 settles
the prototype interface without claiming the production channel has changed.
D03 supersedes the unbudgeted canonical courier sequence in the old build context.

## Interpretation for review

When asked whether to confirm a ₹5,000 cap, Om replied: “Great let's work on
keeping both for different scenario?” The review interprets this as showing both
approval-led and autonomous behaviour in different scenarios: décor seeks a
₹40,000 booking approval, courier operates autonomously. An unbudgeted courier
exception is also retained. This interpretation was stated in the chat; it is
not explicit ratification of a numerical cap or every proposed policy.

The walkthrough uses ₹5,000 as an **illustrative configurable cap**, inherited
from source scenarios. Do not hard-code it as a universal or confirmed limit.

## Proposed design choices, not yet ratified

| ID | Proposal | Why it helps |
|---|---|---|
| P01 | Onboard through four review cards before monitoring starts | Establish outcome, evidence and authority without a long form |
| P02 | Exact-action approval with version, expiry, identity and one-time consumption | Prevent vague assent or stale buttons from authorising spend |
| P03 | Separate recovery resolution, physical fulfilment and financial reconciliation | A replacement booking must not falsely close mandap setup |
| P04 | Verify hamper quantity and condition with a designated venue recipient | A carrier scan alone does not verify 200 usable hampers |
| P05 | Show concise updates on material changes; keep retries in an inspectable log | Reduce interruption while preserving visibility |
| P06 | One core event loop for both journeys; persistent next observations | Prevent fixed demo scripts and forgotten follow-ups |
| P07 | Configure surcharge delegation separately from the ₹40,000 booking approval | Demonstrate bounded autonomy without silently expanding authority |
| P08 | Record one complete journey; keep the other as a rehearsal | Meet five-minute evidence constraint; final selection remains open |

## Unresolved before dependent implementation

| Choice | Current status / consequence |
|---|---|
| Numeric autonomous cap | ₹5,000 illustrative; actual value configurable and unconfirmed |
| Category totals and remaining room | Courier category approved in principle; budgets, reservations and ancillary décor scope need values |
| Approver identity/rule | Meera/Rohan roles known; either-versus-both, verified Telegram IDs and revocation not specified |
| Telegram topology | Group versus private conversations and setup invite mechanism undecided |
| Vendor contact ladder | Contacts, permission, calling hours, retry cap/backoff and backup ranking need confirmation |
| Approval silence | Reminder interval, cap, expiry basis and permitted fallback approver unset |
| Logistics feasibility | Shop origin, addresses, package shape, deadline/SLA and ₹1,200 service support unverified |
| Payment semantics | Exact product, payee, funding, order of operations, ₹40,000 obligations and rail payloads unverified |
| Outcome evidence | Named venue verifier, acceptable décor proof and hamper receipt contract proposed, not confirmed |
| Runtime/hosting | Python confirmed. Render or Vercel are candidates; provider, service tier, database and model unselected. See [Phase 2](PHASE_2.md) |
| Persona | [v0.1](PERSONA.md) proposes a warm coordinator and adaptive language; relationship, default language and voice remain for review |
| Recording | One versus both, valid source events and treatment of compressed scenario time remain open |

## Source precedence

Original competition brief for competition requirements → explicit current user
decisions → approved design decisions → proposals → historical context.
Preserve source files as evidence. A proposal or storyboard does not override an
explicit decision or prove an integration works.

## Implementation decisions · 1 October 2026

- Om requested the end-to-end Python prototype and provided the Telegram bot.
- Om chose OpenRouter for model access; model selection delegated. Gemini 3.8
  Flash is the initial candidate, configurable through MODEL, with live smoke evidence.
- Use existing/free resources first. Render free web + free PostgreSQL selected;
  sleeping compute means deferred due checks, and the DB expires 31 October.
- New PDFs under resources/mails were read; Round 2 source constraints reconciled
  with the later Round 3 simulation. See [RAILS.md](RAILS.md).

- Gemini Flash worked initially but the hosted model path later returned HTTP 402.
  With model selection delegated and no answer to the optional model-route question
  after several minutes, selected a tested free OpenRouter Nemotron candidate as
  temporary default. Gemini remains configurable; this is not a claim of equivalent
  quality or a completed model benchmark.

### 1 October 2026 — WhatsApp request

Om requested a live agent listening for conflicts in WhatsApp conversations. Implemented
receive-only direct-message webhook and scoped conflict-review foundation, disabled
pending source choice and configuration. Whether the intended source is direct messages,
an existing group or forwarded conversations remains open. No personal archive access,
participant posting, automatic conflict resolution or added spending authority inferred.

### Hourly backend monitoring clarification

Om explicitly requires backend automation for the existing wedding group, approximately
hourly, rather than manual Codex checks or exports. Om selected a dedicated WhatsApp
account. Implemented isolated linked-device bridge and hourly Python review job;
pairing, target group ID and always-on hosting remain required for live operation.
Do not call the previous direct-message Cloud API adapter an existing-group connector.

### 2 October 2026 — controlled calling rehearsal

Om authorised a rehearsal call to himself using the number supplied privately in
chat. He chose: negotiate the illustrative décor surcharge from ₹2,500 toward
₹1,500, with ₹2,500 as the negotiation ceiling, preserving the agreed scope and
4 pm readiness deadline; ask Om before agreeing. This does not delegate booking,
payment, or acceptance authority, even below the ceiling. Do not contact the real
venue or Aditya for this rehearsal. Do not put the phone number in tracked files.

Om reports having outbound calling access and will provide its API documentation.
Provider authentication, dialling, callback verification and call-result contracts
remain unverified. The existing Gnani STT adapter cannot place calls.
See [calling rehearsal](CALLING_REHEARSAL.md) for the acceptance sequence.

### 2 October 2026 — public sharing

Om chose “Private demo for each person” for visitors following the Telegram link.
Public visitors get isolated fictional scenarios and demo conversations, not access
to the wedding workspace. Live actions remain unavailable in demo mode. Existing
private-workspace authority is unchanged. See [public demo](PUBLIC_DEMO.md).
