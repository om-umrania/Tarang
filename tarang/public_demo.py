"""Isolated public rehearsal. No access to wedding records or execution tools."""

import asyncio
import time
import uuid
from datetime import datetime
from zoneinfo import ZoneInfo

from pydantic import BaseModel, ConfigDict, Field

from .store import Store


class DemoReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=2200)


MENU = [
    [{"text": "Try décor rescue", "callback_data": "demo:decor"}],
    [{"text": "Try hamper delivery", "callback_data": "demo:courier"}],
]
WELCOME = (
    "Hi, I'm Tarang, your AI wedding coordinator. Welcome to your private demo.\n\n"
    "Try a fictional wedding problem below. Calls, vendor responses, approvals and "
    "payments here are simulated; this demo cannot access any real wedding or WhatsApp group.\n\n"
    "Choosing a scenario enables AI questions: your demo text and recent replies are "
    "processed through OpenRouter. Please use fictional details, not personal information. "
    "Other visitors cannot see your conversation; the service operator can access stored data.\n\n"
    "/demo: scenario menu · /reset: clear and restart · /delete: delete stored demo chat "
    "· /privacy: data details. Free hosting may take a moment to wake up."
)
SCENARIOS = {
    "decor": {
        "facts": "Fictional decor setup due 4 pm IST; guests 5 pm; vendor now says 7 pm. "
        "Same scope: ivory/peach mandap, floral entrance, warm lighting. "
        "Extra crew/vehicle quote INR 2500 inclusive; negotiation target INR 1500, ceiling "
        "INR 2500; every agreement needs the fictional approver's permission.",
        "steps": [
            (
                "The décor vendor now expects to finish at 7 pm, but setup is due at 4 pm. "
                "I'd confirm what caused the delay and whether extra crew can recover the "
                "original deadline without changing the design. You shouldn't have to chase them.",
                "Hear the simulated vendor response",
            ),
            (
                "Simulated vendor response: extra crew and transport can restore 4 pm readiness "
                "for ₹2,500 inclusive. I'd ask for ₹1,500 while preserving scope and timing. "
                "The ₹2,500 ceiling doesn't authorise me to agree.",
                "See the simulated counteroffer",
            ),
            (
                "Simulated counteroffer: ₹2,000 inclusive of crew, transport and taxes; "
                "same décor scope, ready by 4 pm. I'd recommend this recovery if those terms "
                "are confirmed, and ask the authorised approver before agreeing.",
                "Approve ₹2,000 — simulation only",
            ),
            (
                "Demo approval recorded. In a connected workflow I'd confirm these exact "
                "terms and track crew arrival and setup. Approval is not payment or proof "
                "the décor is ready. I'd ask the designated venue coordinator to inspect it.",
                "Inspect the fictional setup",
            ),
            (
                "Simulated inspection: the mandap is set up, but the entrance lights don't work. "
                "The outcome stays open. I'd ask the vendor to fix the defect and obtain "
                "another on-site check, without asking the bride to chase the electrician.",
                "See the final simulated inspection",
            ),
            (
                "Simulated final inspection at 4:25 pm: lights work and the agreed setup is "
                "ready. That's 25 minutes late, before 5 pm guest arrival. In this example, "
                "physical readiness is verified; payment remains unverified. No real vendor "
                "was contacted and no money moved. You can ask me about the decisions here.",
                None,
            ),
        ],
    },
    "courier": {
        "facts": "Fictional 200 hampers due 6 pm IST. Expected dispatch evidence missing. "
        "Confirmed vendor report in the simulation: original courier unavailable, all "
        "hampers packed. Hypothetical replacement verified feasible at INR 1200 within "
        "an exact approved courier budget; no real courier availability or payment.",
        "steps": [
            (
                "The dispatch checkpoint passed without evidence for 200 hampers due by "
                "6 pm. Missing evidence isn't proof of failure. I'd check with the gift "
                "vendor and establish the actual pickup status.",
                "Hear the simulated vendor response",
            ),
            (
                "Simulated vendor response: the original courier is unavailable; all "
                "hampers are packed. Suppose an approved replacement can meet the deadline "
                "for ₹1,200, with package capacity and pickup readiness verified. I'd check "
                "exact scope, payee and remaining budget before arranging it.",
                "Check the fictional authority",
            ),
            (
                "This fixture grants the exact ₹1,200 courier expense within the approved "
                "budget. In a connected workflow, that permits recovery without another "
                "approval. Here nothing is booked or paid. I'd continue tracking pickup "
                "and receipt; a booking alone does not fulfil the outcome.",
                "Inspect the fictional delivery",
            ),
            (
                "The simulated carrier says delivered, but the venue counts only 180 of "
                "200 hampers. I'd keep the shortfall open, reconcile package references "
                "with the carrier and ask the venue to confirm the remaining 20.",
                "See the final simulated receipt",
            ),
            (
                "Simulated venue confirmation: the remaining 20 arrived; all 200 are "
                "undamaged. That would support physical fulfilment. Payment needs its "
                "own receipt. This was a fictional walkthrough, with no shipment or "
                "payment created. Ask me about any decision in the example.",
                None,
            ),
        ],
    },
}


