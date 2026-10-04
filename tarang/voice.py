"""Voice notes for isolated Telegram demos; audio is transient, text is reviewed."""

import asyncio
import time
import uuid

import httpx
from .store import Store

MAX_AUDIO = 10 * 1024 * 1024
NOTICE = (
    "Voice mode uses Gnani to transcribe recordings and generate an AI voice. "
    "Confirmed text and recent conversation context go to OpenRouter. Use made-up names and details, not real wedding information or secrets. "
    "Send a voice note up to 60 seconds (ideally 30); I'll show what I heard before using it. "
    "Replies include text and suggested buttons. /voice off returns to text. "
    "Use /voice en-IN or /voice hi-IN to select the spoken language."
)


class Speech:
    def __init__(self, settings):
        self.settings = settings

    async def transcribe(self, content, language):
        if not self.settings.speech_key:
            raise RuntimeError("speech_not_configured")
        if not content or len(content) > MAX_AUDIO:
            raise ValueError("invalid_audio_size")
        async with httpx.AsyncClient(timeout=45) as client:
            response = await client.post(
                "https://api.vachana.ai/stt/v3",
                headers={"X-API-Key-ID": self.settings.speech_key},
                files={"audio_file": ("voice.ogg", content, "audio/ogg")},
                data={"language_code": language, "format": "transcribe"},
            )
        if response.status_code != 200:
            raise RuntimeError("speech_provider_error")
        result = response.json()
        text = result.get("transcript")
        if (
            result.get("success") is not True
            or not isinstance(text, str)
            or not 0 < len(text.strip()) <= 2000
        ):
            raise RuntimeError("speech_invalid_transcript")
        return text.strip()

    async def synthesize(self, text, language):
        if not self.settings.speech_key:
            raise RuntimeError("speech_not_configured")
        # Standard catalogue voice, never a clone or claimed human identity.
        voice = "Nalini" if language == "hi-IN" else self.settings.speech_voice
        async with httpx.AsyncClient(timeout=45) as client:
            async with client.stream(
                "POST",
                "https://api.vachana.ai/api/v1/tts/inference",
                headers={"X-API-Key-ID": self.settings.speech_key},
                json={
                    "text": text,
                    "voice": voice,
                    "model": "timbre-v2.5",
                    "language": language,
                    "speed": 1.0,
                    "audio_config": {
                        "container": "ogg",
                        "encoding": "oggopus",
                        "sample_rate": 24000,
                        "num_channels": 1,
                    },
                },
            ) as response:
                if response.status_code != 200:
                    raise RuntimeError("speech_provider_error")
                content = bytearray()
                async for chunk in response.aiter_bytes():
                    content.extend(chunk)
                    if len(content) > MAX_AUDIO:
                        raise RuntimeError("speech_audio_too_large")
        if not content.startswith(b"OggS"):
            raise RuntimeError("speech_invalid_audio")
        return bytes(content)


