import json
import re
import time
from zoneinfo import ZoneInfo
from datetime import datetime, timezone
from .store import Store


class Engine:
    def __init__(self, store, settings, model, telegram):
        self.store, self.settings, self.model, self.telegram = (
            store,
            settings,
            model,
            telegram,
        )

    def ingest(self, update):
        message = update.get("message") or update.get("callback_query", {}).get(
            "message", {}
        )
        sender = update.get("callback_query", {}).get("from") or message.get("from", {})
        chat = message.get("chat", {})
        if (
            sender.get("id") not in self.settings.allowed
            or chat.get("type") != "private"
            or chat.get("id") != sender.get("id")
        ):
            return False
        uid = update.get("update_id")
        if not isinstance(uid, int):
            return False
        with self.store.tx() as db:
            db.execute(
                "INSERT OR IGNORE INTO commitments(chat,outcome,owner,next_check) VALUES(?,?,?,?)",
                (
                    chat["id"],
                    "Clarify wedding outcome",
                    str(sender["id"]),
                    time.time() + 3600,
                ),
            )
            c = db.execute(
                "SELECT * FROM commitments WHERE chat=?", (chat["id"],)
            ).fetchone()
            if db.execute(
                "SELECT 1 FROM events WHERE key=?", (f"telegram:{uid}",)
            ).fetchone():
                return True
            text = update.get("message", {}).get("text", "").strip()
            if text.split(" ")[0].lower() == "/pause":
                db.execute("UPDATE commitments SET paused=1 WHERE id=?", (c["id"],))
            Store.event(db, f"telegram:{uid}", c["id"], "telegram", update)
        return True

    def recover(self):
        with self.store.tx() as db:
            db.execute("UPDATE events SET status='pending' WHERE status='processing'")
            # Telegram has no sendMessage idempotency key. Ambiguous sends need review.
            db.execute("UPDATE outbox SET state='unknown' WHERE state='sending'")

    def schedule(self):
        now = time.time()
        with self.store.tx() as db:
            for c in db.execute(
                "SELECT * FROM commitments WHERE state='open' AND next_check<=? AND paused=0",
                (now,),
            ).fetchall():
                Store.event(
                    db,
                    f"clock:{c['id']}:{c['next_check']}",
                    c["id"],
                    "clock",
                    {
                        "observed_at": datetime.now(timezone.utc).isoformat(),
                        "type": "due_check",
                    },
                )
                db.execute(
                    "UPDATE commitments SET next_check=? WHERE id=?",
                    (now + 3600, c["id"]),
                )
            for op in db.execute(
                "SELECT * FROM operations WHERE state='approval' AND expires<=?", (now,)
            ).fetchall():
                db.execute(
                    "UPDATE operations SET state='expired' WHERE id=?", (op["id"],)
                )
                Store.log(
                    db, op["commitment"], "approval_expired", {"operation_id": op["id"]}
                )
                Store.event(
                    db,
                    f"expiry:{op['id']}",
                    op["commitment"],
                    "runtime",
                    {"approval_expired": op["id"]},
                )

    def _approval(self, db, event, c, query):
        data = query.get("data", "").split(":")
        if (
            len(data) != 2
            or data[0] not in ("approve", "reject")
            or not data[1].isdigit()
        ):
            return "This approval button is invalid."
        op = db.execute(
            "SELECT * FROM operations WHERE id=? AND commitment=?",
            (int(data[1]), c["id"]),
        ).fetchone()
        if not op or op["state"] != "approval" or op["expires"] <= time.time():
            return "This proposal is no longer awaiting approval. Ask for the current status."
        if c["paused"]:
            return "Tarang is paused. Resume before approving new actions."
        state = "operator_pending" if data[0] == "approve" else "rejected"
        db.execute("UPDATE operations SET state=? WHERE id=?", (state, op["id"]))
        Store.log(
            db,
            c["id"],
            "scoped_approval",
            {
                "operation_id": op["id"],
                "actor": query["from"]["id"],
                "decision": data[0],
                "exact_proposal": json.loads(op["proposal"]),
            },
        )
        Store.event(
            db,
            f"approval:{op['id']}",
            c["id"],
            "runtime",
            {"operation": op["id"], "state": state},
        )
        return (
            "Approved once for this exact proposal. It is queued for the operator; no real payment or booking has been executed."
            if state == "operator_pending"
            else "Proposal rejected. No action will be executed."
        )

    async def step(self):
        self.schedule()
        with self.store.tx() as db:
            event = db.execute(
                "SELECT * FROM events WHERE status='pending' AND due<=? ORDER BY id LIMIT 1",
                (time.time(),),
            ).fetchone()
            if not event:
                return False
            event = dict(event)
            c = dict(
                db.execute(
                    "SELECT * FROM commitments WHERE id=?", (event["commitment"],)
                ).fetchone()
            )
            payload = json.loads(event["payload"])
            if event["source"] == "telegram":
                query = payload.get("callback_query")
                text = payload.get("message", {}).get("text", "")
                command = text.split()[0].lower() if text else ""
                reply = None
                if query:
                    reply = self._approval(db, event, c, query)
                elif command in ("/pause", "/resume"):
                    paused = command == "/pause"
                    db.execute(
                        "UPDATE commitments SET paused=?,next_check=? WHERE id=?",
                        (paused, time.time() + 30, c["id"]),
                    )
                    if not paused:
                        db.execute(
                            "UPDATE events SET status='pending' WHERE commitment=? AND status='held'",
                            (c["id"],),
                        )
                    reply = (
                        "Paused new coordination. Already queued operator requests may be in flight; inspect the operator console before taking over."
                        if paused
                        else "Monitoring resumed. I will check again in 30 seconds."
                    )
                    Store.log(
                        db,
                        c["id"],
                        "pause" if paused else "resume",
                        {"actor": payload["message"]["from"]["id"]},
                    )
                elif command == "/status":
                    operations = [
                        dict(r)
                        for r in db.execute(
                            "SELECT id,state FROM operations WHERE commitment=?",
                            (c["id"],),
                        )
                    ]
                    reply = f"Outcome: {c['outcome']}\nState: {c['state']}; paused: {bool(c['paused'])}\nOperations: {json.dumps(operations)}"
                elif c["paused"]:
                    reply = "Tarang is paused. Send /resume to continue, or /status to inspect pending work."
                if reply is not None:
                    Store.message(db, f"event:{event['id']}", c["chat"], reply)
                    db.execute(
                        "UPDATE events SET status='done' WHERE id=?", (event["id"],)
                    )
                    return True
            if c["paused"] or c["state"] != "open":
                db.execute("UPDATE events SET status='held' WHERE id=?", (event["id"],))
                return True
            group_context = None
            if self.settings.group_enabled:
                group_run = db.execute(
                    "SELECT created,result FROM group_runs ORDER BY id DESC LIMIT 1"
                ).fetchone()
                group_state = db.execute(
                    "SELECT value FROM metadata WHERE key='group_monitor'"
                ).fetchone()
                gs = json.loads(group_state["value"]) if group_state else {}
                if gs.get("group_id") == self.settings.group_id:
                    group_context = {
                        "last_review_at": group_run["created"] if group_run else None,
                        "review": (
                            json.loads(group_run["result"]) if group_run else None
                        ),
                        "source_fresh": bool(gs.get("source_connected"))
                        and time.time() - gs.get("last_received", 0) < 180,
                        "note": "Source claims only; not verified authority or complete chat history.",
                    }
            context = {
                "wedding_group_review": group_context,
                "now_utc": datetime.now(timezone.utc).isoformat(),
                "commitment": c,
                "incoming": {"source": event["source"], "payload": payload},
                "operations": [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM operations WHERE commitment=?", (c["id"],)
                    )
                ],
                "evidence": [
                    dict(r)
                    for r in db.execute(
                        "SELECT * FROM evidence WHERE commitment=? ORDER BY id DESC LIMIT 30",
                        (c["id"],),
                    )
                ],
                "budgets": [dict(r) for r in db.execute("SELECT * FROM budgets")],
                "recent_sent_messages": [
                    json.loads(r["payload"])["text"]
                    for r in db.execute(
                        "SELECT payload FROM outbox WHERE chat=? AND state='sent' ORDER BY id DESC LIMIT 5",
                        (c["chat"],),
                    )
                ],
                "recent_events": [
                    dict(r)
                    for r in db.execute(
                        "SELECT source,payload FROM events WHERE commitment=? AND id<? ORDER BY id DESC LIMIT 12",
                        (c["id"], event["id"]),
                    )
                ],
            }
            db.execute(
                "UPDATE events SET status='processing',attempts=attempts+1 WHERE id=?",
                (event["id"],),
            )
        try:
            decision = await self.model.decide(context)
            self.apply(event, c, decision)
        except Exception as exc:
            # Exception strings may embed URL credentials. Log only the class.
            with self.store.tx() as db:
                attempts = event["attempts"] + 1
                db.execute(
                    "UPDATE events SET status=?,due=? WHERE id=?",
                    (
                        "pending" if attempts < 3 else "failed",
                        time.time() + 60 * attempts,
                        event["id"],
                    ),
                )
                Store.log(
                    db,
                    c["id"],
                    "decision_error",
                    {
                        "event_id": event["id"],
                        "error_type": type(exc).__name__,
                        "provider_code": (
                            str(exc)
                            if re.fullmatch(
                                r"model_http_[0-9]{3}|model_not_configured", str(exc)
                            )
                            else None
                        ),
                        "attempt": attempts,
                    },
                )
                if attempts >= 3:
                    Store.message(
                        db,
                        f"failed:{event['id']}",
                        c["chat"],
                        "I could not reliably process that update. No new action was authorised. The operator can inspect the failed event; monitoring remains scheduled.",
                    )
        return True

    def apply(self, event, c, d):
        now = time.time()
        with self.store.tx() as db:
            current = db.execute(
                "SELECT * FROM commitments WHERE id=?", (c["id"],)
            ).fetchone()
            if current["paused"] or current["state"] != "open":
                db.execute("UPDATE events SET status='held' WHERE id=?", (event["id"],))
                return
            source_text = (
                json.loads(event["payload"]).get("message", {}).get("text", "")
            )
            if event[
                "source"
            ] == "telegram" and source_text.lstrip().upper().startswith(
                ("TEST ONLY:", "E2E TEST")
            ):
                Store.log(
                    db,
                    c["id"],
                    "test_decision",
                    {
                        "event_id": event["id"],
                        "decision": d.model_dump(),
                        "effects_suppressed": True,
                    },
                )
                text = (
                    d.message
                    if not (d.operation or d.close_with_evidence)
                    else "The model proposed an action during this test. It was blocked; no real operation or closure was applied."
                )
                Store.message(
                    db,
                    f"event:{event['id']}",
                    c["chat"],
                    "[Test only — real commitment and schedule unchanged]\n"
                    + (text or "Test processed.")[:3900],
                )
                db.execute("UPDATE events SET status='done' WHERE id=?", (event["id"],))
                return
            notes = []
            buttons = None
            state = "open"
            if d.close_with_evidence:
                evidence = [
                    db.execute(
                        "SELECT * FROM evidence WHERE id=? AND commitment=? AND verifies=1",
                        (eid, c["id"]),
                    ).fetchone()
                    for eid in d.close_with_evidence
                ]
                pending = db.execute(
                    "SELECT count(*) FROM operations WHERE commitment=? AND state IN ('approval','operator_pending','unknown')",
                    (c["id"],),
                ).fetchone()[0]
                if all(evidence) and not pending and not d.operation:
                    state = "closed"
                    notes.append(
                        "Rehearsal outcome closed using labelled illustrative evidence."
                        if any(
                            e["mode"] in ("illustrative-fixture", "documented-response")
                            for e in evidence
                        )
                        else "Outcome closed against operator-verified evidence."
                    )
                else:
                    notes.append(
                        "Closure blocked: verified outcome evidence and reconciliation of pending operations are required."
                    )
            if d.operation:
                op = d.operation
                old = db.execute(
                    "SELECT * FROM operations WHERE commitment=? AND key=?",
                    (c["id"], op.key),
                ).fetchone()
                if not old and op.amount_paise > 0:
                    # Model-generated keys are not trustworthy idempotency evidence.
                    # Match the actual financial intent as well as the key.
                    for previous in db.execute(
                        "SELECT * FROM operations WHERE commitment=? AND amount>0",
                        (c["id"],),
                    ):
                        proposal = json.loads(previous["proposal"])
                        fields = (
                            "kind",
                            "recipient",
                            "category",
                            "amount_paise",
                            "specification",
                        )
                        if all(
                            proposal[field] == getattr(op, field) for field in fields
                        ):
                            old = previous
                            break
                if old:
                    notes.append(
                        f"Operation #{old['id']} already exists ({old['state']}); no duplicate request created."
                    )
                else:
                    budget = db.execute(
                        "SELECT * FROM budgets WHERE category=?", (op.category,)
                    ).fetchone()
                    used = db.execute(
                        "SELECT COALESCE(SUM(amount),0) FROM operations WHERE category=? AND state IN ('approval','operator_pending','unknown','succeeded')",
                        (op.category,),
                    ).fetchone()[0]
                    unresolved = db.execute(
                        "SELECT count(*) FROM operations WHERE commitment=? AND amount>0 AND state IN ('approval','operator_pending','unknown')",
                        (c["id"],),
                    ).fetchone()[0]
                    spend = op.amount_paise > 0
                    money_kind = op.kind in ("payment", "booking", "shipment")
                    blocked = (
                        (money_kind and not spend)
                        or (not money_kind and spend)
                        or (
                            spend
                            and (
                                unresolved
                                or not budget
                                or used + op.amount_paise > budget["ceiling"]
                            )
                        )
                    )
                    if blocked:
                        notes.append(
                            "Action blocked: confirm total cost, approved category budget, and reconcile pending spending first."
                        )
                    else:
                        # Scope matching is exact, not model interpretation of delegation.
                        delegated = (
                            spend
                            and budget["delegated"]
                            and op.amount_paise <= budget["cap"]
                            and op.specification == budget["scope"]
                            and op.recipient == budget["recipient"]
                            and op.kind == budget["kind"]
                        )
                        status = (
                            "approval"
                            if spend and not delegated
                            else "operator_pending"
                        )
                        cursor = db.execute(
                            "INSERT INTO operations(commitment,key,proposal,category,amount,state,expires) VALUES(?,?,?,?,?,?,?)",
                            (
                                c["id"],
                                op.key,
                                op.model_dump_json(),
                                op.category,
                                op.amount_paise,
                                status,
                                now + op.expires_in_seconds,
                            ),
                        )
                        oid = cursor.lastrowid
                        Store.log(
                            db,
                            c["id"],
                            "operation_intent",
                            {
                                "operation_id": oid,
                                "state": status,
                                "mode": "operator-assisted",
                                "proposal": op.model_dump(),
                            },
                        )
                        if status == "approval":
                            notes.append(
                                f"Approval #{oid}: {op.kind} · {op.recipient}\nINR {op.amount_paise/100:.2f} · {op.category}\n{op.specification}\nValid for {op.expires_in_seconds//60} minutes. Operator-assisted; approval does not execute a real transaction."
                            )
                            buttons = [
                                [
                                    {
                                        "text": "Approve once",
                                        "callback_data": f"approve:{oid}",
                                    },
                                    {
                                        "text": "Reject",
                                        "callback_data": f"reject:{oid}",
                                    },
                                ]
                            ]
                        else:
                            notes.append(
                                f"Operator request #{oid} queued ({op.kind}). No partner action is confirmed yet."
                            )
            db.execute(
                "UPDATE commitments SET outcome=?,owner=?,state=?,next_check=? WHERE id=?",
                (d.outcome, d.owner, state, now + d.next_check_seconds, c["id"]),
            )
            Store.log(
                db,
                c["id"],
                "model_decision",
                {
                    "event_id": event["id"],
                    "model": self.settings.model,
                    "decision": d.model_dump(),
                    "runtime_notes": notes,
                },
            )
            # Keep deterministic execution/approval/closure facts visibly separate from draft wording.
            if d.message or notes:
                text = d.message if not (d.operation or d.close_with_evidence) else ""
                if notes:
                    text += "\n\n" + "\n".join(notes)
                if state == "open":
                    text += f'\n\nNext check saved: {datetime.fromtimestamp(now+d.next_check_seconds,ZoneInfo(self.settings.timezone)).strftime("%d %b %H:%M:%S %Z")}. '
                if self.settings.free_host and state == "open":
                    text += "Free-host checks may run late if the service is asleep."
                Store.message(
                    db, f"event:{event['id']}", c["chat"], text[:4096], buttons
                )
            db.execute("UPDATE events SET status='done' WHERE id=?", (event["id"],))

    def add_evidence(self, e):
        with self.store.tx() as db:
            c = db.execute(
                "SELECT * FROM commitments WHERE id=?", (e.commitment_id,)
            ).fetchone()
            if not c:
                raise ValueError("Unknown commitment")
            if e.operation_id:
                op = db.execute(
                    "SELECT * FROM operations WHERE id=? AND commitment=?",
                    (e.operation_id, e.commitment_id),
                ).fetchone()
                if not op or op["state"] not in ("operator_pending", "unknown"):
                    raise ValueError(
                        "Operation is not authorised or awaiting reconciliation"
                    )
                if e.result != "observation":
                    db.execute(
                        "UPDATE operations SET state=? WHERE id=?",
                        (e.result, e.operation_id),
                    )
            elif e.result != "observation":
                raise ValueError("A result requires an operation ID")
            eid = db.execute(
                "INSERT INTO evidence(commitment,operation,source,mode,content,verifies,created) VALUES(?,?,?,?,?,?,?)",
                (
                    e.commitment_id,
                    e.operation_id,
                    e.source,
                    e.mode,
                    e.content,
                    e.verifies_outcome,
                    time.time(),
                ),
            ).lastrowid
            Store.log(
                db,
                e.commitment_id,
                "evidence_recorded",
                {"evidence_id": eid, "mode": e.mode, "result": e.result},
            )
            Store.event(
                db,
                f"evidence:{eid}",
                e.commitment_id,
                "operator",
                {"evidence_id": eid, "mode": e.mode, "result": e.result},
            )
            return eid

    async def send_one(self):
        with self.store.tx() as db:
            row = db.execute(
                "SELECT * FROM outbox WHERE state='pending' ORDER BY id LIMIT 1"
            ).fetchone()
            if not row:
                return False
            row = dict(row)
            db.execute("UPDATE outbox SET state='sending' WHERE id=?", (row["id"],))
        state = "sent"
        try:
            await self.telegram.call("sendMessage", json.loads(row["payload"]))
        except Exception:
            state = "unknown"
        with self.store.tx() as db:
            db.execute("UPDATE outbox SET state=? WHERE id=?", (state, row["id"]))
            Store.log(
                db, None, "telegram_delivery", {"outbox_id": row["id"], "state": state}
            )
        return True
