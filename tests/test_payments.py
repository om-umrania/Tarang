import asyncio
import copy
import json
import time

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from tarang.app import create_app
from tarang.config import Settings
from tarang.engine import Engine
from tarang.payments import BankBeneficiary, DocumentedPayoutResult, Payments
from tarang.schema import Decision, Operation
from tarang.store import Store


class Model:
    async def decide(self, context):
        return Decision(
            reason="Within the configured courier delegation",
            message="Prepare courier payment",
            outcome="200 hampers received",
            owner="venue verifier",
            next_check_seconds=600,
            operation=Operation(
                key="courier",
                kind="payment",
                recipient="Courier",
                category="courier",
                amount_paise=120000,
                specification="200 hampers delivery",
                expires_in_seconds=600,
            ),
        )


class Telegram:
    async def call(self, method, payload):
        return {}


@pytest.fixture
def ready(demo_database):
    settings = Settings(
        database=demo_database,
        speech_key="",
        model_key="",
        webhook_secret="",
        allowed=frozenset({42}),
        public_demo=False,
        operator_token="test-token",
        bot_token="",
        telegram_mode="webhook",
    )
    store = Store(settings.database)
    engine = Engine(store, settings, Model(), Telegram())
    with store.tx() as db:
        db.execute(
            "INSERT INTO budgets VALUES('courier',500000,120000,1,'200 hampers delivery','Courier','payment')"
        )
    engine.ingest(
        {
            "update_id": 1,
            "message": {
                "from": {"id": 42},
                "chat": {"id": 42, "type": "private"},
                "text": "Handle the courier recovery",
            },
        }
    )
    asyncio.run(engine.step())
    oid = store.snapshot()["operations"][0]["id"]
    beneficiary = BankBeneficiary(
        recipient="Courier",
        verified=True,
        payee_name="Test Vendor",
        account_number="123456789012",
        branch_code="SBIN0011123",
    )
    return settings, store, Payments(store), oid, beneficiary


def response(packet, status="SCHEDULED"):
    req = packet["request"]
    return {
        "clientReferenceId": req["clientReferenceId"],
        "paymentReferenceId": "test-payment-reference",
        "payeeName": req["payeeName"],
        "accountNumber": "********9012",
        "amount": req["amount"],
        "mode": req["mode"],
        "status": status,
    }


def test_authorised_request_and_stable_reference(ready):
    _, store, rail, oid, beneficiary = ready
    packet = rail.prepare(oid, beneficiary)
    again = rail.prepare(oid, beneficiary)
    assert packet == again
    assert packet["executed"] is False
    assert packet["request"]["amount"]["value"] == 120000
    assert packet["url"].endswith("/payouts/v3/payments/banks")
    assert packet["mode"] == "documented-response"
    # No bank account or credential is retained in snapshot metadata/ledger.
    assert beneficiary.account_number not in json.dumps(store.snapshot())
    with store.tx() as db:
        assert beneficiary.account_number not in str(
            db.execute("SELECT value FROM metadata").fetchall()
        )
    changed = beneficiary.model_copy(update={"account_number": "123456789013"})
    with pytest.raises(ValueError, match="details changed"):
        rail.prepare(oid, changed)


@pytest.mark.parametrize(
    "state", ["approval", "rejected", "expired", "succeeded", "failed"]
)
def test_not_authorised_or_terminal_is_blocked(ready, state):
    _, store, rail, oid, beneficiary = ready
    with store.tx() as db:
        db.execute("UPDATE operations SET state=? WHERE id=?", (state, oid))
    with pytest.raises(ValueError):
        rail.prepare(oid, beneficiary)


@pytest.mark.parametrize("status", ["SCHEDULED", "PENDING", "PROCESSING", "PROCESSED"])
def test_pending_remains_reserved_and_cannot_verify_outcome(ready, status):
    _, store, rail, oid, beneficiary = ready
    packet = rail.prepare(oid, beneficiary)
    result = rail.record(
        oid,
        DocumentedPayoutResult(endpoint="create", response=response(packet, status)),
    )
    assert result["state"] == "unknown"
    assert result["next_observation"]["owner"] == "operator"
    assert result["real_payment"] is False
    with store.tx() as db:
        assert db.execute("SELECT verifies FROM evidence").fetchone()["verifies"] == 0
        assert (
            db.execute("SELECT next_check FROM commitments").fetchone()["next_check"]
            <= time.time() + 61
        )
        assert (
            db.execute("SELECT state FROM operations").fetchone()["state"] == "unknown"
        )


