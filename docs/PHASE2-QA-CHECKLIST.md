# Coil Phase 2 QA checklist

Drafted 2026-09-20 against application commit `6a0f8aa`. These are acceptance checks to execute, not claims that the tools passed. The preceding release passed 649 local tests and 143 deployment-container tests; that evidence does not establish all the behavior below.

## Scope and sources

The seven tools come from the website inventory at `/Users/iandolan/General/coil-legal-astro/src/data/coil-phases.json`, commit `08602d453faf2338729174ac2dc28d09c05eb2df`. This matches the inventory used for Ian's Phase 1 review. The older implementation phases in `docs/CONVENTIONS.md` and test filenames describe different groupings.

`docs/TOOL-READINESS.md` supplies additional checks for conflict speed, reports, AI output and volume. Those appear at the end. Its historical status statements are not current QA results.

## Working order and evidence

Finish or report blockers on Grok's current money-fix queue first: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5747481204. Then prioritize agent invoices, multi-currency and HTTP MCP. Run accessibility when a usable client session is available. Rules, desktop capture and deeper LEDES need the deliverables described below before execution.

Use testfirm with synthetic records. Record `/health` at the start and end of each batch. If the commit changes, identify the affected cases and rerun them on a stable release. Keep demo for health checks. Use a disposable environment for bulk fixture generation and concurrent engineering tests.

Each case begins NOT RUN. Record PASS, FAIL, BLOCKED or NOT BUILT after investigation. Each result needs the commit, fixture IDs, exact steps, expected and actual result, and an evidence file or issue link. A screenshot of a page is not proof that its amounts or backend writes are correct. An HTTP-only pass is not a keyboard or screen-reader pass.

Suggested responsibilities, not new assignments: Codex handles local code review, deterministic fixtures and regression tests; Grok handles independent live workflows and browser evidence; Claude can implement missing features through a separate coordination claim. Nobody is assigned work solely by this document.

Known prerequisites: both sites had live Stripe keys at the last deployment check. Do not perform positive card charges until approved test-mode access exists. Fresh portal links are required after the token migration. Email-dependent checks need a working test mailbox and SMTP delivery. Keep usable tokens and credentials out of reports.

## 1. Multi-currency matters

Status: implementation exists, end-to-end verification pending. Saved-card and installment Checkout paths now refuse non-USD payments; that guard is not evidence of non-USD online-payment support.

Use separate USD, CAD, GBP, EUR, AUD and MXN matters. Keep an independent worksheet in integer minor units. Include a 100.01 invoice, a partial manual payment of 25.01 and a 10.00 credit, producing a 65.00 balance. Use separate fixtures for splits and interest.

- [ ] P2-CUR-01: Create each currency matter and invoice. Verify currency and amounts on matter detail, invoice list/detail, PDF, email and public invoice. Shared symbols such as `$` must have enough context to distinguish CAD, AUD, MXN and USD. No silent conversion.
- [x] P2-CUR-02: Change the firm default after creating an invoice, then change the matter currency. Existing invoice denomination must remain intact. Any restriction on changing a matter with financial activity must be clear.
  - September26 Case33: independent matter-change portion PASS on934a366, matter3078 EUR to CAD to EUR, invoice3044/INV-1045 remained EUR throughout. Both saves confirmed; no invoice created or sent. Grok ACK5851049424, result5851062976. September27 Case36 independently PASS5851558085 on934a366: firm default USD to CAD to USD; invoice3044/INV-1045 stayed EUR and matter3078 stayed EUR. ACK5851535488. Both portions now passed for these fixtures. Wider multi-currency tool remains QA pending. Firm-default evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5851558085. Evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5851062976.
