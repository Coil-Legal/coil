# Customization implementation handoff

Owner: Codex, October 9, 2026, America/Chicago. Ian authorized shared-code implementation
and fixing confirmed QA gaps. Current release: ccd9572, deployed to testfirm, qa2 and demo. Earlier local-only notes below are historical.

## U01, first implementation slice

Route: /settings/customization, owner-only GET/POST with CSRF.

- Staff workspace name and three curated colour themes, compact/comfortable spacing,
  standard/wide page width.
- Navigation labels and order within existing sections, preserving tool guards and
  destination URLs. Page headings and client-facing branding are unchanged.
- Preview without saving, optimistic revision checking, audited publish, history and
  restoring a prior revision as a new revision.
- Up to eight new-matter rules matching practice area and billing type. Each matching
  rule creates a normal task assigned to the responsible user with a calendar-day due
  offset. Rules evaluate final matter fields at outer transaction commit. Successful
  importer savepoints retain their tasks when another row rolls back. No external calls.

One shared codebase; choices are stored in each firm's database. No per-firm branches,
server-specific conditionals, provider settings, outgoing messages or payment actions.

## Data and compatibility

Added tables: firm_customization (id, revision, config_json), customization_revisions
(id, config_json, created_at, user_id, note). No columns added to existing model classes.
Startup's existing create_all creates new tables additively. Do not reset or re-seed
existing firm databases. Existing appearance remains the default until owner opt-in.
Configuration and history travel with database backups. Schema version 1 is explicit;
the editor refuses to overwrite unknown future configuration versions.

Full database rollback to an older release must follow the existing schema-aware
restore process, not erase unknown tables or pretend new schema is old-compatible.
A configuration history restore is not a database or application rollback.

## Validation

Focused tests cover firm isolation, preview, permission/CSRF enforcement, invalid input,
HTML escaping, preserved tool guards, stale saves, revision restore, conditional tasks,
transaction rollback, early import flush, failed savepoints, browser-form matter creation,
additive upgrade of an older schema, startup persistence, and SQLite backup/restore.
A real headless-browser form check against an intercepted Flask test client verified
preview leaves the database unchanged and publish preserves appearance, labels and
workflow values. No dev server or live firm was used.

Local synthetic desktop and mobile render artifacts are under
/tmp/coil-qa-coordinator/visual-review/. Browser renders use Flask test-client HTML, no
live firm sessions. Mobile viewport width is 390 pixels, with no page overflow.

Final full suite: 1494 passed, 1 skipped, 154 warnings in 336.87 seconds.
Final customization/tool tests: 41 passed in 8.23 seconds. The optional AI workbench
link placement was corrected during the full run and is covered by the final targeted run.
See the latest recorded results in QA-ACCEPTANCE.md. Do not confuse local database tests
with independent live acceptance or a production source-to-target release upgrade.

## Release and independent QA

No deployment, live restart, commit or push has been performed. Before release, confirm
no overlapping changes, review the patch and pin its artifact. Back up both QA firms
and preserve their configuration manifests. The operator must stage the exact artifact
on isolated copies, validate migrations and upgrade/restore behavior, then follow the
existing three-firm release policy. Never copy one firm's data into the other.

After a verified deployment, post a bounded U01 handoff with its exact commit to each bot,
serialized for settings work. Have profile A choose Forest, Cases and a flat-fee matching
rule, then profile B choose Plum, Client matters and an hourly matching rule. Show actual
matching and nonmatching new matters, role restrictions and configuration restore.
Confirm each firm's settings did not alter the other. Keep synthetic manifests and IDs
for the subsequent upgrade. Do not test local changes as if already live.

## Remaining scope

Arbitrary field groups/layouts, application-wide terminology, customer-defined stages,
additional workflow triggers/actions, firm dashboard defaults and custom logo handling
are not implemented by U01. Prioritize these against C01 evidence and the two-firm
acceptance outcome. Maintain a fix/test/release/independent-retest cycle, without filler.

