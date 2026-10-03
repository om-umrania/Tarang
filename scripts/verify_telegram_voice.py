"""Verify real Gnani and Telegram media transport with labelled synthetic input.

Local updates and transcript confirmation are synthetic, not human client ingress.
Uses only the single configured operator chat and an isolated temporary database.
"""

import asyncio
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from tarang.adapters import OpenRouter, Telegram
from tarang.config import Settings
from tarang.intake import Intake
from tarang.public_demo import PublicDemo
from tarang.store import Store
from tarang.voice import Speech, VoiceDemo


def update(uid, chat, text="", voice=None):
    return {
        "update_id": uid,
        "message": {
            "from": {"id": chat},
            "chat": {"id": chat, "type": "private"},
            **({"voice": voice} if voice else {"text": text}),
        },
    }


async def main():
    settings = Settings(public_demo=True)
    if (
        not all((settings.speech_key, settings.model_key, settings.bot_token))
        or len(settings.allowed) != 1
    ):
        print("BLOCKED: configure speech, model and one operator chat privately.")
        return 2
    stage = "synthesis"
    try:
        chat = next(iter(settings.allowed))
        speech = Speech(settings)
        transport = Telegram(settings.bot_token)
        audio = await speech.synthesize(
            "Test only. The decor is delayed. Please preserve the ivory and peach design and the existing budget.",
            "en-IN",
        )
        await transport.call(
            "sendMessage",
            {
                "chat_id": chat,
                "text": "VOICE TEST ONLY · Testing real Gnani speech and Telegram audio delivery from the local runtime. The next recording is AI-generated fictional input. No phone call, vendor contact, booking or payment occurs.",
            },
        )
        uploaded = await transport.send_voice(chat, audio)
        print(
            "Telegram synthetic upload accepted; duration:",
            uploaded["voice"]["duration"],
            flush=True,
        )
        stage = "transcript review"
        with tempfile.TemporaryDirectory(prefix="tarang-voice-eval-") as directory:
            settings.database = str(Path(directory) / "test.sqlite3")
            store = Store(settings.database)
            model = OpenRouter(settings)
            voice = VoiceDemo(store, settings, transport, speech)
            demo = PublicDemo(store, settings, model, voice)
            demo.ingest(update(1, chat, "/start voice"))
            demo.ingest(update(2, chat, "/voice"))
            demo.ingest(
                update(
                    3,
                    chat,
                    voice={
                        "file_id": uploaded["voice"]["file_id"],
                        "file_size": len(audio),
                        "duration": uploaded["voice"]["duration"],
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
            stage = "model intake"
            demo.ingest(update(4, chat, "/heard"))
            await demo.step()
            with store.tx() as db:
                turn = db.execute("SELECT status FROM demo_turns").fetchone()
                assert turn["status"] == "done"
                facts = Intake.read(db, chat)["facts"]
                assert "delay" in facts["problem"].lower()
                assert facts["constraints"]
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
            stage = "spoken reply delivery"
            output = await speech.synthesize(reply, "en-IN")
            assert output.startswith(b"OggS")
            await transport.call(
                "sendMessage",
                {
                    "chat_id": chat,
                    "text": "VOICE TEST ONLY · Gnani heard: "
                    + transcript
                    + "\n\nThe next recording is the model's spoken follow-up. This input was synthetic and locally confirmed; it was not a human Telegram recording.",
                },
            )
            delivered = await transport.send_voice(chat, output)
            await transport.call("sendMessage", {"chat_id": chat, "text": reply})
            receipt = {
                "synthetic_input": True,
                "human_voice_note_received": False,
                "human_confirmation": False,
                "phone_call_placed": False,
                "gnani_stt_passed": True,
                "gnani_tts_passed": True,
                "telegram_input_voice_message_id": uploaded["message_id"],
                "telegram_reply_voice_message_id": delivered["message_id"],
                "telegram_reply_duration": delivered["voice"]["duration"],
                "input_transcript": transcript,
                "facts": facts,
                "reply_text": reply,
                "spoken_reply_bytes": len(output),
                "passed": True,
            }
            target = Path(".runtime/live-telegram-voice.json")
            target.parent.mkdir(exist_ok=True)
            target.write_text(json.dumps(receipt, indent=2))
            target.chmod(0o600)
            print(
                "PASS: real Gnani STT/TTS and Telegram audio upload/download/reply. Input and confirmation are synthetic; human client ingress is not verified."
            )
            return 0
    except Exception as exc:
        print("Voice pipeline probe failed at", stage, type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
