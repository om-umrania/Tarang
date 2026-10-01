# Tarang project instructions

## Purpose and current scope

Tarang is a wedding operations agent for The Ken Round 3 simulation. On
1 October 2026 Om chose **design both journeys before implementing**, and
confirmed **Telegram for the working prototype**. This repo currently contains
source material, a proposed experience design, and a static review walkthrough.
The walkthrough is not an agent, a Telegram connection, or execution evidence.

Phase 3 implementation is now explicitly authorised. Python/FastAPI, OpenRouter
Gemini Flash, Telegram and free Render/PostgreSQL are the current prototype stack.
Read docs/RUNTIME.md and docs/RAILS.md for actual integration boundaries. Read
`docs/PERSONA.md`, `prompts/tarang-persona.md`, `docs/PERSONA_EVALS.md` and
`docs/PHASE_2.md` when continuing this phase. Persona proposals are not confirmed
voice preferences; authored evaluation cases are not executed model tests.

## Read first

1. `docs/DECISIONS.md`: explicit user decisions and unresolved choices.
2. `docs/EXPERIENCE_DESIGN.md`: proposed journeys, copy, failure paths, acceptance criteria.
3. `docs/ARCHITECTURE.md` and `PLANS.md`: proposed implementation boundaries.
4. `resources/`: original competition materials and historical context.

The original Round 3 brief controls competition requirements. New explicit user
decisions supersede older context. The three historical context files conflict;
do not silently promote their assumptions into accepted requirements.

## Rules

- Implementation and prototype deployment are now requested; preserve source provenance.
- Preserve original source materials. Record decisions separately.
- No invented endpoints, API results, delivery guarantees, payment receipts,
  customer research, or completion evidence.
- Mark walkthrough dialogue and events as illustrative.
- LLM proposes actions; deterministic code must enforce authority and closure.
- Every unresolved commitment must have an owner and next observation.
- A booking, payment submission, or carrier status alone may not prove the target outcome.
- Prototype bot messages are authorised. Real vendor calls, payments and bookings
  still require configured access and exact authority; no live financial adapters exist.
- Never expose credentials or commit `.env` files.
- Keep the static review dependency-free and usable without network access.

## Review and validation

Open `docs/index.html` locally, or serve `docs/` on loopback:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs
./scripts/check.sh
```

Check links, JavaScript syntax, journey navigation, branches, keyboard access,
and a narrow viewport. Report static checks separately from agent/integration
tests; run `python3 -m pytest -q` for the implemented runtime. Preserve unrelated user changes.
