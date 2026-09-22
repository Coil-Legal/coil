# Tool readiness register

Current acceptance status, updated September 22, 2026: Phase 1 is still open. See [Phase 1 readiness](PHASE1-READINESS.md) for deployed commits and evidence, [Phase 2 checks](PHASE2-QA-CHECKLIST.md) and [Phase 3 checks](PHASE3-QA-CHECKLIST.md) for the later review queues. Provider prerequisites and independent Grok retests are not complete.

Current deposition acceptance: `1a33ddb` holds uncertain, identical or source-unresolved comparisons for review across page, note and PDF. Synthetic 3047/doc 91/deposition 14, internal note 31 and unshared PDF 97 passed Codex checks with source/draft unchanged; 778 local and 53 production-image tests passed. Broader meaning accuracy and independent retests remain open. Grok stopped the prior batch on the SHA change and has been retargeted to 1a33ddb: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5773994130. New acknowledgment and case results pending.

Current client-update acceptance: `87de283` holds selected absence/completeness claims and uses the full source-based template. Full 788 / production-image 50 tests passed; two actual previews on 3039 passed the supported-output sample. Rejection path is regression-tested, independent issue-45 retest pending. Broader AI factual accuracy remains defective. Handoff: `docs/PHASE1-READINESS.md`.

Current research acceptance: `60d3acd` stops citation checks on known PDF page/raw-character and plain-text byte extraction limits before lookup or result notes. Public 3053/docs 100,101,102, complete pasted control and browser passed; source unchanged. Full 819 / image 50 passed. Prior repeated-occurrence and 64,000-character fixes retained. Grok acknowledged the seven existing cases 11:47; new source-limit extension assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5776247656. Independent results, OCR/extraction fidelity, unusual reporters, loose name matching and good-law status remain outside signoff.

The per-tool descriptions below originated at `c547c9b` on September 12. They record earlier reports and follow-up ideas, not a current release signoff. Findings go to GitHub issues with the `QA finding` template.

**Proven** means: the launch checklist passed, the adversarial pass passed, every fix was
re-tested by Grok independently, and there is a test in the suite holding it. It does not
mean nothing will ever go wrong. It means what we know how to ask has been asked.

**Second accounts.** Any check below that says *needs a second user* or *needs a clean
firm*: create it. Grok has authority to create users on testfirm and to run first-run
setup on the clean instance Claude provisions. Never on demo.

---

## Phase 1: acceptance in progress

### Trust accounting
Overdraw refused on every route including the importer and the invoice. Cross-matter and
cross-client isolation. Reconciliation with every uncleared item listed. Backdating into a
reconciled period refused. Post-dated deposits not spendable. Apply to invoice.

Further checks worth running:
- A cheque that bounces after deposit. Is there a way to reverse a deposit that keeps the audit trail, and does the client balance go negative correctly rather than silently?
- A bank fee and an interest posting on the trust account, then reconcile. The three-way should still agree.
- A reconciliation where the bank statement is out by one cent. The page must say out of balance and by how much, not round it away.
- Transfer between two matters for the same client. Both sub-ledgers move, client total does not.
- Disbursement to the firm for fees larger than the fees actually earned on that matter. This is the classic bar complaint and nothing in the ledger stops it today; confirm what the screen says.

Inputs that could trip it: a memo line with commas and quotes (check the export), a duplicate deposit entered twice by two users, an amount typed with a trailing period or as "1,100" with no decimals.

### Invoicing
Create, send, resend, part and full payment, interest, void with the paid-invoice explanation, negative and absurd totals guarded, two-tab edits refused, PDFs including non-Latin names, split-payer groups.

Further checks:
- An invoice with 200 time entries. Does the PDF paginate cleanly and does page 2 carry the header?
- A time entry at a zero rate on a billable matter. It should appear at $0.00, not vanish.
- A discount larger than one line but smaller than the total, then a payment, then a void attempt.
- Interest applied in three consecutive months. Simple or compounding, and does the page say which?
- Resend an invoice that is already paid. What does the client receive?
- Tax. Is there a tax line, and does a jurisdiction with no sales tax on legal services get $0.00 or nothing?

