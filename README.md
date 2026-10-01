# Tarang

An AI wedding coordinator with a Python runtime, Telegram interface and persistent follow-through.

**Working prototype:** [Telegram bot](https://t.me/tarang_wedding_bot) · [Operator workspace](https://tarang-prototype.onrender.com). The bot is restricted to configured private-chat users; the workspace requires an operator token.

- [Run and configure](docs/RUNTIME.md)
- [Current deployment and validation](docs/HANDOFF.md)
- [Rail integrations and gaps](docs/RAILS.md)
- [Persona](docs/PERSONA.md) · [Runtime prompt](prompts/runtime.md)
- [Journey design](docs/EXPERIENCE_DESIGN.md) · [Interactive storyboard](docs/index.html)
- [Decisions](docs/DECISIONS.md) · [Architecture](docs/ARCHITECTURE.md)

Telegram and OpenRouter are connected. Partner payment, booking and shipment requests remain operator-assisted and explicitly labelled. Gnani STT has a documented adapter awaiting its key/audio test. No real vendor payouts or bookings are executed by this prototype.

## Run

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements-dev.txt
.venv/bin/python -m tarang.setup
.venv/bin/python -m uvicorn tarang.app:app --host 127.0.0.1 --port 8766 --workers 1
```

Do not run local polling while the hosted Telegram webhook is active. See the runtime guide for configuration. Secrets belong in ignored `.env` or Render secret storage.

## Validate

```bash
.venv/bin/python -m pytest -q
PATH="$PWD/.venv/bin:$PATH" ./scripts/check.sh
```

Tests use fake model/transport adapters for policy and persistence. `scripts/evaluate_model.py` separately calls the configured model with labelled synthetic probes. Neither proves real payment or delivery execution.

Free Render compute can sleep, delaying scheduled checks. PostgreSQL preserves state; the free database expires 31 October 2026. This is a demonstration environment, not an always-on production coordinator.

The original static storyboard remains available with `python3 -m http.server 8765 --bind 127.0.0.1 --directory docs`. Source materials under `resources/` are preserved.
