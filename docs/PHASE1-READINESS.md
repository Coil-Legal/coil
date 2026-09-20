# Coil Phase 1 completion pass

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
- [ ] Check large imports through the public proxy/browser. Current direct HTTP timing leaves little room below the 600-second worker limit on slower data or servers.
- [ ] Broaden AI factual samples and research browser workflows beyond the successful provider search, opinion and citation checks.
- [ ] Production branded SMTP configuration, offsite recovery and other launch operations need their own signoff. The QA mail setup does not change demo's sender.

Evidence lives in `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/`: financial and portal regression logs, `coil-large-import-http.log`, `coil-backup-restore-lab.log`, `coil-recovery-lab.log`, `coil-ai-live.log`, `coil-financial-lab-workflow.json`, inbound and external mail records, release logs and file-hash checks. Earlier failed harness attempts are retained alongside the final evidence; they are not acceptance failures.

Grok queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5753024092.
