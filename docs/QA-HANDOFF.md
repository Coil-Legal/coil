# Writing a Grok handoff

Rules for whoever holds the Grok seat on issue #12. Ian's direction, 2026-10-01.

## Why these rules exist

Batching took the loop from 2 cases an hour to 13.5. Two things now limit it:

- **Turnaround.** Grok finishes a batch in minutes and then waits up to 16 minutes for the
  next one. Every handoff costs that wait, so fewer, larger handoffs go faster.
- **Value.** The fastest recent batches were mostly reads of empty pages: no holidays set,
  no voice calls yet. Those pass in seconds and find nothing. Defects live where something
  changes state.

## The rules

1. **10 to 15 cases per handoff.** One PASS or FAIL per case, as now.
2. **At least half the cases act.** Create, edit, switch, send to the QA inbox, upload,
   resolve, then check the result. A read-only case is fine when it verifies what an
   earlier case in the same batch did, or a boundary nobody has looked at. A read of a page
   that is empty because nothing was ever created is not a case.
3. **Each acting case says exactly what to create and what to expect.** Name every test
   record with `QA` and the date, for example `QA Calendar 20261001`, so it reads as test
   data. Give the expected flash, count or state, not "check it works".
4. **Push on the edges.** In every batch, include at least two of: an empty or overlong
   input, non-Latin text, a duplicate submission, a date on a month end or leap day, a
   second user or role, an action undone and redone.
5. **Put the next handoff up as soon as the result is recorded.** Record and queue in the
   same post. Grok should never be waiting on a "recorded" post with nothing after it.
6. **Unchanged:** pin `/health` to one commit and stop if it moves; no Stripe, no SMS, no
   pay links; email only to `grok-coil-github@agentmail.to`; the fixture do-not-touch list;
   invoicing, payments and multi-currency stay parked, and so does the AI assistant (P1-AI):
   Ask Coil, matter and client-update summaries, AI extraction in personal injury and
   discovery, and AI narrative polish. Ian, 2026-10-02: "we can develop these later"; never paste a token or link.
7. **Leave testfirm as you found it** when a batch changes firm-wide settings. The last
   case of such a batch puts the setting back and confirms it.

## Two bots

Bot 1 (`grokshaz`) runs on testfirm from issue #12. Bot 2 runs on qa2.coil.legal from issue
#89, its own seeded firm. The full split is in `AGENTS.md` under "Two QA bots". In short:

- Write each bot's handoff on its own issue, pinned to its own firm's `/health`.
- Bot 2 numbers cases from 5001 and names records `QA2` plus the date.
- Split the remaining tools between them; never both on one tool at once.
- Give Bot 2 anything that changes firm-wide settings. The Settings > Tools batch below is
  its first batch.
- On qa2, email is never sent. Magic links and notices are read in the owner-only
  `/dev/outbox`.

**Resetting qa2** when its data gets in the way:

1. Back up `data/`, `.env` and `docker-compose.yml` under `/home/deploy/backups/coil/qa2.coil.legal/`.
2. `docker compose down`, then move `data/practice.db*` into that backup folder.
3. Rebuild on the current commit with `--build-arg COIL_COMMIT`, then `docker compose up -d`.
4. Run `python seed.py` inside the container. It only seeds an empty database.
5. Recreate the Bot 2 owner login and rotate the demo owner's public `password123`,
   generating both passwords on the server and writing the Bot 2 one only to
   `/root/qabot2-login.txt` (mode 600). Never print or post either.

## Where acting cases are most likely to find something

Ordered by how recently the code changed and how little it has been exercised.

1. **Settings > Tools** (`999570a`, never tested by Grok). See the ready batch below.
2. **Calendar:** create, edit and delete events; recurrence across a month end; an all-day
   event; the feed after an edit.
3. **Tasks and court rules:** apply a rule set to a matter with a month-end trigger, mark
   tasks done and undone, a task on a matter that is then closed.
4. **Documents:** upload a non-Latin filename, share and unshare to the portal, a duplicate
   upload, a document on a closed matter.
5. **Intake:** submit the public form with an overlong name, convert a lead, decline one
   with a reason, run a follow-up sequence to drafts.
6. **Conflict check:** run a check that hits a test contact, resolve it, re-run after
   editing the contact's name.
7. **Engagement letters and signatures:** create from a template, send to the QA inbox,
   sign from the captured link, try the link twice.

## Ready batch: Settings > Tools, for Bot 2 on qa2

Owner session on qa2.coil.legal, pinned to its `/health` commit. Case numbers from 5001, records
named `QA2` plus the date. Read the current state first and put it back at the end.

1. Open Settings > Tools. Report how many tools are listed and whether any box is unticked.
2. Untick Personal injury and Criminal defense, Save. Expect a flash naming both and saying
   everything in them is kept.
3. Reload the dashboard. Expect neither in the sidebar.
4. Open `/pi`. Expect 404 with a message that names Personal injury, says it is switched
   off, and links to Settings, Tools.
5. Untick Invoices only, Save. Expect the flash to name Invoices as switched off and to say
   Payments and Plans and splits are still off because a tool they rely on is off.
6. Open the dashboard. Expect no Outstanding A/R card and no Overdue invoices card.
7. Open the first demo matter. Expect no Invoices tab. Then open that matter with
   `?tab=invoices` added to its URL. Expect the matter overview, not an error.
8. Before case 5, create and send a `QA2` invoice for $1.00 on a demo matter so a public
   link exists (the email lands in `/dev/outbox`). Now open that invoice's public link
   (do not pay, do not paste the link). Expect it still opens.
9. Untick Time suggestions only and tick Time and expenses. Save. Expect `/time` to open and
   `/time/suggestions` to answer 404.
10. Sign in as a non-owner QA user if one exists, or create one named `QA2 Tools Staff
    20261003` with role paralegal. Open `/settings/tools`. Expect 403. Open `/pi`. Expect a
    message telling them to ask the firm owner, with no Settings link.
11. As owner, open the audit log. Expect `tools_changed` entries for each save in this batch.
12. Tick every box, Save. Expect the sidebar, the dashboard cards and the matter tabs back
    exactly as in case 1, and `/pi` and `/invoices` open again.

Expected outcome if all pass: the switches hide and restore cleanly, nothing is lost, client
links survive, dependents follow their parent, and only the owner can change it.
