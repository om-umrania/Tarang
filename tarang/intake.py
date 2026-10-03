"""Conversational rehearsal state. Never creates operational authority or effects."""

import json
import uuid

from pydantic import BaseModel, ConfigDict, Field

from .store import Store


class IntakeFacts(BaseModel):
    model_config = ConfigDict(extra="forbid")
    problem: str = Field(default="", max_length=500)
    deadline: str = Field(default="", max_length=200)
    contact: str = Field(default="", max_length=200)
    approver: str = Field(default="", max_length=200)
    verifier: str = Field(default="", max_length=200)
    constraints: str = Field(default="", max_length=500)
    priority: str = Field(default="", max_length=200)


class IntakeReply(BaseModel):
    model_config = ConfigDict(extra="forbid")
    message: str = Field(min_length=1, max_length=700)
    facts: IntakeFacts


QUESTIONS = {
    "problem": (
        "What would you like help with first?",
        ["Décor is delayed", "Hampers haven't arrived", "Choosing between options"],
    ),
    "deadline": (
        "When does this need to be resolved? Use an exact date and time if you know them.",
        ["Date/time not decided yet"],
    ),
    "contact": (
        "Who should I coordinate with about this? A fictional name or role is enough.",
        ["Décor vendor", "Gift vendor", "Venue coordinator", "Contact not known yet"],
    ),
    "approver": (
        "Who should decide on changes or extra costs? This records a demo role, not spending permission.",
        ["Me", "My partner and me", "Approver not decided yet"],
    ),
    "verifier": (
        "Who at the venue can check the result?",
        ["Venue coordinator", "A designated friend", "Verifier not decided yet"],
    ),
    "constraints": (
        "What should I preserve when exploring a fix? You can type several requirements together.",
        [
            "Original design and scope",
            "Existing budget",
            "Deadline",
            "Help me work this out",
        ],
    ),
    "priority": (
        "If a trade-off is needed, what matters most?",
        [
            "Meet the deadline",
            "Stay within budget",
            "Keep the original plan",
            "Bring the trade-off to me",
        ],
    ),
}
LABELS = {
    "problem": "Problem",
    "deadline": "Deadline",
    "contact": "Contact",
    "approver": "Decision maker",
    "verifier": "On-site verifier",
    "constraints": "Preserve",
    "priority": "Priority",
}


