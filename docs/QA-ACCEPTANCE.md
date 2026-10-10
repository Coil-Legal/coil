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
| C01 Baseline and capability inventory | Bot 2 | RUNNING | Browser screenshots and non-secret configuration manifest for B; identify actual controls and missing broader UI/workflow capabilities. No setting changes. |
| C02 Configure and use profile A | Bot 1 | WAITING | After R154 ends and C01 returns; snapshot A, configure via UI, create one template/matter/task/milestone journey, reload and new session prove persistence. |
| C03 Configure and use profile B | Bot 2 | WAITING | After C02 releases settings/tools; snapshot B, configure via UI, hourly matter through time, draft invoice and approval with roles. Captured mail only if needed. |
| C04 Compare firms and complete customer journeys | Coordinator + bots | WAITING | After C02/C03; same commit, side-by-side screenshots, shared steps produce intended distinct outcomes; document/portal journey with synthetic client, exact monetary reconciliation. Serialize overlapping tools. |
| C05 Permissions and isolation | Coordinator + bots | WAITING | After profiles exist; intended role visibility and denied direct writes; separate operator harness proves cross-firm credential/session/data isolation without bots logging into another firm. |
| C06 Upgrade both configurations | Engineering/operator, unassigned | BLOCKED | Authorized isolated copies, source and target release artifacts, different commits, baseline manifests, backup and rollback plan. Real upgrade, manifests/data comparisons and browser replay on both at same target commit. |
| C07 Restore and rollback | Engineering/operator, unassigned | BLOCKED | Disposable recovery environment; restore backups and verify file hashes, money totals, settings, dashboards, templates and permissions. Verify rollback compatibility or explicit safe refusal. No live reset. |
| C08 SaaS operating readiness | Coordinator | WAITING | After C01, source/evidence inventory of provisioning, subscription/account lifecycle, export/offboarding, monitoring and support. Record existing evidence or concrete gaps; no assumption features are missing. |

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
The QA bots do not edit code. No live deployment, container restart, commit or push is authorized by this heartbeat.

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
No acceptance gate has been verified yet. This is a plan, not a completion claim.

Transition posts read back and verified:

- 2026-10-10T03:48:59Z: https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093461018
- 2026-10-10T03:49:00Z: https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093461124

C01 returned an HTTP-only inventory; browser evidence is still pending, not verified. Bot 1 completed R154 and is waiting for C02; C01 browser evidence remains pending.

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