Inputs that could trip it: a client called O'Brien (apostrophe in the PDF and the email subject), a matter name of 290 characters, a time entry description with line breaks, JPY or any currency with no minor unit.

### Payments and payment plans
Manual payment, plans, pause and resume and cancel, no-Stripe fallback with a real address.

Further checks:
- An overpayment. Where does the excess go, and is it visible?
- A payment recorded against a void invoice. Must refuse.
- A plan whose invoice balance changes mid-plan because a credit was applied. Do the remaining installments recompute?
- A one-installment plan. Should either work or say why not.
- A payment dated before the invoice was issued. Allowed, but the invoice page should not show it as early.

### Conflict check
Exact, fuzzy at 80% and above, alternate-names field, waiver gate, convert, buried single match found in 760 contacts.

Further checks, and these matter because a missed conflict is malpractice:
- Hyphenated surnames, Jr and Sr and III, middle initials present on one record and absent on the other.
- A company and an individual sharing a surname. Nordvale Freight and a Mr Nordvale.
- A person who is a client on one matter and adverse on another. The check must show both roles.
- A surname that is a common word: Lee, Brown, Long, Young. Fuzzy must not flood.
- A contact with only a company name and no person, matched against a person at that company.
- Names in Greek, Cyrillic and Vietnamese with diacritics, matched against the ASCII spelling.

Inputs that could trip it: contacts imported from CSV with trailing whitespace, a contact whose name was entered in ALL CAPS, the same person entered twice with different email addresses.

### Calendar, deadlines and court rules
Limitation date verified against the source document, chains land on business days, recurrence stops at its end, court rules honest about being generic, iCal correct across time zones and DST, deadlines in both feeds.

Further checks:
- A deadline chain that crosses a federal holiday. Court holidays are not modelled; confirm the page says so rather than silently landing on Thanksgiving.
- A trigger date on 29 February, and one on 31 January with a "one month" step.
- A trigger date in the past. Should compute, and every resulting deadline that is already overdue should say so.
- A rule that counts backwards from a hearing date.
- An event created on the day the clocks change, at 02:30 local.
- The iCal feed subscribed in Outlook, Google Calendar and Apple Calendar, not just parsed. Each has its own idea of DTEND on an all-day event.

Inputs that could trip it: an event title with an emoji, a location with a newline, a task due date typed as 13/09/2026 by a British user.

### Client portal
Cross-client isolation by URL tampering, one-use 30-minute magic links, Spanish, messaging, upload, pay page on a phone.

Further checks:
- Two contacts sharing one email address. Which one does the magic link log in, and does it say?
- Request a link, request another, use the first. Should be dead.
- iOS Safari in private browsing, where the cookie may not persist between the email tap and the page.
- A document shared to the portal, then unshared while the client has it open.
- A client whose matter was closed yesterday. What do they see, and is it polite?

### E-signature
Send, sign, certificate with who and when and IP and both hashes, immutable afterwards, signing survives a mail relay refusing the address.

Further checks:
- A signer name of 200 characters. The certificate and the PDF must both cope.
- Two people open the same link and both sign within seconds. One must win and the other must be told.
- Decline, then the firm re-sends. Does the old token die?
- An engagement letter whose body contains a table and the firm's logo. PDF fidelity.
- Sign from a phone. The typed-name box and the tick box must be usable at 390px.

### Intake, messages, documents
Intake with the conflict waiver gate. Portal messages round-trip; texts stored and clearly not sent without Twilio. Documents: fake extensions refused, downloads nosniff, versions linked to their root.

Further checks:
- A lead with the same email as an existing client. Convert should link, not duplicate.
- Convert the same lead twice, from two tabs.
- A client reply that quotes the whole thread. Does the message view show the new part first?
- A message on a closed matter. Allowed, but the matter should show it.
- A 25 MB file exactly, a zero-byte file, the same filename uploaded twice, a password-protected PDF (text extraction will fail; the page should say so).
- A random .zip renamed to .docx. The signature check accepts this today because both are zip containers; decide whether that matters.

