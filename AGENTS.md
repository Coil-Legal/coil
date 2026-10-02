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
Invoicing, payments, multi-currency and the AI assistant (P1-AI) stay parked.

## Two QA bots

Two bots test in parallel, each on its own firm with its own queue. Sharing a firm does not
speed anything up, because the bots overwrite each other's records.

| | Bot 1 | Bot 2 |
|---|---|---|
| Account | `grokshaz` | QA Bot 2 |
| Firm | testfirm.coil.legal | qa2.coil.legal, "Coil QA Bot 2 Firm" |
| Queue | issue #12 | issue #89 |
| Case numbers | continue from #12 | start at 5001 |
| Record prefix | `QA` plus the date | `QA2` plus the date |

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
- qa2 sends no email (`SMTP_HOST` is empty; mail lands in the owner-only `/dev/outbox`) and
  holds no Stripe, Twilio or AI keys. Keep it that way.
- Do not copy testfirm's data or documents to qa2. To reset qa2, follow
  [docs/QA-HANDOFF.md](docs/QA-HANDOFF.md): back up, set the database aside, rebuild, and
  re-seed from `seed.py`, never from QA leftovers.
- Logins never go in the repo, an issue, a comment or the log. Bot 2's login is in a
  root-only file on the server, `/root/qabot2-login.txt`, for Ian.
