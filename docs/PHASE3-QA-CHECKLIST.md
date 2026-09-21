# Coil Phase 3 review and acceptance checklist

Reviewed September 21, 2026 against application baseline `20571c2` and the eight Phase 3 tools in `/Users/iandolan/General/coil-legal-astro/src/data/coil-phases.json`. Website phases differ from historical test filenames. This is a code inventory and an execution checklist, not a claim that Phase 3 works end to end.

Finish executable Phase 1 acceptance first. Provider-blocked checks remain open while independent Phase 2 and Phase 3 work proceeds. Use synthetic records, record the deployed commit, and keep credentials and usable client links out of evidence. Each case needs PASS, FAIL, BLOCKED or NOT BUILT with fixture IDs and evidence. Unchecked cases are NOT RUN unless stated otherwise.

## Current implementation

| Tool | What exists | Remaining gate |
| --- | --- | --- |
| Harfree AI workbench | Website describes a separate optional Mike-based service. No completed deployment or connection was established in this review. | Identify the actual service, version and authenticated Coil connection. BLOCKED on that inventory. |
| Email filing | `app/blueprints/emailin.py` implements IMAP, deduplication, attachments and manual filing. Real AgentMail receipt, one-message deduplication and manual filing passed in the earlier Phase 1 setup. | Auto-routing, attachments, failures and restart coverage remain open. A mailbox is now available; the old readiness note saying none exists is stale. |
| Phone intake | `app/blueprints/voice.py` implements intake/status/memo APIs and reminder calls. The phone bridge is a separate service. | Prove the configured number reaches the right agent and files one lead. PIN sessions and failure counts live in process memory, while deployment uses two workers; this needs a multiple-process regression before approval. |
| Credit notes and refunds | Invoice credit-note routes and 13 credit-note tests exist. Paid-in-full credit requests explicitly refuse because operating-account refunds are not implemented. | Unpaid credits can be reviewed now. Paid refunds are NOT BUILT, not a failed provider setup. Trust refunds are a different transaction. |
| Document figure checks | AI grounding includes source amounts. No dedicated deterministic document-versus-case amount checker was found. | NOT BUILT in the inspected application. Define supported record fields and comparisons before implementation. |
| Two-way QuickBooks | `app/blueprints/exports.py` provides customer, invoice and payment CSV layouts. No live QuickBooks sync connector was found. | NOT BUILT in the inspected application. Requires a sandbox company and a defined conflict policy. |
| Right-to-left PDFs | `app/services/pdf.py` has Unicode font fallback. No shaping call was found; existing readiness notes acknowledge incorrect shaping/order. | Choose supported fonts and shaping, then visually review Arabic and Hebrew samples with a competent reader. |
| Court e-filing | No filing-provider integration was found. Website says a vendor has not been selected. | NOT BUILT. Requires a provider, supported jurisdiction and vendor sandbox. Never submit a real filing as QA. |

## Harfree AI workbench

- [ ] P3-AI-01: Identify service URL, deployed version, owner and model configuration. Verify login and the intended firm's scoped Coil token.
- [ ] P3-AI-02: Read a synthetic matter over the actual HTTP MCP connection. Compare source IDs, names and amounts with Coil; repeat in redacted mode.
- [ ] P3-AI-03: Draft a document and invoice without sending either. Revoke the token and confirm subsequent access stops. Provider failure must not be described as completed work.

## Email filing

- [ ] P3-MAIL-01: Send two real synthetic messages to the configured QA mailbox, including one with a recognized matter number. Verify automatic routing only when unambiguous; confirm the other remains unfiled. Previous manual-filing evidence is in `docs/PHASE1-READINESS.md`.
- [ ] P3-MAIL-02: Attach a valid PDF, Unicode-named text file, empty file and disallowed executable fixture. Check attachment bytes, validation errors and document search after filing. One attachment failure must be visible.
- [ ] P3-MAIL-03: Fetch the same Message-ID twice, restart, and fetch again. Verify one message and one copy of each attachment. Exercise messages without a Message-ID and record the deduplication policy.
- [ ] P3-MAIL-04: Disconnect IMAP during fetch and during filing. Restore access and verify retry neither loses a message nor duplicates it. Record credential failures without printing credentials.
- [ ] P3-MAIL-05: Have Grok file and refile a message in the UI. Confirm matter/client association and permissions, and verify a portal client cannot read another client's email.