- [ ] P2-CUR-03: Record the manual payment and credit above. Verify 65.00 outstanding across invoice, statement, payment history and applicable exports. Repeat rounding with a split-payer group and confirm group totals agree to the smallest supported unit.
  - September27 Cases38/39 on9cd6964: USD100.01 invoice less25.01 check and10.00 credit correctly leaves65.00, statuspartial. Matter3091/invoice3064/INV-1065/payment13/CN-1018. Filtered statement row/card65.00 passed, but activity closes75.00 and omits CN-1018. Reconciliation remains open, along with split/denomination/export coverage. Evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5852044200.
  - September27 update03:40UTC: credit omission fixed/deployed573222b; seven baseline failures, focused15/full928 passed plus1 skipped/Linux15 passed. Read-only3091/INV-1065/payment13/CN-1018 now closes65.00 with separate paid25.01 and credited10.00; protected records unchanged. Independent HTML/PDF acceptance assigned5852340152, no acknowledgment/results yet. Case40 split independently PASS5852265593 on e2d9e89: matter3092/contact1826, INV-1066 60.01 and INV-1067 40.00, unsent USD drafts totaling100.01. Case41 exports blocked on old gate5852336297, now released on573222b. Remaining denomination/export and broader non-USD coverage keep P2-CUR-03 unchecked. Evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5852340152.
  - September27 update04:16UTC: independent HTML PASS5852513840 and PDF content PASS5852513925 on573222b, ACK5852379150. Fixture3091/INV-1065/payment13/CN-1018 reconciles65.00 with25.01 paid/10.00 credited. Rendered PDF visual inspection is still pending because reported layout evidence used text extraction. ST-CREDIT-VISUAL assigned5852542632, now ACK5852562390; result pending. Export gates below remain open; no full currency signoff.
- [ ] P2-CUR-04: Inspect raw CSV and LEDES behavior. Every supported amount must have an unambiguous denomination. Unsupported export/currency combinations must refuse clearly instead of emitting misleading data. Import an export into the chosen spreadsheet tool to verify it stays numeric.
  - September27 Case41 observation PASS5852514018 on573222b confirms a **denomination defect**: QuickBooks invoice CSV includes EUR INV-1045 with ItemAmount1.00 and no Currency column or EUR text. INV-1065 total100.01 and excluded drafts1066/1067 are correct; matters CSV retains EUR/USD codes. No import/LEDES run. Source confirms invoice/payment QBO headers omit currency. Payment-row observation assigned5852542632, now ACK5852562390; result pending. Recipient-compatible export correction and import acceptance remain outstanding. Evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5852514018.
- [ ] P2-CUR-05: Compare mixed-currency reports and dashboard cards with the source rows. Separate totals by currency or document an explicit conversion method; adding USD and CAD into one dollar total fails. Check the CSV independently.
- [ ] P2-CUR-06: Inspect every online-payment entry point, including ordinary Checkout, saved cards, installments and trust deposit requests. Unsupported denominations must be refused before provider creation. Under approved test mode, any supported flow must create the matching provider currency and amount and reconcile once. Current non-USD saved-card/plan refusal can pass its guard while the broader product claim remains incomplete.

Code/test starting points: `app/helpers.py`, invoice/payment/export/report blueprints; `tests/test_phase2_a.py`, `tests/test_phase2_c.py`, `tests/test_money_review.py`, `tests/test_collection_recovery.py`.

## 2. Web AI tools connected by HTTP MCP

Status: `/mcp` implementation and protocol tests exist. Actual client compatibility must be demonstrated separately.

Prepare scoped synthetic-account tokens in redacted and full modes, plus a read-only token. Use one named, supported HTTP MCP client and record its version. The local stdio bridge is a separate transport.

