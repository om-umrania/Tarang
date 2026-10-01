import asyncio
import hmac
import hashlib
import fcntl
import json
import time
from contextlib import asynccontextmanager, suppress
from pathlib import Path
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import HTMLResponse, PlainTextResponse
from .config import Settings
from .store import Store
from .adapters import OpenRouter, Telegram
from .engine import Engine
from .schema import EvidenceInput, BudgetInput, CheckInput, ConflictReview
from .whatsapp import ConflictMonitor
from .group_monitor import GroupMonitor
from .schema import GroupBatch


def create_app(settings=None, model=None, telegram=None, run_worker=True):
    settings = settings or Settings()
    store = Store(settings.database)
    telegram = telegram or Telegram(settings.bot_token)
    engine = Engine(store, settings, model or OpenRouter(settings), telegram)

    monitor = ConflictMonitor(store, settings, engine.model)
    group_monitor = GroupMonitor(store, settings, engine.model)

    async def worker():
        engine.recover()
        monitor.recover()
        while True:
            try:
                await engine.step()
                await engine.send_one()
                await monitor.step()
            except Exception as exc:
                with store.tx() as db:
                    Store.log(db, None, "worker_error", {"type": type(exc).__name__})
            await asyncio.sleep(1)

    async def group_worker():
        while True:
            try:
                await group_monitor.step()
            except Exception as exc:
                with store.tx() as db:
                    Store.log(
                        db, None, "group_worker_error", {"type": type(exc).__name__}
                    )
                await asyncio.sleep(55)
            await asyncio.sleep(5)

    async def poll():
        while True:
            try:
                with store.tx() as db:
                    row = db.execute(
                        "SELECT value FROM metadata WHERE key='telegram_offset'"
                    ).fetchone()
                updates = await telegram.call(
                    "getUpdates",
                    {
                        "offset": int(row["value"]) if row else 0,
                        "timeout": 25,
                        "allowed_updates": ["message", "callback_query"],
                    },
                )
                for update in updates:
                    engine.ingest(update)
                    if "callback_query" in update:
                        await telegram.call(
                            "answerCallbackQuery",
                            {
                                "callback_query_id": update["callback_query"]["id"],
                                "text": "Received; checking this proposal.",
                            },
                        )
                    with store.tx() as db:
                        db.execute(
                            "INSERT INTO metadata(key,value) VALUES('telegram_offset',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
                            (str(update["update_id"] + 1),),
                        )
            except Exception:
                await asyncio.sleep(5)

    async def lead_worker():
        if not store.postgres:
            await worker()
            return
        import psycopg

        # During Render rolling deploys the new process waits for the old leader.
        # HTTP health can succeed before leadership transfers.
        while True:
            connection = None
            try:
                connection = psycopg.connect(settings.database, autocommit=True)
                acquired = connection.execute(
                    "SELECT pg_try_advisory_lock(7349282)"
                ).fetchone()[0]
                if acquired:
                    engine.recover()
                    monitor.recover()
                    while True:
                        connection.execute("SELECT 1")
                        await engine.step()
                        await engine.send_one()
                        await monitor.step()
                        await asyncio.sleep(1)
            except asyncio.CancelledError:
                raise
            except Exception:
                pass
            finally:
                if connection:
                    connection.close()
            await asyncio.sleep(3)

    @asynccontextmanager
    async def lifespan(app):
        tasks = []
        lock = None
        if run_worker:
            if not store.postgres:
                lock = open(settings.database + ".worker.lock", "a")
                try:
                    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    lock.close()
                    raise RuntimeError(
                        "Only one worker may use this database"
                    ) from None
            tasks.append(asyncio.create_task(lead_worker()))
            tasks.append(asyncio.create_task(group_worker()))
            if settings.telegram_mode == "polling" and settings.bot_token:
                tasks.append(asyncio.create_task(poll()))
        yield
        for task in tasks:
            task.cancel()
        for task in tasks:
            with suppress(asyncio.CancelledError):
                await task
        if lock:
            lock.close()

    app = FastAPI(
        title="Tarang prototype",
        lifespan=lifespan,
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.state.engine = engine
    app.state.monitor = monitor
    app.state.group_monitor = group_monitor

    def authorised(value):
        if not settings.operator_token or not hmac.compare_digest(
            value or "", f"Bearer {settings.operator_token}"
        ):
            raise HTTPException(401, "Operator authentication required")

    @app.get("/health")
    def health():
        with store.tx() as db:
            db.execute("SELECT 1")
        return {"status": "ok", "prototype": True}

    @app.get("/", response_class=HTMLResponse)
    def console():
        return (Path(__file__).parent / "console.html").read_text()

    @app.post("/telegram/webhook")
    async def webhook(
        request: Request, x_telegram_bot_api_secret_token: str = Header(default="")
    ):
        if (
            settings.telegram_mode != "webhook"
            or not settings.webhook_secret
            or not hmac.compare_digest(
                settings.webhook_secret, x_telegram_bot_api_secret_token
            )
        ):
            raise HTTPException(403, "Invalid webhook")
        raw = await request.body()
        if len(raw) > 100000:
            raise HTTPException(413, "Update too large")
        update = json.loads(raw)
        accepted = engine.ingest(update)
        if accepted and "callback_query" in update:
            with suppress(Exception):
                await telegram.call(
                    "answerCallbackQuery",
                    {
                        "callback_query_id": update["callback_query"]["id"],
                        "text": "Received; checking this proposal.",
                    },
                )
        return {"ok": True}

    @app.get("/whatsapp/webhook", response_class=PlainTextResponse)
    def whatsapp_verify(request: Request):
        q = request.query_params
        if (
            not monitor.ready
            or q.get("hub.mode") != "subscribe"
            or not hmac.compare_digest(
                q.get("hub.verify_token", ""), settings.whatsapp_verify_token
            )
        ):
            raise HTTPException(403, "Invalid verification")
        return q.get("hub.challenge", "")

    @app.post("/whatsapp/webhook")
    async def whatsapp_receive(
        request: Request, x_hub_signature_256: str = Header(default="")
    ):
        if not monitor.ready:
            raise HTTPException(503, "WhatsApp intake is disabled")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 100000:
                raise HTTPException(413, "Webhook too large")
        expected = (
            "sha256="
            + hmac.new(
                settings.whatsapp_app_secret.encode(), raw, hashlib.sha256
            ).hexdigest()
        )
        if not hmac.compare_digest(expected, x_hub_signature_256):
            raise HTTPException(403, "Invalid signature")
        try:
            payload = json.loads(raw)
            if not isinstance(payload, dict):
                raise ValueError()
            monitor.ingest(payload)
        except (ValueError, TypeError, AttributeError):
            raise HTTPException(400, "Invalid webhook body") from None
        return {"ok": True}

    @app.get("/api/whatsapp")
    def whatsapp_status(authorization: str = Header(default="")):
        authorised(authorization)
        return {
            "configured": monitor.ready,
            "mode": "receive-only direct text messages",
            "source_limit": "No existing group history or personal-account access",
            "model_configured": bool(settings.model_key),
            "free_host": settings.free_host,
        }

    @app.patch("/api/conflicts/{conflict_id}")
    def review_conflict(
        conflict_id: int, body: ConflictReview, authorization: str = Header(default="")
    ):
        authorised(authorization)
        with store.tx() as db:
            if not db.execute(
                "SELECT id FROM conflicts WHERE id=?", (conflict_id,)
            ).fetchone():
                raise HTTPException(404, "Conflict not found")
            db.execute(
                "UPDATE conflicts SET state=? WHERE id=?", (body.state, conflict_id)
            )
            Store.log(
                db,
                None,
                "conflict_review",
                {"conflict_id": conflict_id, **body.model_dump()},
            )
        return {"ok": True}

    @app.post("/whatsapp/group-batch")
    async def group_batch(request: Request, authorization: str = Header(default="")):
        if not group_monitor.ready or not hmac.compare_digest(
            authorization, "Bearer " + settings.group_bridge_token
        ):
            raise HTTPException(403, "Group bridge is not authorised")
        raw = bytearray()
        async for chunk in request.stream():
            raw.extend(chunk)
            if len(raw) > 1500000:
                raise HTTPException(413, "Batch too large")
        try:
            batch = GroupBatch.model_validate_json(raw)
            count = group_monitor.ingest(batch)
        except ValueError:
            raise HTTPException(400, "Invalid or unauthorised group batch") from None
        return {"accepted": count}

    @app.get("/api/group-monitor")
    def group_status(authorization: str = Header(default="")):
        authorised(authorization)
        return group_monitor.status()

    @app.get("/api/state")
    def state(authorization: str = Header(default="")):
        authorised(authorization)
        return store.snapshot()

    @app.post("/api/evidence")
    def evidence(body: EvidenceInput, authorization: str = Header(default="")):
        authorised(authorization)
        try:
            return {"id": engine.add_evidence(body)}
        except ValueError as exc:
            raise HTTPException(409, str(exc)) from exc

    @app.post("/api/model-check")
    async def model_check(authorization: str = Header(default="")):
        authorised(authorization)
        # Fixed synthetic data only: never replay private chat state for diagnostics.
        try:
            d = await engine.model.decide(
                {
                    "now_utc": "2026-10-01T00:00:00Z",
                    "commitment": {
                        "outcome": "Synthetic setup verification",
                        "owner": "test operator",
                    },
                    "incoming": {
                        "source": "clock",
                        "payload": {"type": "synthetic_due_check"},
                    },
                    "operations": [],
                    "evidence": [],
                    "budgets": [],
                    "recent_sent_messages": [
                        "Synthetic example: waiting for wedding date."
                    ],
                }
            )
            return {"ok": True, "model": settings.model, "schema_valid": True}
        except RuntimeError as exc:
            import re

            code = (
                str(exc)
                if re.fullmatch(r"model_http_[0-9]{3}|model_not_configured", str(exc))
                else "model_error"
            )
            return {"ok": False, "code": code}
        except Exception as exc:
            return {"ok": False, "code": type(exc).__name__}

    @app.post("/api/check")
    def check(body: CheckInput, authorization: str = Header(default="")):
        authorised(authorization)
        due = time.time() + body.delay_seconds
        with store.tx() as db:
            c = db.execute(
                "SELECT * FROM commitments WHERE id=?", (body.commitment_id,)
            ).fetchone()
            if not c or c["state"] != "open" or c["paused"]:
                raise HTTPException(409, "An open, unpaused commitment is required")
            db.execute(
                "UPDATE commitments SET next_check=? WHERE id=?",
                (due, body.commitment_id),
            )
            Store.log(
                db,
                body.commitment_id,
                "operator_requested_check",
                {"due": due, "delay_seconds": body.delay_seconds},
            )
        return {"due": due}

    @app.put("/api/budget")
    def budget(body: BudgetInput, authorization: str = Header(default="")):
        authorised(authorization)
        with store.tx() as db:
            used = db.execute(
                "SELECT COALESCE(SUM(amount),0) FROM operations WHERE category=? AND state IN ('approval','operator_pending','unknown','succeeded')",
                (body.category,),
            ).fetchone()[0]
            if (
                body.ceiling_paise < used
                or body.autonomous_limit_paise > body.ceiling_paise
            ):
                raise HTTPException(
                    409, "Budget below obligations or cap above ceiling"
                )
            db.execute(
                "INSERT INTO budgets VALUES(?,?,?,?,?,?,?) ON CONFLICT(category) DO UPDATE SET ceiling=excluded.ceiling,cap=excluded.cap,delegated=excluded.delegated,scope=excluded.scope,recipient=excluded.recipient,kind=excluded.kind",
                (
                    body.category,
                    body.ceiling_paise,
                    body.autonomous_limit_paise,
                    body.delegate_spend,
                    body.scope,
                    body.recipient,
                    body.kind,
                ),
            )
            Store.log(db, None, "budget_configured", body.model_dump())
        return {"ok": True}

    return app


app = create_app()
