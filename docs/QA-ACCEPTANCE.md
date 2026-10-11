# Two-firm SaaS acceptance

Authorized by Ian on October 9, 2026 (America/Chicago). This is the current QA policy.
It supersedes automatic batch replenishment, reserve quotas, fixed case quotas and
legacy backlog ordering. The objective is two firms with different UIs and workflows
on one release, with their customizations preserved through a real upgrade.

## Definition of done

Both representative firms complete their customer journeys in a browser on the same
release. Their configured screens and workflows are visibly different, customer data
and permissions remain isolated, and an actual old-to-new version upgrade preserves
the configuration and behavior of both. An isolated restore also reproduces those
settings and records. Missing capabilities stay explicit gaps, never assumed passes.
This milestone is necessary for SaaS readiness; it does not alone certify launch.

## Profiles and scope

A, testfirm, Bot 1: criminal-defense solo firm. Practice-focused dashboard ordered
Tasks, Limitations periods, Recent matters; Criminal defense visible, Personal injury
hidden. A flat-fee matter template with a review task, milestone and Case reference
custom field. No automatic statutory deadline assumptions. Existing firm name stays.

B, qa2, Bot 2: small hourly-billing firm. Dashboard ordered Unbilled time, Outstanding
A/R, Invoices awaiting approval, Recent matters; Criminal defense and Personal injury
hidden. Hourly matter template at $150/hour with a review task and Client reference
custom field. Invoice approval required, exercised using a disposable attorney and
owner approval on synthetic records. Existing firm name stays.

These are acceptance profiles, not claims that full customization is already built.
Minimum visible differentiation includes tool navigation, ordered dashboard content,
and practice-specific matter fields/tasks. Separately inventory gaps for application
branding/themes, terminology, navigation order, screen layouts/field groups, and
conditional workflow rules. If absent, mark GAP with the concrete customer need.
Do not silently reduce Ian's broad custom-UI goal to dashboard cards alone.

Each bot stays on its own firm. Serialize work on the same tool and all shared-setting
configuration, using the gate owner below. Snapshot existing non-secret configuration
before changes. Preserve all retained records; optional tools hide data, never delete it.
Profile changes are intentionally retained through upgrade verification, not reset at
the end of each journey. Record exact restoration values and restore only on an explicit
cleanup assignment after acceptance. Never modify provider configuration.

## Gate ledger

States: READY, WAITING, RUNNING, BLOCKED, GAP, VERIFIED. Only evidence can yield VERIFIED.
For every transition record UTC time, owner, build, profile, comment/artifact URL,
record IDs, expected outcome, actual outcome and any open defect. Do not log idle polls.

| Gate | Owner | State | Required evidence and dependency |
|---|---|---|---|
| C01 Baseline and capability inventory | Bot 2 | VERIFIED | Browser screenshots and non-secret configuration manifest for B; identify actual controls and missing broader UI/workflow capabilities. No setting changes. |
| C02 Configure and use profile A | Bot 1 | BLOCKED | Login restored and 3362 to 3367 reported PASS. Saved exhibits verified from result 6106333097; profile A revision 3 retained. Fix #184 deployed on 3fe8cb2; independent case 3368 pending. |
| C03 Configure and use profile B | Bot 2 | BLOCKED | Browser exhibits transferred, hashes verified and visually reviewed; configured workflow and approved $150 unsent invoice supported. Visibility defect #184 confirmed in matter header. Fix deployed on 3fe8cb2; independent cases 7281/7282 pending; preserve revision 3. |
| C04 Compare firms and complete customer journeys | Coordinator + bots | WAITING | After C02/C03; same commit, side-by-side screenshots, shared steps produce intended distinct outcomes; document/portal journey with synthetic client, exact monetary reconciliation. Serialize overlapping tools. |
| C05 Permissions and isolation | Coordinator + bots | WAITING | After profiles exist; intended role visibility and denied direct writes; separate operator harness proves cross-firm credential/session/data isolation without bots logging into another firm. |
| C06 Upgrade both configurations | Codex operator | RUNNING | Authorized isolated copies, source and target release artifacts, different commits, baseline manifests, backup and rollback plan. Real upgrade, manifests/data comparisons and browser replay on both at same target commit. |
| C07 Restore and rollback | Codex operator | RUNNING | Disposable recovery environment; restore backups and verify file hashes, money totals, settings, dashboards, templates and permissions. Verify rollback compatibility or explicit safe refusal. No live reset. |
| C08 SaaS operating readiness | Coordinator | GAP | After C01, source/evidence inventory of provisioning, subscription/account lifecycle, export/offboarding, monitoring and support. Record existing evidence or concrete gaps; no assumption features are missing. |

