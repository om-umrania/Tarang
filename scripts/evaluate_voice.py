"""Live synthetic Gnani round trip; no user recordings or wedding data accessed."""

import asyncio
import hashlib
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tarang.config import Settings
from tarang.voice import Speech


async def main():
    settings = Settings()
    if not settings.speech_key:
        print("BLOCKED: configure GNANI_API_KEY privately; no speech requests made.")
        return 2
    speech = Speech(settings)
    try:
        audio = await speech.synthesize(
            "This is a fictional Tarang test. The decor is delayed.", "en-IN"
        )
        transcript = await speech.transcribe(audio, "en-IN")
        passed = "delay" in transcript.lower() and bool(audio.startswith(b"OggS"))
        receipt = {
            "synthetic": True,
            "audio_bytes": len(audio),
            "audio_sha256": hashlib.sha256(audio).hexdigest(),
            "transcript": transcript,
            "passed": passed,
            "telegram_client_verified": False,
        }
        target = Path(".runtime/voice-evaluation.json")
        target.parent.mkdir(exist_ok=True)
        target.write_text(json.dumps(receipt, indent=2))
        target.chmod(0o600)
        print(
            "PASS" if passed else "FAIL",
            "synthetic speech round trip; receipt saved privately.",
        )
        return 0 if passed else 1
    except Exception as exc:
        print("Speech probe failed:", type(exc).__name__)
        return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
