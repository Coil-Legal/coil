# Coil

Open-source practice management for solo and small law firms. Flask 3, SQLAlchemy, SQLite.

**Build rules live in [docs/CONVENTIONS.md](docs/CONVENTIONS.md). Read that before writing code.** It is the authority on the schema, money handling, CSRF, templates, the URL contract and copy style. Nothing here replaces it.

## Coordination, because more than one agent works in this repo

More than one agent edits this checkout, and one of them commits and deploys on a timer without asking. So:

1. **Read [COORDINATION.md](COORDINATION.md) before you edit anything**, and run `git log --oneline -5` at the same time. The file is a set of reports, not a live monitor, and `main` can move while you are reading it.
2. **Update your own entry** when you start, change scope, hand off, or finish. Never edit or delete another agent's entry. If an entry looks stale, ask Ian or inspect the checkout rather than assuming the work stopped.
3. **Use an isolated checkout** for anything that overlaps work another agent has claimed. Before integrating, diff against the current source and preserve the other agent's commits and uncommitted changes.
4. **A handoff records** the commit or patch location, the files touched, the tests run and their result, what is left to do, and whether it is deployed.
5. **Do not apply or deploy another agent's working copy** until that agent has posted a completed handoff.

Work is finished when it is in the shared checkout, or when the handoff says exactly where it still lives.

## Grok handoffs on issue #12

Whoever holds the Grok seat writes handoffs by [docs/QA-HANDOFF.md](docs/QA-HANDOFF.md):
10 to 15 cases per handoff, at least half of them cases that act (create, edit, switch,
send to the QA inbox) and then check the result, with every test record named `QA` plus
the date, and the next handoff posted in the same comment that records the last result.
Reads of pages that are empty because nothing was created do not count as cases.
Since 2026-10-04 (Ian: "let's do Phase 2") invoicing, manual payments, plans, multi-currency
and trust are back in scope on QA records. The AI assistant (P1-AI) stays parked, and on
testfirm nothing touches card payments while it holds live Stripe keys.
They moved to Phase 2 on 2026-10-03, so Phase 1 is 21 tools. Open Phase 1 tools now get
one sign-off batch each, then a decision: see "Sign-off batches" in docs/QA-HANDOFF.md.
A name that must match nothing is built when the case runs, never written in a handoff.

## Two QA bots

Two bots test in parallel, each on its own firm with its own queue. Sharing a firm does not
speed anything up, because the bots overwrite each other's records.

| | Bot 1 | Bot 2 |
|---|---|---|
| Account | `grokshaz` | QA Bot 2, posting through Ian's `iandolan` account |
| Firm | testfirm.coil.legal | qa2.coil.legal, "Coil QA Bot 2 Firm" |
| Queue | issue #12 | issue #89 |
| Case numbers | continue from #12 | start at 5001 |
| Record prefix | `QA` plus the date | `QA2` plus the date |

- Bot 2 posts through the same GitHub account the coordinators use, so its posts are only
  told apart by their signature. Every Bot 2 ACK, result and finding starts with
  `[QA Bot 2]`, and every coordinator handoff on #89 reminds it to. Bot 2's findings are
  titled `QA2:`.
- A bot never signs in to the other bot's firm, never acts on the other's queue, and deletes
  only records carrying its own prefix.
- Never queue the same tool on both bots at once. COORDINATION.md says which tools each bot
  is on, and who holds each queue's seat.
- Anything that changes firm-wide settings (Settings > Tools, firm settings, shared
  templates) goes to Bot 2, so it never disturbs Bot 1's fixtures.
- Pin each handoff to that firm's own `/health` commit. Do not write a commit hash into these
  instructions; it is stale after the next deploy.
- **Every deploy goes to testfirm, demo and qa2**, same commit, with `--build-arg COIL_COMMIT`.
  Otherwise Bot 2 tests old code.
- qa2 sends no email outside the server. Since 2026-10-04 its SMTP points at its own capture
  inbox (Mailpit stack `/home/deploy/apps/coil-qa2-mail`, alias `coil-qa2-mailpit`), read at
  https://qa2.coil.legal/qa-mail/ by a signed-in qa2 owner, the same way testfirm's works.
  Nothing is relayed out. qa2 holds no Stripe, Twilio or AI keys. Keep it that way.
- Do not copy testfirm's data or documents to qa2. To reset qa2, follow
  [docs/QA-HANDOFF.md](docs/QA-HANDOFF.md): back up, set the database aside, rebuild, and
  re-seed from `seed.py`, never from QA leftovers.
- Logins never go in the repo, an issue, a comment or the log. Bot 2's login is in a
  root-only file on the server, `/root/qabot2-login.txt`, for Ian.

**Progress tabs in the QA Tracker Sheet are rebuilt by a script, not by hand.** Progress log,
Daily progress, Tool history and Status history come from every bot result on #12 and #89,
via `~/.claude/scripts/coil-qa-progress.py` (launchd `com.iandolan.coil-qa-progress`, 08:00
and 20:00 Central). Do not edit those four tabs. Run the script after recording a result if
Ian wants it current sooner. The script finds results by format, so keep result posts
starting with `Cases N–M — Topic — counts` and a per-case `| N | PASS |` table; a batch
title that names the tool ("Calendar", "Conflict checks") files it under the right tool.

**Since 2026-10-03 a launchd coordinator holds both seats.** `com.iandolan.coil-qa-coordinator`
runs every 10 minutes (`~/.claude/scripts/coil-qa-coordinator.sh`, instructions in
`~/.claude/scheduled-tasks/coil-qa-coordinator/SKILL.md`, log
`~/.claude/logs/coil-qa-coordinator.log`). It records each bot result on #12 and #89 and posts
the next batch from `docs/QA-QUEUE.md`, signed `[Claude]`. To steer a bot, add a batch to
that file. When nothing is queued, the coordinator writes the next batch itself from the
backlog in that file (Ian: a bot that finishes always gets a new batch). Codex and Cursor do not post on #12 or #89
while it runs; if Ian hands a seat back to one of them, pause the job first
(`launchctl bootout gui/$(id -u)/com.iandolan.coil-qa-coordinator`).

**Who coordinates which queue changes with usage.** Codex and Cursor take turns holding the
#12 and #89 seats, depending on which one has usage available. When a seat changes hands:

1. The incoming agent records "holding #12" or "holding #89" in its entry in COORDINATION.md
   before posting anything, and the outgoing agent marks itself off that seat when it can.
2. Read the queue issue from its last handoff. If a batch is still in flight, wait for the
   bot's result and record it before posting the next one. Never two coordinators on one queue.
3. Carry on the case numbers, the record prefix, the fixture do-not-touch list and the
   exclusions exactly as the last handoff left them. Re-pin to that firm's `/health`.
4. Sign each post with your own tag, `[Codex]` or `[Cursor]`, so the bot and Ian can see who
   is speaking.