C06 and C07 are release/operator handoffs, not permission to deploy or restart live containers.
Ian subsequently authorized Codex to implement customization gaps and confirmed defects in the shared codebase. Prepare exact work and evidence required;
notify Ian once if an authorized owner or target release is unavailable. Repeatedly
running the same build is not progress toward these gates. A reload is not an upgrade.

## Execution and stopping rules

- No automatic replacement batch when a bot finishes. Select only an eligible gate or
  targeted regression linked to a verified defect. Idle is acceptable.
- Use the smallest sufficient assignment; no 10-to-15-case quota, no reserve quota.
- Customer outcomes define acceptance. Read routes/forms/permissions before writing
  executable cases. Browser use and screenshots establish UI usability. HTTP checks
  supplement browser evidence; they cannot substitute for it.
- Repetitive input matrices belong in deterministic regression tests through engineering.
  Every real defect should have a regression test, fix build and independent retest.
- Keep fixed and verified separate. Verify failure evidence, code and read-only logs
  before filing a defect. Correct bad expectations without filing a product bug.
- No new exploration once a gate is verified unless changed code or new evidence warrants
  it. Report gates closed, remaining risks, defect verification and blocked prerequisites.
- Stop on material gaps and route them to implementation; do not consume time inventing
  nearby passing tests. A gap list with owner/prerequisite is a valid completed assessment.
- When all gates are verified, retire this heartbeat and give the evidence-based decision.

## Standing protections

English and USD. No AI, SMS, Send text, provider changes, real email or real money.
Stripe test cards on testfirm only. qa2 captured mail at /qa-mail/, unchanged configuration.
Never post credentials, tokens, sign-in links or feed URLs. Preserve all older fixtures.
Bot prefixes QA and QA2 with the current Chicago date. Demo is health-check only.
Same-tool assignments do not overlap. Each bot may configure its own profile when
explicitly assigned, superseding the old rule that only Bot 2 can change firm settings.
Codex implements confirmed customization gaps and defects, with meaningful regression tests.
The QA bots do not edit code. Ian separately authorized the bounded U01 release and isolated upgrade testing; unrelated deployments and live resets remain excluded.

Pin each executable assignment to live health. If health changes, check all three firms.
Continue only if all are healthy on the same commit, recording old/new pins. Otherwise
stop. Upgrade acceptance itself requires the recorded source-to-target comparison.
For pending work allow one nudge after 60 minutes without a reply, or 90 minutes from
ACK/RUNNING. Never nudge a retired assignment or repeat a nudge.

## Transition on October 9

R154 cases 3350 to 3361 was ACKed by Bot 1 at 2026-10-10T03:42:44Z. Let it finish or
report a safe stopping point; no additional expense batches. S172 cases 7254 to 7265
had no ACK at transition: cancel it. If execution raced the cancellation, stop safely,
report partial results and retained fixtures before C01. Never claim unrun cases passed.
Retire queued R155, S173 and S174. Keep their text as history. No more reserve batches.
Continue case numbering: C01 begins at 7266; Bot 1's next assignment begins at 3362
unless new recorded evidence requires a higher number. Retired numbers are not reused.

## Evidence log

