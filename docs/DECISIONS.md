# Decisions and unresolved choices

## Confirmed by Om in this chat · 1 October 2026

| ID | Decision | Evidence |
|---|---|---|
| D01 | Design both journeys before implementing the agent | “Design both journeys before implementing” |
| D02 | Telegram is the working prototype's couple interface | “Yes—Telegram for the working prototype (Recommended)” |
| D03 | Canonical courier recovery pays ₹1,200 automatically from an approved courier budget | “Pay automatically from an approved courier budget” |

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
| Model/runtime | No model, hosting or database selected; source recommendations are not implementation commitments |
| Recording | One versus both, valid source events and treatment of compressed scenario time remain open |

## Source precedence

Original competition brief for competition requirements → explicit current user
decisions → approved design decisions → proposals → historical context.
Preserve source files as evidence. A proposal or storyboard does not override an
explicit decision or prove an integration works.
