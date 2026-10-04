"""Read-only operator projections of persisted Telegram and decision state."""

import json
import time


LIMIT = 100


def incoming_text(update):
    query = update.get("callback_query")
    if query:
        for row in (
            query.get("message", {}).get("reply_markup", {}).get("inline_keyboard", [])
        ):
            for button in row:
                if button.get("callback_data") == query.get("data"):
                    return "Selected: " + str(button.get("text", "button"))[:2000]
        # Do not expose callback tokens. Old payloads may omit the button labels.
        action = str(query.get("data", "")).split(":")[0]
        return "Selected: " + {"approve": "Approve once", "reject": "Reject"}.get(
            action, "Telegram button"
        )
    message = update.get("message", {})
    if "voice" in message:
        return "Voice note received · transcript requires review"
    return str(
        message.get("text") or message.get("caption") or "Unsupported attachment"
    )[:4000]


def records(db, sql, args=(), json_fields=()):
    rows = [dict(row) for row in db.execute(sql, args)]
    for row in rows:
        for field in json_fields:
            row[field] = json.loads(row[field])
    return rows


def snapshot(store, settings, scope=None, chat=None):
    """One consistent snapshot; selected chat only, bounded history, no effects."""
    with store.tx() as db:
        conversations = records(
            db,
            """
            SELECT 'workspace' AS scope, c.chat, c.outcome AS title, c.state AS stage,
                   COALESCE((SELECT MAX(e.created) FROM events e WHERE e.commitment=c.id),0) AS updated
              FROM commitments c
            UNION ALL
            SELECT 'demo' AS scope, chat, scenario AS title, stage, updated FROM demo_sessions
            ORDER BY updated DESC LIMIT 1201
        """,
        )
        truncated = len(conversations) > 1200
        conversations = conversations[:1200]
        if scope is None and conversations:
            scope, chat = conversations[0]["scope"], conversations[0]["chat"]
        selected = next(
            (c for c in conversations if c["scope"] == scope and c["chat"] == chat),
            None,
        )
        result = {
            "generated_at": time.time(),
            "transport": settings.telegram_mode,
            "telegram_configured": bool(settings.bot_token),
            "model_configured": bool(settings.model_key),
            "free_host": settings.free_host,
            "conversations": conversations,
            "conversations_truncated": truncated,
            "selected": selected,
            "messages": [],
            "operations": [],
            "decisions": [],
            "evidence": [],
            "commitment": None,
            "intake": None,
            "processing": {},
            "delivery": {},
            "history_limited": False,
        }
        if not selected:
            return result
        prefix = "LIKE" if scope == "demo" else "NOT LIKE"
        result["delivery"] = {
            r["state"]: r["n"]
            for r in db.execute(
                f"SELECT state,COUNT(*) AS n FROM outbox WHERE chat=? AND key {prefix} 'demo:%' GROUP BY state",
                (chat,),
            )
        }
        outgoing = records(
            db,
            f"SELECT id,payload,state,created FROM outbox WHERE chat=? AND key {prefix} 'demo:%' ORDER BY id DESC LIMIT ?",
            (chat, LIMIT + 1),
            ("payload",),
        )
        messages = [
            {
                "id": f"out:{r['id']}",
                "direction": "out",
                "text": r["payload"].get("text")
                or r["payload"].get("speech_text", "Voice reply"),
                "status": r["state"],
                "created": r["created"] or None,
                "kind": "voice" if "speech_text" in r["payload"] else "text",
            }
            for r in outgoing[:LIMIT]
        ]
        result["history_limited"] = len(outgoing) > LIMIT
        if scope == "demo":
            incoming = records(
                db,
                "SELECT key,body,created FROM demo_messages WHERE chat=? ORDER BY created DESC,key DESC LIMIT ?",
                (chat, LIMIT + 1),
            )
            messages += [
                {
                    "id": r["key"],
                    "direction": "in",
                    "text": r["body"],
                    "status": "received",
                    "created": r["created"],
                    "kind": "text",
                }
                for r in incoming[:LIMIT]
            ]
            intake = db.execute(
                "SELECT body FROM demo_intakes WHERE chat=?", (chat,)
            ).fetchone()
            result["intake"] = json.loads(intake["body"]) if intake else None
            result["processing"] = {
                r["status"]: r["n"]
                for r in db.execute(
                    "SELECT status,COUNT(*) AS n FROM demo_turns WHERE chat=? GROUP BY status",
                    (chat,),
                )
            }
            turns = records(
                db,
                "SELECT key,body,status,created FROM demo_turns WHERE chat=? ORDER BY created DESC LIMIT ?",
                (chat, LIMIT + 1),
            )
            # Historical free-text turns predate message capture. Reconstruct only known input.
            known = {m["id"] for m in messages}
            messages += [
                {
                    "id": r["key"],
                    "direction": "in",
                    "text": r["body"],
                    "status": r["status"],
                    "created": r["created"],
                    "kind": "text",
                }
                for r in turns[:LIMIT]
                if r["key"] not in known
            ]
            result["history_limited"] |= len(turns) > LIMIT
            voice = db.execute(
                "SELECT status,transcript FROM voice_jobs WHERE chat=?", (chat,)
            ).fetchone()
            result["voice"] = dict(voice) if voice else None
        else:
            c = db.execute("SELECT * FROM commitments WHERE chat=?", (chat,)).fetchone()
            result["commitment"] = dict(c)
            cid = c["id"]
            incoming = records(
                db,
                "SELECT id,payload,status,created FROM events WHERE commitment=? AND source='telegram' ORDER BY id DESC LIMIT ?",
                (cid, LIMIT + 1),
                ("payload",),
            )
            messages += [
                {
                    "id": f"in:{r['id']}",
                    "direction": "in",
                    "text": incoming_text(r["payload"]),
                    "status": r["status"],
                    "created": r["created"],
                    "kind": "text",
                }
                for r in incoming[:LIMIT]
            ]
            result["processing"] = {
                r["status"]: r["n"]
                for r in db.execute(
                    "SELECT status,COUNT(*) AS n FROM events WHERE commitment=? GROUP BY status",
                    (cid,),
                )
            }
            for table, fields in (
                ("operations", ("proposal",)),
                ("ledger", ("data",)),
                ("evidence", ()),
            ):
                rows = records(
                    db,
                    f"SELECT * FROM {table} WHERE commitment=? ORDER BY id DESC LIMIT ?",
                    (cid, LIMIT + 1),
                    fields,
                )
                result["history_limited"] |= len(rows) > LIMIT
                result["decisions" if table == "ledger" else table] = rows[:LIMIT]
        result["history_limited"] |= len(incoming) > LIMIT
        result["messages"] = sorted(
            messages, key=lambda m: (m["created"] or 0, m["id"])
        )
        return result