Initial source review: app/tools.py, app/models.py, app/blueprints/dashboard.py,
app/blueprints/settings.py, app/blueprints/matters.py, dashboard_customize.html,
settings/template_form.html, app/permissions.py and docs/CUSTOMIZING.md.
Live baseline at transition: all three firms healthy on 11b27da, demo-20261008.
C01 baseline verified from Bot 2 browser report below. Remaining gates require their own evidence.

Transition posts read back and verified:

- 2026-10-10T03:48:59Z: https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093461018
- 2026-10-10T03:49:00Z: https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093461124

C01 browser supplement returned; Bot 1 is assigned C02 and Bot 2 holds C03 pending release of settings ownership.

## Implementation loop, authorized October 9

Codex owns shared-code implementation as QA identifies confirmed gaps. Read evidence and
code, establish the intended customer outcome, implement a bounded change, run regression
tests and the required suite, then prepare a precise release handoff. Independent bot
retesting occurs on the deployed target, never on the assumption local code is live.
No customer-specific forks. Preserve defaults for firms that have not opted in.
Do not wait for extra permission to fix a confirmed gap within this scope.

Initial slice U01: appearance themes, workspace name, density/width, navigation labels
and order within sections, configuration preview/history/restore, conditional ordinary
tasks on new matters. State: implemented and locally verified, not deployed.
Broader field-layout editing, custom workflow stages/triggers and practice profiles
remain follow-up gaps; U01 does not close the whole custom-UI goal.

Implementation update was posted and body-verified on both queues:
- Bot 1: https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093485129
- Bot 2: https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093485237

U01 validation complete: final full suite 1494 passed, 1 skipped (154 warnings);
final customization/tool regressions 41 passed. Desktop/mobile render checks and a
headless browser Preview/Publish interaction passed on synthetic local data. Local
older-schema upgrade and SQLite restore tests passed. C06/C07 remain unverified: no
live release upgrade or independent two-firm recovery exercise has occurred.
Release details: docs/CUSTOMIZATION-IMPLEMENTATION.md.

C01 evidence review, 2026-10-10T04:11:45Z: Bot 2 result
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093597188 reports
six passes on Profile B, release 11b27da/demo-20261008, but explicitly used HTTP
and HTML exhibits without a browser. Accepted as partial inventory only, not gate
verification. Reported existing dashboard/tools/template/invoice-approval controls;
app appearance, navigation and conditional workflows absent on the deployed release.
U01 addresses those areas locally only; screen layout remains an explicit product gap.
No fixtures changed or seeded, S172 never started. Retained contact 2144, closed
matter 323, events 24/26/25, jobs 275 through 282 and templates 1 through 4.
Correction and bounded evidence supplement posted and exact-body verified:
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093635898.
Bot 2 must supply actual browser screenshots and complete non-secret baseline for
existing cases 7266 to 7271, or report browser availability BLOCKED. No new cases,
settings changes or repeated HTTP inventory. C02/C03 remain held. All three firms
healthy on the same baseline at review. This is an evidence-method correction,
not a product defect; no defect issue filed.

Legacy transition completed, 2026-10-10T04:16:04Z: Bot 1 reported R154 cases
3350 to 3361 complete, 12 PASS/0 FAIL/0 BLOCKED, release 11b27da/demo-20261008.
Result: https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093669583.
This closes the legacy assignment only, not an acceptance gate. No defect reported.
Retain contact 2033, closed matter 3331/M-1307, expense 36 (billable/unbilled
$8.91, Other, E101, date 2028-02-29, description QA Code Normalize Expense 20261009)
and all prior fixtures. Bot 1 waits for C02, next case 3362. C01 browser supplement
has no reply yet; no eligible profile assignment or nudge. No acknowledgment-only
GitHub comment posted.

## Authorized release and browser handoffs

Ian authorized commit, push, deployment to all three apps, and isolated upgrade tests.
This supersedes the earlier release prohibition for U01 only. Live reset/recovery is
still excluded. Release f84e37b / customization-20261009 was deployed to all three;
health and image IDs matched. Backups and isolated evidence are under
/home/deploy/apps/coil-u01-release-f84e37b on the VPS, root-only.

