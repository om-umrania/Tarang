import asyncio
import time
import pytest
from fastapi.testclient import TestClient
from tarang.app import create_app
from tarang.config import Settings
from tarang.group_monitor import GroupMonitor
from tarang.schema import GroupBatch, GroupReview
from tarang.store import Store


class Model:
    def __init__(self):
        self.calls = 0
        self.fail = False
        self.invalid = False

    async def review_group(self, context):
        self.calls += 1
        if self.fail:
            raise RuntimeError("provider_unavailable")
        m = context["messages"][0]
        return GroupReview.model_validate(
            {
                "summary": "Proposed date needs confirmation",
                "wedding_date_status": "unknown",
                "facts": (
                    []
                    if m["kind"] != "text"
                    else [
                        {
                            "event": "Mehendi",
                            "date_text": "12 November",
                            "status": "proposed",
                            "source": {
                                "message_id": 999 if self.invalid else m["id"],
                                "quote": m["body"],
                            },
                        }
                    ]
                ),
                "conflicts": [],
                "questions": ["What is the confirmed wedding ceremony date?"],
            }
        )


@pytest.fixture
def setup(tmp_path):
    settings = Settings(
        database=str(tmp_path / "group.sqlite3"),
        group_enabled=True,
        group_id="chosen@g.us",
        group_bridge_token="bridge-token",
        operator_token="operator",
        bot_token="",
    )
    model = Model()
    app = create_app(settings, model=model, run_worker=False)
    return TestClient(app), app.state.group_monitor, model


def batch(
    mid="1", group="chosen@g.us", kind="text", text="Proposed mehendi 12 November"
):
    return {
        "group_id": group,
        "connected": True,
        "messages": [
            {
                "external_id": mid,
                "source_id": "original",
                "sender": "sender",
                "text": text,
                "sent_at": time.time(),
                "kind": kind,
            }
        ],
    }


def post(client, body, token="bridge-token"):
    return client.post(
        "/whatsapp/group-batch", json=body, headers={"Authorization": "Bearer " + token}
    )


def due(monitor):
    with monitor.store.tx() as db:
        state = monitor.read_state(db)
        state["next_run"] = 0
        monitor.save_state(db, state)


def test_auth_group_filter_and_dedup(setup):
    c, m, _ = setup
    assert post(c, batch(), token="wrong").status_code == 403
    assert post(c, batch(group="other@g.us")).status_code == 400
    assert post(c, batch()).json()["accepted"] == 1
    assert post(c, batch()).json()["accepted"] == 0
    assert c.get("/api/group-monitor").status_code == 401


def test_hourly_cursor_restart_and_no_empty_model_calls(setup, monkeypatch):
    c, m, model = setup
    clock = [time.time()]
    monkeypatch.setattr("tarang.group_monitor.time.time", lambda: clock[0])
    post(c, batch())
    asyncio.run(m.step())
    assert model.calls == 1
    assert m.status()["state"]["cursor"] == 1
    post(c, batch("2", text="Proposed mehendi 13 November"))
    asyncio.run(m.step())
    assert model.calls == 1
    restarted = GroupMonitor(Store(m.settings.database), m.settings, model)
    asyncio.run(restarted.step())
    assert model.calls == 1
    clock[0] += 3599
    asyncio.run(restarted.step())
    assert model.calls == 1
    clock[0] += 1
    asyncio.run(restarted.step())
    assert model.calls == 2
    due(restarted)
    asyncio.run(restarted.step())
    assert model.calls == 2
    assert len(m.store.snapshot()["group_runs"]) == 2


def test_failure_never_advances_cursor_and_stale_source_visible(setup):
    c, m, model = setup
    post(c, batch())
    model.fail = True
    asyncio.run(m.step())
    assert m.status()["state"]["cursor"] == 0
    assert m.status()["state"]["failures"] == 1
    with m.store.tx() as db:
        state = m.read_state(db)
        state["last_received"] = time.time() - 500
        m.save_state(db, state)
    assert m.status()["source_status"] == "stale_or_disconnected"
    model.fail = False
    due(m)
    asyncio.run(m.step())
    assert m.status()["state"]["cursor"] == 1


def test_invalid_sources_not_saved(setup):
    c, m, model = setup
    post(c, batch())
    model.invalid = True
    asyncio.run(m.step())
    assert m.store.snapshot()["group_runs"] == []
    assert m.status()["state"]["cursor"] == 0


def test_group_change_fails_closed_and_no_operations(setup):
    c, m, _ = setup
    post(c, batch())
    asyncio.run(m.step())
    assert m.store.snapshot()["operations"] == []
    assert m.store.snapshot()["outbox"] == []
    m.settings.group_id = "different@g.us"
    with pytest.raises(ValueError):
        m.status()


def test_inconsistent_conflict_report_is_rejected(setup):
    c, m, model = setup
    original = model.review_group

    async def inconsistent(context):
        result = await original(context)
        result.facts[0].status = "conflicting"
        return result

    model.review_group = inconsistent
    post(c, batch())
    asyncio.run(m.step())
    assert m.store.snapshot()["group_runs"] == []
    assert m.status()["state"]["cursor"] == 0


def test_stalled_model_has_wall_clock_timeout(setup):
    c, m, model = setup

    async def stalled(context):
        await asyncio.sleep(1)

    model.review_group = stalled
    m.model_timeout = 0.001
    post(c, batch())
    asyncio.run(m.step())
    assert m.status()["state"]["error"] == "TimeoutError"
    assert m.status()["state"]["cursor"] == 0


def test_concurrent_workers_claim_only_one_review(setup):
    c, m, model = setup
    original = model.review_group

    async def slow(context):
        await asyncio.sleep(0.01)
        return await original(context)

    model.review_group = slow
    post(c, batch())
    other = GroupMonitor(Store(m.settings.database), m.settings, model)

    async def run():
        await asyncio.gather(m.step(), other.step())

    asyncio.run(run())
    assert model.calls == 1
    assert len(m.store.snapshot()["group_runs"]) == 1