- [ ] P2-MCP-01: Connect the real client to `/mcp`, initialize, list tools and run a harmless read. Record the negotiated protocol version and actual tool list. Show that the client can use HTTP directly, rather than accidentally exercising the stdio bridge.
- [ ] P2-MCP-02: Compare tool discovery and calls with token scopes. A hidden write tool must also refuse direct invocation. Missing, revoked and deactivated-account tokens must fail without exposing records.
- [ ] P2-MCP-03: In redacted mode, search and read contacts, matters, notes, time and invoices containing distinctive synthetic names and narratives. Inspect raw responses for disclosure. Repeat with a full token as the positive control. The assistant must explain withholding rather than invent identities.
- [ ] P2-MCP-04: Downgrade the token owner's role while the client remains connected. The next prohibited write must fail. A cached tool list cannot grant access. Check another user's existing session remains unaffected.
- [ ] P2-MCP-05: Exercise malformed arguments, unknown tool and a controlled rate-limit response. Errors must be useful; a 429 must remain a rate-limit error with retry guidance. Do not create a sustained load test on shared testfirm.
- [ ] P2-MCP-06: Reconnect after a client/network interruption. Read-only calls recover; a mutation with an uncertain result is checked against Coil before resubmission. Record any duplicate-write behavior as a defect, not a transport success.

Starting points: `app/blueprints/mcp_http.py`, `mcp/coil_mcp.py`, `mcp/README.md`, `tests/test_mcp_http.py`, `tests/test_api_scopes.py`, `tests/test_review_fixes.py`.

## 3. Invoices drafted by an AI agent

Status: REST `POST /api/v1/invoices` and MCP `draft_invoice` exist. Verify both paths against separate identical fixtures.

Fixture: two billable 30-minute entries at 200.00/hour, a 25.00 billable expense, an excluded non-billable item and an already-billed item. Expected new draft: 225.00. Test due and future flat-fee milestones on a separate matter.

- [ ] P2-INV-01: Draft through REST and through the actual MCP client. Compare invoice IDs, currency, line descriptions, source links and the 225.00 total with the UI. The assistant reports the real returned invoice and totals.
- [ ] P2-INV-02: Confirm draft-only behavior. No sending, approval, payment, trust movement or client email occurs. Check pending-approval rules for the creator role and attribution in the audit trail.
- [ ] P2-INV-03: Repeat with full and redacted tokens carrying invoice write scope. Both can perform the allowed operation; redacted responses must still withhold client identity and work narratives. Repeat without write scope and confirm no invoice is created.
- [ ] P2-INV-04: Submit missing/unknown matter IDs, invalid dates, an empty matter and unsupported inputs. Expect a clear refusal without partial writes or a server error. Record the policy for closed matters rather than guessing it.
- [ ] P2-INV-05: Resubmit after a successful draft, then test genuine concurrent requests in a disposable fixture. The same source time, expense or milestone cannot be billed twice. After an uncertain response, verify existing drafts before retrying.
- [ ] P2-INV-06: Repeat for a split-payer matter and for a non-USD matter. Group totals and rounding must match the normal builder, source entries link once and currency remains intact. No online payment is needed for this case.

Starting points: `app/blueprints/api.py:invoice_create`, `app/blueprints/invoices.py:build_for_matter`, MCP `draft_invoice`; `tests/test_phase3_g.py:test_api_invoice_draft_create` and scope/MCP tests. One existing happy-path test is not completion evidence for this section.

## 4. Real jurisdiction court rules

Status: inspected code provides generic federal and Texas starter sets. A maintained, verified jurisdiction package has not been established by this review. Mark that deliverable NOT BUILT or BLOCKED until supplied. These are proposed release requirements, not assertions about current law.

- [ ] P2-RULE-01: Name the exact courts, rule families and exclusions supported. Each rule needs an official source, effective date, last verification date and an identified maintainer. Generic sets remain visibly generic.
- [ ] P2-RULE-02: Obtain independently calculated expected dates from current official rules for each supported trigger. A qualified reviewer signs off the fixture and exceptions before software results are accepted. Do not derive the expected answer using Coil's own calculator.
- [ ] P2-RULE-03: Test forward/backward counting, weekends, applicable court holidays, service methods, leap days and month/year boundaries wherever the selected rules require them. Include local overrides and trigger prerequisites. No silent fallback to an inapplicable rule.
- [ ] P2-RULE-04: Apply a rule twice and confirm no duplicate tasks. Change the trigger and verify which deadlines are recalculated, retained or superseded. Previously completed tasks and manual changes need an explicit policy and audit evidence.
- [ ] P2-RULE-05: Update a rule package. Existing matters retain traceable rule versions and affected deadlines are surfaced for review. Exported calendars must agree with the approved dates.