C01: VERIFIED baseline from Bot 2's browser supplement, comment 6093712522,
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093712522.
Evidence is bot-reported browser screenshots plus complete card/tool manifest;
coordinator has not independently opened the bot's filesystem screenshots.
Missing features describe source release 11b27da, not the newly deployed release.

C02/U01-A: cases 3362 to 3367 posted, exact body verified at 2026-10-10T04:33:16Z:
https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093803569.
C03/U01-B: cases 7272 to 7277 posted HOLD, exact body verified at 04:33:18Z:
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093803735.
Release Bot 2 only after Bot 1 finishes and relinquishes settings ownership.
Invoice approval journey remains unverified beyond these customization steps.

Isolated engineering checks: both source 11b27da images opened copied firm DBs,
then f84e37b opened the same copies without changing any existing table data.
Distinct Forest/flat and Plum/hourly profiles created the expected task. Isolated
SQLite backup/restores retained every table, profile and task. No live copy was
modified by this harness. Actual worker startup exposed a schema-creation race
in live release logs; all containers recovered. Dockerfile correction ccd9572
initializes the schema once before starting the two workers. Real-container
regression and f84e37b-to-ccd9572 configuration preservation checks passed on both copied firms.
C06/C07 are not fully verified from HTTP or table hashes alone; browser replay,
full acceptance profiles and recovery evidence remain explicit outstanding work.

Final deployed pin ccd9572/customization-20261009.1, verified healthy with identical image IDs and no startup errors/restarts on all three apps at 04:36Z. Pin corrections body-verified: #12 comment 6093825385 (04:36:14Z), #89 comment 6093825602 (04:36:16Z). C02 active; C03 remains held. Detailed engineering upgrade/restore evidence and next coordinator steps are in CUSTOMIZATION-IMPLEMENTATION.md.

C02 prerequisite blocker, 2026-10-10T05:15:16Z:
https://github.com/Coil-Legal/coil/issues/12#issuecomment-6094116817.
Bot 1 reports no owner session in its browser; customization redirects to login.
No cases run or live changes made. Bot requested Ian sign into its browser and will
resume the same cases 3362 to 3367 afterward. This is a browser authentication
prerequisite, not an application defect. No credentials or sessions transferred.
C03 remains held; do not replace C02 or nudge while this explicit blocker persists.
All three firms remain healthy on ccd9572/customization-20261009.1.

2026-10-10T05:31:02Z: Ian explicitly authorized Bot 1 to use its stored testfirm
credentials through the normal browser login, including future session expiry during
assigned QA. Authorization relayed and exact-body verified:
https://github.com/Coil-Legal/coil/issues/12#issuecomment-6094230786.
C02 awaits resumed execution, not a claimed successful sign-in. Same cases and
fixtures; Bot 2 remains held. Never publish credentials or session material.

C02 changed blocker, 2026-10-10T06:21:48Z:
https://github.com/Coil-Legal/coil/issues/12#issuecomment-6094605638.
Bot 1 reports baseline 3362 done and 3363 PASS. Dashboard/tools were saved during
3364 in an existing owner session, but login after logout rejected stored credentials
with Email or password did not match. Two attempts then stopped. 3365 to 3367 unrun.
Treat as an authentication prerequisite, not a verified product defect. Preserve the
published profile and dashboard/tools changes; no reset, cleanup or repeat creation.
Need corrected stored credentials through the existing private channel or explicit
account-reset authorization. Prior permission covered using credentials, not resetting
an owner's password. C03 remains held; same C02 assignment resumes at the incomplete
fresh-session check after access is repaired. All health pins still ccd9572.


## C08 source inventory, October 10, 2026

Scope: source at HEAD 1900e8c, application release ccd9572, both acceptance profiles.
This is a source assessment, not an operational acceptance pass. Fresh health checks
confirmed all three apps on ccd9572/customization-20261009.1. Neither bot has posted
new evidence beyond the recorded credential blocker and held assignment.

