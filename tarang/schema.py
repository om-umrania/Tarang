from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Operation(Strict):
    key: str = Field(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9_-]+$")
    kind: Literal["call", "quote", "booking", "payment", "shipment", "tracking"]
    recipient: str = Field(min_length=1, max_length=200)
    category: str = Field(min_length=1, max_length=80)
    amount_paise: int = Field(ge=0, le=100000000)
    specification: str = Field(min_length=1, max_length=2000)
    expires_in_seconds: int = Field(ge=60, le=86400)


class Decision(Strict):
    reason: str = Field(max_length=1000)
    message: str = Field(max_length=3000)
    outcome: str = Field(min_length=1, max_length=1000)
    owner: str = Field(min_length=1, max_length=200)
    next_check_seconds: int = Field(ge=30, le=86400)
    operation: Operation | None = None
    close_with_evidence: list[int] = Field(default_factory=list, max_length=20)


class EvidenceInput(Strict):
    commitment_id: int
    operation_id: int | None = None
    source: str = Field(min_length=1, max_length=500)
    mode: Literal[
        "manual-real-api",
        "documented-response",
        "illustrative-fixture",
        "human-verification",
    ]
    content: str = Field(min_length=1, max_length=20000)
    result: Literal["observation", "succeeded", "failed", "unknown"] = "observation"
    verifies_outcome: bool = False


class BudgetInput(Strict):
    category: str = Field(min_length=1, max_length=80)
    ceiling_paise: int = Field(ge=0)
    autonomous_limit_paise: int = Field(ge=0)
    delegate_spend: bool = False
    recipient: str = Field(min_length=1, max_length=200)
    kind: Literal["payment", "booking", "shipment"]
    scope: str = Field(min_length=1, max_length=2000)


class CheckInput(Strict):
    commitment_id: int
    delay_seconds: int = Field(ge=30, le=86400)


class ConflictSource(Strict):
    message_id: int
    quote: str = Field(min_length=1, max_length=1000)


class Conflict(Strict):
    kind: Literal[
        "schedule", "budget", "quantity", "specification", "responsibility", "delivery"
    ]
    summary: str = Field(min_length=1, max_length=1000)
    sources: list[ConflictSource] = Field(min_length=2, max_length=6)
    clarification: str = Field(min_length=1, max_length=500)


class ConflictReport(Strict):
    conflicts: list[Conflict] = Field(max_length=8)


class ConflictReview(Strict):
    state: Literal["resolved", "dismissed", "review"]
    note: str = Field(min_length=1, max_length=1000)


class GroupMessage(Strict):
    source_id: str = Field(min_length=1, max_length=300)
    external_id: str = Field(min_length=1, max_length=300)
    sender: str = Field(min_length=1, max_length=200)
    text: str = Field(max_length=12000)
    sent_at: float = Field(gt=0)
    kind: Literal["text", "unsupported", "deleted"] = "text"


class GroupBatch(Strict):
    group_id: str = Field(min_length=1, max_length=200)
    connected: bool
    messages: list[GroupMessage] = Field(max_length=100)


class WeddingFact(Strict):
    event: str = Field(min_length=1, max_length=200)
    date_text: str = Field(max_length=300)
    status: Literal[
        "proposed", "source_confirmed", "cancelled", "conflicting", "unknown"
    ]
    source: ConflictSource


class GroupReview(Strict):
    summary: str = Field(max_length=1500)
    wedding_date_status: Literal[
        "unknown", "proposed", "source_confirmed", "conflicting", "past_needs_review"
    ]
    facts: list[WeddingFact] = Field(max_length=40)
    conflicts: list[Conflict] = Field(max_length=8)
    questions: list[str] = Field(max_length=5)
