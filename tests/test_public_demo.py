import asyncio
import json
import time

import pytest
from fastapi.testclient import TestClient

from tarang.app import create_app
from tarang.config import Settings
from tarang.public_demo import DemoReply, PublicDemo
from tarang.store import Store


def update(uid, chat=101, text="", callback=None):
    message = {
        "from": {"id": chat},
        "chat": {"id": chat, "type": "private"},
        "text": text,
    }
    if callback:
        return {
            "update_id": uid,
            "callback_query": {
                "id": str(uid),
                "from": {"id": chat},
                "message": message,
                "data": callback,
            },
        }
    return {"update_id": uid, "message": message}


class Model:
    def __init__(self):
        self.contexts = []

    async def demo_reply(self, context):
        self.contexts.append(context)
        return DemoReply(
            message="I'd preserve the original deadline and ask the approver before agreeing."
        )


@pytest.fixture
def demo(demo_database):
    settings = Settings(
        database=demo_database,
        public_demo=True,
        allowed=frozenset({42}),
    )
    return PublicDemo(Store(settings.database), settings, Model())


def rows(demo, table):
    with demo.store.tx() as db:
        return [dict(r) for r in db.execute(f"SELECT * FROM {table}")]


def start(demo, uid=1, chat=101):
    assert demo.ingest(update(uid, chat, "/start demo"))
    assert demo.ingest(update(uid + 1, chat, callback="demo:decor"))


def button(demo):
    return json.loads(rows(demo, "outbox")[-1]["payload"])["reply_markup"][
        "inline_keyboard"
    ][0][0]["callback_data"]


def test_explanation_receives_reached_approvals_without_future_events(demo):
    start(demo)
    next_button = button(demo)
    demo.ingest(update(3, text="What has happened?"))
    assert asyncio.run(demo.step())
    initial = demo.model.contexts[-1]["reached_guided_steps"]
    assert len(initial) == 1
    assert "approval recorded" not in " ".join(initial)
    for uid in range(4, 9):
        demo.ingest(update(uid, callback=next_button))
        next_button = button(demo)
    demo.ingest(update(9, text="Is approval still pending?"))
    assert asyncio.run(demo.step())
    reached = demo.model.contexts[-1]["reached_guided_steps"]
    assert len(reached) == 6
    assert "₹2,000" in reached[2]
    assert "Approval recorded for ₹2,000" in reached[3]
    assert "entrance lights don't work" in reached[4]
    assert "payment remains unverified" in reached[5]


def test_visitors_are_isolated_from_private_wedding_and_each_other(demo):
    with demo.store.tx() as db:
        db.execute(
            "INSERT INTO commitments(chat,outcome,owner,next_check) VALUES(42,'SECRET wedding','SECRET owner',?)",
            (time.time() + 3600,),
        )
        db.execute(
            "INSERT INTO budgets VALUES('SECRET category',500000,500000,1,'SECRET scope','SECRET payee','payment')"
        )
        db.execute(
            "INSERT INTO group_runs(created,through_id,result) VALUES(?,1,?)",
            (time.time(), '{"private":"SECRET group"}'),
        )
    start(demo)
    demo.ingest(update(3, text="visitor-one-only"))
    assert asyncio.run(demo.step())
    start(demo, 4, 202)
    demo.ingest(update(6, 202, "Explain the approval"))
    assert asyncio.run(demo.step())
    assert "SECRET" not in json.dumps(demo.model.contexts)
    assert "visitor-one-only" not in json.dumps(demo.model.contexts[-1])
    assert not rows(demo, "operations")
    assert not rows(demo, "events")
    assert len(rows(demo, "commitments")) == 1
    assert {r["chat"] for r in rows(demo, "outbox")} == {101, 202}


def test_consent_required_before_model_and_no_automatic_followups(demo):
    demo.ingest(update(1, text="Private information"))
    demo.ingest(update(2, text="Answer me"))
    assert not rows(demo, "demo_turns")
    assert not asyncio.run(demo.step())
    assert not rows(demo, "commitments")
    assert "Private information" not in json.dumps(rows(demo, "demo_sessions"))