| Area | Existing evidence | Remaining acceptance requirement |
|---|---|---|
| Provisioning | ops/new-firm.sh creates a separate data directory, fresh session secret, firm-specific routing and container from shared source. It refuses an existing destination. | Disposable provisioning rehearsal with an exact release pin, owner setup, backup enrollment and isolation proof. Current script builds copied source without explicit commit/version build arguments. Do not run it on live firms for this inventory. |
| Subscription and account lifecycle | Application payment routes handle a firm's client payments. Operator creation/removal scripts exist. | No hosted subscription lifecycle implementation located in the reviewed application models, blueprints or ops scripts. Identify any external billing/control service before deciding what to build. Trial, cancellation, suspension and reactivation need explicit policy and evidence. Client invoice payments do not establish this capability. |
| Export and offboarding | app/blueprints/exports.py provides CSV exports; app/cli.py backup includes database, uploads and PDFs. ops/remove-firm.sh preserves the directory by default. | Prove a departing firm receives usable complete data and customizations. Purge currently accepts any existing archive count after a best-effort backup, without verifying freshness or restore integrity. Do not use that as evidence of safe deletion. Retention and deletion authorization remain required. |
| Monitoring and recovery | /health reports release metadata; ops/self-update.sh polls health and supports rollback; backup/restore scripts and regression tests exist. | /health intentionally does not query the database. Healthy responses do not prove database access, background jobs, disk capacity or recent offsite backups. Verify operator alerts and recovery evidence separately. |
| Support | app/blueprints/feedback.py provides authenticated feedback with page/build context, and tests/test_feedback.py covers its behavior. | Confirm delivery, responsible support owner and response process without sending live feedback during QA. Availability of a feedback form is not proof of incident handling. |

Owner: coordinator for evidence and engineering handoffs. C08 remains GAP until
these operating requirements have evidence or an explicitly accepted operating
procedure. No product defect was filed from source inventory alone. No application
code changed and no provisioning, purge, provider changes or real billing ran.
C02 still needs corrected private credentials or explicit password-reset authority;
C03 remains held. The existing isolated upgrade evidence does not close C06/C07.


Authentication recovery and serialized release, 2026-10-11T03:56:46Z:
Ian explicitly authorized the Bot 1 testfirm password reset. Reset owner ID 1,
verified the new hash, updated the root-only server credential record (0600), and
invalidated prior sessions. Transaction-level comparison of all 80 tables confirmed
all other data and configuration unchanged. No deploy or container restart occurred.
The bot's separate environment credential store is not yet synchronized. Requested
its existing private retrieval method or a non-secret path/access description.
Bot 1 holds C02 settings/template/matter writes while it recovers authentication;
its cases and partial profile remain intact. Bot 2 now exclusively owns the settings,
template and matter-workflow turn for existing C03 cases 7272 to 7277. After its
result and release, resume Bot 1's incomplete 3364 check and 3365 to 3367.
Body-verified posts:
- https://github.com/Coil-Legal/coil/issues/12#issuecomment-6105215457 (03:56:45Z)
- https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105215651 (03:56:46Z)
No browser login success or acceptance pass is claimed from password verification.


2026-10-11T04:12Z credential transport prerequisite:
Bot 1 reply https://github.com/Coil-Legal/coil/issues/12#issuecomment-6105309634
confirms no SSH keys or private host access. Its separate QA box needs
/workspace/coil-qa/secrets/testfirm-owner.env updated, keys COIL_URL,
COIL_OWNER_EMAIL and COIL_OWNER_PASS. This path is not mounted in the coordinator
workspace and no QA box connection is configured in the available tools. The server
credential record is updated, but bot synchronization and browser login remain
BLOCKED pending a private QA box access method from Ian. Never send values on GitHub.
Bot 2 ACKed existing cases at 04:05:23Z:
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105273641.
It is executing C03 and retains exclusive settings ownership. No result or new gate
pass yet. All three monitored apps remain healthy on ccd9572.


