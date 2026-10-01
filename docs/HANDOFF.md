# Project Handoff

## Current State

Phase 2 now has a proposed persona, full/short prompt and 15 synthetic evaluation
cases. These have not been run against a model. Python is confirmed; Render and
Vercel are hosting candidates. Render is recommended for the worker architecture,
but no provider/tier/database/model is selected and nothing is deployed.
Start with `docs/PERSONA.md` and `docs/PHASE_2.md` for this iteration.

Experience design completed on 1 October 2026 for review. Om requested both
journeys be designed before implementation, confirmed Telegram for the prototype,
and chose autonomous ₹1,200 courier recovery within an approved category budget.
The numeric spending cap remains configurable; ₹5,000 is illustrative.

## What Has Been Implemented

- Static interactive review: 7 décor moments, 7 courier moments, 3 unbudgeted
  courier moments and 4 proposed onboarding cards.
- Seven types of exception exposed where relevant: vendor silence, unanswered
  approval, decline, unknown payment, missing proof, infeasible delivery, restart.
- Written experience contract, proposed architecture, decision register and
  project harness. No agent runtime, scheduler, model or integrations exist.

## Important Files

- `docs/index.html`: standalone review, no external dependencies.
- `docs/EXPERIENCE_DESIGN.md`: full journeys, vendor scripts and failure handling.
- `docs/DECISIONS.md`: confirmed decisions versus proposals and unknowns.
- `docs/ARCHITECTURE.md`: proposed persistence, policy, operations and evidence.
- `resources/`: unchanged original briefs and historical context.

## How To Run

Open `docs/index.html` directly, or serve `docs/` on loopback with
the command in README. The review tab was left open in Codex. The preview server
was started on port 8765 for this session; restart it if that process ends.

## How To Validate

`./scripts/check.sh` passed: JavaScript syntax, duplicate HTML IDs, local links
and `git diff --check`. Browser review traversed all 21 moments and 16 exception
selections, plus approval/detail/decline/return navigation using keyboard controls.
The 390px layout initially overflowed; `min-width: 0` on grid children fixed it.
Read-only DOM checks then measured no horizontal page overflow at 390 and 1280px.

Mouse automation in the in-app browser was inconsistent around scrolling and
viewport overrides; keyboard activation reliably exercised the actual controls.
Do not call this an exhaustive cross-browser or accessibility audit. No live
agent, API, payment, scheduling or recovery behaviour has been tested.

## Known Issues

Exact rail endpoints/payloads and account access need validation. A same-day
Delhivery rescue for 200 hampers at ₹1,200 is not established. Confirm origin,
package details, payment semantics, budgets, cap, approver rule, verifier and
retry/expiry timings before affected implementation. See the decision register.

The ₹40,000 replacement approval cannot silently authorise the later ₹2,500
surcharge: that autonomous action needs its own pre-existing delegated scope.
Recovery, physical fulfilment and financial reconciliation are separate outcomes.

## Next Steps

Review the persona relationship/language and representative copy with Om, select
the model and run the evaluation cases, resolve dependent authority/hosting
choices, then implement the smallest complete Python commitment loop.
Do not implement a fixed sequence of storyboard actions as the agent.

## Notes For Future Codex Sessions

Follow the current decision register over conflicting historical context. Preserve
unverified status and source provenance. The user’s `.DS_Store` modification was
already present before this work; leave it alone. No deployment or external
messages were performed. Git history records publication of the design artifacts.