class PublicDemo:
    def __init__(self, store, settings, model):
        self.store, self.settings, self.model = store, settings, model

    @staticmethod
    def _clear(db, chat):
        db.execute("DELETE FROM demo_turns WHERE chat=?", (chat,))
        db.execute("DELETE FROM demo_sessions WHERE chat=?", (chat,))
        # Only this chat's demo output. Never alter the private wedding workspace.
        db.execute("DELETE FROM outbox WHERE chat=? AND key LIKE 'demo:%'", (chat,))

    @staticmethod
    def _quota(db, chat, kind, now, per_user, global_limit):
        day = datetime.fromtimestamp(now, ZoneInfo("Asia/Kolkata")).date().isoformat()
        for target, limit in ((chat, per_user), (0, global_limit)):
            r = db.execute(
                "SELECT count FROM demo_usage WHERE day=? AND chat=? AND kind=?",
                (day, target, kind),
            ).fetchone()
            if r and r["count"] >= limit:
                return False
        for target in (chat, 0):
            db.execute(
                "INSERT INTO demo_usage(day,chat,kind,count) VALUES(?,?,?,1) "
                "ON CONFLICT(day,chat,kind) DO UPDATE SET count=demo_usage.count+1",
                (day, target, kind),
            )
        return True

    def ingest(self, update):
        """True means handled here; False leaves the allowlisted engine in control."""
        query = update.get("callback_query") or {}
        message = update.get("message") or query.get("message") or {}
        sender = query.get("from") or message.get("from") or {}
        chat = message.get("chat") or {}
        cid = chat.get("id")
        uid = update.get("update_id")
        if (
            not isinstance(cid, int)
            or isinstance(cid, bool)
            or cid <= 0
            or cid != sender.get("id")
            or chat.get("type") != "private"
            or not isinstance(uid, int)
            or isinstance(uid, bool)
        ):
            return False
        text = message.get("text", "") if not query else ""
        text = text if isinstance(text, str) else ""
        command = text.strip().lower()
        data = query.get("data", "")
        now = time.time()
        key = f"demo:{uid}"
        with self.store.tx() as db:
            session = db.execute(
                "SELECT * FROM demo_sessions WHERE chat=?", (cid,)
            ).fetchone()
            is_owner = cid in self.settings.allowed
            wants_demo = command in ("/demo", "/start demo") or data.startswith("demo:")
            if is_owner and not session and not wants_demo:
                return False
            # /live is available even after the public feature is disabled.
            if command == "/live" and is_owner:
                self._clear(db, cid)
                Store.message(
                    db,
                    key,
                    cid,
                    "Back to your restricted wedding workspace. Send /status to inspect it.",
                )
                return True
            if not self.settings.public_demo:
                return not is_owner  # closed to new visitors; no state or model use
            if db.execute("SELECT 1 FROM demo_seen WHERE key=?", (key,)).fetchone():
                return True
            db.execute("INSERT INTO demo_seen(key,created) VALUES(?,?)", (key, now))
            allowed = self._quota(db, cid, "input", now, 100, 2000)
            if command == "/delete":
                self._clear(db, cid)
                if allowed:
                    Store.message(
                        db,
                        key,
                        cid,
                        "Stored demo conversation deleted. Messages already delivered in Telegram and provider records are separate. Minimal anti-abuse counts remain for up to 8 days while the service runs. Send /start to begin again.",
                    )
                return True
            if not allowed:
                return True  # hard bound also prevents response amplification
            if command == "/privacy":
                Store.message(
                    db,
                    key,
                    cid,
                    "Your demo is separate from other visitors and the owner's wedding. The service operator can access stored demo data. AI questions send your text, fictional scenario and recent replies to OpenRouter; never send secrets or personal wedding data. Stored demo data expires after 7 days of inactivity while the service runs. /delete clears it now; provider records, hosting backups and Telegram messages have separate retention. No real calls, bookings, payments or background monitoring run in this demo.",
                )
                return True
            if command == "/live":
                Store.message(
                    db,
                    key,
                    cid,
                    "This link provides a private demo only. It does not grant access to the owner's wedding.",
                )
                return True
            if command in ("/reset", "/start", "/start demo"):
                self._clear(db, cid)
                session = None
            if not session:
                count = db.execute(
                    "SELECT COUNT(*) AS n FROM demo_sessions"
                ).fetchone()["n"]
                if count >= 1000:
                    Store.message(
                        db,
                        key,
                        cid,
                        "The free demo is at capacity. Please try again later.",
                    )
                    return True
                db.execute(
                    "INSERT INTO demo_sessions(chat,scenario,stage,generation,consent,updated) VALUES(?,?,?,?,0,?)",
                    (cid, "", "menu", uuid.uuid4().hex, now),
                )
                Store.message(db, key, cid, WELCOME, MENU)
                return True
            db.execute("UPDATE demo_sessions SET updated=? WHERE chat=?", (now, cid))
            if command in ("/demo", "/help", "/status"):
                Store.message(
                    db,
                    key,
                    cid,
                    "Private demo · no live actions. Choose a scenario, use its buttons, or ask an AI question after choosing. /reset clears the conversation; /delete removes stored demo data."
                    + (
                        " /live returns to your restricted workspace."
                        if is_owner
                        else ""
                    ),
                    MENU,
                )
                return True
            if data in ("demo:decor", "demo:courier"):
                scenario = data.split(":")[1]
                generation = uuid.uuid4().hex
                db.execute("DELETE FROM demo_turns WHERE chat=?", (cid,))
                db.execute(
                    "UPDATE outbox SET state='cancelled' WHERE chat=? AND key LIKE 'demo:ai:%' AND state='pending'",
                    (cid,),
                )
                db.execute(
                    "UPDATE demo_sessions SET scenario=?,stage='0',generation=?,consent=1 WHERE chat=?",
                    (scenario, generation, cid),
                )
                self._scene(db, key, cid, scenario, 0, generation)
                return True
            if data.startswith("demo:next:"):
                expected = f"demo:next:{session['generation']}:{session['stage']}"
                if (
                    data != expected
                    or not session["scenario"]
                    or not session["stage"].isdigit()
                ):
                    Store.message(
                        db,
                        key,
                        cid,
                        "That demo step is no longer current. Use the latest buttons or /demo.",
                    )
                    return True
                stage = int(session["stage"]) + 1
                if stage >= len(SCENARIOS[session["scenario"]]["steps"]):
                    return True
                db.execute(
                    "UPDATE demo_sessions SET stage=? WHERE chat=?", (str(stage), cid)
                )
                self._scene(
                    db, key, cid, session["scenario"], stage, session["generation"]
                )
                return True
            if query:
                Store.message(
                    db,
                    key,
                    cid,
                    "This is a demo. Real approval buttons cannot be used here. Choose /demo.",
                )
                return True
            if not session["consent"]:
                Store.message(
                    db,
                    key,
                    cid,
                    "Choose a fictional scenario first to begin. Please review the privacy notice in /start.",
                    MENU,
                )
                return True
            if not text or len(text) > 2000 or text.startswith("/"):
                Store.message(
                    db,
                    key,
                    cid,
                    "Send a text question up to 2,000 characters, or use /demo, /reset, /privacy or /delete. Voice notes and files are not processed.",
                )
                return True
            pending = db.execute(
                "SELECT 1 FROM demo_turns WHERE chat=? AND status IN ('pending','processing')",
                (cid,),
            ).fetchone()
            if pending:
                Store.message(
                    db,
                    key,
                    cid,
                    "I'm still working on your previous demo question. Please wait for that reply.",
                )
                return True
            if not self._quota(db, cid, "model", now, 10, 100):
                Store.message(
                    db,
                    key,
                    cid,
                    "The free AI demo limit has been reached for today. The guided scenario buttons still work. Limits reset at midnight IST.",
                    MENU,
                )
                return True
            db.execute(
                "INSERT INTO demo_turns(key,chat,generation,body,status,created) VALUES(?,?,?,?,'pending',?)",
                (key, cid, session["generation"], text, now),
            )
        return True

    @staticmethod
    def _scene(db, key, chat, scenario, stage, generation):
        text, label = SCENARIOS[scenario]["steps"][stage]
        buttons = (
            [[{"text": label, "callback_data": f"demo:next:{generation}:{stage}"}]]
            if label
            else MENU
        )
        Store.message(db, key, chat, "DEMO · fictional scenario\n\n" + text, buttons)

    def cleanup(self):
        cutoff = time.time() - 7 * 86400
        day = (
            datetime.fromtimestamp(cutoff, ZoneInfo("Asia/Kolkata")).date().isoformat()
        )
        with self.store.tx() as db:
            for row in db.execute(
                "SELECT chat FROM demo_sessions WHERE updated<?", (cutoff,)
            ).fetchall():
                self._clear(db, row["chat"])
            db.execute("DELETE FROM demo_seen WHERE created<?", (cutoff,))
            db.execute("DELETE FROM demo_usage WHERE day<?", (day,))

    async def step(self):
        if not self.settings.public_demo:
            return False
        now = time.time()
        with self.store.tx() as db:
            # After a crash, report interruption; do not replay a model request.
            for stale in db.execute(
                "SELECT * FROM demo_turns WHERE status='processing' AND lease<?", (now,)
            ).fetchall():
                db.execute(
                    "UPDATE demo_turns SET status='failed' WHERE key=?", (stale["key"],)
                )
                Store.message(
                    db,
                    "demo:ai:" + stale["key"],
                    stale["chat"],
                    "DEMO · That AI reply was interrupted. Please try your question again; the guided scenarios remain available.",
                    MENU,
                )
            # Cross-process lease serialises demo model calls without blocking the
            # private wedding worker, including during rolling deployments.
            if db.execute(
                "SELECT 1 FROM demo_turns WHERE status='processing'"
            ).fetchone():
                return False
            turn = db.execute(
                "SELECT * FROM demo_turns WHERE status='pending' ORDER BY created,key LIMIT 1"
            ).fetchone()
            if not turn:
                return False
            turn = dict(turn)
            session = db.execute(
                "SELECT * FROM demo_sessions WHERE chat=? AND generation=?",
                (turn["chat"], turn["generation"]),
            ).fetchone()
            if not session:
                db.execute("DELETE FROM demo_turns WHERE key=?", (turn["key"],))
                return True
            history = [
                dict(r)
                for r in db.execute(
                    "SELECT body,reply FROM demo_turns WHERE chat=? AND generation=? AND status='done' ORDER BY created DESC,key DESC LIMIT 6",
                    (turn["chat"], turn["generation"]),
                )
            ]
            context = {
                "mode": "fictional_private_demo",
                "scenario": SCENARIOS[session["scenario"]]["facts"],
                "current_guided_step": SCENARIOS[session["scenario"]]["steps"][
                    int(session["stage"])
                ][0],
                "history": list(reversed(history)),
                "question": turn["body"],
            }
            db.execute(
                "UPDATE demo_turns SET status='processing',lease=? WHERE key=?",
                (now + 60, turn["key"]),
            )
        try:
            async with asyncio.timeout(40):
                result = await self.model.demo_reply(context)
            reply, status = result.message, "done"
        except Exception:
            reply, status = (
                "The AI is unavailable right now. You can still explore the guided scenarios below, or try your question later.",
                "failed",
            )
        with self.store.tx() as db:
            current = db.execute(
                "SELECT 1 FROM demo_turns t JOIN demo_sessions s ON s.chat=t.chat AND s.generation=t.generation WHERE t.key=? AND t.status='processing'",
                (turn["key"],),
            ).fetchone()
            if not current:  # deletion/reset during the request cancels its reply
                return True
            db.execute(
                "UPDATE demo_turns SET status=?,reply=? WHERE key=?",
                (status, reply, turn["key"]),
            )
            Store.message(
                db,
                "demo:ai:" + turn["key"],
                turn["chat"],
                "DEMO · AI explanation, no live actions\n\n" + reply,
                MENU,
            )
        return True