class Intake:
    @staticmethod
    def read(db, chat):
        row = db.execute(
            "SELECT body FROM demo_intakes WHERE chat=?", (chat,)
        ).fetchone()
        return json.loads(row["body"]) if row else None

    @staticmethod
    def save(db, chat, state):
        state["revision"] = uuid.uuid4().hex[:16]
        db.execute(
            "INSERT INTO demo_intakes(chat,body) VALUES(?,?) ON CONFLICT(chat) DO UPDATE SET body=excluded.body",
            (chat, json.dumps(state)),
        )

    @classmethod
    def start(cls, db, key, chat):
        state = {
            "facts": IntakeFacts().model_dump(),
            "phase": "collect",
            "revision": "",
        }
        cls.save(db, chat, state)
        cls.render(
            db,
            key,
            chat,
            state,
            "Let's work through a fictional problem together. Choose a suggestion or type your own answer; you can correct me along the way.",
        )

    @staticmethod
    def choices(state):
        if state["phase"] == "review":
            return ["Rehearse the contact check", "Change a detail", "Pause rehearsal"]
        if state["phase"] == "investigated":
            return [
                "Explore alternatives",
                "Keep the original requirements",
                "Change a detail",
                "Pause rehearsal",
            ]
        if state["phase"] == "feedback":
            return ["Change a detail", "Pause rehearsal"]
        if state["phase"] == "paused":
            return ["Resume rehearsal", "Change a detail"]
        field = next((k for k in QUESTIONS if not state["facts"][k]), None)
        if not field:
            return []
        options = list(QUESTIONS[field][1])
        if field == "contact":
            if (
                "décor" in state["facts"]["problem"].lower()
                or "decor" in state["facts"]["problem"].lower()
            ):
                options = ["Décor vendor", "Venue coordinator", "Contact not known yet"]
            elif "hamper" in state["facts"]["problem"].lower():
                options = ["Gift vendor", "Courier contact", "Contact not known yet"]
        return options + ["I'll type my answer"]

    @classmethod
    def render(cls, db, key, chat, state, lead=""):
        missing = next((k for k in QUESTIONS if not state["facts"][k]), None)
        if state["phase"] == "collect" and not missing:
            state["phase"] = "review"
            cls.save(db, chat, state)
        if state["phase"] == "collect":
            text = QUESTIONS[missing][0]
        elif state["phase"] == "review":
            text = "Here's the plan so far:\n" + "\n".join(
                f"{LABELS[k]}: {v}" for k, v in state["facts"].items()
            )
            text += "\n\nI'd first ask the contact for the current status and feasible recovery options, preserving your requirements. Then I'd bring material trade-offs to your decision maker and seek an on-site check. Shall we rehearse that next step, or change something?"
        elif state["phase"] == "investigated":
            text = (
                "Simulated contact response: the original plan cannot yet be confirmed; recovery options, costs and timing still need checking. This is an authored test event, not a real vendor response.\n\n"
                f"Your priority is: {state['facts']['priority']}. I'd investigate options that preserve: {state['facts']['constraints']}. Should I explore alternatives or keep the original requirements?"
            )
        elif state["phase"] == "feedback":
            text = (
                f"Demo preference recorded: {state['feedback']}. I'd request feasibility, exact scope, timing and all-inclusive cost from {state['facts']['contact']}, then bring any change to {state['facts']['approver']} before agreeing. "
                f"The next observation would be that contact's response, followed by verification from {state['facts']['verifier']}. Nothing is booked, paid, scheduled or verified here. You can change any detail by typing it."
            )
        else:
            text = "Rehearsal paused. No background actions run in this demo. You can resume or change a detail."
        options = cls.choices(state)
        if options:
            text += "\n\n" + " · ".join(
                f"{i + 1}. {label}" for i, label in enumerate(options)
            )
            text += "\nTap a button or reply /choose followed by its number. You can also type your own answer."
        buttons = [
            [{"text": label, "callback_data": f"demo:pick:{state['revision']}:{i}"}]
            for i, label in enumerate(options)
        ]
        Store.message(
            db,
            key,
            chat,
            (lead + "\n\n" if lead else "") + text,
            buttons,
        )

    @classmethod
    def pick(cls, db, key, chat, data):
        state = cls.read(db, chat)
        parts = data.split(":")
        options = cls.choices(state) if state else []
        if (
            not state
            or len(parts) != 4
            or parts[2] != state["revision"]
            or not parts[3].isdigit()
            or int(parts[3]) >= len(options)
        ):
            Store.message(
                db,
                key,
                chat,
                "That choice is no longer current. Please use the latest question or /demo.",
            )
            return
        label = options[int(parts[3])]
        if label in ("I'll type my answer", "Change a detail"):
            Store.message(
                db,
                key,
                chat,
                "Type your answer or correction, including which detail you want to change. You can give several details at once. Please use fictional details.",
            )
            return
        if label == "Pause rehearsal":
            state["resume_phase"] = state["phase"]
            state["phase"] = "paused"
        elif label == "Resume rehearsal":
            state["phase"] = state.pop("resume_phase", "review")
        elif state["phase"] == "review":
            state["phase"] = "investigated"
        elif state["phase"] == "investigated":
            state["phase"] = "feedback"
            state["feedback"] = label
        else:
            field = next(k for k in QUESTIONS if not state["facts"][k])
            state["facts"][field] = label
        cls.save(db, chat, state)
        cls.render(db, key, chat, state)

    @classmethod
    def apply(cls, db, key, chat, result):
        state = cls.read(db, chat)
        for field, value in result.facts.model_dump().items():
            if value:
                state["facts"][field] = value
        if state["phase"] != "paused":
            state["phase"] = (
                "collect"  # corrected plan must be reviewed before another rehearsal
            )
        cls.save(db, chat, state)
        cls.render(db, key, chat, state, result.message)