2026-10-11T04:25:31Z, C03 profile B partial result and remaining journey:
Bot 2 result https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105336988
reports browser PASS for 7272 to 7277 on ccd9572/customization-20261009.1.
Plum/Comfortable/Standard, QA2 Hourly 20261010, Client matters; revision 3
restores published revision 1. Four dashboard cards, PI/Criminal off. Template 5,
contact 2145, hourly matter 324/M-1324 ($150/hour), nonmatching flat matter
325/M-1325 ($500), paralegal 167 retained. Matching tasks due March 1 and March 2,
2028; edit caused no duplicate tasks. Stale publish 409 and non-owner GET 403
reported. Non-owner POST evidence not explicit. All older fixtures preserved.
27 screenshots and manifest exist on the bot box, not yet accessible for coordinator
pixel review. No defect filed; full C03 not verified. Settings ownership released.
Remaining hourly time, draft invoice and owner approval journey assigned as cases
7278 to 7279, with screenshot transfer and permission-evidence clarification:
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105413970
Posted at 2026-10-11T04:25:31Z, exact body read back and verified. Bot 2 owns
this time/invoicing journey and disposable attorney setup. Bot 1 remains blocked
on private credential transport. No further password reset or live data changes.
All three public health endpoints match the pinned release and report healthy.


2026-10-11T04:43:11Z, C03 profile B approval evidence and remaining boundary:
Result https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105468346
reports 7278 and 7279 PASS on ccd9572/customization-20261009.1, real owner
and attorney browser sessions. Attorney 168 logged entry 88, one hour at $150
on matter 324, then invoice 92/INV-1092 for $150, pending approval. Valid-CSRF
attorney approval POST returned 403. Owner approved in UI; attorney fresh login
confirmed approved, draft, unsent. Entry marked invoiced, unbilled $0, one invoice,
no duplicates. Retain these records and all prior profile B fixtures.
Tool ownership released. No defect reported. Owner pre-approval screenshot was
not saved; post-approval and attorney pending/approved screenshots reported saved.
Exhibits remain bot-local under /workspace/qa2-batch-7278/browser-exhibits/;
external artifact transfer unavailable. Coordinator has not reviewed their pixels.
Prior 7275 non-owner customization POST explicitly unrun. Case 7280 now fills
that boundary with paralegal 167, valid CSRF, unchanged profile B revision 3,
expecting 403 and no new history/revision. Exact posted body verified:
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105533046
at 2026-10-11T04:43:11Z. Bot 2 holds this customization permission check only.
C03 remains RUNNING, not VERIFIED. Bot 1 credential transport prerequisite
unchanged. All three apps healthy on the same release. No live reset or deployment.


2026-10-11T05:02Z, C03 profile B permission supplement returned:
https://github.com/Coil-Legal/coil/issues/89#issuecomment-6105598049
at 2026-10-11T04:53:04Z reports 7280 PASS on ccd9572/customization-20261009.1.
Paralegal 167 GET and valid-CSRF publish POST both returned 403. Owner browser
re-check found revision 3, history and profile B unchanged. Bot reports resetting
only the disposable paralegal password for this check, credentials kept box-local.
All retained records remain in place; tool ownership RELEASED. No defect reported.
Exhibits under /workspace/qa2-batch-7280/exhibits/ remain box-local, alongside
prior profile and approval evidence. C03 now BLOCKED on accessible visual evidence
for coordinator review, not on an unrun customer journey. Do not rerun passing
cases to replace missing artifact transport. Bot 2 waits with no tool ownership;
C04/C05 still depend on completed profiles, and full C06/C07 replay awaits profile A.
Bot 1 private credential transport remains blocked, with its existing assignment
preserved. No new GitHub acknowledgment or filler assignment posted.


