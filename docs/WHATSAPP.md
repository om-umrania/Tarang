# WhatsApp conflict monitoring

Implemented 1 October 2026. Receive-only Cloud API adapter; real WhatsApp delivery
has NOT been verified. The source choice (direct business-number messages, existing
wedding group, or explicitly forwarded conversations) remains pending. Do not enable
intake until that scope and the sender routes are agreed.

## What it does

Signed webhook -> durable text inbox -> bounded recent context for one wedding ->
OpenRouter structured conflict detector -> source-quoted possible conflict -> operator
review. No WhatsApp messages, financial operations or vendor calls are sent. Telegram
coordination continues separately. Conflicts do not change commitment authority or
prove completion. Review results are recorded in the ledger.

Two additive database tables, `conversation_messages` and `conflicts`, are created on
startup. Existing data is retained. Incoming messages are deduplicated by WhatsApp ID.
Only exact configured business phone ID and sender-to-wedding mappings are accepted.
Different wedding scopes never share model context. The latest 24 text messages are
considered, not complete history. Text is sent to the configured OpenRouter model for
analysis; configure only conversations authorised for that processing. Persisted text
currently has no automatic retention expiry. This prototype has no personal-account
login, archive import or existing-group connector.

## Configure after choosing the source

Set these in the ignored local `.env` for local testing, or on the existing Render
service's Environment page for the deployed app (local `.env` does not update Render):

```dotenv
WHATSAPP_ENABLED=false
WHATSAPP_APP_SECRET=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ROUTES={}
```

- App secret: the Meta app secret, used to verify POST signatures.
- Verify token: your own random secret; use the same value in Meta webhook setup.
- Phone number ID: the Cloud API business number identifier, not its phone number.
- Routes: JSON mapping of authorised sender digits including country code, without `+`,
  to a wedding identifier. Example with fictitious values:
  `{"919000000001":"demo-wedding","919000000002":"demo-wedding"}`.
  Two senders share context only when explicitly assigned the same wedding.
- Set enabled to `true` only after all settings and scope are correct. Empty routes
  fail closed. Setting enabled to `false` pauses intake and processing.

Webhook callback: `https://tarang-prototype.onrender.com/whatsapp/webhook`.
Configure the Meta app's WhatsApp messages subscription and its connection to the
Business account/number. GET verification checks `hub.verify_token` and returns
`hub.challenge`; POST checks `X-Hub-Signature-256` against the raw body and app secret.
Business API credentials/permissions may be needed for Meta-side subscription setup;
this receive-only runtime does not need or use a sending access token.

Primary protocol reference: [Meta's webhook server documentation](https://whatsapp.github.io/WhatsApp-Nodejs-SDK/api-reference/webhooks/start/).
That SDK is archived; this implementation uses Python and implements the documented
signature protocol directly. [Meta's Cloud API collection](https://www.postman.com/meta/whatsapp-business-platform/documentation/wlk6lh4/whatsapp-cloud-api)
is a further setup reference. Current Groups API eligibility and access to an existing
user-created group have not been established; do not promise that a business-number
connection will expose it.

## Verify end to end

Use two authorised synthetic text messages about the same task with contradictory
setup times. Confirm webhook acceptance, two persisted messages marked `done`, and a
possible conflict quoting both real message IDs. Confirm no outgoing WhatsApp message
or operation is created. Resolve/dismiss it in the authenticated operator console,
with a reason. Then test agreement and an explicitly accepted schedule revision to
check false positives. These live steps remain outstanding until connected.

Voice/media messages are marked unsupported; no transcription occurs. Forwarded text
is attributed to its sender, not authenticated as the original speaker. Failed model
calls or invalid source citations retry up to three times, then remain visible as
failed in the console. Restart recovers interrupted analysis. Quotes and IDs are
checked in code; semantic accuracy still needs human review. There are no push alerts;
refresh the operator console to inspect flags. A model call can delay other work in
the shared worker. Free Render sleep and free-model capacity prevent continuous or
real-time guarantees.
