import asyncio
import json
import time

import httpx
import pytest

from tarang.config import Settings
from tarang.engine import Engine
from tarang.intake import Intake, IntakeFacts, IntakeReply
from tarang.public_demo import PublicDemo
from tarang.store import Store
from tarang.voice import Speech, VoiceDemo
from tarang.adapters import Telegram
from test_public_demo import update, rows


class Model:
    def __init__(self):
        self.contexts = []

    async def intake_reply(self, context):
        self.contexts.append(context)
        return IntakeReply(
            message="Noted the fictional problem.",
            facts=IntakeFacts(problem=context["question"]),
        )


class Transport:
    def __init__(self):
        self.downloads, self.sent, self.audio = [], [], []

    async def download_voice(self, file_id, limit):
        self.downloads.append(file_id)
        return b"OggSfictional-fixture"

    async def call(self, method, payload):
        self.sent.append((method, payload))

    async def send_voice(self, chat, audio):
        self.audio.append((chat, audio))


class FakeSpeech:
    async def transcribe(self, content, language):
        assert language == "en-IN"
        return "Fictional decor is delayed"

    async def synthesize(self, text, language):
        return b"OggSfictional-output"


@pytest.fixture
def demo(demo_database):
    settings = Settings(database=demo_database, public_demo=True, speech_key="fake")
    store, model, transport = Store(settings.database), Model(), Transport()
    voice = VoiceDemo(store, settings, transport, FakeSpeech())
    result = PublicDemo(store, settings, model, voice)
    result.transport = transport
    return result


def start(demo):
    demo.ingest(update(1, text="/start demo"))
    demo.ingest(update(2, text="/talk"))


def note(uid=4, chat=101, duration=15, size=1024):
    result = update(uid, chat)
    result["message"].pop("text")
    result["message"]["voice"] = {
        "file_id": "test-voice",
        "duration": duration,
        "file_size": size,
    }
    return result


def last(demo):
    return json.loads(rows(demo, "outbox")[-1]["payload"])