def test_both_guided_journeys_never_create_real_operations(demo):
    for uid, scenario in [(1, "decor"), (20, "courier")]:
        demo.ingest(update(uid, text="/start demo"))
        demo.ingest(update(uid + 1, callback="demo:" + scenario))
        for i in range(5 if scenario == "decor" else 4):
            action = button(demo)
            assert len(action.encode()) <= 64
            demo.ingest(update(uid + 2 + i, callback=action))
        assert "payment" in rows(demo, "outbox")[-1]["payload"].lower()
    for table in ("commitments", "operations", "budgets", "events", "evidence"):
        assert not rows(demo, table)


def test_stale_duplicate_and_cross_user_buttons_do_not_advance(demo):
    start(demo)
    action = button(demo)
    demo.ingest(update(3, callback=action))
    demo.ingest(update(3, callback=action))
    demo.ingest(update(4, callback=action))
    assert rows(demo, "demo_sessions")[0]["stage"] == "1"
    start(demo, 5, 202)
    demo.ingest(update(7, 202, callback=action))
    assert rows(demo, "demo_sessions")[1]["stage"] == "0"
    demo.ingest(update(8, 202, callback="approve:1"))
    assert not rows(demo, "operations")


def test_model_budget_survives_reset_and_global_limit(demo):
    start(demo)
    for n in range(10):
        demo.ingest(update(3 + n, text="Question"))
        asyncio.run(demo.step())
    demo.ingest(update(20, text="/reset"))
    demo.ingest(update(21, callback="demo:decor"))
    demo.ingest(update(22, text="One more"))
    assert not asyncio.run(demo.step())
    assert len(demo.model.contexts) == 10
    with demo.store.tx() as db:
        db.execute("UPDATE demo_usage SET count=100 WHERE chat=0 AND kind='model'")
    start(demo, 30, 202)
    demo.ingest(update(32, 202, "Question"))
    assert not asyncio.run(demo.step())


def test_one_pending_question_and_restart_preserves_history(demo):
    start(demo)
    demo.ingest(update(3, text="first"))
    demo.ingest(update(4, text="second"))
    assert len(rows(demo, "demo_turns")) == 1
    restarted = PublicDemo(demo.store, demo.settings, demo.model)
    asyncio.run(restarted.step())
    restarted.ingest(update(5, text="third"))
    asyncio.run(restarted.step())
    assert demo.model.contexts[-1]["history"][0]["body"] == "first"


def test_delete_during_model_call_suppresses_late_reply(demo):
    start(demo)
    demo.ingest(update(3, text="question"))

    async def during(context):
        demo.ingest(update(4, text="/delete"))
        return DemoReply(message="late reply must disappear")

    demo.model.demo_reply = during
    asyncio.run(demo.step())
    assert not rows(demo, "demo_turns")
    assert not rows(demo, "demo_sessions")
    assert "late reply" not in json.dumps(rows(demo, "outbox"))
    assert len(rows(demo, "outbox")) == 1


def test_provider_failure_is_visible_and_no_automatic_retry(demo):
    start(demo)
    demo.ingest(update(3, text="question"))

    async def fail(context):
        raise RuntimeError("sensitive provider detail")

    demo.model.demo_reply = fail
    asyncio.run(demo.step())
    assert rows(demo, "demo_turns")[0]["status"] == "failed"
    assert "haven't applied" in rows(demo, "outbox")[-1]["payload"]
    assert "sensitive" not in json.dumps(rows(demo, "outbox"))
    assert not asyncio.run(demo.step())


