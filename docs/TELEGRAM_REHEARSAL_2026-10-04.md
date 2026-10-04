# Telegram rehearsal — 4 October 2026

Observed in the native Telegram app at approximately 21:21–21:24 IST.
All vendor actions, approval amounts and inspections below are fictional.

## Observed live

- The Tarang chat displayed the décor recovery sequence: ₹2,500 quote,
  ₹2,000 counteroffer, simulation approval, failed lighting inspection and final
  physical-readiness inspection at 4:25 pm. The final message explicitly kept
  payment unverified and stated that no vendor was contacted or money moved.
- A free-text question was sent through the Telegram composer asking why the
  outcome stayed open after approval and what remained unverified.
- The bot answered, but incorrectly described fictional approval as still pending.
  This contradicted the earlier recorded approval.
- Authenticated hosted `/api/state` returned the final-inspection reply in outbox
  row 83 and the AI explanation in row 84. Both were also visible in Telegram.
  No delivery-status field was returned by that snapshot; UI visibility is the
  delivery evidence here. Credentials and chat identifiers are omitted.

## Fix and validation

The guided model context previously included the initial scenario and current
step, but omitted intervening button-controlled events. It now includes only the
ordered steps already reached. The explanation prompt prioritises that record
over stale dialogue and distinguishes approval, physical readiness and payment.
The regression check covers both initial-stage future-event exclusion and final
stage retention of the negotiated amount, approval, defect and payment uncertainty.

`./scripts/check.sh`: static checks, 3 bridge tests and 125 Python tests passed.
This validates context construction, not the correctness of a newly deployed
model reply. The fix remains local and has not been pushed or released.

## Remaining end-to-end boundaries

- Hosted `/health`: HTTP 200; demo and interactive demo enabled; voice unconfigured.
- Hosted `/api/dashboard`: HTTP 404. The Telegram-to-live-dashboard chain is not
  complete and should not be presented as a successful final dashboard demo.
- Hosted `/api/state`: HTTP 200 and saved replies verified, but this endpoint does
  not establish the backing database engine. Live PostgreSQL provenance for this
  conversation remains unverified. The separate PostgreSQL integration rehearsal
  is documented in `TELEGRAM_DASHBOARD_E2E.md`; it uses synthetic Telegram transport.
- No real payment, vendor agreement or booking was attempted. No Vercel deployment,
  deployment-setting change or PR merge was performed.
