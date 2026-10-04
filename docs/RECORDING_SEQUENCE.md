# Clean recording sequence

Prepared 4 October 2026. Recording pending release and live verification.

For copy-ready input messages across the Jaipur, décor, hamper, voice and correction
cases, use the [conversation test runbook](CONVERSATION_TEST_RUNBOOK.md).

Use one décor story throughout. Keep the welcome disclosure once, before the
use-case conversation. The greeting states the capability limits without demo or
rehearsal labels. Do not repeat those labels in ordinary messages or buttons.
Retain this disclosure in the opening caption: “Prototype:
vendor responses, inspections and payments are simulated.” Do not present the
scripted external events as actual vendor execution.

1. Open a new scenario from the menu without deleting existing chat evidence.
2. Show the problem: setup needed at 4 pm; vendor forecasts 7 pm; guests at 5 pm.
3. View vendor update: extra crew and transport quoted at ₹2,500.
4. Review counteroffer: ₹2,000 inclusive, unchanged design and readiness deadline.
5. Ask: “Why do you need approval if this is below ₹2,500?”
6. Select “Approve ₹2,000”; show the recorded approval.
7. Review setup inspection: entrance lights fail; the outcome stays open.
8. Review final inspection: readiness at 4:25 pm, 25 minutes late; payment unverified.
9. Ask: “What is complete, and what is still waiting?” Verify that the answer
   remembers the ₹2,000 approval and distinguishes readiness from payment.
10. Show the same conversation's saved dashboard evidence only after the hosted
    dashboard endpoint works and the entries are correlated with Telegram.

Do not capture a final take from the currently deployed older bot: it still has
the old wording. Release requires the normal approved GitHub workflow. A local
test or saved outbox record alone does not prove the live dashboard/PostgreSQL path.

The copy changes preserve session isolation, authority checks and lack of real
payment/vendor execution. Privacy and explicit capability questions remain truthful.