def test_transient_failure_recovers_without_error_message(demo):
    start(demo)
    demo.ingest(update(3, text="Explain the approval"))
    calls = []

    async def recover(context):
        calls.append(context)
        if len(calls) == 1:
            raise RuntimeError("model_http_503")
        return DemoReply(message="The quoted amount needs your approval.")

    demo.model.demo_reply = recover
    assert asyncio.run(demo.step())
    assert len(calls) == 2
    assert calls[0] == calls[1]
    turn = rows(demo, "demo_turns")[0]
    assert turn["status"] == "done"
    assert turn["reply"] == "The quoted amount needs your approval."
    assert "couldn't finish" not in json.dumps(rows(demo, "outbox"))


def test_transient_failure_is_bounded_and_does_not_claim_success(demo):
    start(demo)
    demo.ingest(update(3, text="Approve the charge"))
    calls = []

    async def fail(context):
        calls.append(context)
        raise TimeoutError()

    demo.model.demo_reply = fail
    assert asyncio.run(demo.step())
    assert len(calls) == 2
    assert rows(demo, "demo_turns")[0]["status"] == "failed"
    payload = json.loads(rows(demo, "outbox")[-1]["payload"])
    assert "haven't applied" in payload["text"]
    assert "guided scenarios" not in payload["text"]
    assert "reply_markup" not in payload
    assert not asyncio.run(demo.step())


def test_reset_during_transient_failure_cancels_retry(demo):
    start(demo)
    demo.ingest(update(3, text="question"))
    calls = []

    async def reset(context):
        calls.append(context)
        demo.ingest(update(4, text="/reset"))
        raise TimeoutError()

    demo.model.demo_reply = reset
    assert asyncio.run(demo.step())
    assert len(calls) == 1
    assert not rows(demo, "demo_turns")


def test_lease_blocks_other_worker_and_expired_request_not_replayed(demo):
    start(demo)
    demo.ingest(update(3, text="question"))
    with demo.store.tx() as db:
        db.execute(
            "UPDATE demo_turns SET status='processing',lease=?", (time.time() + 60,)
        )
    assert not asyncio.run(demo.step())
    with demo.store.tx() as db:
        db.execute("UPDATE demo_turns SET lease=0")
    assert not asyncio.run(demo.step())
    assert rows(demo, "demo_turns")[0]["status"] == "failed"
    assert not demo.model.contexts


def test_disabled_group_and_owner_routes(demo):
    assert not demo.ingest(update(1, 42, "/status"))
    start(demo, 2, 42)
    assert demo.ingest(update(4, 42, "/live"))
    assert not demo.ingest(update(5, 42, "/status"))
    group = update(6)
    group["message"]["chat"]["type"] = "group"
    assert not demo.ingest(group)
    demo.settings.public_demo = False
    assert demo.ingest(update(7, text="/start"))
    assert not rows(demo, "demo_sessions")


def test_retention_removes_only_expired_demo(demo):
    start(demo)
    start(demo, 3, 202)
    with demo.store.tx() as db:
        db.execute("UPDATE demo_sessions SET updated=0 WHERE chat=101")
    demo.cleanup()
    assert [r["chat"] for r in rows(demo, "demo_sessions")] == [202]
    assert {r["chat"] for r in rows(demo, "outbox")} == {202}


def test_signed_webhook_routes_public_demo_and_keeps_owner_restricted(tmp_path):
    settings = Settings(
        database=str(tmp_path / "web.sqlite3"),
        public_demo=True,
        allowed=frozenset({42}),
        telegram_mode="webhook",
        webhook_secret="test-secret",
    )
    app = create_app(settings, model=Model(), run_worker=False)
    client = TestClient(app)
    payload = update(1, text="/start demo")
    assert client.post("/telegram/webhook", json=payload).status_code == 403
    headers = {"X-Telegram-Bot-Api-Secret-Token": "test-secret"}
    assert (
        client.post("/telegram/webhook", json=payload, headers=headers).status_code
        == 200
    )
    assert not rows(app.state.demo, "commitments")
    client.post("/telegram/webhook", json=update(2, 42, "/status"), headers=headers)
    assert len(rows(app.state.demo, "commitments")) == 1
    assert client.get("/api/state").status_code == 401
