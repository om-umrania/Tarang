"""Synthetic webhook journey; fake model/Telegram, real PostgreSQL when configured."""

import asyncio
import json
import os
from pathlib import Path

from fastapi.testclient import TestClient

from tarang.app import create_app
from tarang.config import Settings
from test_engine import Model, Telegram, decision, operation, update


def test_conversation_saved_evidence_and_restart(demo_database):
    settings = Settings(
        database=demo_database,
        allowed=frozenset({42}),
        public_demo=False,
        operator_token="fixture-operator",
        webhook_secret="fixture-webhook",
        telegram_mode="webhook",
        bot_token="",
        model_key="",
        speech_key="",
        whatsapp_enabled=False,
        group_enabled=False,
    )
    model, telegram = Model(decision(operation())), Telegram()
    app = create_app(settings, model, telegram, run_worker=False)
    engine = app.state.engine
    expected_postgres = bool(os.getenv("TARANG_TEST_POSTGRES"))
    assert engine.store.postgres is expected_postgres
    version = "SQLite"
    if expected_postgres:
        with engine.store.tx() as db:
            version = db.execute("SELECT version()").fetchone()[0]
            assert "PostgreSQL" in version
            assert (
                db.execute("SELECT current_schema()")
                .fetchone()[0]
                .startswith("tarang_test_")
            )
    auth = {"Authorization": "Bearer fixture-operator"}
    webhook = {"X-Telegram-Bot-Api-Secret-Token": "fixture-webhook"}
    stages = []

    def snapshot(client, stage):
        response = client.get(
            "/api/dashboard", headers=auth, params={"scope": "workspace", "chat": 42}
        )
        assert response.status_code == 200
        assert response.headers["cache-control"] == "private, no-store"
        data = response.json()
        stages.append(
            {
                "stage": stage,
                "commitment_state": data["commitment"]["state"]
                if data["commitment"]
                else None,
                "operation_states": [op["state"] for op in data["operations"]],
                "delivery": data["delivery"],
            }
        )
        return data

    def pump():
        async def run():
            for _ in range(20):
                if not await engine.step():
                    break
            else:
                raise AssertionError("Event queue did not drain")
            for _ in range(20):
                if not await engine.send_one():
                    break
            else:
                raise AssertionError("Outbox did not drain")

        asyncio.run(run())

    with TestClient(app) as client:
        assert client.get("/api/dashboard").status_code == 401
        assert client.post("/telegram/webhook", json=update()).status_code == 403
        assert snapshot(client, "unauthenticated_rejected")["messages"] == []
        assert (
            client.put(
                "/api/budget",
                headers=auth,
                json={
                    "category": "courier",
                    "ceiling_paise": 500000,
                    "autonomous_limit_paise": 120000,
                    "delegate_spend": False,
                    "recipient": "Courier",
                    "kind": "payment",
                    "scope": "200 hampers local delivery",
                },
            ).status_code
            == 200
        )
        for _ in range(2):
            assert (
                client.post(
                    "/telegram/webhook", headers=webhook, json=update()
                ).status_code
                == 200
            )
        received = snapshot(client, "received")
        assert len(received["messages"]) == 1
        pump()
        approved = snapshot(client, "approval_requested")
        assert approved["operations"][0]["state"] == "approval"
        assert approved["delivery"] == {"sent": 1}
        assert model.calls == 1
        cid, oid = approved["commitment"]["id"], approved["operations"][0]["id"]
        assert any(
            method == "sendMessage" and "Approval #" in payload["text"]
            for method, payload in telegram.sent
        )
        assert (
            client.post(
                "/telegram/webhook",
                headers=webhook,
                json=update(2, user=99, callback=f"approve:{oid}"),
            ).status_code
            == 200
        )
        pump()
        assert (
            snapshot(client, "unauthorised_chat_rejected")["operations"][0]["state"]
            == "approval"
        )
        for _ in range(2):
            assert (
                client.post(
                    "/telegram/webhook",
                    headers=webhook,
                    json=update(3, callback=f"approve:{oid}"),
                ).status_code
                == 200
            )
        model.decision = decision()
        pump()
        data = snapshot(client, "approved_once")
        assert data["operations"][0]["state"] == "operator_pending"
        assert (
            len([d for d in data["decisions"] if d["kind"] == "scoped_approval"]) == 1
        )
        for number, command, paused in ((4, "/pause", 1), (5, "/resume", 0)):
            assert (
                client.post(
                    "/telegram/webhook", headers=webhook, json=update(number, command)
                ).status_code
                == 200
            )
            pump()
            assert snapshot(client, command)["commitment"]["paused"] == paused
        evidence = {
            "commitment_id": cid,
            "operation_id": oid,
            "source": "Synthetic courier fixture",
            "mode": "illustrative-fixture",
            "content": "Fixture payment reconciled; physical receipt not yet verified.",
            "result": "succeeded",
        }
        assert client.post("/api/evidence", json=evidence).status_code == 401
        response = client.post("/api/evidence", headers=auth, json=evidence)
        assert response.status_code == 200
        payment_eid = response.json()["id"]
        pump()
        data = snapshot(client, "operation_reconciled_outcome_open")
        assert data["operations"][0]["state"] == "succeeded"
        assert data["commitment"]["state"] == "open"
        response = client.post(
            "/api/evidence",
            headers=auth,
            json={
                "commitment_id": cid,
                "source": "Synthetic venue verifier",
                "mode": "illustrative-fixture",
                "content": "Fixture: all 200 hampers received intact at the venue.",
                "verifies_outcome": True,
            },
        )
        assert response.status_code == 200
        outcome_eid = response.json()["id"]
        model.decision = decision(close=[outcome_eid])
        pump()
        final = snapshot(client, "rehearsal_closed")
        assert final["commitment"]["state"] == "closed"
        assert {e["id"] for e in final["evidence"]} == {payment_eid, outcome_eid}
        assert any("Rehearsal outcome closed" in m["text"] for m in final["messages"])
        assert all(
            m["status"] == "sent" for m in final["messages"] if m["direction"] == "out"
        )
        assert any(d["kind"] == "evidence_recorded" for d in final["decisions"])
        other = client.get(
            "/api/dashboard", headers=auth, params={"scope": "workspace", "chat": 99}
        ).json()
        assert other["messages"] == [] and other["evidence"] == []
        assert client.get("/dashboard").status_code == 200

    restarted = create_app(settings, Model(decision()), Telegram(), run_worker=False)
    restarted.state.engine.recover()
    with TestClient(restarted) as client:
        recovered = snapshot(client, "reopened_app_same_database")
        for field in (
            "messages",
            "commitment",
            "operations",
            "decisions",
            "evidence",
            "delivery",
        ):
            assert recovered[field] == final[field]
        assert client.get("/api/dashboard").status_code == 401

    artifact = os.getenv("TARANG_E2E_ARTIFACT")
    if artifact:
        assert expected_postgres, "PostgreSQL verification artifact must use PostgreSQL"
        Path(artifact).write_text(
            json.dumps(
                {
                    "verification_kind": "synthetic integration test; NOT live Telegram or hosted verification",
                    "database_engine": "PostgreSQL",
                    "database_version": version,
                    "isolation": "temporary database cluster and unique per-test schema; schema removed after test",
                    "transport": "authenticated FastAPI TestClient webhook; fake Telegram sendMessage adapter",
                    "model": "deterministic fixture",
                    "stages": stages,
                    "checks": [
                        "webhook and operator authentication",
                        "duplicate webhook deduplication",
                        "wrong-chat approval rejected",
                        "single-use scoped approval",
                        "operator evidence API persistence",
                        "operation success does not close outcome",
                        "verified fixture evidence allows labelled rehearsal closure",
                        "selected-chat isolation",
                        "dashboard assets served",
                        "fresh app/store reload retains messages, decisions, evidence and delivery",
                    ],
                    "evidence": final["evidence"],
                    "messages": final["messages"],
                    "decisions": final["decisions"],
                    "restart_fields_equal": True,
                    "live_verification": "not performed: Telegram service/client, OpenRouter, Render, Vercel proxy, browser refresh and real partner rails",
                },
                indent=2,
            )
            + "\n"
        )
