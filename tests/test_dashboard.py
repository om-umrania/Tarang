"""Dashboard contracts use isolated fixtures, never real Telegram/model calls."""

import asyncio
import json
import sqlite3
import time

import pytest
from fastapi.testclient import TestClient

from tarang.app import create_app
from tarang.config import Settings
from tarang.store import Store
from test_engine import Model, Telegram, decision, operation, update, budget


@pytest.fixture
def dashboard(demo_database):
    settings = Settings(
        database=demo_database,
        allowed=frozenset({42}),
        public_demo=True,
        operator_token="dashboard-test",
        bot_token="",
        model_key="",
        telegram_mode="webhook",
        webhook_secret="webhook-test",
    )
    tg = Telegram()
    app = create_app(settings, Model(decision(operation())), tg, run_worker=False)
    with TestClient(app) as client:
        yield app, client, tg


def read(client, scope=None, chat=None):
    return client.get(
        "/api/dashboard",
        headers={"Authorization": "Bearer dashboard-test"},
        params={"scope": scope, "chat": chat} if scope else {},
    )


def test_dashboard_auth_and_no_store(dashboard):
    _, client, _ = dashboard
    assert client.get("/api/dashboard").status_code == 401
    assert (
        client.get(
            "/api/dashboard", headers={"Authorization": "Bearer wrong"}
        ).status_code
        == 401
    )
    response = read(client)
    assert response.headers["cache-control"] == "private, no-store"
    assert response.headers["vary"] == "Authorization"
    assert response.json()["conversations"] == []
    assert client.get("/dashboard").status_code == 200
    assert client.get("/dashboard.js").status_code == 200
    assert "dashboard-test" not in client.get("/dashboard").text
    for query in ("?scope=demo", "?scope=bad&chat=42", "?scope=demo&chat=-1"):
        assert (
            client.get(
                "/api/dashboard" + query,
                headers={"Authorization": "Bearer dashboard-test"},
            ).status_code
            == 422
        )


def test_telegram_to_approval_to_evidence_dashboard(dashboard):
    app, client, _ = dashboard
    e = app.state.engine
    budget(e, delegated=False)
    response = client.post(
        "/telegram/webhook",
        json=update(),
        headers={"X-Telegram-Bot-Api-Secret-Token": "webhook-test"},
    )
    assert response.status_code == 200
    assert (
        read(client, "workspace", 42).json()["messages"][0]["text"]
        == "Track my hampers"
    )
    asyncio.run(e.step())
    data = read(client, "workspace", 42).json()
    assert data["operations"][0]["state"] == "approval"
    assert data["delivery"]["pending"] == 1
    assert data["commitment"]["state"] == "open"
    asyncio.run(e.send_one())
    assert read(client, "workspace", 42).json()["delivery"]["sent"] == 1
    oid = data["operations"][0]["id"]
    app.state.ingest(update(2, callback=f"approve:{oid}"))
    asyncio.run(e.step())
    data = read(client, "workspace", 42).json()
    assert data["operations"][0]["state"] == "operator_pending"
    assert any(d["kind"] == "scoped_approval" for d in data["decisions"])
    assert any(m["text"] == "Selected: Approve once" for m in data["messages"])
    with e.store.tx() as db:
        db.execute(
            "INSERT INTO evidence(commitment,source,mode,content,verifies,created) VALUES(?,?,?,?,?,?)",
            (
                data["commitment"]["id"],
                "Fixture venue",
                "illustrative-fixture",
                "Only 180 of 200 received",
                0,
                time.time(),
            ),
        )
    data = read(client, "workspace", 42).json()
    assert data["evidence"][0]["content"] == "Only 180 of 200 received"
    assert data["commitment"]["state"] == "open"


