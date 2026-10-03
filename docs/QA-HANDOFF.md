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

8. **A name that must match nothing is built when the case runs, never written in the
   handoff.** testfirm files every #12 notification email as a message, so a "made-up"
   name typed into a handoff is already in the firm and gets an exact hit (case 1162).
   Tell the bot to build it, for example `QA Nohit` plus the clock time it runs the case,
   or give no-match cases to Bot 2, whose firm takes in no mail.

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

## Sign-off batches (Ian, 2026-10-03)

Phase 1 is now 21 tools: invoicing, payments and the AI assistant moved to Phase 2. Most
Phase 1 tools already pass case after case, so more breadth no longer moves the count.
Each open tool now gets **one sign-off batch** on the current release, then a decision.

**What a sign-off batch is:** 12 to 15 cases that run the tool's core jobs end to end on
the current `/health` commit, acting rather than reading, with the edges from rule 4 and
at least one non-owner role. It re-proves on today's code what earlier batches proved on
older builds. It does not hunt new corners.

**After the result:**
- All PASS: the coordinator marks the tool `QA complete` on the Tools tab, with the
  release, the result link, and the accepted limitations below copied into "Remaining
  before signoff" as limitations, not open work.
- A FAIL: it is filed, fixed, and only the failing cases are rerun. Then mark it.
- A limitation not listed here goes to Ian before the tool is marked.

The outlines below say what to cover. The coordinator turns each into an exact handoff:
fixture IDs, expected flashes and the do-not-touch list.

### Calendar, deadlines and court rules (Bot 1, #12)
Accepted limitations: subscribing from an outside calendar app (Google, Apple, Outlook)
is not bot-tested; choosing the second of two repeated clock times and editing one
occurrence of a series are not built; court-specific rule completeness is the Phase 2 row.
1. Baseline: month view, count of this month's events.
2. Create a timed firm-wide event `QA Signoff Cal` plus the date. Expect the flash and the grid.
3. Edit its time. Expect the grid, the event page and the owner feed to show the new time once, same UID.
4. All-day event on a month's last day. Expect that day only, in grid and feed.
5. Monthly repeat from Jan 31 2027 to Jun 30 2027. Expect Feb 28, Mar 31, Apr 30.
6. Weekly 09:00 Chicago event across the March 2027 clock change. Expect 09:00 local on both sides.
7. Empty title, and an end before the start. Expect both refused, nothing saved.
8. Non-Latin title. Expect it saved and shown exactly.
9. New matter `QA Signoff Matter` plus the date; apply a rule set with a Jan 31 trigger. Expect previewed dates equal saved task dates.
10. A deadline landing on a weekend. Expect it rolled as the rule says.
11. Mark one generated task done, then undone. Expect it to leave and return to the feed.
12. Second role: the staff user opens the event and the matter's deadlines. Expect what the role matrix allows.
13. Delete the repeating series. Expect it gone from grid and feed.
14. Clean up the batch's events; close the matter.
15. What remains: fixtures intact, nothing from this batch left but the closed matter.

### Conflict check (Bot 1, #12)
Accepted limitations: Greek and Cyrillic names are matched exactly and through saved
other names, not transliterated automatically; no large-firm scale test.
1. Baseline: check history count.
2. Create a QA person contact. Run a check on the exact name. Expect an exact hit, unresolved.
3. Same name in different case and spacing. Expect the same hit.
4. Add an other name. Check on it. Expect a hit on that contact.
5. QA company contact. Check on the company name. Expect a hit.
6. Add the person as adverse party on a QA matter. Check. Expect the party role shown.
7. A QA intake lead. Check its name. Expect a lead hit.
8. Non-Latin exact name. Expect an exact hit.
9. No-match name built when the case runs (rule 8). Expect clear, zero hits.
10. Waive with no reason. Expect refused.
11. Waive with a reason, then mark unresolved. Expect both flashes and history.
12. Staff user runs a check. Expect allowed, recorded under that user.
13. Clean up the batch's contacts, lead and matter.
14. What remains: checks 89 and 99 to 110 untouched.

### Client portal (Bot 1, #12)
Accepted limitations: paying from the portal is Phase 2 with payments; screen-reader
coverage is the Phase 2 accessibility row.
1. Create a QA client contact with a QA matter.
2. Upload a small document to the matter and share it to the portal.
3. Request a sign-in link; read it in `/qa-mail/` as owner.
4. Open it. Expect the shared document listed.
5. Download it. Expect the same size and bytes as uploaded.
6. Unshare it while the client is signed in. Expect it gone and its direct URL refused.
7. Second QA client contact signs in. Expect no access to the first client's document by URL.
8. First client uploads a small file with a non-Latin name. Expect it on the matter, marked as from the client.
9. Client sends a portal message. Expect it in the firm's messages; no SMS.
10. Portal at 390px wide. Expect no sideways scrolling and every control reachable.
11. Sign out. Expect the login page; the old link refused.
12. Clean up the batch's contacts, matter and documents.

### Users, roles, offices and audit (Bot 2, #89)
After Matters and Offices 5064 to 5076. One sweep: each role (attorney, paralegal,
billing, readonly) tries one allowed and one refused action in settings, trust, matters
and reports; deactivating a user ends their session; the last owner cannot be demoted;
Settings > Tools stays owner-only; every change lands in the audit log.

### Intake and leads (Bot 2, #89)
Reopened by the 7acb3a4 decline fix. The intake regression batch already planned in
`docs/PHASE1-READINESS.md` is its sign-off batch.

### Not batches
- **Messages:** waits on Ian's text from a phone. Outbound can be signed off now.
- **Backup, restore and self-update:** an operator test on a disposable copy, not a bot batch.