def test_status_success_and_no_late_overwrite(ready):
    _, store, rail, oid, beneficiary = ready
    packet = rail.prepare(oid, beneficiary)
    rail.record(
        oid, DocumentedPayoutResult(endpoint="create", response=response(packet))
    )
    result = rail.record(
        oid,
        DocumentedPayoutResult(
            endpoint="status", response={"payments": [response(packet, "SUCCESS")]}
        ),
    )
    assert result["state"] == "succeeded" and not result["real_payment"]
    assert store.snapshot()["commitments"][0]["state"] == "open"
    with pytest.raises(ValueError):
        rail.record(
            oid,
            DocumentedPayoutResult(
                endpoint="create", response=response(packet, "FAILED")
            ),
        )


@pytest.mark.parametrize(
    "field,value",
    [
        ("clientReferenceId", "wrong"),
        ("amount", {"currency": "INR", "value": 1200}),
        ("payeeName", "Other Vendor"),
        ("mode", "NEFT"),
        ("accountNumber", "*****0000"),
        ("status", "APPROVED"),
        ("fees", {"currency": "INR", "value": 10}),
    ],
)
def test_response_mismatch_rejected(ready, field, value):
    _, store, rail, oid, beneficiary = ready
    packet = rail.prepare(oid, beneficiary)
    data = copy.deepcopy(response(packet))
    data[field] = value
    with pytest.raises(ValueError):
        rail.record(oid, DocumentedPayoutResult(endpoint="create", response=data))
    assert store.snapshot()["operations"][0]["state"] == "operator_pending"
    assert not store.snapshot()["evidence"]


def test_pause_expiry_and_recipient_binding(ready):
    _, store, rail, oid, beneficiary = ready
    with pytest.raises(ValueError):
        rail.prepare(oid, beneficiary.model_copy(update={"recipient": "Other Vendor"}))
    with store.tx() as db:
        db.execute("UPDATE commitments SET paused=1")
    with pytest.raises(ValueError):
        rail.prepare(oid, beneficiary)
    with store.tx() as db:
        db.execute("UPDATE commitments SET paused=0")
        db.execute("UPDATE operations SET expires=0")
    with pytest.raises(ValueError):
        rail.prepare(oid, beneficiary)


def test_operator_routes_and_no_network_execution_route(ready):
    settings, _, _, oid, beneficiary = ready
    app = create_app(settings, Model(), Telegram(), run_worker=False)
    with TestClient(app) as client:
        url = f"/api/payments/{oid}/prepare"
        assert client.post(url, json=beneficiary.model_dump()).status_code == 401
        auth = {"Authorization": "Bearer test-token"}
        packet = client.post(url, headers=auth, json=beneficiary.model_dump()).json()
        result = client.post(
            f"/api/payments/{oid}/documented-result",
            headers=auth,
            json={"endpoint": "create", "response": response(packet)},
        ).json()
        assert result["state"] == "unknown"
        assert (
            client.post(f"/api/payments/{oid}/execute", headers=auth).status_code == 404
        )


def test_unverified_beneficiary_cannot_enter():
    with pytest.raises(ValidationError):
        BankBeneficiary(
            recipient="Courier",
            verified=False,
            payee_name="Test Vendor",
            account_number="123456789012",
            branch_code="SBIN0011123",
        )


def test_revoked_delegation_blocks_preparation(ready):
    _, store, rail, oid, beneficiary = ready
    with store.tx() as db:
        db.execute("UPDATE budgets SET delegated=0")
    with pytest.raises(ValueError, match="Current delegation"):
        rail.prepare(oid, beneficiary)


def test_exact_approval_allows_request_after_delegation_removed(ready):
    settings, store, rail, oid, beneficiary = ready
    with store.tx() as db:
        db.execute("UPDATE budgets SET delegated=0")
        db.execute("UPDATE operations SET state='approval' WHERE id=?", (oid,))
    engine = Engine(store, settings, Model(), Telegram())
    engine.ingest(
        {
            "update_id": 2,
            "callback_query": {
                "id": "approval-test",
                "from": {"id": 42},
                "message": {"chat": {"id": 42, "type": "private"}},
                "data": f"approve:{oid}",
            },
        }
    )
    asyncio.run(engine.step())
    assert rail.prepare(oid, beneficiary)["executed"] is False


def test_settings_diagnostics_do_not_include_credentials():
    private = "synthetic-diagnostic-secret"
    settings = Settings(
        database=private,
        speech_key=private,
        model_key=private,
        bot_token=private,
        webhook_secret=private,
        operator_token=private,
        whatsapp_app_secret=private,
        whatsapp_verify_token=private,
        group_bridge_token=private,
    )
    assert private not in repr(settings)


def test_failed_payout_does_not_close_fulfilment(ready):
    _, store, rail, oid, beneficiary = ready
    packet = rail.prepare(oid, beneficiary)
    result = rail.record(
        oid,
        DocumentedPayoutResult(endpoint="create", response=response(packet, "FAILED")),
    )
    assert result["state"] == "failed"
    assert store.snapshot()["commitments"][0]["state"] == "open"
