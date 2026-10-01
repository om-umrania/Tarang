import asyncio
import hashlib
import hmac
import json
import time
import pytest
from fastapi.testclient import TestClient
from tarang.app import create_app
from tarang.config import Settings
from tarang.schema import ConflictReport


class Model:
    def __init__(self):
        self.context = None
        self.report = ConflictReport(conflicts=[])

    async def detect_conflicts(self, context):
        self.context = context
        return self.report


@pytest.fixture
def setup(tmp_path):
    settings = Settings(
        database=str(tmp_path / "wa.sqlite3"),
        whatsapp_enabled=True,
        whatsapp_app_secret="secret",
        whatsapp_verify_token="verify",
        whatsapp_phone_id="123",
        whatsapp_routes={"111": "wedding-a", "222": "wedding-b"},
        operator_token="operator",
        bot_token="",
    )
    model = Model()
    app = create_app(settings, model=model, run_worker=False)
    return TestClient(app), app.state.monitor, model


def payload(mid="one", sender="111", text="Setup at 4pm", phone="123", kind="text"):
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "changes": [
                    {
                        "field": "messages",
                        "value": {
                            "metadata": {"phone_number_id": phone},
                            "messages": [
                                {
                                    "id": mid,
                                    "from": sender,
                                    "timestamp": str(int(time.time())),
                                    "type": kind,
                                    "text": {"body": text},
                                }
                            ],
                        },
                    }
                ]
            }
        ],
    }


def post(client, body, valid=True):
    raw = json.dumps(body).encode()
    sig = hmac.new(b"secret", raw, hashlib.sha256).hexdigest() if valid else "wrong"
    return client.post(
        "/whatsapp/webhook",
        content=raw,
        headers={"X-Hub-Signature-256": "sha256=" + sig},
    )


def test_webhook_auth_and_durable_dedup(setup):
    client, monitor, _ = setup
    assert (
        client.get(
            "/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=verify&hub.challenge=123"
        ).text
        == "123"
    )
    assert (
        client.get(
            "/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=bad"
        ).status_code
        == 403
    )
    assert post(client, payload(), False).status_code == 403
    assert post(client, payload()).status_code == 200
    assert post(client, payload()).status_code == 200
    assert len(monitor.store.snapshot()["conversation_messages"]) == 1
    monitor.settings.whatsapp_enabled = False
    assert post(client, payload()).status_code == 503


def test_allowlist_phone_media_and_scope_isolation(setup):
    client, monitor, model = setup
    post(client, payload(sender="unknown"))
    post(client, payload(phone="wrong"))
    assert monitor.store.snapshot()["conversation_messages"] == []
    post(client, payload("other", sender="222"))
    post(client, payload())
    post(client, payload("audio", kind="audio"))
    asyncio.run(monitor.step())
    asyncio.run(monitor.step())
    assert [m["sender"] for m in model.context["messages"]] == ["111"]
    assert (
        monitor.store.snapshot()["conversation_messages"][0]["status"] == "unsupported"
    )


def conflict(ids=(1, 2), quote="Setup at 4pm"):
    return ConflictReport.model_validate(
        {
            "conflicts": [
                {
                    "kind": "schedule",
                    "summary": "Possible time mismatch",
                    "sources": [
                        {"message_id": ids[0], "quote": quote},
                        {"message_id": ids[1], "quote": "Setup at 6pm"},
                    ],
                    "clarification": "Which setup time is agreed?",
                }
            ]
        }
    )


def test_grounded_conflict_review_and_no_actions(setup):
    client, monitor, model = setup
    post(client, payload())
    asyncio.run(monitor.step())
    post(client, payload("two", text="Setup at 6pm"))
    model.report = conflict()
    asyncio.run(monitor.step())
    snapshot = monitor.store.snapshot()
    assert len(snapshot["conflicts"]) == 1
    assert snapshot["operations"] == snapshot["outbox"] == []
    assert (
        client.patch(
            "/api/conflicts/1", json={"state": "dismissed", "note": "Revision accepted"}
        ).status_code
        == 401
    )
    assert (
        client.patch(
            "/api/conflicts/1",
            json={"state": "dismissed", "note": "Revision accepted"},
            headers={"Authorization": "Bearer operator"},
        ).status_code
        == 200
    )
    assert monitor.store.snapshot()["conflicts"][0]["state"] == "dismissed"


@pytest.mark.parametrize(
    "report", [conflict((999, 2)), conflict(quote="invented quote"), conflict((2, 2))]
)
def test_invalid_evidence_fails_closed_with_bounded_retry(setup, report):
    client, monitor, model = setup
    post(client, payload())
    asyncio.run(monitor.step())
    post(client, payload("two", text="Setup at 6pm"))
    model.report = report
    for _ in range(3):
        with monitor.store.tx() as db:
            db.execute("UPDATE conversation_messages SET due=0")
        asyncio.run(monitor.step())
    snapshot = monitor.store.snapshot()
    assert snapshot["conflicts"] == []
    assert snapshot["conversation_messages"][0]["status"] == "failed"
    assert snapshot["conversation_messages"][0]["attempts"] == 3


def test_recovery_and_route_revocation(setup):
    client, monitor, model = setup
    post(client, payload())
    with monitor.store.tx() as db:
        db.execute("UPDATE conversation_messages SET status='processing'")
    monitor.recover()
    monitor.settings.whatsapp_routes = {}
    # Not ready means no processing at all.
    asyncio.run(monitor.step())
    assert model.context is None
    monitor.settings.whatsapp_routes = {"222": "wedding-b"}
    asyncio.run(monitor.step())
    assert monitor.store.snapshot()["conversation_messages"][0]["status"] == "revoked"


def test_oversized_and_malformed_webhooks(setup):
    client, monitor, _ = setup
    assert client.post("/whatsapp/webhook", content=b"x" * 100001).status_code == 413
    assert (
        post(client, {"object": "whatsapp_business_account", "entry": None}).status_code
        == 400
    )
    assert monitor.store.snapshot()["conversation_messages"] == []


def test_explicit_group_payload_is_not_ingested(setup):
    client, monitor, _ = setup
    body = payload()
    body["entry"][0]["changes"][0]["value"]["messages"][0][
        "group_id"
    ] = "unapproved-group"
    assert post(client, body).status_code == 200
    assert monitor.store.snapshot()["conversation_messages"] == []