class VoiceDemo:
    def __init__(self, store, settings, telegram, speech):
        self.store, self.settings, self.telegram, self.speech = (
            store,
            settings,
            telegram,
            speech,
        )

    def handle(self, db, key, chat, session, message, data, command, quota):
        """Called after public-demo identity, dedup and input quota checks."""
        pref = db.execute(
            "SELECT * FROM voice_preferences WHERE chat=?", (chat,)
        ).fetchone()
        if command.startswith("/voice"):
            arg = command.removeprefix("/voice").strip()
            if arg == "off":
                db.execute("DELETE FROM voice_preferences WHERE chat=?", (chat,))
                db.execute("DELETE FROM voice_jobs WHERE chat=?", (chat,))
                db.execute(
                    "UPDATE outbox SET state='cancelled' WHERE chat=? AND key LIKE 'demo:speech:%' AND state='pending'",
                    (chat,),
                )
                Store.message(
                    db, key, chat, "Voice mode off. Continue with text or buttons."
                )
            elif not self.settings.speech_key:
                Store.message(
                    db,
                    key,
                    chat,
                    "Voice service is not configured yet. Text and suggested buttons still work.",
                )
            elif not session["consent"] or session["scenario"] != "conversation":
                Store.message(
                    db,
                    key,
                    chat,
                    "Choose Start with voice or send /voice to start a voice conversation.",
                )
            elif arg and arg not in {"en-in", "hi-in"}:
                Store.message(
                    db, key, chat, "Use /voice en-IN, /voice hi-IN, or /voice off."
                )
            else:
                language = "hi-IN" if arg == "hi-in" else "en-IN"
                db.execute(
                    "INSERT INTO voice_preferences(chat,language) VALUES(?,?) ON CONFLICT(chat) DO UPDATE SET language=excluded.language",
                    (chat, language),
                )
                Store.message(db, key, chat, NOTICE)
            return True
        if data.startswith("demo:heard:") or command in {"/heard", "/discard"}:
            job = db.execute(
                "SELECT * FROM voice_jobs WHERE chat=? AND generation=? AND status='review'",
                (chat, session["generation"]),
            ).fetchone()
            valid = job and (
                not data
                or data
                in {f"demo:heard:{job['token']}:yes", f"demo:heard:{job['token']}:no"}
            )
            if not valid:
                Store.message(
                    db,
                    key,
                    chat,
                    "That transcript is no longer current. Send a new voice note or type your answer.",
                )
                return True
            if command == "/discard" or data.endswith(":no"):
                db.execute("DELETE FROM voice_jobs WHERE chat=?", (chat,))
                Store.message(
                    db,
                    key,
                    chat,
                    "Transcript discarded. Record again or type the corrected answer.",
                )
                return True
            if db.execute(
                "SELECT 1 FROM demo_turns WHERE chat=? AND status IN ('pending','processing')",
                (chat,),
            ).fetchone():
                Store.message(
                    db,
                    key,
                    chat,
                    "Please wait for the previous answer before confirming this transcript.",
                )
                return True
            if not quota(db, chat, "model", time.time(), 10, 100):
                Store.message(
                    db,
                    key,
                    chat,
                    "Today's AI limit has been reached. Use the suggested buttons.",
                )
                return True
            from .intake import Intake

            Intake.save(db, chat, Intake.read(db, chat))
            db.execute(
                "INSERT INTO demo_turns(key,chat,generation,body,status,created) VALUES(?,?,?,?,'pending',?)",
                (key, chat, session["generation"], job["transcript"], time.time()),
            )
            db.execute("DELETE FROM voice_jobs WHERE chat=?", (chat,))
            return True
        voice = message.get("voice")
        if not voice:
            # A new text answer supersedes a previous unconfirmed recording.
            if (command and not command.startswith("/")) or data.startswith(
                "demo:pick:"
            ):
                db.execute("DELETE FROM voice_jobs WHERE chat=?", (chat,))
            return False
        if (
            not pref
            or not self.settings.speech_key
            or session["scenario"] != "conversation"
        ):
            Store.message(
                db,
                key,
                chat,
                "Choose Start with voice or send /voice to enable transcription. This recording has not been downloaded or processed.",
            )
            return True
        size, duration, file_id = (
            voice.get("file_size"),
            voice.get("duration"),
            voice.get("file_id"),
        )
        if (
            not isinstance(duration, int)
            or isinstance(duration, bool)
            or not 0 < duration <= 60
            or not isinstance(size, int)
            or isinstance(size, bool)
            or not 0 < size <= MAX_AUDIO
            or not isinstance(file_id, str)
            or not 0 < len(file_id) <= 512
        ):
            Store.message(
                db,
                key,
                chat,
                "Please send a voice note up to 60 seconds and 10 MB, or type your answer.",
            )
            return True
        if (
            db.execute(
                "SELECT 1 FROM voice_jobs WHERE chat=? AND status IN ('pending','processing')",
                (chat,),
            ).fetchone()
            or db.execute(
                "SELECT 1 FROM demo_turns WHERE chat=? AND status IN ('pending','processing')",
                (chat,),
            ).fetchone()
        ):
            Store.message(
                db,
                key,
                chat,
                "Please wait for your previous answer before sending another recording.",
            )
            return True
        if not quota(db, chat, "speech", time.time(), 10, 100):
            Store.message(
                db,
                key,
                chat,
                "Today's voice limit has been reached. Text and buttons still work.",
            )
            return True
        db.execute("DELETE FROM voice_jobs WHERE chat=?", (chat,))
        db.execute(
            "INSERT INTO voice_jobs(chat,key,generation,file_id,language,token,status,created) VALUES(?,?,?,?,?,?,'pending',?)",
            (
                chat,
                key,
                session["generation"],
                file_id,
                pref["language"],
                uuid.uuid4().hex[:16],
                time.time(),
            ),
        )
        Store.message(
            db,
            key,
            chat,
            "I'll transcribe that recording and ask you to check what I heard.",
        )
        return True

    async def step(self):
        now = time.time()
        with self.store.tx() as db:
            for job in db.execute(
                "SELECT * FROM voice_jobs WHERE status='processing' AND lease<?", (now,)
            ).fetchall():
                Store.message(
                    db,
                    job["key"] + ":interrupted",
                    job["chat"],
                    "Voice processing was interrupted. Please record again or type your answer.",
                )
                db.execute("DELETE FROM voice_jobs WHERE chat=?", (job["chat"],))
            if db.execute(
                "SELECT 1 FROM voice_jobs WHERE status='processing'"
            ).fetchone():
                return False
            job = db.execute(
                "SELECT * FROM voice_jobs WHERE status='pending' ORDER BY created LIMIT 1"
            ).fetchone()
            if not job:
                return False
            job = dict(job)
            db.execute(
                "UPDATE voice_jobs SET status='processing',lease=? WHERE chat=?",
                (now + 90, job["chat"]),
            )
        try:
            async with asyncio.timeout(65):
                audio = await self.telegram.download_voice(job["file_id"], MAX_AUDIO)
                transcript = await self.speech.transcribe(audio, job["language"])
            if (
                not isinstance(transcript, str)
                or not 0 < len(transcript.strip()) <= 2000
            ):
                raise ValueError("invalid_transcript")
        except Exception:
            transcript = None
        with self.store.tx() as db:
            current = db.execute(
                "SELECT 1 FROM voice_jobs v JOIN demo_sessions s ON s.chat=v.chat AND s.generation=v.generation JOIN voice_preferences p ON p.chat=v.chat WHERE v.token=? AND v.status='processing'",
                (job["token"],),
            ).fetchone()
            if not current or not self.settings.public_demo:
                return True
            if transcript is None:
                db.execute("DELETE FROM voice_jobs WHERE chat=?", (job["chat"],))
                Store.message(
                    db,
                    job["key"] + ":transcript",
                    job["chat"],
                    "I couldn't transcribe that recording. Please try a shorter note or type your answer; your existing plan is unchanged.",
                )
            else:
                db.execute(
                    "UPDATE voice_jobs SET status='review',transcript=?,file_id='' WHERE token=?",
                    (transcript.strip(), job["token"]),
                )
                buttons = [
                    [
                        {
                            "text": "Use this transcript",
                            "callback_data": f"demo:heard:{job['token']}:yes",
                        }
                    ],
                    [
                        {
                            "text": "Discard / record again",
                            "callback_data": f"demo:heard:{job['token']}:no",
                        }
                    ],
                ]
                Store.message(
                    db,
                    job["key"] + ":transcript",
                    job["chat"],
                    "I heard:\n\n"
                    + transcript.strip()
                    + "\n\nIs this accurate? Check names, dates, years, amounts and times. Tap Use this transcript or send /heard to continue. /discard rejects it; you can also type a corrected answer.",
                    buttons,
                )
        return True