Starting points: `app/blueprints/rules.py`, `docs/PHASE3.md`, calendar and month-deadline tests. Testing the calculation engine does not certify jurisdiction coverage.

## 5. Screen-reader and keyboard coverage

Status: fresh portal session and real browser/assistive-technology checks required. Start with portal and public invoices, then signing, uploads and messaging.

- [ ] P2-A11Y-01: Complete fresh login, navigation and logout using only the keyboard. Focus order is sensible and visible, no trap occurs, and the login result or error is announced. Expired/used links provide a usable recovery route.
- [ ] P2-A11Y-02: With a named screen reader/browser pair, inspect headings, landmarks, labels, links, amount/currency announcements and document names. Controls must make sense without visual proximity.
- [ ] P2-A11Y-03: Trigger validation errors on upload, message and signing forms. Associate errors with fields, preserve entered content where appropriate, announce outcomes and place focus where the user can recover.
- [ ] P2-A11Y-04: At 390px width and 200% zoom, complete invoice review and portal tasks. Check clipped controls, table reading, scrolling, modal behavior and touch targets. Separate keyboard evidence from touch evidence.
- [ ] P2-A11Y-05: Repeat key flows in Spanish. Page language and accessible names match the visible language; amounts and statuses remain understandable. Check the two client accounts separately so accessibility testing also preserves client isolation.
- [ ] P2-A11Y-06: Record a second browser/assistive-technology combination and run automated checks as supporting evidence. A scan with no findings does not substitute for completing the tasks. State the tested coverage rather than claiming blanket certification.

Starting points: public/portal/signature templates, `tests/test_phase2_d.py` and the portal regression tests. Prefer VoiceOver/Safari and NVDA/Firefox if those environments are available; record any unavailable combination as BLOCKED.

## 6. Automatic time capture in Word and Outlook

Status: the inspected repository contains a Chrome extension that captures browser-tab suggestions. No Word/Outlook desktop implementation was identified. The website explicitly says desktop capture is not yet present. Proposed checks below wait for that implementation.

- [ ] P2-TIME-01: Define supported operating systems, desktop/web app versions, installation method and captured fields. Identify the deliverable and permissions before testing. A browser extension pass does not prove desktop capture.
- [ ] P2-TIME-02: Work on two synthetic matters in Word and Outlook. Verify matter suggestions, elapsed time, attribution and switching behavior. Ambiguous or unmatched activity must stay reviewable rather than silently attaching to a client.
- [ ] P2-TIME-03: Measure against a stopwatch through idle, lock, sleep, app switching, overlapping windows and midnight. No idle time or simultaneous app activity is counted twice. Document the intended rounding rule.
- [ ] P2-TIME-04: Pause and disable capture, exclude a private document/mailbox and revoke access. Inspect captured payloads to confirm the documented data boundary and that disabled activity stops being sent.
- [ ] P2-TIME-05: Edit, accept and dismiss suggestions. Nothing becomes billable before the intended approval step. Double acceptance, reconnect and replay must not create duplicate time entries.
- [ ] P2-TIME-06: Test offline/restart recovery and uninstall. Explain what queued data survives or is removed. Existing timers and manually entered time must remain correct.

Starting points for the existing browser behavior only: `extension/README.md`, `extension/background.js`, `app/blueprints/capture.py`. These are references, not a desktop implementation.

## 7. Deeper LEDES for insurance defense

Status: LEDES 1998B export exists. The advertised expansion beyond it lacks a defined target in the inspected inventory. Agree on the insurer/recipient requirements and exact supported format/version before calling this testable.