### Personal injury
Settlement worksheet reconciles to the cent, demand package with exhibits, records and billing letters, lien reduction letters using the reduced figure.

Further checks:
- A lien larger than the settlement. The worksheet must refuse or show a negative net and say so.
- Two liens from one provider, one reduced and one not.
- A reduction to zero. The letter should still make sense.
- A demand package with 50 exhibits. Index and PDF size.
- A provider with records received but no bills. Specials should be $0.00 for them, not missing.

### Criminal defense
Charges with attorney-entered ranges, court date chain, speedy trial says what it counts from, disposition PDF.

Further checks:
- Three charges with different statutory maximums on one matter. The disposition must list each.
- Speedy trial with a tolling period. If tolling is not modelled, the page must say the count is unadjusted.
- A disposition after a plea to a lesser charge than the one filed.

### Discovery and depositions
Current deployed evidence: QA loop source-resolution fix 4fdb41b is included in 0438bad. Codex still sees the false scarlet-door/uncertainty contradiction on deposition 14, now with an ambiguity warning. Citation correction is not semantic acceptance. Issue 46 remains a known semantic defect; separate Grok retest assigned.

Current September 22 independent result: Grok confirmed false contradiction #46 on matter 3047/document 91/deposition 14. Citation and PDF case passes remain valid, but contradiction semantics are defective. Both statements need source-context validation; existing draft preserved. See current Phase 1 readiness.

Current September 22 evidence: `16c533f` fixed transcript request coverage and condensation truncation. `f5135a3` checks unique exact quotes against source markers and warns on absent/repeated quotes; old saved drafts receive the same checks on viewing/export. Public fixtures 3041/3042, depositions 12/13, notes 26/27 and PDFs 88/90 passed the documented short samples and artifact text checks. Full local 727 and deployment-image 128 tests passed. Repeated/OCR-modified quotes still require manual source review; cross-part contradiction quality and independent QA remain open. Narrative date attribution is defective. This tool has no complete acceptance signoff.

Earlier report: Contradictions caught, internal and external, 3 of 3 runs, cited to page and line. Summaries not wiped by an empty save.

Further checks:
- A transcript over 500 pages. Does it clip, and does the page say where?
- A transcript with page numbers that restart per volume. Citations must say which volume.
- A witness who contradicts himself and corrects it in the next answer. Should be reported as corrected, not as a contradiction.

### Research and cite check
Current independent acceptance: Grok passed 390px/320px and keyboard save/export on 146ed23, unshared memo 96. Doc 84's earlier 404 was the bare unsupported URL; actual download passed. Edge citations and complete-tool signoff remain open.

Current September 22 evidence: Grok passed keyboard search, court filter, opinion, save/note and literal memo text on 94d4c21, matter 3050/authority 2/document 94. Its 390px saved-authority overflow is fixed in `146ed23`, deployed to both sites. Codex passed 320px, 390px, 1280px and keyboard save/export; document 95 is unshared and its authenticated download preserves literal text. Full 752 and deployment-image 26 tests passed. Independent mobile retest is assigned, not yet acknowledged. Read-only current-release checks found reference document 84 present with working download and navigation links; documents 84/94/95 returned exact stored PDF bytes and literal notes, all unshared. Earlier 404 cause remains unestablished pending Grok's exact URL/session evidence. Edge citations and complete research signoff remain open.

Resolved, not found, and the wrong-case pincite trap all correct. States plainly that it cannot say whether a case is still good law.

Further checks:
- A citation to an unpublished opinion, a state intermediate court, a string cite of five cases, a reporter abbreviation with a typo (F.3d as F3d).
- Feed it a brief that the AI narrative tool itself drafted. Any citation it invented must come back not found.

### Exports and importer
Current September 21 evidence: CSV batches on `7e15867` passed 50,000 rows and browser pause/resume. ZIP recovery on `2e52988` passed 3,000 unique files and worker restart. Paged ZIP previews on `b98647e` passed 500 folders with mixed Word/PDF/text/email documents, saved choices and exact byte/text checks. Blank and ambiguous matter names now require a choice. Full local suite: 697 passed; deployment suites: 98 passed. Independent Grok browser checks remain open. See Phase 1 readiness for fixtures, limits and deployment details.

