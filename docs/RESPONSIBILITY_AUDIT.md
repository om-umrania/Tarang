# Muskan's coordination burden → Tarang's responsibilities

Reviewed 2 October 2026. The checked-in experience design names Meera and Rohan;
the newer conversation rehearsal names Muskan, Om, Aditya and Anushka. This maps
the rehearsal roles without changing the original competition source materials.
It is a target workflow, not evidence that these integrations are live.

## Who does what

| Work that must not fall back on Muskan | Tarang's responsibility | Human contribution that remains | Current implementation |
|---|---|---|---|
| Reading every group message and maintaining a timeline | Extract sourced promises, dates, changes and dependencies; keep uncertainty visible | Confirm genuinely missing or disputed preferences/dates | Hourly review and bridge implemented; pairing and model acceptance pending |
| Asking whether the vendor is on schedule | Trigger checks from persisted commitments and expected milestones | Vendor supplies actual progress | General due checks implemented; outbound calls are operator requests |
| Spotting a 7 pm setup against a 4 pm deadline | Flag the conflict and investigate recovery without waiting for her prompt | Vendor explains constraints | Group conflict review exists; no automatic group-review-to-recovery dispatch |
| Calling and chasing Aditya | Contact the authorised vendor, track response deadlines and bounded retries | Correct contact and calling permission supplied once | Live calling adapter absent; API documentation awaited |
| Bargaining over the surcharge | Seek ₹1,500 inclusive, preserve scope and 4 pm deadline, collect exact counteroffer | Om approves before agreement in this rehearsal | Authorised rehearsal policy documented; live negotiation unimplemented |
| Comparing options and forwarding quotes | Check feasibility, exclusions, total cost, validity and recommendation | Decide material tradeoffs outside delegated authority | Model can propose operations; live sourcing unimplemented |
| Repeating the vendor's proposal to Om | Prepare one concise approval with exact price, scope, deadline and unresolved terms | Om makes the rehearsal decision; do not route it to Muskan by default | Telegram approval primitives exist; no full negotiated-offer integration |
| Relaying approved instructions to the vendor | Validate exact approval and confirm the agreed terms through a tracked operation | No repeated family coordination | External confirmation remains operator-assisted |
| Coordinating unloading, access and inspection | Ask the designated coordinator for access readiness and verification; chase missing answers | Anushka supplies on-site facts in the illustrative role | No live coordinator messaging adapter or configured identity |
| Inspecting setup remotely or chasing photos herself | Request independent checks against the agreed décor scope; pursue defects | On-site verifier physically checks lights, setup and debris | Evidence ingestion/closure gates exist; evidence collection is operator-assisted |
| Remembering the next follow-up | Persist next observation; escalate meaningful delays, recover after restart | Only respond when an actual decision is required | General scheduler exists; free-host sleep limits timely execution |
| Reconciling “approved,” “paid,” and “ready” | Keep these separate, report evidence and unresolved balances | Authorise finance within configured rules | Budget/approval/evidence controls exist; live payment adapter absent |

Muskan retains aesthetic preferences, personal priorities and any decisions expressly
reserved for her. Being the bride does not automatically make her the approver for
every expense. Om's authority here is limited to the agreed calling rehearsal;
Anushka's proposed coordinator role is not a verified production identity.

## Revised illustrative scene

1. **Muskan, once:** supplies her décor preferences and confirms the relevant event
   plan. Tarang reuses known facts rather than onboarding her again on every issue.
2. **Aditya:** reports that his team now expects to finish at 7 pm.
3. **Tarang:** detects the conflict with the 4 pm readiness requirement, checks the
   authorised recovery route, and contacts Aditya without a prompt from Muskan.
4. **Aditya:** offers extra crew and transport for ₹2,500. Tarang seeks ₹1,500,
   confirms taxes/inclusions and preserves design, quantity and deadline. It does
   not invent competing quotes or promise repeat business to obtain a discount.
5. **Tarang → Om:** presents the actual counteroffer and asks before agreeing.
   Example only: “Aditya offers the same scope ready by 4 pm for ₹2,000 extra,
   including crew, vehicle and taxes. Approve these exact terms?”
6. **After valid approval:** Tarang confirms through the authorised channel and
   retains the setup commitment, with arrival and readiness checks still open.
7. **Tarang → Anushka:** requests access and physical readiness checks through a
   configured contact. If lights fail, Tarang follows up with Aditya and obtains
   a new inspection. It does not ask Muskan to chase the electrician.
8. **Tarang → family:** reports only verified completion, actual lateness and
   separate payment status. Approval or a vendor's “done” message cannot close it.

All dialogue and counteroffers above are fictional. The current runtime must not
claim these steps happened while the required adapters remain unavailable.

## Acceptance test for taking work off Muskan

- Start from a vendor event or a due checkpoint; no “please follow up” prompt.
- Preserve sourced preferences and dates; do not ask Muskan to repeat known facts.
- Never tell Muskan to call, bargain, forward the quote or chase inspection when
  Tarang has an authorised, functioning route to the responsible person.
- Missing tools must produce an honest operator/setup requirement with owner and
  next checkpoint, not a false claim of action or an unexplained task for Muskan.
- Route the rehearsal's exact approval to Om. Price within ceiling still requires
  approval; scope reductions and later completion are not bargaining concessions.
- After approval, continue until independently verified fulfilment or an explicit
  unresolved escalation. Keep unknown payments and defects open.
- Muskan contributes preferences/decisions, not routine coordination messages.
- Record actual group intake, call, counteroffer, approval, follow-up and evidence
  separately. Until those pass, describe this as a target rather than live autonomy.

## Next implementation gaps

1. Pair the dedicated account and pass the structured group-review evaluation.
2. Connect validated group findings to a persistent recovery commitment, preserving
   source references and preventing duplicate recoveries or policy changes.
3. Integrate the documented outbound calling API with bounded attempts, durable
   results and a negotiation policy that cannot agree before exact approval.
4. Configure approved recipients and verification channels, then test the entire
   sequence in isolation before using real wedding commitments.
5. Provide awake compute and durable bridge storage for unattended checks.