def test_demo_capture_isolation_duplicates_and_deletion(dashboard):
    app, client, _ = dashboard
    app.state.ingest(update(1, "Private wedding detail"))
    app.state.ingest(update(2, "/start", user=101))
    callback = update(3, user=101, callback="demo:decor")
    callback["callback_query"]["message"]["reply_markup"] = {
        "inline_keyboard": [
            [{"text": "Try décor rescue", "callback_data": "demo:decor"}]
        ]
    }
    app.state.ingest(callback)
    app.state.ingest(callback)
    app.state.ingest(update(4, "/start", user=202))
    app.state.ingest(update(5, "Another visitor", user=202))
    data = read(client, "demo", 101).json()
    assert len([m for m in data["messages"] if m["direction"] == "in"]) == 2
    assert any(m["text"] == "Selected: Try décor rescue" for m in data["messages"])
    assert "Private wedding detail" not in json.dumps(data)
    assert "Another visitor" not in json.dumps(data)
    assert data["operations"] == [] and data["commitment"] is None
    app.state.ingest(update(6, "/delete", user=101))
    data = read(client, "demo", 101).json()
    assert data["selected"] is None and data["messages"] == []
    with app.state.engine.store.tx() as db:
        assert (
            db.execute("SELECT COUNT(*) FROM demo_messages WHERE chat=101").fetchone()[
                0
            ]
            == 0
        )
    assert read(client, "demo", 202).json()["selected"] is not None


def test_same_chat_demo_and_workspace_do_not_mix(dashboard):
    app, client, _ = dashboard
    app.state.ingest(update(1, "Private wedding detail"))
    app.state.ingest(update(2, "/demo"))
    workspace = read(client, "workspace", 42).json()
    demo = read(client, "demo", 42).json()
    assert "Private wedding detail" not in json.dumps(demo["messages"])
    assert not any("private demo" in m["text"] for m in workspace["messages"])
    app.state.ingest(update(3, "/reset"))
    assert (
        len(
            [
                m
                for m in read(client, "demo", 42).json()["messages"]
                if m["direction"] == "in"
            ]
        )
        == 1
    )


def test_unknown_delivery_not_reported_as_sent(dashboard):
    app, client, tg = dashboard
    app.state.ingest(update(1, "/status"))
    asyncio.run(app.state.engine.step())
    tg.fail = True
    asyncio.run(app.state.engine.send_one())
    data = read(client, "workspace", 42).json()
    assert data["delivery"] == {"unknown": 1}
    assert (
        next(m for m in data["messages"] if m["direction"] == "out")["status"]
        == "unknown"
    )


def test_demo_history_bounded_and_capture_cleanup(dashboard):
    app, client, _ = dashboard
    app.state.ingest(update(1, "/start", user=101))
    with app.state.engine.store.tx() as db:
        for n in range(105):
            db.execute(
                "INSERT INTO demo_messages VALUES(?,?,?,?)",
                (f"fixture:{n}", 101, f"Message {n}", time.time() + n),
            )
    data = read(client, "demo", 101).json()
    assert data["history_limited"]
    assert len([m for m in data["messages"] if m["direction"] == "in"]) == 100
    with app.state.engine.store.tx() as db:
        db.execute("UPDATE demo_sessions SET updated=0 WHERE chat=101")
    app.state.demo.cleanup()
    assert read(client, "demo", 101).json()["messages"] == []


def test_additive_outbox_migration_retains_old_messages(tmp_path):
    path = str(tmp_path / "old.sqlite3")
    with sqlite3.connect(path) as db:
        db.execute(
            "CREATE TABLE outbox(id INTEGER PRIMARY KEY,key TEXT NOT NULL UNIQUE,chat INTEGER NOT NULL,payload TEXT NOT NULL,state TEXT NOT NULL DEFAULT 'pending')"
        )
        db.execute("INSERT INTO outbox(key,chat,payload) VALUES('old',42,'{}')")
    for _ in range(2):
        store = Store(path)
    with store.tx() as db:
        assert (
            db.execute("SELECT created FROM outbox WHERE key='old'").fetchone()[0] == 0
        )
        Store.message(db, "new", 42, "New reply")
        assert (
            db.execute("SELECT created FROM outbox WHERE key='new'").fetchone()[0] > 0
        )