def test_voice_confirm_then_existing_intake_and_spoken_reply(demo, monkeypatch):
    start(demo)
    demo.ingest(update(3, text="/voice"))
    assert any("Gnani" in r["payload"] for r in rows(demo, "outbox"))
    demo.ingest(note())
    demo.ingest(note())  # actual Telegram duplicate
    asyncio.run(demo.voice.step())
    assert demo.transport.downloads == ["test-voice"]
    assert "I heard:" in last(demo)["text"]
    assert not demo.model.contexts
    assert not rows(demo, "demo_turns")
    action = last(demo)["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    demo.ingest(update(5, callback=action))
    demo.ingest(update(6, callback=action))  # old confirmation cannot repeat
    assert len(rows(demo, "demo_turns")) == 1
    asyncio.run(demo.step())
    assert demo.model.contexts[0]["question"] == "Fictional decor is delayed"
    with demo.store.tx() as db:
        assert Intake.read(db, 101)["facts"]["problem"] == "Fictional decor is delayed"
    monkeypatch.setattr(Speech, "synthesize", FakeSpeech.synthesize)
    engine = Engine(demo.store, demo.settings, demo.model, demo.transport)
    for _ in range(30):
        if not asyncio.run(engine.send_one()):
            break
    assert demo.transport.audio
    assert all(method == "sendMessage" for method, _ in demo.transport.sent)
    for table in ("events", "commitments", "operations", "budgets", "evidence"):
        assert not rows(demo, table)


def test_no_download_without_opt_in_or_oversized_or_cross_user(demo):
    start(demo)
    demo.ingest(note(3))
    assert "not been downloaded" in last(demo)["text"]
    demo.ingest(update(4, text="/voice"))
    for uid, duration, size in [(5, 61, 100), (6, 10, 11 * 1024 * 1024), (7, -1, 10)]:
        demo.ingest(note(uid, duration=duration, size=size))
    wrong = note(8)
    wrong["message"]["from"]["id"] = 202
    assert not demo.ingest(wrong)
    assert not asyncio.run(demo.voice.step())
    assert not demo.transport.downloads


def test_transcript_correction_supersedes_confirmation_and_keeps_case(demo):
    start(demo)
    demo.ingest(update(3, text="/voice"))
    demo.ingest(note())
    asyncio.run(demo.voice.step())
    action = last(demo)["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    assert demo.ingest(update(5, chat=202, callback=action))  # isolated welcome
    assert not rows(demo, "demo_turns")
    demo.ingest(update(6, text="Fictional corrected problem, preserve IVORY"))
    demo.ingest(update(7, callback=action))
    assert len(rows(demo, "demo_turns")) == 1
    asyncio.run(demo.step())
    assert demo.model.contexts[-1]["question"].endswith("IVORY")


@pytest.mark.parametrize("command", ["/reset", "/delete", "/voice off", "/talk"])
def test_reset_off_delete_during_transcription_suppresses_result(demo, command):
    start(demo)
    demo.ingest(update(3, text="/voice"))
    demo.ingest(note())

    async def interrupted(content, language):
        demo.ingest(update(5, text=command))
        return "late transcript"

    demo.voice.speech.transcribe = interrupted
    asyncio.run(demo.voice.step())
    assert not rows(demo, "voice_jobs")
    assert all("late transcript" not in r["payload"] for r in rows(demo, "outbox"))


def test_speech_failure_crash_and_quota_preserve_text_flow(demo):
    start(demo)
    demo.ingest(update(3, text="/voice"))
    demo.ingest(note())

    async def fail(*args):
        raise RuntimeError("private provider failure")

    demo.voice.speech.transcribe = fail
    asyncio.run(demo.voice.step())
    assert "couldn't transcribe" in last(demo)["text"]
    assert "private provider" not in last(demo)["text"]
    demo.ingest(note(5))
    with demo.store.tx() as db:
        db.execute(
            "UPDATE voice_jobs SET status='processing',lease=?", (time.time() - 1,)
        )
    asyncio.run(demo.voice.step())
    assert "interrupted" in last(demo)["text"]
    for uid in range(6, 14):
        demo.ingest(note(uid))
        asyncio.run(demo.voice.step())
    demo.ingest(note(14))
    assert "limit" in last(demo)["text"]
    demo.ingest(update(15, text="Text still works"))
    asyncio.run(demo.step())
    assert demo.model.contexts[-1]["question"] == "Text still works"


def test_tts_failure_keeps_sent_text_and_does_not_retry(demo, monkeypatch):
    start(demo)
    demo.ingest(update(3, text="/voice"))

    async def fail(*args):
        raise RuntimeError("private error")

    monkeypatch.setattr(Speech, "synthesize", fail)
    engine = Engine(demo.store, demo.settings, demo.model, demo.transport)
    for _ in range(20):
        if not asyncio.run(engine.send_one()):
            break
    assert demo.transport.sent
    assert not demo.transport.audio
    assert any(r["state"] == "failed" for r in rows(demo, "outbox"))
    assert any("couldn't generate" in p["text"] for _, p in demo.transport.sent)
    assert not asyncio.run(engine.send_one())


def test_speech_http_contract_and_download_bounds(monkeypatch):
    actual_client = httpx.AsyncClient
    requests = []

    def handle(request):
        requests.append(request)
        if request.url.path == "/stt/v3":
            assert request.headers["x-api-key-id"] == "fake"
            assert b'name="language_code"' in request.content
            return httpx.Response(
                200, json={"success": True, "transcript": "Fictional delay"}
            )
        if request.url.path == "/api/v1/tts/inference":
            body = json.loads(request.content)
            assert body["model"] == "timbre-v2.5"
            assert body["audio_config"]["container"] == "ogg"
            assert body["voice"] == "Nalini"
            return httpx.Response(200, content=b"OggSoutput")
        if request.url.path.endswith("/getFile"):
            return httpx.Response(
                200, json={"ok": True, "result": {"file_path": "voice/test.oga"}}
            )
        if "/file/bot" in request.url.path:
            return httpx.Response(200, content=b"x" * 21)
        raise AssertionError("Unexpected request")

    monkeypatch.setattr(
        httpx,
        "AsyncClient",
        lambda **kw: actual_client(transport=httpx.MockTransport(handle), **kw),
    )
    speech = Speech(Settings(speech_key="fake"))
    assert asyncio.run(speech.transcribe(b"OggSinput", "en-IN")) == "Fictional delay"
    assert asyncio.run(speech.synthesize("Fictional demo", "hi-IN")) == b"OggSoutput"
    with pytest.raises(RuntimeError, match="too_large"):
        asyncio.run(Telegram("fake").download_voice("file", 20))


def test_voice_unconfigured_is_explicit_and_does_not_queue(demo):
    start(demo)
    demo.settings.speech_key = ""
    demo.ingest(update(3, text="/voice"))
    assert "not configured" in last(demo)["text"]
    assert not rows(demo, "voice_preferences")
    demo.ingest(note())
    assert not rows(demo, "voice_jobs")


def test_voice_off_during_synthesis_cancels_before_send(demo, monkeypatch):
    start(demo)
    demo.ingest(update(3, text="/voice"))
    engine = Engine(demo.store, demo.settings, demo.model, demo.transport)
    for _ in range(3):
        asyncio.run(engine.send_one())

    async def interrupted(self, text, language):
        demo.ingest(update(5, text="/voice off"))
        return b"OggSfictional-output"

    monkeypatch.setattr(Speech, "synthesize", interrupted)
    asyncio.run(engine.send_one())
    assert not demo.transport.audio
    assert not any(r["state"] == "sending" for r in rows(demo, "outbox"))


def test_ambiguous_voice_send_is_unknown_and_never_retried(demo, monkeypatch):
    start(demo)
    demo.ingest(update(3, text="/voice"))
    monkeypatch.setattr(Speech, "synthesize", FakeSpeech.synthesize)
    calls = []

    async def ambiguous(chat, audio):
        calls.append(chat)
        raise TimeoutError()

    demo.transport.send_voice = ambiguous
    engine = Engine(demo.store, demo.settings, demo.model, demo.transport)
    for _ in range(20):
        if not asyncio.run(engine.send_one()):
            break
    before = len(calls)
    engine.recover()
    assert not asyncio.run(engine.send_one())
    assert len(calls) == before
    assert any(r["state"] == "unknown" for r in rows(demo, "outbox"))


def test_signed_webhook_accepts_voice_and_preserves_authority(demo_database):
    from fastapi.testclient import TestClient
    from tarang.app import create_app

    settings = Settings(
        database=demo_database,
        public_demo=True,
        speech_key="fake",
        webhook_secret="test-secret",
        telegram_mode="webhook",
    )
    model, transport = Model(), Transport()
    app = create_app(settings, model=model, telegram=transport, run_worker=False)
    app.state.voice.speech = FakeSpeech()
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    with TestClient(app) as client:
        assert client.post("/telegram/webhook", json=note()).status_code == 403
        for body in [
            update(1, text="/start demo"),
            update(2, text="/talk"),
            update(3, text="/voice"),
            note(),
        ]:
            assert (
                client.post("/telegram/webhook", headers=headers, json=body).status_code
                == 200
            )
        asyncio.run(app.state.voice.step())
        assert (
            client.post(
                "/telegram/webhook", headers=headers, json=update(5, text="/heard")
            ).status_code
            == 200
        )
        asyncio.run(app.state.demo.step())
        assert model.contexts[0]["question"] == "Fictional decor is delayed"
        with app.state.demo.store.tx() as db:
            assert not db.execute("SELECT 1 FROM operations").fetchone()
            assert not db.execute("SELECT 1 FROM commitments").fetchone()


def test_voice_first_entry_from_welcome_and_existing_plan(demo):
    demo.ingest(update(1, text="/start voice"))
    buttons = last(demo)["reply_markup"]["inline_keyboard"]
    assert buttons[0][0]["text"] == "Start with voice"
    assert not rows(demo, "voice_preferences")
    demo.ingest(update(2, callback="demo:voice"))
    assert rows(demo, "voice_preferences")[0]["language"] == "en-IN"
    with demo.store.tx() as db:
        state = Intake.read(db, 101)
        assert state["phase"] == "collect"
    demo.ingest(update(3, text="/choose 1"))
    demo.ingest(update(4, text="/voice hi-IN"))
    with demo.store.tx() as db:
        assert Intake.read(db, 101)["facts"]["problem"] == "Décor is delayed"
    assert rows(demo, "voice_preferences")[0]["language"] == "hi-IN"
    assert "voice note" in last(demo)["text"]


def test_voice_first_missing_key_and_owner_routing(demo):
    demo.settings.allowed = frozenset({101})
    assert demo.ingest(update(1, text="/voice"))
    assert not rows(demo, "voice_preferences")
    assert "Gnani" in last(demo)["text"]
    demo.settings.speech_key = ""
    demo.ingest(update(2, callback="demo:voice"))
    assert "not configured" in last(demo)["text"]
    assert not rows(demo, "voice_preferences")
    assert not rows(demo, "commitments")