## Release authorization

Ian explicitly authorized commit, push, deployment to all three apps and isolated-copy upgrade testing on October 9. Codex is executing this bounded release. CLAUDE.md points to these shared handoff files for a future user-requested coding-agent takeover. Live recovery/reset remains excluded. Release evidence will be recorded here.

## Completed release and takeover checklist

Final live release: ccd9572 / customization-20261009.1 on testfirm, qa2 and demo.
All three use image sha256:0b448a6bd012c0ada5eaa286716f087d845c230081067df6bdf000b436bb58bf.
Verified 2026-10-10T04:36Z: healthy, zero container restarts, zero startup tracebacks.
Customization commit f84e37b and startup correction ccd9572 are pushed to origin/main.
The correction performs schema initialization before concurrent Gunicorn workers.
First f84e37b rollout recovered from a SQLite initialization race; the correction
passed actual two-worker startup on both old-schema copies without that failure.
No provider configuration, live data or compose settings were replaced. Server code
was refreshed from the exact archive; live environment and data were excluded.

Evidence directory on VPS: /home/deploy/apps/coil-u01-release-f84e37b (root-only).
Backups: backups/testfirm, backups/qa2, backups/demo, each with SQLite-consistent DB.
Original image IDs and backup paths: manifest.json. Rollback image tags:
coil-u01-testfirm:rollback-f84e37b, coil-u01-qa2:rollback-f84e37b,
coil-u01-demo:rollback-f84e37b. Do not restore live data without explicit authority.
Build logs, deploy logs, source archives extracted in source and startup-source,
and executable harnesses are retained there. No secrets are included in this handoff.

Isolated engineering evidence:
* 11b27da to f84e37b: both firm copies preserved every existing table digest.
* Saved Forest/flat and Plum/hourly profiles generated matching ordinary tasks.
* Independent SQLite restores preserved all table digests, themes and tasks.
* f84e37b to ccd9572: both configured copies booted the new image with two workers,
  zero tracebacks/restarts and identical table digests, themes and tasks.
* Original non-DB file hashes preserved: testfirm 405 files, qa2 236 files.
* startup-regression.log records four real-container startup checks passing.
* The first harness attempt used an incorrect User.active field; corrected to
  is_active plus session version and rerun from fresh copies. It was a harness error.
* Python urllib health polling was rejected by Cloudflare; curl verified the release.

Independent browser acceptance is pending, not implied by engineering checks.
Bot 1 owns C02 cases 3362 to 3367 on testfirm, handoff 6093803569, final pin correction
6093825385 at 2026-10-10T04:36:14Z. Bot 2 has C03 cases 7272 to 7277 on qa2 HOLD,
handoff 6093803735, pin correction 6093825602 at 04:36:16Z. All bodies read back exact.
Read streams after those IDs. Release Bot 2 with a concrete comment only after Bot 1
returns and releases settings; never replace a pending assignment. Both must use
real browsers and screenshots. C03 invoice approval remains a further explicit step.
Bot 2 C01 browser baseline is comment 6093712522; full manifest is in that result.

Claude Code takeover: read CLAUDE.md, AGENTS.md, COORDINATION.md, QA-ACCEPTANCE.md and
current QA-QUEUE.md. Check Git and issue state before acting. On Ian's explicit switch,
claim your own coordination entry, do not edit another agent's entry, and do not
restart legacy launchd jobs. The Codex heartbeat must yield to a newer coordinator.
The next meaningful work is review Bot 1's browser evidence, fix verified defects,
release Bot 2, then compare profiles and complete remaining acceptance gates.
Do not redeploy merely because documentation commits are newer than ccd9572.
C06/C07 remain partially evidenced until full accepted profiles and browser replay
support the ledger. Keep the stronger milestone claim separate from completed
engineering upgrade tests. There is no requirement to run filler batches while waiting.
