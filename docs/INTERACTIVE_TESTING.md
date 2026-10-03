# Interactive Telegram persona rehearsal

3 October 2026. Questions → suggestions/free text → plan review → simulated contact
check → feedback. This is an isolated fictional prototype, not real vendor execution.

## Try it

Open [Tarang](https://t.me/tarang_wedding_bot?start=demo), send `/start demo`, and
choose **Start a conversation**. The welcome explains model processing before that
choice. Choose suggested answers or type fictional details. Multiple details in
one message skip already-answered questions. Correct a detail at any time by typing
what changed. Review the plan, choose **Rehearse the contact check**, then give
feedback about alternatives or preserving the original requirements. Pause/resume
buttons affect this rehearsal only. `/reset` starts again; `/delete` clears stored
demo data. For an allowlisted operator, `/live` returns to the wedding workspace.

The intake captures problem, deadline, contact, decision maker, on-site verifier,
constraints and priority separately. Missing details may be explicitly undecided;
a demo plan containing unknowns is not ready for real execution. Suggestions are
private selection buttons, not a group poll. Selection never grants real authority.
Only free-text turns need OpenRouter; guided choices keep working during provider
failure or after the daily AI limit. Existing free-host wake delays still apply.

## Implementation and persistence

`tarang/intake.py` supplies the questions, contextual contact suggestions, plan and
labelled simulated feedback steps. `prompts/intake.md` supplies structured extraction
and brief acknowledgement for free text. The model has no execution tools. The
next question comes from missing fields; known answers are not asked again.

One additive `demo_intakes` table stores JSON facts, phase and a revision token per
visitor. It is cleared on scenario changes, reset, deletion and existing retention
cleanup. No operational tables are changed by intake. All choice callbacks are
bound to the current visitor's revision, invalidated on new free text and rejected
when stale or another answer is processing. Reset/deletion during a model call
suppresses late results. The model can still misinterpret free text; the review
summary and correction path are required before rehearsing the next step.

## Acceptance sequence

1. Greeting and choice: confirm welcome, question and readable buttons in Telegram.
2. Choose décor delay; verify the next question asks about deadline.
3. Type fictional deadline, contact, approver, verifier, constraints and priority in
   one message. Verify those facts appear accurately in the plan without repeated questions.
4. Correct deadline; verify other details survive and the updated plan asks for review.
5. Rehearse the contact check; verify its response is explicitly simulated.
6. Explore alternatives; verify feedback is reflected, with no claimed real action.
7. Pause/resume, try an older choice, and switch scenarios. Check privacy/isolation.
8. Test model unavailability locally; suggestions remain usable and facts survive.

## Validation evidence

Run `PATH="$PWD/.venv/bin:$PATH" ./scripts/check.sh` for static checks and runtime
tests. The intake tests cover the full selection journey, multi-field free text,
corrections/restart, stale/cross-user/duplicate choices, pending input, provider
failure, crash recovery, reset/deletion races, retention and signed webhook-to-
message transport with a captured Telegram adapter. These are contract tests.

Run `.venv/bin/python scripts/evaluate_intake.py` for live-model synthetic multi-turn
checks in an isolated database. Receipt: `.runtime/intake-evaluation.json` (ignored).
Review wording separately from extraction/zero-operation checks. Neither synthetic
webhooks nor captured sends establish an actual Telegram-client round trip.

Deployment and client evidence is recorded below. The full
persona rubric in PERSONA_EVALS.md remains a separate, broader evaluation.

### Local and model verification — 3 October 2026

57 runtime tests passed, including ten new intake tests; static link/JavaScript and
whitespace checks passed. Three live synthetic model turns passed extraction,
correction and zero-real-record checks. Semantic review exposed user-chasing wording
in the first run; the updated prompt's repeat probe proposed agent coordination
conditionally instead. The model still repeats some supplied details in its
acknowledgement, so brevity remains a persona improvement rather than a proven property.

### PostgreSQL transport fix and keyboard access

The first real-client `/start demo` test exposed a PostgreSQL-only webhook failure:
literal `%` in demo cleanup `LIKE` queries was parsed as a psycopg parameter. The
adapter now escapes literal percent signs before converting placeholders. SQLite
checks alone had missed this failure. The public-demo and intake fixtures support
`TARANG_TEST_POSTGRES` for parity runs, with a fresh disposable schema per test.
Use only a dedicated test database: the fixture creates and drops its test schemas.

The conversation also supports `/talk` after the welcome, and `/choose N` for the
numbered suggestions shown in each message. This uses the same choice validation
as button taps and makes the flow usable with keyboard-only clients. Free-text
answers and corrections remain available. `/talk` on first contact shows the
privacy welcome before any model use.

The corrected flow passed 58 SQLite runtime tests and all 23 public-demo/intake
checks against an isolated local PostgreSQL server. The disposable server was
stopped after the run. Oversized numeric selections are rejected before integer
conversion; the keyboard-selection regression passes.

### Actual Telegram client rehearsal — 3 October 2026

The repaired welcome, `/talk` question and suggested buttons were visible in the
Mac Telegram client. Real button callbacks advanced décor delay, deadline,
contact, decision maker and verifier. The operator then continued with keyboard
input and `/choose N`, because the pointer automation could not tap native buttons.

A fictional typed answer set the deadline to 12 November 2026 at 4 pm IST,
preserved the ivory/peach design and existing budget, and prioritised the deadline.
Tarang skipped the answered priority question and displayed the full plan. A typed
correction changed only the deadline to 3 pm IST; contact, decision maker, verifier,
constraints and priority remained intact in the visible updated plan.

Keyboard selections then displayed the explicitly simulated contact response,
recorded **Explore alternatives**, identified the next contact response and on-site
verification, and passed pause/resume while preserving feedback. All these replies
were visible in the real client by 11:53 IST. An incidental voice note received the
unsupported-input response; voice processing is not implemented.

The final runtime commit is `6714a273d8e987b14d26e655de7f1998806a17b2`.
Render deployment `dep-db09qme0tbcc73etu2gg` became live at
06:15:43 UTC. The hosted health and fixed-fictional intake diagnostic passed;
unauthenticated diagnostic access returned 401. Final Telegram webhook backlog
was zero and the rehearsal outbox replies were `sent`. Telegram retains the earlier
500 error timestamp as historical metadata; successful subsequent client turns
and the cleared backlog establish recovery.

Private ignored receipts: `.runtime/interactive-deployment-verification.json`,
`.runtime/telegram-intake-rehearsal.json`, `.runtime/intake-evaluation.json`.
This verifies one actual client journey plus automated edge-case contracts. The
15-case voice rubric and real vendor integrations remain unverified. Calls,
bookings, payments and physical completion are simulated or unavailable.
