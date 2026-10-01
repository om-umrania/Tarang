import asyncio
import json
import time
import pytest
from fastapi.testclient import TestClient
from tarang.config import Settings
from tarang.store import Store
from tarang.schema import Decision, Operation, EvidenceInput
from tarang.engine import Engine
from tarang.app import create_app


class Model:
    def __init__(self, decision):
        self.decision = decision
        self.calls = 0

    async def decide(self, context):
        self.calls += 1
        return self.decision


class Telegram:
    def __init__(self, fail=False):
        self.sent = []
        self.fail = fail

    async def call(self, method, payload):
        if self.fail:
            raise TimeoutError("ambiguous")
        self.sent.append((method, payload))
        return {}


def decision(op=None, close=None):
    return Decision(
        reason="Test proposal",
        message="Checking the next step.",
        outcome="200 usable hampers received",
        owner="venue verifier",
        next_check_seconds=30,
        operation=op,
        close_with_evidence=close or [],
    )


def operation(key="courier", amount=120000, recipient="Courier"):
    return Operation(
        key=key,
        kind="payment",
        recipient=recipient,
        category="courier",
        amount_paise=amount,
        specification="200 hampers local delivery",
        expires_in_seconds=600,
    )


def update(n=1, text="Track my hampers", user=42, callback=None):
    m = {"from": {"id": user}, "chat": {"id": user, "type": "private"}, "text": text}
    return {
        "update_id": n,
        **(
            {
                "callback_query": {
                    "id": str(n),
                    "from": {"id": user},
                    "message": m,
                    "data": callback,
                }
            }
            if callback
            else {"message": m}
        ),
    }


@pytest.fixture
def env(tmp_path):
    settings = Settings(
        database=str(tmp_path / "test.sqlite3"),
        allowed=frozenset({42}),
        bot_token="",
        operator_token="test-token",
        telegram_mode="webhook",
        webhook_secret="test-secret",
    )
    store = Store(settings.database)
    model = Model(decision())
    tg = Telegram()
    return Engine(store, settings, model, tg)


def budget(e, delegated=True, ceiling=500000):
    with e.store.tx() as db:
        db.execute(
            "INSERT INTO budgets VALUES(?,?,?,?,?,?,?)",
            (
                "courier",
                ceiling,
                500000,
                delegated,
                "200 hampers local delivery",
                "Courier",
                "payment",
            ),
        )


def step(e):
    asyncio.run(e.step())


def ops(e):
    return e.store.snapshot()["operations"]


def test_duplicate_update_and_operation(env):
    budget(env)
    env.model.decision = decision(operation())
    env.ingest(update())
    env.ingest(update())
    step(env)
    env.ingest(update(2))
    step(env)
    assert len(ops(env)) == 1
    assert ops(env)[0]["state"] == "operator_pending"
    assert env.model.calls == 2


def test_unbudgeted_never_executes(env):
    env.model.decision = decision(operation())
    env.ingest(update())
    step(env)
    assert ops(env) == []


def test_scope_payee_and_single_use_approval(env):
    budget(env)
    env.model.decision = decision(operation(recipient="Different payee"))
    env.ingest(update())
    step(env)
    assert ops(env)[0]["state"] == "approval"
    assert not env.ingest(update(2, user=99, callback="approve:1"))
    env.ingest(update(3, callback="approve:1"))
    step(env)
    assert ops(env)[0]["state"] == "operator_pending"
    env.ingest(update(4, callback="approve:1"))
    step(env)
    step(env)
    approvals = [
        l for l in env.store.snapshot()["ledger"] if l["kind"] == "scoped_approval"
    ]
    assert len(approvals) == 1


def test_expiry_releases_reservation(env):
    budget(env, False)
    env.model.decision = decision(operation())
    env.ingest(update())
    step(env)
    with env.store.tx() as db:
        db.execute("UPDATE operations SET expires=?", (time.time() - 1,))
    env.ingest(update(2, callback="approve:1"))
    step(env)
    assert ops(env)[0]["state"] == "expired"


def test_unknown_blocks_new_spending(env):
    budget(env)
    env.model.decision = decision(operation())
    env.ingest(update())
    step(env)
    env.add_evidence(
        EvidenceInput(
            commitment_id=1,
            operation_id=1,
            source="Timeout observed",
            mode="illustrative-fixture",
            content="Unknown result",
            result="unknown",
        )
    )
    env.model.decision = decision(operation("retry-different-key"))
    step(env)
    assert len(ops(env)) == 1 and ops(env)[0]["state"] == "unknown"