- [ ] P2-LEDES-01: Specify the target format/version, required IDs, code sets, adjustments, currency/tax handling and recipient billing rules. Obtain the recipient's validator and approved sample outputs. Do not infer requirements from the current 1998B builder.
- [ ] P2-LEDES-02: Export fees, expenses, discounts, credits and split payers as applicable. Independently reconcile quantities, rates, line totals and invoice totals to the cent. Repeat with supported currencies.
- [ ] P2-LEDES-03: Submit missing IDs, invalid UTBMS codes, unsupported adjustments and incompatible currencies. Refuse with actionable errors; do not export a plausible but invalid file or falsely mark success.
- [ ] P2-LEDES-04: Test delimiters, newlines, Unicode, long narratives and large invoices. Validate encoding, field counts and escaping with the actual target validator.
- [ ] P2-LEDES-05: Run a synthetic file through the recipient's test intake process. Retain the acceptance/rejection report and reconcile any rejected lines. A locally parseable file alone does not pass recipient compatibility.
- [ ] P2-LEDES-06: Correct and re-export a rejected invoice. Preserve audit history and an agreed duplicate/submission policy. Re-run existing 1998B tests so the expansion does not break today's export.

Starting points: `app/blueprints/ledes.py`, `app/blueprints/exports.py`, `tests/test_phase2_a.py` and billing/export regression tests.

## Supporting readiness checks

These come from the readiness register and support the seven product tools above.

- [ ] P2-SUP-01: Measure conflict requests at 5,000 synthetic contacts, including a buried known match and no-match control. Record cold/warm request durations, fixture counts and query counts separately from browser-automation time. Report median and worst observed request; agree on a performance budget before a speed pass. Verify match completeness as well as speed.
- [ ] P2-SUP-02: After two staff users create time, expenses, invoices, credits and manual payments, reconcile every affected report with an independent worksheet and raw CSV. Separate currencies and include date boundaries, voids, partial payments and missing cost rates.
- [ ] P2-SUP-03: On two new synthetic matters, compare AI outputs with a prepared source-fact checklist. Include an unfavorable fact, conflicting documents and a missing fact. Every material assertion needs support; uncertainty and contradictions must remain visible. Record model/provider, document set, prompt and each run. Repeat to measure consistency, with configured usage limits.
- [ ] P2-SUP-04: Inventory the actual volume fixture before generating more data. On a disposable copy, measure matters, dashboard, trust and export paths at the documented scale; verify row counts and exact totals. Test pagination for missing/duplicate rows. Keep the separate 50,000-row import/export exercise distinct from the 300-row concurrent-import regression.

## Completion and handoff

A tool is ready only when its required cases pass on an identified release, failures have regression evidence and independent retests, and remaining limitations are stated. NOT BUILT and BLOCKED are valid findings, not passes. Product claims must match supported currencies, integrations, courts, formats and tested accessibility coverage.

Result record: case ID; result; deployed commit; tester; fixture IDs; steps; expected; actual; evidence path; issue; retest commit/date. Log active ownership in COORDINATION.md before implementation. This checklist is documentation only; no new Phase 2 QA run, implementation or deployment is implied.

## September 21 review progress

A focused review reproduced P2-INV-04 date failures on baseline `20571c2`: malformed strings, an impossible date, a valid date with trailing garbage, an integer and an object each created a draft instead of returning an error. The fix validates explicitly supplied dates as exact `YYYY-MM-DD` values before calling the builder. Omitted/null dates retain the documented default behavior. Five refusal regressions plus one positive control pass; the related API/MCP group passed 62 tests. This is deterministic local evidence, not an actual MCP client or live browser pass. Deployment and final release evidence belong in the latest coordination handoff.

Remaining priorities: genuine simultaneous invoice requests (P2-INV-05), mixed-currency totals (P2-CUR-05), actual HTTP MCP client operation, and keyboard/screen-reader QA. Phase 1 provider and independent browser gates remain open. Phase 3 inventory and prerequisites are now in `docs/PHASE3-QA-CHECKLIST.md`.
