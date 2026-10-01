"""Synthetic live-model group review; never uses a real WhatsApp account or history."""

import asyncio
import json
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tarang.adapters import OpenRouter
from tarang.config import Settings
from tarang.group_monitor import GroupMonitor
from tarang.schema import GroupBatch
from tarang.store import Store


class RecordingModel(OpenRouter):
    last_report = None

    async def review_group(self, context):
        try:
            self.last_report = await super().review_group(context)
        except Exception as exc:
            if hasattr(exc, "errors"):
                print(json.dumps(exc.errors(include_input=False, include_url=False)))
            raise
        return self.last_report


async def main():
    with tempfile.TemporaryDirectory() as temp:
        settings = Settings(
            **({"model": sys.argv[1]} if len(sys.argv) > 1 else {}),
            database=temp + "/test.sqlite3",
            group_enabled=True,
            group_id="synthetic@g.us",
            group_bridge_token="synthetic",
        )
        model = RecordingModel(settings)
        monitor = GroupMonitor(Store(settings.database), settings, model)
        texts = [
            "Our wedding ceremony is confirmed for 12 November 2027 at 6 pm IST.",
            "Mandap setup will be complete at 7 pm IST on 12 November 2027.",
        ]
        monitor.ingest(
            GroupBatch.model_validate(
                {
                    "group_id": settings.group_id,
                    "connected": True,
                    "messages": [
                        {
                            "external_id": str(i),
                            "source_id": str(i),
                            "sender": "synthetic-source-" + str(i),
                            "text": text,
                            "kind": "text",
                            "sent_at": time.time(),
                        }
                        for i, text in enumerate(texts)
                    ],
                }
            )
        )
        await monitor.step()
        status = monitor.status()
        review = (
            json.loads(status["latest_review"]["result"])
            if status["latest_review"]
            else None
        )
        passed = bool(
            review
            and review["wedding_date_status"] == "source_confirmed"
            and any(c["kind"] == "schedule" for c in review["conflicts"])
        )
        receipt = {
            "source": "synthetic only; no WhatsApp transport",
            "passed": passed,
            "review": review,
            "raw_synthetic_report": (
                model.last_report.model_dump() if model.last_report else None
            ),
            "error": status["state"].get("error"),
        }
        Path(
            ".runtime/hourly-group-evaluation-"
            + settings.model.replace("/", "_").replace(":", "_")
            + ".json"
        ).write_text(json.dumps(receipt, indent=2))
        print(json.dumps(receipt))
        if not passed:
            raise SystemExit(1)


if __name__ == "__main__":
    asyncio.run(main())