def test_budget_reserved_across_changed_intents(env):
    budget(env, True, 120000)
    env.model.decision = decision(operation())
    env.ingest(update())
    step(env)
    env.add_evidence(
        EvidenceInput(
            commitment_id=1,
            operation_id=1,
            source="fixture receipt",
            mode="illustrative-fixture",
            content="Paid",
            result="succeeded",
        )
    )
    env.model.decision = decision(operation("another"))
    step(env)
    assert len(ops(env)) == 1


def test_closure_requires_verified_evidence(env):
    env.model.decision = decision(close=[999])
    env.ingest(update())
    step(env)
    assert env.store.snapshot()["commitments"][0]["state"] == "open"
    eid = env.add_evidence(
        EvidenceInput(
            commitment_id=1,
            source="venue fixture",
            mode="illustrative-fixture",
            content="200 checked on time, undamaged",
            verifies_outcome=True,
        )
    )
    env.model.decision = decision(close=[eid])
    step(env)
    assert env.store.snapshot()["commitments"][0]["state"] == "closed"
    assert "Rehearsal" in env.store.snapshot()["outbox"][0]["payload"]


def test_unapproved_result_rejected(env):
    budget(env, False)
    env.model.decision = decision(operation())
    env.ingest(update())
    step(env)
    with pytest.raises(ValueError):
        env.add_evidence(
            EvidenceInput(
                commitment_id=1,
                operation_id=1,
                source="fixture",
                mode="illustrative-fixture",
                content="Paid",
                result="succeeded",
            )
        )


def test_restart_due_event_and_ambiguous_delivery(env):
    env.ingest(update())
    step(env)
    with env.store.tx() as db:
        db.execute("UPDATE commitments SET next_check=?", (time.time() - 1,))
        db.execute("UPDATE outbox SET state='sending'")
    restarted = Engine(
        Store(env.settings.database), env.settings, env.model, env.telegram
    )
    restarted.recover()
    step(restarted)
    assert env.model.calls == 2
    assert any(x["state"] == "unknown" for x in restarted.store.snapshot()["outbox"])


def test_pause_is_immediate_and_holds_model_result(env):
    env.ingest(update())
    step(env)
    env.ingest(update(2, "/pause"))
    assert env.store.snapshot()["commitments"][0]["paused"] == 1
    step(env)
    before = env.model.calls
    env.ingest(update(3))
    step(env)
    assert env.model.calls == before


def test_transport_timeout_not_retried(env):
    env.ingest(update())
    step(env)
    env.telegram = Telegram(True)
    asyncio.run(env.send_one())
    assert not asyncio.run(env.send_one())
    assert env.store.snapshot()["outbox"][0]["state"] == "unknown"


def test_api_auth_webhook_and_budget(env):
    app = create_app(env.settings, env.model, env.telegram, run_worker=False)
    client = TestClient(app)
    assert client.get("/api/state").status_code == 401
    assert client.post("/telegram/webhook", json=update()).status_code == 403
    assert (
        client.post(
            "/telegram/webhook",
            json=update(),
            headers={"X-Telegram-Bot-Api-Secret-Token": "test-secret"},
        ).status_code
        == 200
    )
    h = {"Authorization": "Bearer test-token"}
    assert client.get("/api/state", headers=h).status_code == 200
    assert (
        client.put(
            "/api/budget",
            headers=h,
            json={
                "category": "courier",
                "ceiling_paise": 120000,
                "autonomous_limit_paise": 500000,
                "scope": "exact",
                "recipient": "Courier",
                "kind": "payment",
            },
        ).status_code
        == 409
    )


def test_new_model_key_cannot_duplicate_successful_payment(env):
    budget(env)
    env.model.decision = decision(operation())
    env.ingest(update())
    step(env)
    env.add_evidence(
        EvidenceInput(
            commitment_id=1,
            operation_id=1,
            source="fixture receipt",
            mode="illustrative-fixture",
            content="Paid",
            result="succeeded",
        )
    )
    env.model.decision = decision(operation("fresh-key"))
    step(env)
    assert len(ops(env)) == 1


def test_operator_scheduled_check_is_authenticated(env):
    app = create_app(env.settings, env.model, env.telegram, run_worker=False)
    client = TestClient(app)
    env.ingest(update())
    step(env)
    body = {"commitment_id": 1, "delay_seconds": 30}
    assert client.post("/api/check", json=body).status_code == 401
    assert (
        client.post(
            "/api/check", json=body, headers={"Authorization": "Bearer test-token"}
        ).status_code
        == 200
    )
    assert env.store.snapshot()["commitments"][0]["next_check"] <= time.time() + 31
