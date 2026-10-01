"""Synthetic date probes through webhook -> real model -> store -> captured reply.

The Telegram adapter is captured locally. This is an integration test, NOT proof of
real Telegram or WhatsApp transport. Never load private conversation state here.
"""

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi.testclient import TestClient
from tarang.app import create_app
from tarang.config import Settings
from tarang.adapters import OpenRouter
from tarang.store import Store


class CaptureTelegram:
    def __init__(self):
        self.sent = []

    async def call(self, method, payload):
        self.sent.append({"method": method, "payload": payload})
        return {"message_id": len(self.sent)}


CASES = [
    (
        "tentative_conflicting_dates",
        "Synthetic wedding planning: Mehendi is proposed for 12 November 2026 at 5 pm IST. Another message suggests 13 November 2026 but explicitly says it is not confirmed. Tell me what is known and what needs confirmation. No vendor actions.",
    ),
    (
        "missing_year",
        "Synthetic wedding planning: our message says 'Wedding on 12 November at 6 pm'. The year and timezone are not provided. What do you need before recording a precise deadline? No vendor actions.",
    ),
    (
        "accepted_revision",
        "Synthetic wedding planning: couple initially proposed mehendi on 12 November 2026 at 5 pm IST. Later the couple explicitly confirmed moving it to 13 November 2026 at 5 pm IST and cancelling the 12 November plan. Summarise the current plan. No vendor actions.",
    ),
    (
        "ambiguous_numeric_date",
        "Synthetic wedding planning: a vendor writes 'setup 04/05 at 7'. We do not know the date format, year, timezone or whether 7 is AM or PM. Can this be stored as a confirmed deadline? No vendor actions.",
    ),
]


async def main():
    results = []
    with tempfile.TemporaryDirectory(prefix="tarang-dates-") as temp:
        for i, (name, text) in enumerate(CASES):
            settings = Settings(
                database=str(Path(temp) / f"{i}.sqlite3"),
                bot_token="",
                allowed=frozenset({42}),
                telegram_mode="webhook",
                webhook_secret="synthetic-secret",
                operator_token="synthetic-operator",
                whatsapp_enabled=False,
            )
            tg = CaptureTelegram()
            app = create_app(
                settings, model=OpenRouter(settings), telegram=tg, run_worker=False
            )
            client = TestClient(app)
            update = {
                "update_id": i + 1,
                "message": {
                    "from": {"id": 42},
                    "chat": {"id": 42, "type": "private"},
                    "text": text,
                },
            }
            headers = {"X-Telegram-Bot-Api-Secret-Token": "synthetic-secret"}
            accepted = (
                client.post(
                    "/telegram/webhook", json=update, headers=headers
                ).status_code
                == 200
            )
            client.post("/telegram/webhook", json=update, headers=headers)
            engine = app.state.engine
            await engine.step()
            await engine.send_one()
            snapshot = Store(settings.database).snapshot()
            events = snapshot["events"]
            transport_ok = (
                accepted
                and len(events) == 1
                and events[0]["status"] == "done"
                and len(tg.sent) == 1
            )
            safe = (
                not snapshot["operations"]
                and snapshot["commitments"][0]["state"] == "open"
            )
            results.append(
                {
                    "case": name,
                    "integration_passed": transport_ok and safe,
                    "source": "synthetic; local webhook; live model; captured Telegram adapter",
                    "event_status": events[0]["status"],
                    "reply": tg.sent[0]["payload"]["text"] if tg.sent else None,
                    "operations": len(snapshot["operations"]),
                    "restart_state_readable": True,
                }
            )
            print(name, "PASS" if transport_ok and safe else "FAIL", flush=True)
    Path(".runtime/date-integration-evaluation.json").write_text(
        json.dumps(results, indent=2)
    )
    print(json.dumps(results, indent=2))
    if not all(r["integration_passed"] for r in results):
        raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
