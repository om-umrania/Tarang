"""Receive-only Cloud API intake. No personal-account or group-history access."""

import hashlib
import json
import time
from .store import Store


class ConflictMonitor:
    def __init__(self, store, settings, model):
        self.store, self.settings, self.model = store, settings, model

    @property
    def ready(self):
        s = self.settings
        return bool(
            s.whatsapp_enabled
            and s.whatsapp_app_secret
            and s.whatsapp_verify_token
            and s.whatsapp_phone_id
            and s.whatsapp_routes
        )

    def ingest(self, payload):
        if not self.ready or payload.get("object") != "whatsapp_business_account":
            return 0
        count = 0
        with self.store.tx() as db:
            for entry in payload.get("entry", []):
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    if (
                        change.get("field") != "messages"
                        or value.get("metadata", {}).get("phone_number_id")
                        != self.settings.whatsapp_phone_id
                    ):
                        continue
                    for msg in value.get("messages", []):
                        sender = msg.get("from", "")
                        scope = self.settings.whatsapp_routes.get(sender)
                        # Only the documented direct-message envelope is supported.
                        if not scope or msg.get("group_id") or value.get("group_id"):
                            continue
                        mid = msg.get("id")
                        if not isinstance(mid, str) or not mid or len(mid) > 300:
                            continue
                        if db.execute(
                            "SELECT id FROM conversation_messages WHERE external_id=?",
                            (mid,),
                        ).fetchone():
                            continue
                        body = (
                            msg.get("text", {}).get("body", "")
                            if msg.get("type") == "text"
                            else ""
                        )
                        if not isinstance(body, str):
                            continue
                        supported = 0 < len(body) <= 12000
                        try:
                            sent_at = float(msg["timestamp"])
                            if not 0 < sent_at <= time.time() + 300:
                                continue
                        except (ValueError, TypeError, KeyError):
                            continue
                        db.execute(
                            "INSERT INTO conversation_messages(external_id,scope,sender,body,sent_at,received_at,status,due,error) VALUES(?,?,?,?,?,?,?,?,?)",
                            (
                                mid,
                                scope,
                                sender,
                                body if supported else "",
                                sent_at,
                                time.time(),
                                "pending" if supported else "unsupported",
                                time.time(),
                                None if supported else "text_only_or_too_large",
                            ),
                        )
                        count += 1
        return count

    def recover(self):
        with self.store.tx() as db:
            db.execute(
                "UPDATE conversation_messages SET status='pending' WHERE status='processing'"
            )

    async def step(self):
        if not self.ready:
            return
        with self.store.tx() as db:
            row = db.execute(
                "SELECT * FROM conversation_messages WHERE status='pending' AND due<=? ORDER BY id LIMIT 1",
                (time.time(),),
            ).fetchone()
            if not row:
                return
            row = dict(row)
            # Revoked routes must not continue processing already queued messages.
            if self.settings.whatsapp_routes.get(row["sender"]) != row["scope"]:
                db.execute(
                    "UPDATE conversation_messages SET status='revoked' WHERE id=?",
                    (row["id"],),
                )
                return
            history = [
                dict(r)
                for r in db.execute(
                    "SELECT id,sender,body,sent_at FROM conversation_messages WHERE scope=? AND id<=? AND body<>'' ORDER BY id DESC LIMIT 24",
                    (row["scope"], row["id"]),
                )
            ]
            history = [
                m
                for m in history
                if self.settings.whatsapp_routes.get(m["sender"]) == row["scope"]
            ]
            db.execute(
                "UPDATE conversation_messages SET status='processing',attempts=attempts+1 WHERE id=?",
                (row["id"],),
            )
        try:
            result = await self.model.detect_conflicts(
                {
                    "scope": row["scope"],
                    "trigger_message_id": row["id"],
                    "messages": list(reversed(history)),
                }
            )
            known = {m["id"]: m["body"] for m in history}
            reports = []
            for conflict in result.conflicts:
                ids = {source.message_id for source in conflict.sources}
                if (
                    len(ids) < 2
                    or row["id"] not in ids
                    or any(
                        source.message_id not in known
                        or source.quote not in known[source.message_id]
                        for source in conflict.sources
                    )
                ):
                    raise ValueError("ungrounded_conflict")
                fingerprint = hashlib.sha256(
                    json.dumps([row["scope"], conflict.kind, sorted(ids)]).encode()
                ).hexdigest()
                reports.append((fingerprint, conflict.model_dump()))
            with self.store.tx() as db:
                for fingerprint, report in reports:
                    db.execute(
                        "INSERT OR IGNORE INTO conflicts(fingerprint,scope,report,created) VALUES(?,?,?,?)",
                        (fingerprint, row["scope"], json.dumps(report), time.time()),
                    )
                db.execute(
                    "UPDATE conversation_messages SET status='done',error=NULL WHERE id=?",
                    (row["id"],),
                )
        except Exception as exc:
            # Never log payloads, credentials, provider response bodies or URLs.
            with self.store.tx() as db:
                db.execute(
                    "UPDATE conversation_messages SET status=?,due=?,error=? WHERE id=?",
                    (
                        "failed" if row["attempts"] >= 2 else "pending",
                        time.time() + 60 * (row["attempts"] + 1),
                        type(exc).__name__,
                        row["id"],
                    ),
                )
