# Coil Phase 1 completion pass

## Latest: ZIP batching and recovery, September 21

Both sites run `2e52988`. ZIP imports start saved jobs and process up to 20 entries or 25 MB of uncompressed data per request. Counts, document records and progress commit together. Repeated starts/cursors do not duplicate work. A file manifest supports cleanup after a failed save or worker exit while preserving committed documents. Recovery after an abrupt exit happens when the job resumes. Upload and guide limits now match: 48 MB per ZIP, 25 MB per document.

Local full suite: 690 passed. Deployment Python 3.12 affected suites: 91 passed. Tests include actual subprocess exit after writing bytes, checkpoint rollback, same-cursor/start concurrency, post-commit preservation, missing archive recovery and permissions. A real multipart check accepted a 46 MB ZIP for preview and gave a clear split-file message for 49 MB.

A separate authenticated firm imported 3,000 unique synthetic text documents through Cloudflare in 150 batches. Maximum batch request: 0.284 seconds. Every stored file matched its expected bytes; three public downloads matched. After restarting workers at file 1,000, a fresh login and replay resumed without duplicates. Lab job 1 completed with 3,000 created, zero errors and 1,931,700 stored bytes. The temporary lab was removed and both public/origin paths return 404.

Both sites are healthy, six changed file hashes match, SQLite integrity is OK and restart counts are zero. Grok's independent browser queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5767641831. Full handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-zip-resume-handoff.md`. Mixed Office/PDF archives, many-folder previews, wider AI/research samples, provider access and independent browser acceptance remain open. Phase 1 is not complete.

## Earlier: ZIP mapping and identity verification, September 21

Both sites run `27c6bd3`. Explicit folder skips survive saving and commit. Windows ZIP paths import their original bytes. Long paths no longer collide at 120 characters; ambiguous legacy shortened references require review. Duplicate member paths, including slash/backslash aliases, are reported and skipped. No schema or provider changes.

Six new regression cases failed before the fix. Final local suite: 682 passed; deployment Python 3.12 affected suites: 74 passed. The initial full run hit a SQLite lock in an unrelated fixture; that fixture passed alone and a fresh full suite passed. Both sites are healthy with three matching file hashes, SQLite integrity OK and zero restarts.

Public Cloudflare job 27 imported Windows and two long-path files while preserving a saved skip choice: documents 80, 81 and 82 on synthetic matter 3033. Exact downloaded bytes matched. Repeat job 28 created nothing and skipped four. Job 29 created unique document 83 and skipped both ambiguous duplicate members. No files were shared to the portal. Grok's independent retest is queued at https://github.com/Coil-Legal/coil/issues/12#issuecomment-5767064351; acknowledgment/results are pending.

Full handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-zip-review-handoff.md`. ZIP imports remain synchronous; volume, interruption, concurrent commits and cleanup after failed database writes are still open. Phase 1 is not complete. The provider, AI/research and independent browser gates below remain applicable.

## Earlier: resumable CSV verification, September 21

Both sites now run `7e15867`. Large CSVs use owner-authenticated batches with atomic saved progress. Previews clearly sample the first 200 rows. Local suite: 676 passed. Deployment-image affected tests: 68 passed. Both sites are healthy, files match, SQLite integrity is OK and containers have zero restarts.

The 50,000-row import now passes through the actual Cloudflare proxy into a disposable firm. Preview: 0.955 seconds; maximum batch request: 1.655 seconds; total import: 493.843 seconds. All 50,000 rows, 300,000 minutes and 30,000,000 cents reconcile in storage and export. Reconnection and replay passed. The temporary authenticated route was removed after testing.

Actual browser testfirm job 26 passed pause at 1,400, keyboard resume, close/reopen and completion at 5,001 rows. It repeatedly updated one synthetic contact (1809), leaving 1 created, 5,000 updated and 0 errors. Grok's independent verification is still pending: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5766422082.

Full handoff, file list, evidence and recovery paths: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-import-resume-handoff.md`. Phase 1 is still open for provider access and remaining acceptance checks. Large ZIP imports retain their old flow and need separate volume verification.

## Earlier September 21 evidence