## Phone intake

- [ ] P3-VOICE-01: Inspect current Twilio routing and the bridge health before making a call. Verify which agent answers the actual number; do not repoint a shared demonstration number without resolving its existing use.
- [ ] P3-VOICE-02: Run a synthetic after-hours call. Confirm the approved opening, read-back, callback expectations, one intake lead and one matching call record. Record audio/transcript only through the established QA harness.
- [ ] P3-VOICE-03: Test interruption, dropped call and retried submission. The agent must report successful filing only after Coil confirms it, with no duplicate lead.
- [ ] P3-VOICE-04: Test an advice request, incorrect identity and sensitive information in a synthetic script. Compare spoken responses and stored records with the firm's configured rules.
- [ ] P3-VOICE-05: Verify attorney PIN and subsequent memo across distinct application workers. Repeat incorrect PIN attempts across workers; expiry and lockout must apply consistently. Code review found process-local state, so this is a release gate for attorney phone actions.

## Credit notes and refunds

- [ ] P3-CREDIT-01: On a 100.00 unpaid invoice, credit 25.00. Verify the 75.00 balance, credit PDF, audit entry, statement and exports without moving cash or trust.
- [ ] P3-CREDIT-02: On a partially paid invoice, credit only the remaining balance. Reject excess, duplicate and concurrent credits without negative balances.
- [ ] P3-CREDIT-03: Attempt a credit on a fully paid invoice. Current expected behavior is a clear refusal; no reversal of income or fictitious cash movement. This verifies the guard, not refund support.
- [ ] P3-CREDIT-04: Once operating refunds exist, use a provider sandbox to prove partial/full refunds, delivery retries, failed refunds, reconciliation and the original payment link. BLOCKED by missing implementation and test-mode provider access.

## Document figure checks

- [ ] P3-FIG-01: Specify supported fields, currencies, source types and evidence references. An unrelated dollar figure must not be treated as a contradiction.
- [ ] P3-FIG-02: Use a synthetic demand with one matching amount, one inconsistent amount and one explicitly corrected amount. Expect cited discrepancies and no invented source figures.
- [ ] P3-FIG-03: Test OCR uncertainty, ranges, negative numbers, cents and multiple currencies. Unreadable evidence must be reported as unchecked.

All three figure-check cases are NOT BUILT pending a dedicated checker.

## Two-way QuickBooks

- [ ] P3-QBO-01: Define which system owns each field and connect a sandbox company with the minimum scopes. Match accounts and currencies explicitly.
- [ ] P3-QBO-02: Round-trip a synthetic customer, invoice and payment; replay notifications and verify no duplicates. Include credits only if supported.
- [ ] P3-QBO-03: Change a record on both sides, expire access and interrupt sync. Resolve conflicts visibly and reconcile integer minor-unit totals after recovery.

All three live-sync cases are NOT BUILT. CSV export checks do not satisfy them.

## Right-to-left PDFs

- [ ] P3-RTL-01: Render Arabic and Hebrew names, paragraphs and mixed Latin identifiers. Verify shaping, reading order, punctuation, wrapping and searchable text.
- [ ] P3-RTL-02: Repeat in invoice, engagement letter, signature certificate and statement PDFs, including long names and numbers with currency codes.
- [ ] P3-RTL-03: Inspect rendered pages with a competent reader and verify font embedding on another viewer. Keep the approved samples as regression artifacts.

## Court e-filing

- [ ] P3-FILE-01: Select a vendor and jurisdiction; establish sandbox credentials, document constraints and the acceptance receipt contract.
- [ ] P3-FILE-02: Submit synthetic filings in the vendor sandbox, including oversized files and missing required fields. Distinguish submitted, accepted and rejected states.
- [ ] P3-FILE-03: Retry after a lost response and process delayed/duplicate receipts. Verify no duplicate filing, clear fee treatment and retained audit history.

All three e-filing cases are NOT BUILT. No production submission is authorized by this QA checklist.
