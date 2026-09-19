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
