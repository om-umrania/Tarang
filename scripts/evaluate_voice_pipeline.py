"""Synthetic voice -> STT -> review -> live model -> TTS, isolated DB.

Telegram input and delivery are captured; this does not verify an actual client.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tarang.adapters import OpenRouter
from tarang.config import Settings
from tarang.intake import Intake
from tarang.public_demo import PublicDemo
from tarang.store import Store
from tarang.voice import Speech, VoiceDemo


class CapturedTelegram:
    def __init__(self, audio):
        self.input, self.text, self.voice = audio, [], []

    async def download_voice(self, file_id, limit):
        assert len(self.input) <= limit
        return self.input

    async def call(self, method, payload):
        assert method == "sendMessage"
        self.text.append(payload["text"])

    async def send_voice(self, chat, audio):
        assert audio.startswith(b"OggS")
        self.voice.append(len(audio))


def update(uid, text="", voice=None):
    return {
        "update_id": uid,
        "message": {
            "from": {"id": 900001},
            "chat": {"id": 900001, "type": "private"},
            **({"voice": voice} if voice else {"text": text}),
        },
    }


async def main():
    settings = Settings(public_demo=True)
    if not settings.speech_key or not settings.model_key:
        print("BLOCKED: configure speech and model access privately.")
        return 2
    try:
        speech = Speech(settings)
        audio = await speech.synthesize(
            "This is fictional. The decor is delayed. The deadline is November twelfth twenty twenty six at three P M Indian Standard Time.",
            "en-IN",
        )
        transport = CapturedTelegram(audio)
        with tempfile.TemporaryDirectory(prefix="tarang-voice-eval-") as directory:
            settings.database = str(Path(directory) / "test.sqlite3")
            store = Store(settings.database)
            model = OpenRouter(settings)
            voice = VoiceDemo(store, settings, transport, speech)
            demo = PublicDemo(store, settings, model, voice)
            demo.ingest(update(1, "/start voice"))
            demo.ingest(update(2, "/voice"))
            demo.ingest(
                update(
                    3,
                    voice={
                        "file_id": "synthetic-clip",
                        "file_size": len(audio),
                        "duration": 15,
                    },
                )
            )
            await voice.step()
            with store.tx() as db:
                job = db.execute(
                    "SELECT * FROM voice_jobs WHERE status='review'"
                ).fetchone()
                assert job
                transcript = job["transcript"]
                assert not db.execute("SELECT 1 FROM demo_turns").fetchone()
            demo.ingest(update(4, "/heard"))
            await demo.step()
            with store.tx() as db:
                turn = db.execute("SELECT status FROM demo_turns").fetchone()
                assert turn["status"] == "done"
                facts = Intake.read(db, 900001)["facts"]
                assert "delay" in facts["problem"].lower()
                assert facts["deadline"]
                for table in (
                    "commitments",
                    "operations",
                    "budgets",
                    "evidence",
                    "events",
                ):
                    assert not db.execute(f"SELECT 1 FROM {table}").fetchone()
                # Generate the resulting next question, rather than synthesizing the whole test transcript history.
                row = db.execute(
                    "SELECT payload FROM outbox WHERE key='demo:ai:demo:4'"
                ).fetchone()
                reply = json.loads(row["payload"])["text"]
            output = await speech.synthesize(reply, "en-IN")
            assert output.startswith(b"OggS")
            receipt = {
                "synthetic": True,
                "actual_telegram_client": False,
                "input_transcript": transcript,
                "facts": facts,
                "reply_text": reply,
                "spoken_reply_bytes": len(output),
                "passed": True,
                "date_accuracy_verified": False,
                "transcript_review_required": True,
            }
            target = Path(".runtime/voice-pipeline-evaluation.json")
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps(receipt, indent=2))
            target.chmod(0o600)
            print(
                "PASS: live synthetic speech, transcript review, model intake and spoken next question. Telegram is captured."
            )
            return 0
    except Exception as exc:
        print("Voice pipeline probe failed:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