Contacts, matters, time, trust ledger, QuickBooks layouts, LEDES. Formula injection neutralised, negatives still numeric. Importer with preview, commit, failed-rows CSV, duplicate handling, concurrent-write lock fixed.

Further checks:
- A description with a newline inside a CSV cell. Excel and Sheets must show one row.
- Unicode in a CSV opened in Excel on Windows, which wants a BOM. Does José become JosÃ©?
- 50,000 time rows. Time to generate and file size.
- LEDES output run through a real e-billing validator, not just opened.
- Import a genuine Clio export with Clio's own column names, then a MyCase one. Not a hand-made CSV.
- A CSV with a BOM, one with Windows line endings, dates as DD/MM/YYYY, and 10,000 rows.

### Webhooks
Fire on task.completed and matter.closed, retry on failure, secret masked and hidden from readonly.

Further checks:
- An endpoint that returns 500 five times then recovers. How many retries, at what spacing, and does it give up loudly?
- An endpoint that takes 30 seconds to answer. Does the app wait, and does it block anything?
- Rotate the secret. In-flight deliveries and the next one.

### Backup, restore, self-update, install
All proven by doing them: backup lands before an update, a broken build pins the previous digest and holds, a good build unpins, restore boots on real data with the trust balance intact.

Further checks:
- Restore a backup onto a Coil that is two versions newer. Additive migrations should handle it; confirm.
- Restore onto a Coil that is older than the backup. Must refuse or warn, not corrupt.
- The nightly backup at 02:40 and the update at 03:17 on a slow machine where the backup is still running. Overlap behaviour.
- Disk full during a backup. Claude runs this one.

### Setup guide, settings, permissions, API and MCP, fee splits, offices, audit log, feedback
All passed, including permissions by POST rather than by hidden nav, redacted API tokens leaking no names, multi-office rates, and 1,743 audit entries spot-checked as an auditor would.

Further checks:
- Remove the last owner. Must refuse.
- Deactivate a user who owns open tasks and unbilled time. What happens to them?
- A paralegal POSTing to change their own role. Must refuse.
- A user with no office on a firm that has two.
- Delete an office that still has users.
- Fee splits that sum to 99%. Refuse or warn.
- An API token revoked while a request is in flight.
- A redacted token asked to find a matter by client name. Cannot see names, so what does it get?
- The audit log filtered by one user across a month, and exported.

---

## Phase 2: earlier evidence, current review open

**Conflict check speed: withdrawn.** Grok measured 11 to 14 seconds at 760 contacts and this register repeated it without reproducing it. Measured on the live database: the index builds in 0.15s, the scan runs in 0.03s, the full request including the results page is 0.19s, and the round trip from a browser through Cloudflare is 0.2 to 0.9s. Grok's figure was its own automation overhead, which is why it cost the same with 500 hits as with none. Re-measure at five thousand contacts once the volume fixture exists, timing the request rather than the tester.

**Non-USD currency.** Fixed in `72bc741` (matter page and raw exports). Grok re-tests: a CAD matter through invoice, PDF, payment, exports, reports and the public pay page, looking for a stray dollar sign.

**Draft invoice through the API and MCP.** Added in `c547c9b` after §S found the scope advertised but the tool missing. One test, no re-test yet. Grok: drive it end to end with an unredacted and a redacted token.

**Reports reconciled against their rows.** Done by Grok for §L on one firm state. Repeat after the two-user day in §O, so the figures have something to disagree about.