Both sites now run `2b21f25`. Portal uploads use staff file validation and text extraction; signing and document delivery verify the sent file hash; the invoice API rejects malformed dates before creating drafts. Full suite: 670 passed. Deployment Python 3.12 affected tests: 117 passed. Both sites have matching hashes, SQLite integrity OK and zero restarts. Public testfirm rejected invalid files and completed valid document 79/signature 6 with a PDF certificate.

Phase 1 still needs the acceptance gates below. Large-import public-proxy behavior is particularly important: the direct 425.5-second commit exceeds Cloudflare's documented default 125-second read timeout. Actual zone behavior is not yet measured; do not count the direct HTTP result as a public browser pass.

Grok's current release queue is https://github.com/Coil-Legal/coil/issues/12#issuecomment-5756766063. No new independent result since September 20 at 03:45 UTC. A recurring review follow-up is active every 30 minutes. Full evidence and recovery paths: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-phase-review-handoff.md`. Phase 2 progress and Phase 3 prerequisites are recorded in their QA checklists.

## September 20 evidence

2026-09-20. Deployed release `475b50fb72fd7e62ba7b21b990047515389bf6d7` on testfirm and demo. Phase 1 still needs Stripe test-mode checks, authentic SMS delivery and Grok's browser signoff.

Completed application fixes:

- Realization includes receipts from every split payer and uses actual invoice cents, preserving rounding.
- New unbilled work on an already invoiced matter stays WIP instead of becoming a write-down.
- Portal uploads use unique storage names. Two same-name uploads in one second preserve both documents.

Files: `app/blueprints/reports.py`, `app/blueprints/portal.py`, `app/templates/reports/realization.html`, `tests/test_financial_completion.py`, `tests/test_portal_upload_preservation.py`. No schema changes. Shared checkout `/Users/iandolan/General/solo-practice`; isolated implementation `/Users/iandolan/Documents/Codex/2026-09-19/reve/work/coil-money-review`. GitHub main was not pushed.

Validation:

- Full local suite: 655 passed, 114 existing warnings. Log `phase1-completion-full.log`.
- Deployment Python 3.12 affected suites: 64 passed, 7 warnings. Server log `/home/deploy/backups/coil/testfirm.coil.legal/tests-475b50f.log`.
- Both sites healthy on `475b50f`; all five deployed hashes match; both SQLite integrity checks pass.
- Two synthetic portal clients authenticated using actual captured emails. Used links returned 410. Both uploads downloaded identical bytes; other-client downloads returned 404; other-client uploads added no document; private messages stayed isolated.
- Three live summaries retained the unfavorable witness account, exact $1,234.56 estimate and each provider's record status. Actual configured provider was OpenRouter with google/gemini-2.5-flash. Estimated usage rose by 3 cents. CourtListener search and full opinion retrieval worked. The known citation resolved to the same opinion, and the wrong-party-name example returned name_mismatch with found=false. This is sample-based evidence, not a guarantee of every AI answer.
- Direct HTTP import: 50,000 activities, zero errors, 300,000 minutes and 30,000,000 cents. Export matched rows, minutes and cents. Upload 1.7 seconds, preview 122.2 seconds, commit 425.5 seconds, export 5.1 seconds. Public proxy/browser behavior at that duration remains unverified.
- Backup restored all 50,000 records, the 500,000-cent seeded trust balance, upload/PDF hashes and environment into a separate healthy app. Existing-database overwrite was refused. The PDF fixture tested byte preservation, not rendering.
- Actual Docker self-update: a deliberately unhealthy image rolled back; a repeated bad channel stayed pinned; a healthy successor unpinned and started. Backup archives were created before changes.
- Full financial chain in the updated disposable lab: $120 time plus $30 expense invoiced and sent through capture SMTP; $100 deposited to trust; $50 applied; $60 received by check; $40 credited. Result: total $150, paid $110, credit $40, due $0, status paid, remaining trust $50. Revenue CSV showed $110, payment CSV had exactly the two receipts, PDF returned successfully.
- Testfirm's reconciled-through-today guard correctly rejected the same-day deposit. Its reconciliation was preserved. Synthetic testfirm matter QAF1001 (3034), invoice 3033 remains sent at $150 with no payment; the completed accounting chain is in the disposable lab, matter 3/invoice 1.

Email setup:

- Owner-only capture inbox: https://testfirm.coil.legal/qa-mail/. Use an existing owner session. Anonymous and non-owner requests return 403. SMTP uses authentication and STARTTLS. All testfirm mail is captured; demo mail settings are unchanged.
- Synthetic portal clients: phase1-client-a@coil.test (contact 1807, matter 3032) and phase1-client-b@coil.test (1808, 3033). QA staff/owner passwords remain in a protected server file and are not in this report.
- Receiving alias ian+coil-qa@iandolan.com verified in Gmail. Existing receiving account grok-coil-github@agentmail.to authenticates to AgentMail IMAP. One synthetic incoming message was imported once, duplicate import was skipped, and message 125 was manually filed to matter 3032. The custom QA-P1-A number does not match the existing automatic email matter-number pattern.
- Existing Gmail SMTP authentication failed with 535. Working AgentMail SMTP was verified using the already configured inbox credentials. Coil sent a synthetic message and attachment to Ian's receiving alias: Gmail message `1a0c0d3c76faea88`.
- A captured message was delivered externally by a QA-only helper: Gmail message `1a0c0db2ed0f79dc`. Helper location `/home/deploy/apps/coil-qa-mail/send-qa-mail.py`, source `outputs/coil-qa-send-external.py`. Run inside the testfirm container with a captured message ID and either approved QA address. It rewrites MIME recipients and SMTP recipients, preserves attachments, and refuses all other addresses.
- Mailpit's experimental manual relay was disabled after AgentMail retained the original MIME recipient despite the changed SMTP envelope. Capture is the final default. The server helper is the supported external QA path.
- Official configuration references: https://docs.agentmail.to/imap-smtp and https://mailpit.axllent.org/docs/configuration/smtp-relay/.

Infrastructure and recovery:

- Private inbox: `/home/deploy/apps/coil-qa-mail`. SMTP/UI secrets and external relay credential file are protected server files. No public host SMTP port. Original testfirm environment backup is `testfirm-env-before-qa-mail` in that directory.
- Disposable labs: `/home/deploy/apps/coil-phase1-lab`, `coil-phase1-restored`, `coil-phase1-recovery`. Registry and lab containers were stopped after testing; data and evidence remain. The final financial lab uses only the private capture SMTP, no payment credentials.
- Both releases have rollback tags `<project>:before-475b50f` and source archives `/home/deploy/backups/coil/<domain>/source-before-475b50f.tar.gz`. Environment and Compose hashes were preserved by deployment.

Remaining acceptance gates:

- [ ] Ian signs into the open Stripe Chrome tab. Install test keys and the correct signed webhook subscription, then verify successful/declined cards, saved-card retries, installments and real provider redelivery. Current live keys were not used for charges.
- [ ] Authentic Twilio inbound SMS and reply from an authorized external handset. Credentials and webhook configuration are valid; number ending 7961 targets testfirm. Carrier delivery is not yet verified.
- [ ] Grok independently checks report examples, upload preservation, unsharing, signatures and final email/PDF artifacts, client separation, mobile layouts and keyboard behavior.
- [x] Codex CSV proxy/browser checks: 50,000 unique rows through Cloudflare and a 5,001-row browser pause/resume fixture passed on `7e15867`. Independent Grok verification remains part of the browser signoff above.
- [x] Synthetic text ZIP volume and recovery: 3,000 unique files through the public proxy, worker restart, replay, exact stored/downloaded bytes and cleanup verified on `2e52988`.
- [ ] Broader ZIP samples with Office/PDF files and many matter folders, plus Grok's independent pause/resume browser checks.
- [ ] Broaden AI factual samples and research browser workflows beyond the successful provider search, opinion and citation checks.
- [ ] Production branded SMTP configuration, offsite recovery and other launch operations need their own signoff. The QA mail setup does not change demo's sender.

Evidence lives in `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/`: financial and portal regression logs, `coil-large-import-http.log`, `coil-backup-restore-lab.log`, `coil-recovery-lab.log`, `coil-ai-live.log`, `coil-financial-lab-workflow.json`, inbound and external mail records, release logs and file-hash checks. Earlier failed harness attempts are retained alongside the final evidence; they are not acceptance failures.

Grok queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5753024092.
