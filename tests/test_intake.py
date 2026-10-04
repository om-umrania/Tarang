import asyncio
import json

import pytest

from tarang.intake import Intake, IntakeFacts, IntakeReply
from tarang.public_demo import PublicDemo
from tarang.config import Settings
from tarang.store import Store
from test_public_demo import update, rows


class Model:
    def __init__(self):
        self.contexts = []
        self.result = IntakeReply(
            message="Thanks, I've noted that.", facts=IntakeFacts()
        )

    async def intake_reply(self, context):
        self.contexts.append(context)
        return self.result


@pytest.fixture
def demo(demo_database):
    settings = Settings(
        database=demo_database,
        public_demo=True,
        allowed=frozenset({42}),
    )
    return PublicDemo(Store(settings.database), settings, Model())


def payload(demo):
    return json.loads(rows(demo, "outbox")[-1]["payload"])


def choose(demo, uid, label, chat=101):
    buttons = payload(demo)["reply_markup"]["inline_keyboard"]
    action = next(b[0]["callback_data"] for b in buttons if b[0]["text"] == label)
    assert len(action.encode()) <= 64
    demo.ingest(update(uid, chat, callback=action))
    return action


def start(demo, chat=101, uid=1):
    demo.ingest(update(uid, chat, "/start demo"))
    choose(demo, uid + 1, "Start a conversation", chat)


def facts(demo, chat=101):
    with demo.store.tx() as db:
        return Intake.read(db, chat)


def test_question_suggestions_complete_action_feedback_and_pause(demo):
    start(demo)
    choose(demo, 3, "Décor is delayed")
    choose(demo, 4, "Date/time not decided yet")
    assert "Décor vendor" in payload(demo)["text"] or any(
        b[0]["text"] == "Décor vendor"
        for b in payload(demo)["reply_markup"]["inline_keyboard"]
    )
    for uid, label in enumerate(
        [
            "Décor vendor",
            "Me",
            "Venue coordinator",
            "Original design and scope",
            "Meet the deadline",
        ],
        5,
    ):
        choose(demo, uid, label)
    assert "Here's the plan" in payload(demo)["text"]
    choose(demo, 10, "Review contact status")
    assert "Contact status" in payload(demo)["text"]
    choose(demo, 11, "Explore alternatives")
    assert facts(demo)["feedback"] == "Explore alternatives"
    assert "Nothing is booked" in payload(demo)["text"]
    choose(demo, 12, "Pause")
    assert facts(demo)["phase"] == "paused"
    choose(demo, 13, "Resume")
    assert facts(demo)["phase"] == "feedback"
    assert not demo.model.contexts
    for table in ("commitments", "operations", "budgets", "events", "evidence"):
        assert not rows(demo, table)


def test_free_text_multiple_facts_skip_questions_and_correction_survives_restart(demo):
    start(demo)
    demo.model.result = IntakeReply(
        message="I've noted your requirements.",
        facts=IntakeFacts(
            problem="Delayed décor",
            deadline="12 November 2026 at 4 pm IST",
            contact="Fictional vendor",
            approver="Me",
            verifier="Venue coordinator",
            constraints="Same design, no extra spend",
            priority="Deadline",
        ),
    )
    demo.ingest(update(3, text="Fictional full problem and requirements"))
    asyncio.run(demo.step())
    assert facts(demo)["phase"] == "review"
    assert "4 pm IST" in payload(demo)["text"]
    restarted = PublicDemo(demo.store, demo.settings, demo.model)
    demo.model.result = IntakeReply(
        message="I've updated the deadline.",
        facts=IntakeFacts(deadline="12 November 2026 at 3 pm IST"),
    )
    restarted.ingest(
        update(4, text="Correction: deadline 12 November 2026 at 3 pm IST")
    )
    asyncio.run(restarted.step())
    assert facts(demo)["facts"]["deadline"].endswith("3 pm IST")
    assert facts(demo)["facts"]["constraints"] == "Same design, no extra spend"
    assert (
        demo.model.contexts[-1]["history"][0]["body"]
        == "Fictional full problem and requirements"
    )