2026-10-11T05:53Z: Ian explicitly authorized public QA issues for encrypted
credentials and sanitized synthetic-test screenshots. No plaintext secrets permitted.
Bot 1 temporary RSA public-key handoff: #12 comment 6106000700 at 05:53:04Z;
Bot 2 existing evidence transfer: #89 comment 6106000901 at 05:53:06Z.
Both exact bodies read back and verified. Bot 1 has exclusive profile A settings/
template/matter-workflow ownership after credential update and successful browser
login; Bot 2 transfers evidence only. No password reset, deploy, data cleanup or
configuration reset. C02/C03 remain unverified until actual evidence arrives.

2026-10-11T06:01:44Z: Bot 1 public RSA key from 6106048786 matched its DER
SHA256 fingerprint. Existing credentials encrypted on the server using RSA-OAEP
SHA256/MGF1-SHA256; only ciphertext exported. Posted encrypted payload and local
update/login instructions in #12 comment 6106059110, exact body read back verified.
No new password reset or live database change. Browser login verification pending.
Bot 2 ACKed evidence transfer in 6106053961 at 06:01:01Z, no application writes.

2026-10-11T06:12:28Z: Bot 1 confirms successful RSA decryption, atomic update
of its private environment file (600), and removal of temporary plaintext artifacts:
https://github.com/Coil-Legal/coil/issues/12#issuecomment-6106134372.
Credential transport is repaired. Browser login verification/C02 continuation is
RUNNING, not yet a pass. No data/customization resets.
Bot 2 dashboard PNG reconstructed from 6106071090 through 6106072919, 170762 bytes,
SHA256 75285887847f90184cf86b329a45fdf12aa9cfd0f2f23224047a92f81a7e06fa.
Coordinator viewed pixels: Plum workspace QA2 Hourly 20261010, Client matters label,
four intended dashboard cards. Old mixed-currency fixture totals remain visible;
no new non-USD tests or cleanup performed. Verified artifact saved at
/Users/iandolan/General/coil-qa-evidence/ccd9572/profile-b/7277-dashboard-nav.png.
Customization PNG chunks 1/4/5/6 missing, only 2/3 received; remaining images and
manifest pending. Precise receiver feedback posted in 6106132925 at 06:12:15Z,
exact body verified. No duplicate dashboard transfer or repeated customer tests.

2026-10-11T06:16:47Z: Bot 1 result 6106165017 confirms owner browser login
restored and C02 3362 to 3367 reported PASS on ccd9572/customization-20261009.1.
Logout/login in same browser profile proved persistence (incognito unavailable).
Retained A: revision 3 restores published revision 1, Forest/Compact/Cases,
QA Defense 20261009, flat Criminal Defense rule due +2. Template 5, contact 2034,
flat matter 3332/M-1308 opened 2028-02-28: template task Feb 29, rule task Mar 1,
milestone Mar 2 $100. Edit produced no duplicates. Hourly control 3333/M-1309
has no flat-rule task. Original-history restore retained tasks; profile A restored.
Settings ownership RELEASED. No invoices/payments/mail/reset created by recovery.
Side observations of UTC history display and hidden-tool matter-header link are
unverified observations, no new defect filed without code/log/evidence validation.
Saved sanitized visual evidence/manifest requested in 6106174765 at 06:18:09Z,
exact body verified. C02 not marked VERIFIED before visual review. Both transport
channels now work; Bot 2 missing chunks still pending, dashboard already verified.

2026-10-11T06:34:42Z: Profile B evidence transfer completed in result 6106215995
(06:24:03Z). All four images reconstructed with matching byte counts and SHA256;
coordinator reviewed dashboard, customization revision 3/hourly rule +1, matter 324
with two intended task dates and redacted owner-approved invoice for $150 USD,
$0 paid, $150 balance, not sent. Stored under
/Users/iandolan/General/coil-qa-evidence/ccd9572/profile-b/.
Manifest 6106212843 is the earlier 7277 snapshot; its invoice-not-verified field
is superseded by approval result 6105468346 and the reviewed approval image.
Bot 1 evidence transfer ACK 6106242101 at 06:27:48Z, no new app writes.