**Current AI acceptance, September 22:** matter isolation and complete summary inputs are deployed; `3cf4af4` also preserves whole client-update statements, bypasses the model for oversized input and separates file notes from work performed. Public 3043 retained a correction after the old cutoff; 3044 preserved the full overflow note in draft 144 with zero model calls. Factual acceptance is still defective: new live samples inferred recent receipt from an undated note on 3039 and asserted no other developments from selected records on 3043. Matter-summary date attribution is unchanged. Full local 734 and deployment-image 135 tests passed. See Phase 1 readiness for exact samples, test-fixture limitations and remaining acceptance gates. Release `500abb8` adds consistent internal/billing-text exclusions for work, completed/upcoming task titles and event titles before record limits. Public fixtures 3045/3046 passed selected-source, model/template exclusion and record-preservation checks, with draft 146 saved and no email sent. Full 746 and deployment 147 tests passed. General narrative reliability and independent acceptance remain open. Release `94d4c21` fixes concurrent document-date acceptance failures; 752 local and 153 deployment tests passed. Four public simultaneous submissions plus replay created exactly one task/event pair on matter 3049. Grok independently passed filter/fallback, citations/PDF and sequential date replay on 500abb8, without closing general narrative acceptance. Issue 45 remains defective; issue 44's quoted note-recency claim is supported by record metadata. See current Phase 1 readiness.

**AI output quality on clean inputs.** Audited once on M-1008; one real grounding gap fixed. Repeat on two other matters with different document sets. What matters is a confident sentence the sources do not support.

**Portal accessibility.** Keyboard and screen-reader pass on the invoice done; the portal half was blocked for lack of a session. *Needs a second client account with a magic link Grok can read.*

**Volume: measured and fixed (`b2d7f5a`).** testfirm now carries `ops/volume_fixture.py`: 3,013 matters, 31,288 time entries, 3,019 invoices, 3,940 trust rows. Before the fix the matters list took 21s, `matters.csv` 26s on 13,067 queries and `time.csv` 23s on 38,313, against a 30s gunicorn timeout. After: 0.22s, 0.86s on 8 queries, 3.6s on 4. Cause in every case was a query per row, including `Firm.get()` once per row through `Matter.currency_code` (the identity map holds weak references, so an instance read once and dropped is fetched again). `tests/test_volume.py` seeds the fixture and fails if any count grows. A second pass (`3bbd7ed`) caught the dashboard at 910 queries (the overdue card rendered every overdue invoice with a client lookup each; now the oldest twelve and a count) and the trust overview at 954 (one query per client for its matters); now 27 and 14. Every page on the daily path is flat. Grok re-runs the export exactness checks and §P at this size; the conflict check itself was never slow (0.19s), see below.

---

## Phase 3: hardest, or not yet possible

**§E, the AI failure modes.** What every AI tool does with a wrong key, an expired key, and a key with no credit. Three different failures a firm will hit in its first month, three messages. *Blocked on Ian: a restorable key.*

**§Q and §R, the setup wizard and the install key on a truly empty firm.** Every wizard test so far ran on demo data; the install key has never been tested on a first run because testfirm was already installed. *Claude provisions a clean instance; Grok runs first-run setup on it, which is the second account.* Issues #7 and #8.

**IMAP email filing.** Never exercised; testfirm has no mailbox. *Grok's own AgentMail address may support IMAP. If it does, point testfirm at it and this unblocks itself.*

**The voice line.** Needs Twilio configured and a deliberate switch-on. *Blocked on Ian.*

**Arabic and other right-to-left scripts in PDFs.** Renders now, but unshaped and in logical order. Legible, not correct. Needs a shaping library and a decision.

**Credit notes.** Decided (credit rather than void), explanation shipped, the instrument itself not built.

**Document-figure conflict scan.** A deterministic check that dollar figures in a matter's documents agree with the case record. Not built. Ian's call.

**A real firm.** Everything above is what two machines thought to ask. The first solo practitioner will do something neither imagined within a week. That is not a test; it is the reason to ship to one firm you can talk to before you ship to ten.

---

## Blocked on Ian, unchanged

The GHCR package is private, so nobody can install Coil. `github.com/orgs/Coil-Legal/packages`, web UI only.

## Invoice polish qualifier guard, September 22

Release `0438bad` holds suggestions that change protected English qualifier markers and rechecks Apply atomically. Full 770 / deployment 45 tests passed. Public invoice 3035/line 9832 preserved complete rows and audits on unsafe submission; one real browser preview retained the sample limits and negatives. This is bounded phrase validation, not general semantic equivalence. Independent retest and broader factual acceptance remain open. See current Phase 1 readiness.