def test_stale_cross_user_duplicate_and_pending_choices_cannot_change_facts(demo):
    start(demo)
    action = choose(demo, 3, "Décor is delayed")
    demo.ingest(update(3, callback=action))
    demo.ingest(update(4, callback=action))
    assert facts(demo)["facts"]["deadline"] == ""
    start(demo, 202, 5)
    demo.ingest(update(7, 202, callback=action))
    assert facts(demo, 202)["facts"]["problem"] == ""
    start(demo, uid=8)
    current = payload(demo)["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    demo.ingest(update(10, text="Custom problem"))
    demo.ingest(update(11, callback=current))
    assert facts(demo)["facts"]["problem"] == ""
    assert "wait" in payload(demo)["text"].lower()


def test_reset_delete_and_scenario_switch_clear_intake(demo):
    start(demo)
    choose(demo, 3, "Décor is delayed")
    demo.ingest(update(4, text="/reset"))
    assert facts(demo) is None
    choose(demo, 5, "Start a conversation")
    demo.ingest(update(6, callback="demo:courier"))
    assert facts(demo) is None
    demo.ingest(update(7, callback="demo:talk"))
    demo.ingest(update(8, text="/delete"))
    assert facts(demo) is None
    assert not rows(demo, "demo_sessions")


def test_provider_failure_preserves_answers_and_question_buttons(demo):
    start(demo)
    choose(demo, 3, "Hampers haven't arrived")
    demo.ingest(update(4, text="deadline tomorrow"))

    async def fail(context):
        raise RuntimeError("sensitive provider failure")

    demo.model.intake_reply = fail
    asyncio.run(demo.step())
    assert "unavailable" in payload(demo)["text"]
    choose(demo, 5, "Date/time not decided yet")
    assert facts(demo)["facts"]["problem"] == "Hampers haven't arrived"
    assert "sensitive" not in json.dumps(rows(demo, "outbox"))


def test_reset_during_free_text_request_suppresses_late_fact_changes(demo):
    start(demo)
    demo.ingest(update(3, text="question"))

    async def during(context):
        demo.ingest(update(4, text="/reset"))
        return IntakeReply(
            message="DISCARDED_RESPONSE",
            facts=IntakeFacts(problem="DISCARDED_RESPONSE"),
        )

    demo.model.intake_reply = during
    asyncio.run(demo.step())
    assert facts(demo) is None
    assert "DISCARDED_RESPONSE" not in json.dumps(rows(demo, "outbox"))


def test_intake_isolated_and_retention_cleans_it(demo):
    start(demo)
    choose(demo, 3, "Décor is delayed")
    start(demo, 202, 4)
    demo.ingest(update(6, 202, "My fictional question"))
    asyncio.run(demo.step())
    assert "Décor is delayed" not in json.dumps(demo.model.contexts)
    with demo.store.tx() as db:
        db.execute("UPDATE demo_sessions SET updated=0 WHERE chat=101")
    demo.cleanup()
    assert facts(demo) is None
    assert facts(demo, 202)


def test_typed_answer_invitation_does_not_advance_and_unknowns_not_guessed(demo):
    start(demo)
    choose(demo, 3, "I'll type my answer")
    assert facts(demo)["facts"]["problem"] == ""
    demo.model.result = IntakeReply(
        message="We'll keep the deadline unconfirmed.",
        facts=IntakeFacts(problem="Choosing music", deadline="Not decided"),
    )
    demo.ingest(update(4, text="Choosing music; deadline not decided"))
    asyncio.run(demo.step())
    assert facts(demo)["facts"]["deadline"] == "Not decided"
    assert "Who should I coordinate" in payload(demo)["text"]


def test_expired_model_request_restores_current_question(demo):
    start(demo)
    choose(demo, 3, "Décor is delayed")
    demo.ingest(update(4, text="12 November 2026 at 4 pm IST"))
    with demo.store.tx() as db:
        db.execute("UPDATE demo_turns SET status='processing',lease=0")
    assert not asyncio.run(demo.step())
    assert "interrupted" in payload(demo)["text"]
    choose(demo, 5, "Date/time not decided yet")
    assert facts(demo)["facts"]["problem"] == "Décor is delayed"
    assert not demo.model.contexts


def test_signed_intake_webhook_to_message_outbox_and_transport(tmp_path):
    from fastapi.testclient import TestClient
    from tarang.app import create_app

    class Telegram:
        def __init__(self):
            self.sent = []

        async def call(self, method, body):
            if method == "sendMessage":
                self.sent.append(body)
            return {"message_id": 1}

    settings = Settings(
        database=str(tmp_path / "web.sqlite3"),
        public_demo=True,
        allowed=frozenset(),
        telegram_mode="webhook",
        webhook_secret="test-secret",
    )
    telegram = Telegram()
    app = create_app(settings, model=Model(), telegram=telegram, run_worker=False)
    client = TestClient(app)
    assert client.post("/api/intake-check").status_code == 401
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    for event in [update(1, text="/start demo"), update(2, callback="demo:talk")]:
        assert (
            client.post("/telegram/webhook", json=event, headers=headers).status_code
            == 200
        )
        asyncio.run(app.state.engine.send_one())
    action = telegram.sent[-1]["reply_markup"]["inline_keyboard"][0][0]["callback_data"]
    event = update(3, callback=action)
    assert client.post("/telegram/webhook", json=event).status_code == 403
    assert (
        client.post("/telegram/webhook", json=event, headers=headers).status_code == 200
    )
    asyncio.run(app.state.engine.send_one())
    assert "When does this" in telegram.sent[-1]["text"]
    assert len(telegram.sent) == 3
    assert all(row["state"] == "sent" for row in rows(app.state.demo, "outbox"))
    assert not rows(app.state.demo, "commitments")


def test_keyboard_selections_use_same_flow_and_respect_pending_answer(demo):
    demo.ingest(update(1, 42, "/talk"))  # first command shows disclosure
    assert not rows(demo, "demo_turns")
    demo.ingest(update(2, 42, "/talk"))
    assert facts(demo, 42)["phase"] == "collect"
    demo.ingest(update(3, 42, "/choose " + "9" * 5000))
    assert facts(demo, 42)["facts"]["problem"] == ""
    demo.ingest(update(4, 42, "/choose 1"))
    assert facts(demo, 42)["facts"]["problem"] == "Décor is delayed"
    demo.ingest(update(5, 42, "Custom deadline"))
    demo.ingest(update(6, 42, "/choose 1"))
    assert facts(demo, 42)["facts"]["deadline"] == ""
    asyncio.run(demo.step())
    for uid in range(7, 13):
        demo.ingest(update(uid, 42, "/choose 1"))
    assert facts(demo, 42)["phase"] == "review"
    demo.ingest(update(13, 42, "/choose 1"))
    assert facts(demo, 42)["phase"] == "investigated"
    demo.ingest(update(14, 42, "/choose 1"))
    assert facts(demo, 42)["phase"] == "feedback"
    assert not rows(demo, "operations")
