# QA queue

What the two QA bots test next. Ian and Claude Code write the batches here; the launchd
coordinator (`com.iandolan.coil-qa-coordinator`, every 10 minutes) posts them. Rules for
the coordinator are in `~/.claude/scheduled-tasks/coil-qa-coordinator/SKILL.md`.

How a batch moves:

- `status: queued` means not posted yet. The coordinator posts the first queued batch for a
  bot only after that bot's previous result has been recorded, in the same comment as the
  record.
- When it posts one, it changes the line to `status: posted <comment URL> <UTC time>`.
- `status: hold` means written but not to be posted yet; skip it.
- Cases inside a batch are numbered `1.`, `2.` and so on. The coordinator renumbers them to
  continue that bot's case numbers (Bot 1 after its last case, Bot 2 after its last 5xxx case).
- Each batch says what to create, what to expect, and what to leave alone. The coordinator
  adds the standard header (pin, bot identity, drift rule, signing) itself.

A bot with nothing queued stands by. That is correct; do not invent work.

## Bot 1 (#12, grokshaz, testfirm.coil.legal)

(Nothing queued. Phase 1's 19 bot-testable tools are signed off; Ian and Claude Code are
choosing the next area.)

## Bot 2 (#89, QA Bot 2, qa2.coil.legal)

(Nothing queued. Same reason.)
