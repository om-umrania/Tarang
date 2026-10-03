# Pine Labs payments — Round 3 implementation

Reviewed 3 October 2026. This is Pine Labs/Plural, the payments rail. Pinecone is
not required for this payment integration.

## Source requirements

Read Muskan's 30 September emails in the Masters' Union mailbox:

- [Round 3 official brief](https://mail.google.com/mail/u/?authuser=om.umrania2028%40mastersunion.org#all/1a0f262b15493a2c): use a running model for decisions, actual Gnani API responses, and documentation-shaped Pine Labs/Delhivery responses. External events must have a real source. Record every rail request/response and human message; recording maximum five minutes. Submission deadline stated: 4 October 2026, 11:59 PM IST.
- [KEN ROUND 3: AGENT MAKING](https://mail.google.com/mail/u/?authuser=om.umrania2028%40mastersunion.org#all/1a0f2616e6c8f564): read both `Scenario - Voice and Payment.pdf` and `The Ken Case Competition.docx` in full. They propose delegated vendor advances, an exceptional logistics expense requiring approval, and a final payment after delivery.
- Read the forwarded Round 2 instructions and organiser FAQ; their no-build restriction applies to Round 2, not the later Round 3 brief.

The scenario attachment uses a INR 35,000 backup decorator within a INR 40,000
ceiling, an unspecified advance, a INR 6,000 logistics exception, and an alternative
INR 400 priority courier payment. These are team-authored scenario assumptions,
not an actual bank mandate or provider response. The advance/final split is still
unspecified. Om's later INR 1,200 approved courier budget remains the canonical
prototype decision; do not silently replace it with the attachment's INR 400.

A voice transcript, a Telegram approval and a merchant subscription mandate are
not interchangeable. Tarang's delegation binds category, amount, recipient and
scope. A provider funding/mandate arrangement must separately authorise the
actual source of funds and eligible beneficiaries.

## Verified documentation contracts

Official [OpenAPI download](https://www.pinelabs.com/docs/online-payments/api/downloads/openapi-spec)
was read alongside the [Pine Labs API reference](https://www.pinelabs.com/docs/online-payments/api/payouts).
The private downloaded snapshot is `.runtime/pinelabs-openapi.yaml`.

| Purpose | Exact documented contract | Interpretation |
|---|---|---|
| Authentication | `POST /api/auth/v1/token` | JSON client_id, client_secret, grant_type=client_credentials; returns access_token and expires_at |
| Bank payout | `POST /payouts/v3/payments/banks` | Bank beneficiary, amount in paisa, mode, remarks, stable clientReferenceId; 201 means created/scheduled |
| Reconciliation | `GET /payouts/v3/payments?clientReferenceId=...` | Match exact client reference, beneficiary, amount, mode and payment reference |
| Funding | `GET /payouts/v3/payments/funding-account` | Linked funding account and balance; available only when an account is linked |

UAT host: `https://pluraluat.v2.pinepg.in`. Production host in the documentation:
`https://api.pluralpay.in`; this implementation does not execute against it.
Payout clientReferenceId is documented as the idempotency key. Do not derive it
from a fresh model key for each retry. Bank fields: payeeName, accountNumber,
branchCode (IFSC). Only bank IMPS/NEFT/RTGS packets are implemented here; UPI VPA
and subscriptions are separate contracts. INR 1,200 is `amount.value=120000`.

SCHEDULED is receipt of instruction, PENDING can mean insufficient funding,
PROCESSING/PROCESSED remain unconfirmed, SUCCESS means debit and credit success,
and FAILED means failure. All intermediate states retain the local obligation.
Additional fees/tax require reconciliation against the approved total.

The [agent toolkit](https://www.pinelabs.com/docs/online-payments/ai/agent-enablement-toolkit)
currently lists order/get/cancel/refund tools. Adding it alone does not implement
Tarang's vendor payout or category budget. Do not infer a maker-checker approval
API, a category-ceiling API or delivery-triggered escrow endpoint from dashboard
features or subscription permission APIs. Those exact contracts remain unverified.
Final vendor payment must be a separate authorised payment after acceptable
outcome evidence; logistics tracking alone does not prove complete décor readiness.

## Implemented operator flow

`tarang/payments.py` adds two operator-authenticated local API routes:

1. `POST /api/payments/{operation_id}/prepare`, JSON beneficiary:
   recipient, verified=true, payee_name, account_number, branch_code, mode.
   The operation must already be a payment in operator_pending/unknown state,
   have an open unpaused commitment, unexpired proposal, category budget, and
   current exact delegation or a previously recorded exact Telegram approval.
   The beneficiary's recipient must equal the approved recipient. Returns the
   documented method/URL, full request and next status-query packet. No request
   is sent to Pine Labs. The model never supplies the bank destination.
2. `POST /api/payments/{operation_id}/documented-result`, JSON with endpoint
   `create` or `status`, and the documentation-shaped response. A status response
   wraps matching records in `payments`. The response must match the prepared
   reference, amount, currency, payee, account suffix and payment mode. Unknown
   statuses/mismatches/additional fees are rejected. The resulting evidence is
   always marked documented-response, real_payment=false, verifies_outcome=false.

The request hash, stable UUID reference and minimal beneficiary identity are
stored using the existing metadata table. No schema migration or bank account
persistence is added. Changing beneficiary/payment details under an existing
reference is blocked. The full account is returned only to the authenticated
operator preparing the request; keep any full packet receipt private. Ledger and
state evidence retain only reconciliation identifiers and a redacted projection.
For the competition recording, show the original request and exact raw documented
response as well as the normalized interpretation, using fictional bank details.
No token generation response, secret or real bank number should appear on camera.

These routes feed results back to the existing model event loop. They do not
create a new spend, grant authority, initiate a real transfer, close the outcome,
or expose payment controls to public demo visitors. Unknown payments persist a
next observation within 60 seconds with the operator responsible for the provider
status; the scheduler can prompt follow-up, but does not fabricate that response.
Failed/successful terminal results cannot be overwritten by a later response.

## What Om needs to provide for the next stage

For Round 3 documented simulation: no Pine Labs key is required. Provide fictional
verified beneficiary details, exact category/transaction limits, total inclusive
cost, advance/final split, approver and delivery evidence. The wizard supplies
only the documented world response, never a suggested next model decision.

For an actual UAT integration: create an Online/Plural sandbox merchant account,
confirm Payouts entitlement, obtain its client_id/client_secret, link an eligible
test funding account and use Pine Labs-approved test beneficiary details. Configure
`PINE_CLIENT_ID` and `PINE_CLIENT_SECRET` privately in `.env`, not in chat. Run
`.venv/bin/python scripts/check_pinelabs_sandbox.py` for authentication and a
read-only balance check. That script does not submit a payout or print accounts,
credentials or balance. It is currently blocked because these credentials are
absent; no live Pine Labs call or payment was performed.

Production needs provider-approved onboarding/funding, verified beneficiaries,
exact spending authority, fee reservation, durable dispatch/reconciliation,
revocation, authenticated status events and a tested source-of-funds model for
paying on behalf of a family. An API credential alone does not provide that model.
Actual money-moving dispatch is not implemented or enabled in this iteration.

## Validation

Run `python3 -m pytest tests/test_payments.py -q` and `./scripts/check.sh`.
Tests exercise model-created delegated operations, exact Telegram approvals,
operator API authentication, revocation/pause/expiry, immutable destinations,
response correlation, intermediate reservations, terminal monotonicity and no
payment-based outcome closure. These are contract tests using authored responses;
they are not live Pine Labs transactions or a completed competition simulation.

Validation result: 99 runtime tests and static checks passed after adding the
payment contracts. The sandbox readiness probe reported missing credentials
before making any external request. SQLite is verified; PostgreSQL parity for
these new payment tests has not been run. Settings credentials/connection strings
are excluded from diagnostic representations; new tests use blank provider keys.
