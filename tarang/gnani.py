"""Run the documented Gnani speech rail and persist its exact response as evidence.

Usage: python -m tarang.gnani --audio path.ogg --commitment 1 --language hi-IN
Requires GNANI_API_KEY, OPERATOR_TOKEN and TARANG_URL (defaults to localhost).
Only use recordings the speakers have authorised for transcription.
"""

import argparse
import asyncio
import hashlib
import json
import os
import time
from pathlib import Path
import httpx
from .config import Settings


async def transcribe(audio: Path, language: str):
    key = os.getenv("GNANI_API_KEY", "")
    if not key:
        raise ValueError("GNANI_API_KEY is required; no simulated fallback")
    content = audio.read_bytes()
    if len(content) > 10 * 1024 * 1024:
        raise ValueError("Use a short audio file, maximum 10 MB and 60 seconds")
    async with httpx.AsyncClient(timeout=60) as client:
        response = await client.post(
            "https://api.vachana.ai/stt/v3",
            headers={"X-API-Key-ID": key},
            files={"audio_file": (audio.name, content)},
            data={"language_code": language, "format": "verbatim"},
        )
        receipt = {
            "rail": "gnani",
            "method": "POST",
            "endpoint": "https://api.vachana.ai/stt/v3",
            "request": {
                "audio_sha256": hashlib.sha256(content).hexdigest(),
                "language_code": language,
                "format": "verbatim",
            },
            "http_status": response.status_code,
            "exact_response": response.text,
        }
        return receipt


async def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audio", type=Path, required=True)
    parser.add_argument("--commitment", type=int, required=True)
    parser.add_argument(
        "--language",
        choices=[
            "hi-IN",
            "en-IN",
            "gu-IN",
            "bn-IN",
            "kn-IN",
            "ml-IN",
            "mr-IN",
            "pa-IN",
            "ta-IN",
            "te-IN",
        ],
        required=True,
    )
    args = parser.parse_args()
    settings = Settings()
    try:
        receipt = await transcribe(args.audio, args.language)
        saved = Path(".runtime") / f"gnani-receipt-{time.time_ns()}.json"
        saved.parent.mkdir(exist_ok=True)
        saved.write_text(json.dumps(receipt, indent=2))
        saved.chmod(0o600)
        print("Exact API receipt saved locally:", saved)
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(
                os.getenv("TARANG_URL", "http://127.0.0.1:8766").rstrip("/")
                + "/api/evidence",
                headers={"Authorization": "Bearer " + settings.operator_token},
                json={
                    "commitment_id": args.commitment,
                    "source": "Gnani STT live API; audio hash in receipt",
                    "mode": "manual-real-api",
                    "content": json.dumps(receipt),
                    "verifies_outcome": False,
                },
            )
            print(
                "Gnani HTTP status:",
                receipt["http_status"],
                "Evidence save HTTP status:",
                r.status_code,
            )
    except Exception as exc:
        print("Voice rail failed:", type(exc).__name__)
        raise SystemExit(1) from None


if __name__ == "__main__":
    asyncio.run(main())
