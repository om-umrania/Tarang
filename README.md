# Tarang

The wedding companion that keeps following through.

**Current stage: experience design.** Both recovery journeys are being designed
before agent implementation. Telegram is confirmed for the working prototype.

- [Open the interactive experience review](docs/experience-review.html)
- [Read the complete journey design](docs/EXPERIENCE_DESIGN.md)
- [Confirmed decisions and open choices](docs/DECISIONS.md)
- [Proposed automation architecture](docs/ARCHITECTURE.md)
- [Plan](PLANS.md) · [Handoff](docs/HANDOFF.md)

The review contains illustrative conversations, selectable journey steps, and
failure branches. It does not connect to Telegram, run an AI agent, call vendors,
make payments, or create shipments. Original briefs and planning material are
preserved in `resources/`.

## Preview

Open `docs/experience-review.html` in a browser, or run:

```bash
python3 -m http.server 8765 --bind 127.0.0.1 --directory docs
```

Then visit `http://127.0.0.1:8765/experience-review.html`.

## Validate

```bash
./scripts/check.sh
```

This checks the review artifacts, not the future automation. No application
dependencies, model credentials, or partner accounts are needed for the review.
