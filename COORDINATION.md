# Coil agent coordination

Repository: `/Users/iandolan/General/solo-practice`

Read this file and the current Git status before editing. Update your own active-work entry when starting, changing scope, handing off, or finishing. Do not overwrite another agent's entry. If an entry says active but its timestamp is old, ask Ian or inspect the checkout before assuming that work has stopped. This file records agent reports, not a live process monitor.

Use an isolated checkout for overlapping work. Before integrating, compare against the latest source and preserve other agents' commits and uncommitted changes. A task is complete only when its changes are in the shared checkout or the handoff identifies exactly where they remain.

## Active work

Updated 2026-09-19 20:27 UTC.

- **Codex: complete, no files held.** All 19 review fixes are committed locally as `448d70d` and deployed to testfirm only. `/health`: `448d70d`, `test-20260919`, healthy. Full suite: 628 passed. All 24 changed application/updater files in the running image match the tested copy; public route and unsigned-webhook checks pass. Demo remains on `0e340ce`. Grok was notified: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5746240228. GitHub main push was rejected by automatic approval review because the request authorized test deployment, not that branch push; do not push it until Ian explicitly authorizes it. This coordination update is uncommitted. Timestamp 2026-09-19 23:56 UTC.

- **Claude Code: idle, no files held.** Last task was setting up this log, finished and committed as `23aba35` on `main` (`COORDINATION.md`, `CLAUDE.md`, `AGENTS.md`, plus the loop's own instructions outside the repo). No application code touched. Codex's branch has right of way on every file it lists; Claude Code will not edit `app/blueprints/trust.py`, `app/blueprints/invoices.py` or `app/helpers.py` until Codex's handoff lands, and will update this entry first if that changes. Working directory `/Users/iandolan/General/solo-practice`. Timestamp 2026-09-19 20:27 UTC.

- **Autonomous QA loop: running unattended.** This is a fourth participant the draft did not list, and it is the one most likely to surprise the others. launchd job `com.iandolan.coil-grok-check` fires every 10 minutes, runs `~/.claude/scripts/coil-grok-check.sh`, and acts on GitHub issues in `Coil-Legal/coil`. When it finds a reported defect it edits **this shared checkout**, commits to `main`, and deploys to testfirm and demo without asking anyone. It fixed two findings during the afternoon of 2026-09-19 (`bd1589e`, `e239275`). It does not report here on its own. Its instructions are at `~/.claude/scheduled-tasks/coil-grok-handoff-check/SKILL.md`, which now carries the same read-first requirement, but nobody should rely on that alone: **check `git log` immediately before integrating any branch, because `main` can move while you are reading this file.** To stop it for a long integration: `launchctl bootout gui/$(id -u)/com.iandolan.coil-grok-check`, and afterwards `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.iandolan.coil-grok-check.plist`.

- **Grokbot: live QA, reports on GitHub.** Ian reports live QA work. Current test scope and status have not been reported here. Record findings with the deployed commit/version so local fixes can be distinguished from deployed behavior. It has no write access to this checkout; it files issues, and the loop above is what turns them into commits.

## Overlap to watch right now

Codex's branch and the four changes shipped on 2026-09-19 touch the same three files. Anyone integrating should diff rather than assume:

| File | Codex `codex/review-fixes` | Already on `main` at `0e340ce` |
|---|---|---|
| `app/blueprints/trust.py` | +51 lines | inter-matter transfer, `firm_fee` type and its warning |
| `app/blueprints/invoices.py` | +13 lines | credit notes, `CREDIT_REASONS`, two credit routes |
| `app/helpers.py` | +12 lines | `_day_type_label` template global |

Claude Code will not edit these files until Codex's handoff lands, and will say so here if that changes.

## Recent handoffs, newest first

- **2026-09-20 01:37 UTC, Autonomous QA loop.** Found two fixes already staged uncommitted in this checkout (`app/blueprints/conflicts.py`, `app/blueprints/settings.py`, plus two new test files) matching open issues #41 and #42, from a prior run of this same loop that had not reached commit/deploy. Verified both new tests fail on the pre-fix code and pass after, then ran the full suite: 632 passed. Committed as `edcfe51` on `main` (on top of Codex's `448d70d`). Deployed to both `testfirm.coil.legal` and `demo.coil.legal` (`--build-arg COIL_COMMIT=edcfe51`); `/health` on both reports `edcfe51`, healthy. Did not touch `app/blueprints/trust.py`, `app/blueprints/invoices.py`, or `app/helpers.py`. Did not push to GitHub origin, per Codex's note above that the pending push needs Ian's explicit go-ahead first (`main` is still 2 commits ahead of `origin/main`). Issues #41 and #42 commented with repro + re-test steps and moved to `qa:fixed`.

- **2026-09-19 23:56 UTC, Codex.** Deployed release `448d70d` to `testfirm.coil.legal` at Ian's request. Health and public smoke checks passed; zero container restarts. Backup: `data/backups/coil-backup-20260919-235239.tar.gz` under the testfirm app. Rollback image: `coil-testfirm:before-448d70d`; source backup: `/home/deploy/backups/coil/testfirm.coil.legal/source-before-448d70d.tar.gz`. Settings and Compose configuration were preserved. Grok can start section Y: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5746240228. Demo unchanged. Local release commit remains unpushed because automatic approval review rejected that separate action.

- **2026-09-19 23:26 UTC, Codex.** Completed all seven original fixes and 12 Phase 1 fixes. Combined patch and file list are in `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-all-fixes-handoff.md`. Full suite: 628 passed. Application, updater and regression tests are integrated into the shared checkout, uncommitted. Every integrated file matched the tested copy. No schema changes, new dependencies, commits or deployment. Do not apply the older seven-fix patch separately.

- **2026-09-19 20:27 UTC, Claude Code.** Coordination log set up. Commit `23aba35` on `main`: this file, `CLAUDE.md`, `AGENTS.md`. Also added the same read-first requirement to the autonomous loop's instructions at `~/.claude/scheduled-tasks/coil-grok-handoff-check/SKILL.md`, which is outside the repo and therefore not in that commit. Tests: full suite `545 passed`, unchanged, since no application code was touched. Remaining work: none. Deployment status: not deployed and none needed, documentation only.

- **2026-09-19 20:24 UTC, Claude Code.** Four product decisions built and shipped, all on `main`, all deployed.
  - Commits: `9039d96` month and year deadline units, `e007fa9` inter-matter trust transfer, `3e21e95` credit notes, `0e340ce` firm fee type and earned-fee warning.
  - Tests: full suite `545 passed`, run before each commit. New files `tests/test_month_deadlines.py` (20), `tests/test_trust_transfer.py` (10), `tests/test_credit_notes.py` (13), `tests/test_firm_fee.py` (7). One existing assertion in `tests/test_destructive_guards.py` was updated to name the credit note now that the instrument exists.
  - Deployment status: deployed to `testfirm.coil.legal` and `demo.coil.legal`; `/health` on both reports `0e340ce`.
  - Remaining work: none on these four. GitHub issues #14, #15, #16 and #19 are labelled `qa:fixed` and queued with Grokbot for verification as section X on issue #12.
  - Notes for whoever integrates next: `COIL_COMMIT` is a Dockerfile ARG, so it must be passed with `--build-arg` or `/health` reports `unknown`. `app/blueprints/invoices.py` has no `url_prefix`, so every route spells `/invoices/...` itself. Crediting an invoice needs `db.session.expire(inv, ["credit_notes"])` before `recalc()` or the eager backref cache hides the new credit.

- **2026-09-19 20:21 UTC, Codex.** Seven fixes are being validated in an isolated checkout. Original application files are unchanged. Review: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-code-review.md`.

- **Observed Git history:** `0e340ce`, paying the firm from trust; `3e21e95`, credit notes; `e007fa9`, transfers between matters. These commits are included in Codex's starting point. Git records their full authorship and diffs.

For each handoff, record the timestamp, agent, commit or patch location, affected files, checks run, outstanding work and deployment status. Keep only recent entries here; use Git history for older committed changes.
