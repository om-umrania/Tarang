"""Durable hourly group reviews. A separately paired bridge supplies group updates."""

import json
import asyncio
import time
from datetime import datetime, timezone
from .store import Store


class GroupMonitor:
    interval = 3600
    model_timeout = 75

    def __init__(self, store, settings, model):
        self.store, self.settings, self.model = store, settings, model

    @property
    def ready(self):
        return bool(
            self.settings.group_enabled
            and self.settings.group_id
            and self.settings.group_bridge_token
        )

    def read_state(self, db):
        row = db.execute(
            "SELECT value FROM metadata WHERE key='group_monitor'"
        ).fetchone()
        state = (
            json.loads(row["value"])
            if row
            else {"cursor": 0, "next_run": 0, "failures": 0}
        )
        # Changing groups requires a separate database/reset, never mix wedding histories.
        if state.get("group_id", self.settings.group_id) != self.settings.group_id:
            raise ValueError("group_change_requires_separate_store")
        return state

    @staticmethod
    def save_state(db, state):
        db.execute(
            "INSERT INTO metadata(key,value) VALUES('group_monitor',?) ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (json.dumps(state),),
        )

    def ingest(self, batch):
        if not self.ready or batch.group_id != self.settings.group_id:
            raise ValueError("group_not_allowed")
        now = time.time()
        with self.store.tx() as db:
            state = self.read_state(db)
            count = 0
            for m in batch.messages:
                if m.sent_at > now + 300:
                    raise ValueError("future_message_timestamp")
                # Each edited/deleted version is a separate durable observation.
                version = m.external_id
                if db.execute(
                    "SELECT id FROM group_messages WHERE external_id=?", (version,)
                ).fetchone():
                    continue
                db.execute(
                    "INSERT INTO group_messages(external_id,source_id,sender,body,sent_at,received_at,kind) VALUES(?,?,?,?,?,?,?)",
                    (version, m.source_id, m.sender, m.text, m.sent_at, now, m.kind),
                )
                count += 1
            state.update(
                group_id=batch.group_id,
                last_received=now,
                source_connected=batch.connected,
            )
            self.save_state(db, state)
        return count

    def status(self):
        if not self.ready:
            return {
                "enabled": False,
                "source_status": "not_connected",
                "interval_seconds": self.interval,
            }
        with self.store.tx() as db:
            state = self.read_state(db)
            latest = db.execute(
                "SELECT * FROM group_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
        age = time.time() - state.get("last_received", 0)
        return {
            "enabled": True,
            "source_status": (
                "connected"
                if state.get("source_connected") and age < 180
                else "stale_or_disconnected"
            ),
            "interval_seconds": self.interval,
            "state": {k: v for k, v in state.items() if k != "group_id"},
            "latest_review": dict(latest) if latest else None,
        }

    async def step(self):
        if not self.ready:
            return
        now = time.time()
        with self.store.tx() as db:
            state = self.read_state(db)
            if now < state["next_run"]:
                return
            messages = [
                dict(r)
                for r in db.execute(
                    "SELECT * FROM group_messages WHERE id>? ORDER BY id LIMIT 50",
                    (state["cursor"],),
                )
            ]
            bounded = []
            size = 0
            for message in messages:
                if bounded and size + len(message["body"]) > 48000:
                    break
                bounded.append(message)
                size += len(message["body"])
            messages = bounded
            if not messages:
                state.update(next_run=now + self.interval, last_checked=now)
                self.save_state(db, state)
                return
            previous = db.execute(
                "SELECT result FROM group_runs ORDER BY id DESC LIMIT 1"
            ).fetchone()
            prior = json.loads(previous["result"]) if previous else None
            context_messages = list(messages)
            if prior:
                refs = {f["source"]["message_id"] for f in prior["facts"]}
                refs.update(
                    s["message_id"] for c in prior["conflicts"] for s in c["sources"]
                )
                for mid in refs - {m["id"] for m in messages}:
                    old = db.execute(
                        "SELECT * FROM group_messages WHERE id=?", (mid,)
                    ).fetchone()
                    if old:
                        latest = db.execute(
                            "SELECT * FROM group_messages WHERE source_id=? AND id<=? ORDER BY id DESC LIMIT 1",
                            (old["source_id"], messages[-1]["id"]),
                        ).fetchone()
                        if latest and latest["id"] not in {
                            m["id"] for m in context_messages
                        }:
                            context_messages.append(dict(latest))
            # Reserve this run; an interrupted process retries after this short lease.
            state["next_run"] = now + 120
            self.save_state(db, state)
        try:
            async with asyncio.timeout(self.model_timeout):
                review = await self.model.review_group(
                    {
                        "now_utc": datetime.now(timezone.utc).isoformat(),
                        "source_connected": bool(state.get("source_connected"))
                        and now - state.get("last_received", 0) < 180,
                        "previous_review": prior,
                        "messages": [
                            {
                                k: m[k]
                                for k in ("id", "sender", "body", "sent_at", "kind")
                            }
                            for m in context_messages
                        ],
                    }
                )
            latest_by_source = {}
            for m in context_messages:
                if m["id"] > latest_by_source.get(m["source_id"], {}).get("id", 0):
                    latest_by_source[m["source_id"]] = m
            known = {m["id"]: m for m in latest_by_source.values()}
            sources = [f.source for f in review.facts] + [
                s for c in review.conflicts for s in c.sources
            ]
            if any(
                s.message_id not in known
                or known[s.message_id]["kind"] != "text"
                or s.quote not in known[s.message_id]["body"]
                for s in sources
            ):
                raise ValueError("ungrounded_group_review")
            if any(
                len({s.message_id for s in c.sources}) < 2 for c in review.conflicts
            ):
                raise ValueError("conflict_requires_two_sources")
            conflict_ids = {s.message_id for c in review.conflicts for s in c.sources}
            if any(
                f.status == "conflicting" and f.source.message_id not in conflict_ids
                for f in review.facts
            ):
                raise ValueError("inconsistent_conflict_report")
            if review.wedding_date_status == "conflicting" and not review.conflicts:
                raise ValueError("inconsistent_wedding_date_status")
            # A model-written summary must not contradict its own structured findings.
            review.summary = f"{len(review.facts)} source observations; {len(review.conflicts)} possible conflicts. Wedding date status: {review.wedding_date_status}."
            with self.store.tx() as db:
                current = self.read_state(
                    db
                )  # Preserve heartbeats arriving during inference.
                backlog = db.execute(
                    "SELECT id FROM group_messages WHERE id>? LIMIT 1",
                    (messages[-1]["id"],),
                ).fetchone()
                current.update(
                    cursor=messages[-1]["id"],
                    next_run=time.time() + (1 if backlog else self.interval),
                    last_success=time.time(),
                    failures=0,
                    error=None,
                )
                db.execute(
                    "INSERT INTO group_runs(created,through_id,result) VALUES(?,?,?)",
                    (time.time(), messages[-1]["id"], review.model_dump_json()),
                )
                self.save_state(db, current)
        except Exception as exc:
            with self.store.tx() as db:
                current = self.read_state(db)
                failures = current.get("failures", 0) + 1
                current.update(
                    failures=failures,
                    error=type(exc).__name__,
                    next_run=time.time()
                    + min(self.interval, 60 * 2 ** min(failures, 6)),
                )
                self.save_state(db, current)
