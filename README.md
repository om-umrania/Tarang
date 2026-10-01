# Tarang Python prototype

The Python agent is implemented with Telegram, OpenRouter, persistent jobs, scoped approvals and an authenticated operator workspace. Start with [Runtime setup](docs/RUNTIME.md) and [rail integration status](docs/RAILS.md). Hosted verification is recorded in [Handoff](docs/HANDOFF.md).

# Tarang

The wedding companion that keeps following through.

**Current stage: persona and Python architecture iteration.** Both recovery
journeys have review designs. Telegram and Python are confirmed for the working
prototype; Render or Vercel will host the agent, with provider selection still open.

- [Persona v0.1](docs/PERSONA.md) · [Prompt](prompts/tarang-persona.md) · [Evaluation cases](docs/PERSONA_EVALS.md)
- [Phase 2: Python foundation and hosting](docs/PHASE_2.md)

- [Open the interactive experience review](docs/index.html)
- [Read the complete journey design](docs/EXPERIENCE_DESIGN.md)
- [Confirmed decisions and open choices](docs/DECISIONS.md)
- [Proposed automation architecture](docs/ARCHITECTURE.md)
- [Plan](PLANS.md) · [Handoff](docs/HANDOFF.md)

The review contains illustrative conversations, selectable journey steps, and
failure branches. It does not connect to Telegram, run an AI agent, call vendors,
make payments, or create shipments. Original briefs and planning material are
preserved in `resources/`.

## Preview

Open `docs/index.html` in a browser, or run:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Then visit `http://127.0.0.1:8765/index.html`.

## Validate

```bash
./scripts/check.sh
```

This checks the review artifacts, not the future automation. No application
dependencies, model credentials, or partner accounts are needed for the review.