Verified defect https://github.com/Coil-Legal/coil/issues/184, created
2026-10-11T06:34:42Z, body read back verified. Both disabled practice tools remain
on the matter header in B; A also reported PI link. Source renders links
unconditionally; route denial remains effective. Recent read-only qa2 logs had
no lines/tracebacks. Three regression variants reproduced the visibility failure.
Local bounded fix uses existing tool_on for PI/Criminal header links; all 28
firm-tool tests pass, including restoration of visibility and unchanged counts.
Full suite started, session 94811, log /tmp/coil-qa-coordinator/matter-tools-full-suite.log.
Do not launch a duplicate suite; inspect this process/log on continuation.
Implemented locally and focused-tested; full suite pending, not committed,
deployed or independently verified. Live all three healthy on ccd9572 and
customization-20261009.1. No live reset or customization/data changes.
C02/C03 remain BLOCKED on #184, so no filler or downstream journey is assigned.

2026-10-11T06:42:46Z: Full suite completed: 1497 passed, 1 skipped, 154 warnings,
314.71 seconds. Focused firm-tool suite: 28 passed. Validation comment
https://github.com/Coil-Legal/coil/issues/184#issuecomment-6106346582 read back exact-body verified.
Fix remains local in app/templates/matters/detail.html and tests/test_firm_tools.py;
no schema or data changes. No commit/push/deploy. Prior bounded U01 release is
complete; follow-up release authorization requested before deploying #184.

Bot 1 evidence result 6106333097 at 06:40:52Z: five sanitized review JPEGs
and manifest transferred; byte counts/SHA256 verified and pixels reviewed.
Artifacts: /Users/iandolan/General/coil-qa-evidence/ccd9572/profile-a/.
Observed Forest/Compact/Cases, intended three-card dashboard, PI unchecked and
Criminal enabled, flat $100 M-1308/template 5/Case reference, two tasks with
Feb 29 and Mar 1 2028 due dates and March 2 $100 milestone, revision 3.
Review copies have small text but support visible profile differences from B.
Original PNGs retained by bot. Both bots have released tools and preserve profiles;
no repeat journey or nudge needed. C02/C03 stay blocked on #184 release and
independent browser verification. After authorization, release the two-file fix
to all three apps, then assign each bot a read-only check of existing matter
headers against retained tool configuration and capture sanitized screenshots.


2026-10-11T17:34:09Z: Ian explicitly approved #184 commit/push/deployment to all three apps. Commit 3fe8cb2 is pushed and deployed as customization-20261011.1 on testfirm, qa2 and demo, all healthy on identical image sha256:9018075fb938ed4f6ff1b310439ae1d4e35d867d7cc03e5201e0ceb50e6c2ef4. Every database table digest and retained non-DB file hash matched the consistent pre-deployment backup, zero container restarts. No settings, provider, data reset or seed changes. Backups, rollback image tags, build/deploy logs and digest manifest: /home/deploy/apps/coil-184-3fe8cb2 (root-only). Existing 1497 passed/1 skipped and 28 focused test results apply to the unchanged two-file fix. Implemented, tested, committed, pushed and deployed; independent verification pending.

Bot 1 case 3368 assigned https://github.com/Coil-Legal/coil/issues/12#issuecomment-6111759114 at 2026-10-11T17:34:08Z; exclusive read-only matter-header/task verification on retained A matters 3332/3333. Bot 2 case 7281 READY for read-only dashboard/customization/tools preservation and 7282 conditional on Bot 1 explicit matter-header release: https://github.com/Coil-Legal/coil/issues/89#issuecomment-6111759402 at 2026-10-11T17:34:09Z. Both bodies read back exactly. No overlapping tool ownership or new application writes. Preserve profiles A/B revision 3 and all fixtures. C02/C03 remain BLOCKED until these independent results and screenshots are reviewed; no isolated upgrade/restore gate claimed from deployment alone.
