"""Pine Labs bank-payout contracts and Round 3 documented-response integration.

No network or money-moving endpoint is exposed by this module. Operator routes
prepare exact requests and ingest labelled documentation-shaped world responses.
"""

import hashlib
import json
import time
import uuid
from typing import Literal

from pydantic import Field

from .schema import Strict
from .store import Store

UAT = "https://pluraluat.v2.pinepg.in"
CREATE = "/payouts/v3/payments/banks"
STATUS = "/payouts/v3/payments"
DOCS = "https://www.pinelabs.com/docs/online-payments/api/payouts"


class BankBeneficiary(Strict):
    # Chosen by the operator from verified vendor records, never from model text.
    recipient: str = Field(min_length=1, max_length=200)
    verified: Literal[True]
    payee_name: str = Field(min_length=1, max_length=40, pattern=r"^[A-Za-z ]+$")
    account_number: str = Field(pattern=r"^[0-9]{9,18}$")
    branch_code: str = Field(pattern=r"^[A-Z]{4}0[A-Z0-9]{6}$")
    mode: Literal["IMPS", "NEFT", "RTGS"] = "IMPS"


class DocumentedPayoutResult(Strict):
    endpoint: Literal["create", "status"]
    response: dict


class Payments:
    def __init__(self, store):
        self.store = store

    @staticmethod
    def operation(db, oid, prepare=False):
        op = db.execute("SELECT * FROM operations WHERE id=?", (oid,)).fetchone()
        if not op or op["state"] not in {"operator_pending", "unknown"}:
            raise ValueError("An authorised pending payment is required")
        c = db.execute(
            "SELECT * FROM commitments WHERE id=?", (op["commitment"],)
        ).fetchone()
        if prepare and (
            c["paused"] or c["state"] != "open" or op["expires"] <= time.time()
        ):
            raise ValueError("Payment preparation is paused, closed or expired")
        proposal = json.loads(op["proposal"])
        if proposal["kind"] != "payment" or not 100 <= op["amount"] <= 100000000:
            raise ValueError("Bank payouts require a payment of at least INR 1")
        return op, proposal

    def prepare(self, oid, beneficiary):
        with self.store.tx() as db:
            op, proposal = self.operation(db, oid, prepare=True)
            if beneficiary.recipient != proposal["recipient"]:
                raise ValueError("Beneficiary does not match the authorised recipient")
            # Preparation cannot be used after authority/budget was revoked.
            budget = db.execute(
                "SELECT * FROM budgets WHERE category=?", (op["category"],)
            ).fetchone()
            if not budget:
                raise ValueError("Approved category budget is required")
            delegated = (
                budget["delegated"]
                and op["amount"] <= budget["cap"]
                and proposal["recipient"] == budget["recipient"]
                and proposal["specification"] == budget["scope"]
                and proposal["kind"] == budget["kind"]
            )
            approved = any(
                (entry := json.loads(row["data"])).get("operation_id") == oid
                and entry.get("decision") == "approve"
                and entry.get("exact_proposal") == proposal
                for row in db.execute(
                    "SELECT data FROM ledger WHERE commitment=? AND kind='scoped_approval'",
                    (op["commitment"],),
                )
            )
            if not delegated and not approved:
                raise ValueError("Current delegation or exact approval is required")
            namespace = db.execute(
                "SELECT value FROM metadata WHERE key='payout_namespace'"
            ).fetchone()
            if not namespace:
                value = str(uuid.uuid4())
                db.execute(
                    "INSERT INTO metadata VALUES('payout_namespace',?)", (value,)
                )
            else:
                value = namespace["value"]
            reference = str(uuid.uuid5(uuid.UUID(value), str(oid)))
            body = {
                "clientReferenceId": reference,
                "payeeName": beneficiary.payee_name,
                "accountNumber": beneficiary.account_number,
                "branchCode": beneficiary.branch_code,
                "amount": {"value": op["amount"], "currency": "INR"},
                "mode": beneficiary.mode,
                "remarks": f"Tarang payment {oid}",
            }
            fingerprint = hashlib.sha256(
                json.dumps(body, sort_keys=True).encode()
            ).hexdigest()
            key = f"payout_packet:{oid}"
            old = db.execute(
                "SELECT value FROM metadata WHERE key=?", (key,)
            ).fetchone()
            if old and json.loads(old["value"])["request_hash"] != fingerprint:
                raise ValueError(
                    "Payment details changed; create a new approved proposal"
                )
            safe = {
                k: body[k] for k in ("clientReferenceId", "payeeName", "amount", "mode")
            }
            safe["account_last4"] = beneficiary.account_number[-4:]
            packet = {"request_hash": fingerprint, "expected": safe}
            if not old:
                db.execute(
                    "INSERT INTO metadata VALUES(?,?)", (key, json.dumps(packet))
                )
                Store.log(
                    db,
                    op["commitment"],
                    "payout_request_prepared",
                    {
                        "operation_id": oid,
                        "endpoint": CREATE,
                        "mode": "documented-response",
                        "request_hash": fingerprint,
                        "clientReferenceId": reference,
                    },
                )
            return {
                "operation_id": oid,
                "mode": "documented-response",
                "executed": False,
                "method": "POST",
                "url": UAT + CREATE,
                "request": body,
                "documentation": DOCS,
                "next_observation": {
                    "method": "GET",
                    "url": UAT + STATUS,
                    "query": {"clientReferenceId": reference},
                },
            }

    def record(self, oid, incoming):
        if len(json.dumps(incoming.response)) > 20000:
            raise ValueError("Response exceeds evidence limit")
        with self.store.tx() as db:
            op, _ = self.operation(db, oid)
            row = db.execute(
                "SELECT value FROM metadata WHERE key=?", (f"payout_packet:{oid}",)
            ).fetchone()
            if not row:
                raise ValueError("Prepare the exact payment request first")
            expected = json.loads(row["value"])["expected"]
            raw = incoming.response
            if incoming.endpoint == "status":
                items = raw.get("payments")
                if not isinstance(items, list):
                    raise ValueError("Status response must contain payments")
                matching = [
                    x
                    for x in items
                    if isinstance(x, dict)
                    and x.get("clientReferenceId") == expected["clientReferenceId"]
                ]
                if len(matching) != 1:
                    raise ValueError("Exactly one matching payout record is required")
                raw = matching[0]
            for field in ("clientReferenceId", "payeeName", "amount", "mode"):
                if raw.get(field) != expected[field]:
                    raise ValueError(
                        "Payout response does not match the approved request"
                    )
            if not isinstance(raw.get("accountNumber"), str) or not raw[
                "accountNumber"
            ].endswith(expected["account_last4"]):
                raise ValueError("Payout beneficiary account does not match")
            if (
                not isinstance(raw.get("paymentReferenceId"), str)
                or not raw["paymentReferenceId"]
            ):
                raise ValueError("Payment reference is required")
            status = raw.get("status")
            if status not in {
                "SCHEDULED",
                "PENDING",
                "PROCESSING",
                "PROCESSED",
                "SUCCESS",
                "FAILED",
            }:
                raise ValueError(
                    "Unsupported payout status; reconcile before continuing"
                )
            # Processed is bank processing, NOT confirmation of successful credit.
            result = (
                "succeeded"
                if status == "SUCCESS"
                else "failed"
                if status == "FAILED"
                else "unknown"
            )
            for fee_field in ("fees", "tax"):
                fee = raw.get(fee_field)
                if fee is not None and fee != {"currency": "INR", "value": 0}:
                    raise ValueError(
                        "Additional fees or tax need reconciliation against the approved total"
                    )
            safe = {
                k: raw.get(k)
                for k in (
                    "clientReferenceId",
                    "paymentReferenceId",
                    "status",
                    "amount",
                    "mode",
                    "bankTransactionReferenceId",
                )
            }
            content = json.dumps(
                {
                    "endpoint": CREATE if incoming.endpoint == "create" else STATUS,
                    "mode": "documented-response",
                    "response": safe,
                    "real_payment": False,
                }
            )
            eid = db.execute(
                "INSERT INTO evidence(commitment,operation,source,mode,content,verifies,created) VALUES(?,?,?,'documented-response',?,0,?)",
                (op["commitment"], oid, DOCS, content, time.time()),
            ).lastrowid
            db.execute("UPDATE operations SET state=? WHERE id=?", (result, oid))
            Store.log(
                db,
                op["commitment"],
                "documented_payout_result",
                {
                    "operation_id": oid,
                    "evidence_id": eid,
                    "result": result,
                    "status": status,
                    "real_payment": False,
                },
            )
            Store.event(
                db,
                f"evidence:{eid}",
                op["commitment"],
                "operator",
                {"evidence_id": eid, "mode": "documented-response", "result": result},
            )
            if result == "unknown":
                db.execute(
                    "UPDATE commitments SET next_check=CASE WHEN next_check>? THEN ? ELSE next_check END WHERE id=?",
                    (time.time() + 60, time.time() + 60, op["commitment"]),
                )
            return {
                "evidence_id": eid,
                "state": result,
                "provider_status": status,
                "real_payment": False,
                "verifies_outcome": False,
                "next_observation": None
                if result != "unknown"
                else {
                    "owner": "operator",
                    "endpoint": STATUS,
                    "query": {"clientReferenceId": expected["clientReferenceId"]},
                    "due_utc_epoch": time.time() + 60,
                },
            }
