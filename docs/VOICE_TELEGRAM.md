# Telegram voice conversation

3 October 2026. Implementation and automated contracts are complete. Live Gnani
speech and a real Telegram voice round trip await a configured speech credential.
Calls are a separate integration; this version uses asynchronous voice notes.

## Conversation

1. Open [Tarang](https://t.me/tarang_wedding_bot?start=demo), send `/start demo`, then `/talk`.
2. Send `/voice` (English) or `/voice hi-IN` (Hindi recognition). This opts into
   Gnani processing of recordings and reply text. Use fictional details only.
3. Record a Telegram voice note, ideally 30 seconds, maximum 60 seconds and 10 MB.
4. Tarang displays **I heard** with the transcript. Check names, times and amounts.
   Select **Use this transcript** or send `/heard`. `/discard` rejects it; a typed
   correction supersedes the unconfirmed recording.
5. The confirmed answer runs through the same intake, plan review and feedback as
   text. Tarang's replies retain text/buttons and also produce an AI voice note.
6. `/voice off` stops voice processing and pending voice replies. `/reset`,
   `/delete` and leaving the conversation clear pending recordings; reset/delete
   also clear voice preferences. Re-enable `/voice` after resetting.

Voice mode is restricted to the isolated fictional conversation. Recordings never
enter operational approval handling. Recognition does not grant spending authority.
The first version's deterministic questions and suggestions are English; selecting
Hindi recognition does not establish complete Hindi localisation. Kaveri is the
configurable English catalogue voice; Hindi mode selects Nalini. These are prototype
choices, not Om's confirmed voice identity. Voice cloning is not used.

## Setup

Configure `GNANI_API_KEY` privately in ignored `.env` and the existing Render secret
file `/etc/secrets/tarang.env`, or Render environment variables. `GNANI_VOICE` can
select the English catalogue voice (default Kaveri). Do not paste keys into chat,
Git, command arguments or recordings. `/health` reports `voice_configured`, never
credentials. The service must restart/redeploy after changing its configuration.
Without a key, `/voice` explicitly reports unavailable and does not download audio.
No additional paid hosting or services were created. Gnani usage/credits are separate.

The adapters implement official [Gnani STT](https://docs.gnani.ai/api/STT/speech-to-text)
and [TTS](https://docs.gnani.ai/api/TTS/tts-inference) contracts. OGG Opus is uploaded
using [Telegram sendVoice](https://core.telegram.org/bots/api#sendvoice). No new audio
package or media conversion binary is needed.

## Persistence and failure handling

Two additive tables hold voice preference and one pending transcription/review job
per demo chat. Audio bytes are downloaded and processed in memory, never written to
Tarang's filesystem or database. Telegram and Gnani have separate retention policies.
Unconfirmed transcript and file reference are cleared on reset/delete, superseding
text, or scenario switch. Review transcripts retain the same seven-day inactive-demo
retention as existing text. Provider responses/URLs/credentials are not logged.

Input identity, Telegram deduplication, webhook secret and demo consent apply before
queuing a voice job. Limits: ten STT notes per visitor/day, 100 service-wide; twenty
TTS replies per visitor/day, 200 service-wide, resetting at midnight IST. Existing
input and model limits still apply. Quota exhaustion leaves text/buttons available.
Raw audio is capped again during download; external requests have bounded timeouts.
A crashed STT job asks for a new recording rather than replaying the provider call.

Generated speech uses the existing durable outbox, after a successful text delivery.
Synthesis failure preserves text and supplies a fallback notice. Ambiguous Telegram
voice sends become `unknown` and are not retried automatically. Opt-in and session
are checked again before audio transmission. An already-transmitted Telegram note
cannot be recalled by `/voice off`. Free-host waking and speech-provider processing
add latency; this is not a streaming call experience.

## Verification and next live acceptance

72 runtime tests and static checks passed. All 37 public-demo/intake/voice checks
passed against disposable PostgreSQL. Fourteen voice tests cover opt-in, limits,
identity/isolation, confirmation, correction, reset/delete/off races, provider/crash
failure, quotas, spoken output, ambiguous sends, HTTP contracts and a signed webhook
through intake. Fake audio and fake providers establish contracts, not speech quality.

Run `.venv/bin/python scripts/evaluate_voice.py` after configuring the key. This uses
only synthetic TTS audio and checks a live STT round trip, saving an ignored private
receipt. It currently reports missing credential without making a speech request.
Then use the real Telegram client to record a fictional problem, verify transcription,
confirm it, listen to the spoken question, correct a date, and finish feedback.
Check quiet/noisy audio, names/amounts, Hindi/mixed speech, and failed-provider fallback
before promoting voice quality. The full persona rubric remains separately unexecuted.

### Deployed readiness check

Commit `b2de1413435d6281032521deea4201e43f8281d9` was deployed to the existing free
service as `dep-db0a52mgekts738qj3i0`, live at 06:37:57 UTC on 3 October.
Hosted health returned 200 and `voice_configured: false`. A real Mac Telegram
`/voice` turn at 12:08 IST displayed the explicit missing-configuration message;
the reply was recorded `sent`, and the webhook backlog was zero. This confirms
routing and honest fallback, not a successful audio interaction. Private receipt:
`.runtime/telegram-voice-readiness.json`. GNANI_API_KEY remains the live-test blocker.
