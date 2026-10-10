# QA queue

## Current QA direction, Ian, October 9, 2026

[Two-firm acceptance](QA-ACCEPTANCE.md) is authoritative for new QA work.
Stop endless batches. No fixed case quota, automatic next batch, or reserve quota.
Only eligible acceptance gates or targeted defect retests may be assigned.
Legacy content below is historical wherever it conflicts with this direction.


What the two QA bots test next. Ian and Claude Code write the batches here; the launchd
coordinator (`com.iandolan.coil-qa-coordinator`, every 10 minutes) posts them. Rules for
the coordinator are in `~/.claude/scheduled-tasks/coil-qa-coordinator/SKILL.md`.

How a batch moves:

- `status: queued` means not posted yet. The coordinator posts the first queued batch for a
  bot after that bot's previous result is recorded (in the same comment), or straight away
  if the bot is standing by.
- When it posts one, it changes the line to `status: posted <comment URL> <UTC time>`.
- `status: hold` means written but not to be posted yet; skip it.
- Cases inside a batch are numbered `1.`, `2.` and so on. The coordinator renumbers them to
  continue that bot's case numbers (Bot 1 after its last case, Bot 2 after its last 5xxx case).
- Each batch says what to create, what to expect, and what to leave alone. The coordinator
  adds the standard header (pin, bot identity, drift rule, signing, exclusions) itself.

Ian, 2026-10-03: a bot that finishes always gets a new batch. If nothing is queued for it,
the coordinator writes the next batch itself from the top open area in that bot's backlog
below, appends it here, and posts it. If a bot's backlog is used up, it writes a regression
batch over whatever changed in the code since that bot's last batch.

Direction (Ian, 2026-10-03): Claude Code manages both bots. Bot 1 re-certifies the Phase 1
tools last signed off before tonight's fixes; Bot 2 runs a deliberate security sweep on its
clean firm. Invoicing, payments, multi-currency, trust and the AI assistant stay parked.

## Current acceptance assignments

- Bot 1: R154 completed, reported 12 PASS/0 FAIL/0 BLOCKED at 2026-10-10T04:16:04Z, comment 6093669583. Wait for C02; next case 3362. Retain contact 2033, closed matter 3331/M-1307 and expense 36, plus all older fixtures. No R155.
- Bot 2: S172 cancelled; C01 HTTP inventory returned, browser evidence supplement pending on the same cases. No new assignment.
- C02 through C08 are controlled by docs/QA-ACCEPTANCE.md dependencies. These are not
  auto-postable batches. Read code and evidence before drafting their executable steps.
- No legacy queued item below may restart. No reserve replenishment.

### C01. Profile B baseline and customization capability inventory (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093461124 2026-10-10T03:49:00Z
Gate: C01. Cases 7266 to 7271. Owner only. Browser first. No configuration saves.
Evidence supplement: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6093635898 2026-10-10T04:11:45Z, body verified. HTTP-only result is partial evidence; actual browser screenshots and full baseline required, or explicit browser blocker.

7266. Open / and /health on qa2. Record release and a dashboard screenshot. Read
      /dashboard/customize, record selected card keys/order without saving. Do not
      include cookies, session values, credentials or private links in evidence.
7267. Open /settings/tools as owner. Record raw checked choices, dependency-disabled
      tools, visible navigation and available optional tools. Do not toggle or save.
      This becomes the restoration baseline; distinguish visibility from permissions.
7268. Open /settings/templates and one existing template, or the unsaved new-template
      form if none exist. Record whether billing defaults, tasks, milestones and custom
      fields can be configured through the UI. Do not submit. The list may seed built-in
      sample templates if empty; report that side effect. Preserve all existing records.
7269. Inspect the UI for app-wide theme/branding, navigation order/labels, screen field
      layout and conditional workflow rules. Report the exact accessible control if
      present, or NOT FOUND with pages checked. Invoice branding is not app branding;
      generated template tasks are not a conditional workflow engine. Do not guess.
7270. Assess profile B feasibility: cards Unbilled time, Outstanding A/R, Invoices
      awaiting approval and Recent matters; hourly $150 template with a review task
      and Client reference field; invoice approval required. Record available controls,
      prerequisites and missing capabilities. Do not configure the profile yet.
7271. Return a concise baseline manifest, screenshots, capability table, friction and
      restoration notes. Separate observed support, missing capability and untested.
      List any incidental seeded records and all preserved fixtures. No cleanup deletes.
      Stop and wait. No import cases, no invented follow-up batch.

## Bot 1 (#12, grokshaz, testfirm.coil.legal)

### R1. Re-certify tasks, documents and e-signature
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5972084249 2026-10-03T18:17:22Z

Re-certification on today's build of three tools signed off days ago. Create only records named `QA Recert 20261003`. Use matter 3112 (M-1088, closed) only to read; for anything you create, use a new matter `QA Recert Matter 20261003` for client contact 1852 (`QA Day Client 20261003`), office none, no template.

1. Open the new matter `QA Recert Matter 20261003`. Expect `Matter M-.... opened.` Record its ID.
2. Add task `QA Recert Task 20261003` due Oct 15, 2026, assigned to QA Tools Staff 20261001. Expect `Task added.` It shows on the matter and on /tasks filtered to that user.
3. Add a task with an empty title. Expect `A title is required.` and nothing saved.
4. Edit the task's due date to Oct 31, 2026. Expect `Task saved.` Mark it done, then not done; it ends open, due Oct 31.
5. Upload `qa-recert-20261003.txt` (one line, `QA Recert 20261003`) to the matter. Expect `Uploaded qa-recert-20261003.txt.` Upload the same file again and report what Coil does with the duplicate (version, rename or second copy).
6. Upload a file named `QA Recert Ελληνικά 20261003.txt`. The Greek name is kept exactly in the list and on download.
7. Download the first file. The bytes match what you uploaded.
8. Create a signature request on that first document for the matter's client (contact 1852, email `qa-day-20261003@coil.test`). Expect `Signature request sent to qa-day-20261003@coil.test.` The request shows status sent.
9. In https://testfirm.coil.legal/qa-mail/ the sign email is there. Open its sign link (do not paste it), type the name `QA Day Client 20261003`, tick the consent box, sign. The page confirms it is signed.
10. Open the same sign link again. It does not allow a second signature; report the page.
11. As owner, the request shows signed, and its certificate opens and names the signer, the time and a document hash.
12. Try to void the signed request. Expect `A signed document cannot be voided.`
13. Delete the task (`Task deleted.`), delete the Greek-named file, and close the matter. The signed document and its certificate stay.

### R2. Re-certify personal injury, criminal defense and discovery
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5972379583 2026-10-03T18:52:40Z

Re-certification on today's build. Create only records named `QA Recert 20261003`. Do not click any AI button (Tailor with AI, Draft responses with AI, Re-run AI, Summarise). Do not touch a settlement worksheet or anything that posts to trust.

1. New matter `QA Recert PI 20261003` for contact 1852, no template. Start a personal injury case on it. Expect `Started a personal injury case on ...`.
2. Save case facts with an accident date of Feb 29, 2024 and a description with Greek text. Expect `Case facts saved.` Both show exactly after a reload.
3. Add provider `QA Recert Clinic 20261003`. Expect `Added QA Recert Clinic 20261003.` Add a provider with no name: `The provider needs a name.`
4. Request records from that provider. Expect a flash that the records letter was saved to Documents (Medical records). The letter is in the matter's documents.
5. Add a lien from `QA Recert Lienholder 20261003` for 100.00. Expect `Added lien from QA Recert Lienholder 20261003.` Remove it: `Removed the lien from QA Recert Lienholder 20261003.`
6. New matter `QA Recert Criminal 20261003` for contact 1852. Start a criminal case on it. Expect `Criminal case started on M-....`
7. Add a charge with an empty description: `Describe the charge.` Add charge `QA Recert charge 20261003`: `Charge added.`
8. Set an arrest date of Sep 1, 2026 and save facts. Add the speedy-trial deadline. Expect a flash naming the due date. Add it again: `That deadline already exists.`
9. Set the next setting date to Nov 2, 2026 and create the court-chain tasks. Expect a flash naming how many tasks. Run it again: `Those tasks already exist for this setting date.`
10. Save the disposition summary PDF. Expect a flash that it was saved to the Criminal folder; the document opens.
11. On the PI matter, create a discovery set we propound with two typed requests, no AI. Expect a success flash. Set the served date to Oct 1, 2026 and create the deadline task: `Deadline task created, due Oct 31, 2026.` Run it again: `That deadline task already exists (due Oct 31, 2026).`
12. Export the set to PDF. Expect `PDF filed under Documents in the Discovery folder: ...`; it opens.
13. Close both new matters. Report everything created.

### R3. Re-certify research, reports and exports
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5972722291 2026-10-03T19:28:00Z

Re-certification on today's build. Read-mostly. Do not click Summarise or any AI button. Create only records named `QA Recert 20261003`.

1. Open /research and search case law for `Miranda v. Arizona`. Report the first three results. If the outside search service does not answer, mark this case and the next two BLOCKED with the message shown.
2. Save the first result to matter `QA Recert PI 20261003` from batch R2 (reopen it first if it is closed, and close it again at the end). Expect a flash that it was saved to that matter.
3. Add the note `QA Recert note Καλημέρα 20261003` to the saved authority: `Note saved.` Export the memo for that matter: a flash that the memo was saved to the Research folder; it opens with the note text exact.
4. Cite check: paste `See Miranda v. Arizona, 384 U.S. 436 (1966).` and run it. Report what it finds.
5. Open each report under /reports (A/R aging, work in progress, revenue, productivity, origination, realization, profitability, compensation, trust balances). Each opens with HTTP 200 and no error page. Report any that do not. Do not change filters beyond the defaults.
6. On productivity, pick last month, then this month. Both load.
7. Download /exports/contacts.csv, /exports/matters.csv and /exports/time.csv. Each opens as CSV with a header row. Contact 1852 appears in contacts with its address on one line. Do not save them outside your run.
8. The matters export lists `QA Recert PI 20261003` and its status.
9. The time export includes a header and does not error on non-Latin descriptions.
10. Close the PI matter again if you reopened it. Report everything created.

### R4. Re-certify API tokens and webhooks
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5973184840 2026-10-03T20:26:00Z

Re-certification on today's build. Never paste a token. Token `QA-MCP-20260930` stays; do not revoke or edit it. Webhooks 9 and 10 stay paused; do not edit webhooks 1 to 10.

1. Create an API token named `QA Recert token 20261003` with read-only scope if offered. Keep it inside your session. Report the scopes shown.
2. `GET /api/me` with it: 200, names the owner.
3. `GET /api/matters` and `GET /api/contacts`: 200, JSON lists. Contact 1852 is in contacts.
4. `POST /api/time` with that token for a new matter you open first, `QA Recert API 20261003`: if the token is read-only, expect a refusal (401 or 403) and nothing saved; if it is not, expect 201 and a time entry, then delete that entry in the UI. Report which.
5. `GET /api/me` with a token string that is wrong by one character: 401, no data.
6. Revoke `QA Recert token 20261003`. `GET /api/me` with it: 401.
7. Create webhook `https://httpbin.org/status/200` subscribed to task.completed only. Report the flash.
8. Try to create a webhook to `http://127.0.0.1:8000/x`. Expect a refusal naming a private address.
9. On the API matter, add task `QA Recert Hook 20261003` and mark it done. The click returns in under a second. Within a minute the new webhook shows a delivery for task.completed with status ok.
10. Pause the new webhook, mark the task not done and done again. No new delivery appears for the paused webhook.
11. Delete the new webhook, delete the task, close the API matter. Webhooks 1 to 10 and token `QA-MCP-20260930` are unchanged.

### R5. Calendar feed keyboard check, then document templates and letter generation
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5973350386 2026-10-03T20:50:00Z

Re-certification on today's build. Create only records named `QA Recert 20261003`. Use
contact 1852 (`QA Day Client 20261003`) for the new matter. Do not touch the retained
fixtures (contact 1852; matters 3112/3113/3115/3116/3117, all closed; docs 145-152;
signature 20; provider 15; lien 7; discovery set 5 on M-1091; charge 7; webhooks 1-10;
token `QA-MCP-20260930`).

1. Open https://testfirm.coil.legal/calendar. Tab through the page from the top until
   focus reaches a feed URL box. Report whether Tab stops on it (confirms the
   `scrollable-region-focusable` fix for the calendar feed boxes still holds).
2. Open /doctemplates. Report how many templates are listed and whether "Closing letter
   (sample)" is active.
3. New template `QA Recert Template 20261003`, HTML kind, practice area Business, body
   `<p>{{ client_name }}</p><p>Matter: {{ matter_number }}</p><p>Σημείωση: Καλημέρα
   {DEADLINE}</p>`. Expect `Template QA Recert Template 20261003 saved with 3 merge
   field(s).` and the fields list shows client_name, matter_number, DEADLINE.
4. Try to save a new template with an empty name. Expect `A name is required.` and nothing
   created.
5. Open a new matter `QA Recert Templates Matter 20261003` for contact 1852, office none,
   no template. Expect `Matter M-.... opened.`
6. Generate `QA Recert Template 20261003` on that matter, leaving DEADLINE blank in the
   form. Expect `Generated QA Recert Template 20261003 - <its M-number>.pdf.` with no
   "could not be filled" warning. Open the PDF: client_name and matter_number show the real
   values; the Σημείωση line ends blank where `{DEADLINE}` was.
7. Generate the same template again, typing `QA Recert Deadline Οκτωβρίου 2026` into
   DEADLINE. Expect a second `Generated ...` document, with that Greek text filled in where
   `{DEADLINE}` was written.
8. Edit `QA Recert Template 20261003`: remove the DEADLINE line, add `{{ practice_area }}`.
   Save. Expect `Template saved with 3 merge field(s).` Open the two documents from cases 6
   and 7 again: both still show the old body including the DEADLINE line, confirming
   editing a template does not change documents already generated.
9. New template, kind Word (.docx), upload `qa-recert-notaword.txt` as the file. Expect
   `Upload a .docx file (Word format).` and nothing saved.
10. New template, kind Word (.docx), save with no file attached. Expect `Upload a .docx
    file for a Word template.`
11. Delete `QA Recert Template 20261003`. It was used for 2 documents, so expect `QA Recert
    Template 20261003 was used for 2 document(s), so it was deactivated instead of
    deleted.` It still shows in the list, inactive, and the two generated documents still
    exist.
12. Close matter `QA Recert Templates Matter 20261003`. Report everything created: the
    template id, the matter id, and the two generated document ids.

### R6. Matter templates (Settings > Templates)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5973632285 2026-10-03T21:25:00Z

Re-certification on today's build. Use contact 1852 (`QA Day Client 20261003`) for the new
matter. For the non-owner check, use the existing staff user `QA Tools Staff 20261001`
(user id 22, paralegal) signed in separately; do not change their role or deactivate them.

1. Open /settings/templates. Report how many templates are listed and which are active.
2. New matter template `QA Recert MT 20261003`, practice area Business, flat billing, one
   task (title `QA Recert MT Task 20261003`, kind task, offset 7 days, priority normal,
   assignee "responsible"), one milestone (description `QA Recert MT Milestone 20261003`,
   offset 14 days, amount left blank), one custom field (key `qa_recert_field`, value
   `QA Recert 20261003`). Expect `Template QA Recert MT 20261003 created.`
3. Try to save a new template with an empty name (other fields filled). Expect `A template
   name is required.` and nothing created.
4. Open a new matter `QA Recert MT Matter 20261003` for contact 1852, office none, using the
   `QA Recert MT 20261003` template. Expect `Matter M-.... opened.` Report that the task and
   milestone from the template already exist on the matter (template application happens at
   matter creation, not as a separate step).
5. Apply the same template to that matter again via its "apply template" action. Since the
   task title and milestone description already exist, expect `Applied QA Recert MT
   20261003: 0 milestone(s) and 0 task(s) added.` and no duplicate rows.
6. Edit `QA Recert MT 20261003`: add a second custom field, key `qa_recert_δεύτερο`, value
   `Δεύτερο πεδίο 20261003`. Save. Expect `Template saved.`
7. Apply the edited template to the matter a third time. Expect `Applied QA Recert MT
   20261003: 0 milestone(s) and 0 task(s) added.` (no new milestones or tasks), but report
   whether the matter's custom fields now include `qa_recert_δεύτερο` = `Δεύτερο πεδίο
   20261003` exactly, alongside the unchanged `qa_recert_field`.
8. Signed in as `QA Tools Staff 20261001` (paralegal, not owner), try to open the edit page
   for `QA Recert MT 20261003` (GET is enough; POST too if you want). Expect a 403, not the
   form.
9. Back as owner: duplicate `QA Recert MT 20261003`. Expect `Duplicated as QA Recert MT
   20261003 (copy).` Immediately delete the copy (it is unused). Expect `Deleted template
   QA Recert MT 20261003 (copy).`
10. Delete the original `QA Recert MT 20261003` (now used by 1 matter). Expect `QA Recert MT
    20261003 is used by 1 matter(s), so it was deactivated instead of deleted.` It still
    lists on /settings/templates, inactive.
11. Open the new-matter form's template dropdown. Confirm the now-inactive `QA Recert MT
    20261003` is no longer offered.
12. Close matter `QA Recert MT Matter 20261003`. Report everything created: the template id,
    the matter id, the task id and title, the milestone id, and both custom field values.

### R7. Time and expenses beyond the basics
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5973871228 2026-10-03T21:57:30Z

See the batch body in the comment above (cases 1539-1550): a new matter, the timer's
start/pause/resume/stop, rounding to the next 6 minutes, editing with non-Latin text, the
over-a-day confirmation, a discarded timer (stop then delete), an expense with and without
a receipt, the receipt download headers, and a close-out.

### R8. Engagement letters: templates, send, sign, decline/void
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5974230060 2026-10-03T22:34:00Z

See the batch body in the comment above (cases 1551-1565): a new engagement template (plus
a blank-name and a bad-syntax refusal), a new matter, a preview with non-Latin scope text,
save and send, the outbox email and tracking pixel, viewing the sign link, an overlong-name
refusal, a blank-name refusal, signing with a non-Latin name, reloading the same link after
signing (duplicate), refusing to void a signed letter, a second letter drafted then voided,
a readonly-role POST refusal, and a close-out. Still open for a later batch: the decline
flow, the reminder button on an open letter, and a letter sent to a contact with no email.

### R9. Contacts and lists under load (CSV import, search, conflict check)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5974522739 2026-10-03T23:17:36Z

See the batch body in the comment above (cases 1566-1578): downloading the import
template, a 60-row CSV import with non-Latin aliases (plus a dropped blank row and an
overlong-name edge), re-importing the same file under skip/update/create duplicate modes,
search correctness and timing on the loaded set (including the typeahead endpoint), a
check of whether the contacts list has sort/paging controls at all, a conflict check
against the loaded names, a readonly-role import refusal, and a 60-row clean-up. Written
from the code (no sort/page UI found in `contacts/index.html`), so this closes B1-6 as
"search and conflict-check load only" rather than leaving it open on sort/paging that
does not exist in the product today.

### R10. Setup guide, feature map and the feedback form

status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5974736157 2026-10-03T23:49:37Z

See the batch body in the comment above (cases 1579-1590): a read-only pass over
`/features` (exact count check) and `/setup-guide` (badge states, no save/skip), a
readonly-role check on both, and the feedback form exercised for real (a normal send,
a blank-message refusal, an overlong non-Latin send, an immediate duplicate, and a
readonly-role send), each message marked plainly as an automated QA test since it is a
real send to coil.legal. Narrowed from B1-7: the setup guide's five save/skip actions
are provider settings (parked), and the firm's own `/settings` page is firm-wide so it
stays Bot 2's, already covered in S7.

### R11. Session cookie invalidation on logout (regression for #101)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5974996102 2026-10-04T00:29:07Z

Bot 1's backlog (B1-1 through B1-7) was fully done, so per the standing rule this is a
regression batch over what changed in the code since R10's pin (`e77e6f6..7c595c7` touches
only one commit, `7c595c7`, "Invalidate every outstanding copy of a session cookie on
logout", issue #101). See the batch body in the comment above (cases 1591-1600): copying a
session cookie to a second session, confirming both work, logging out of one and
confirming the copy is refused, a clean re-login afterward, a double-logout edge, the same
check against a second role (readonly), three simultaneous copies invalidated by one
logout, and an ordinary session proven unaffected. Case 1595 doubles as a direct check of
whether the "stored owner password no longer authenticates" note from Bot 2's S8 result on
qa2 (issue #89) also shows up on testfirm.

### R12. Calendar, deadlines and court rules (sign-off)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5975193544 2026-10-04T00:51:00Z

No code under `app/` changed since R11's pin (`7c595c7`), so this is the sign-off outline
from docs/QA-HANDOFF.md rather than a regression batch. See the batch body in the comment
above (cases 1601-1615): timed/all-day/monthly/weekly events including a Chicago DST
weekly check, an empty-title refusal versus the end-before-start auto-correction (the
outline's assumption there was wrong; corrected after reading `calendar.py`), a non-Latin
title, a new matter with a court-rule-set deadline applied across a weekend roll (Sun Feb
21 2027 -> Mon Feb 22), a second-role (paralegal) read, deleting a recurring series, and
cleanup.

### R13. Conflict check (sign-off)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5975395216 2026-10-04T01:16:00Z

Bot 1's backlog (B1-1 through B1-8) is fully used up and no code under `app/` changed
since R12's pin (`7c595c7`), so this is the next area from the sign-off outline rather
than a regression batch. See the batch body in the comment above (cases 1616-1630): an
exact-name hit and a case/whitespace-insensitive repeat, an other-name (alias) hit, a
company-contact hit, a matter party hit (role `adverse`), an intake-lead hit, a non-Latin
name, a deliberate no-match built at run time, the empty-input refusal, the waive-with-no-
reason refusal versus waive-with-a-reason followed by unresolved, a paralegal running a
check (allowed) and a readonly user refused (403) on the write route, and cleanup.

### R14. Client portal (sign-off)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5975799195 2026-10-04T02:32:00Z

Bot 1's backlog is fully used up and no code under `app/` changed since R13's pin
(`7c595c7`), so this is the next area from the sign-off outline. See the batch body in
the comment above (cases 1631-1642): a new client contact and matter, a staff upload
shared to the portal, the magic-link sign-in flow read from `/dev/outbox` (correcting
the outline's stale `/qa-mail/` route), reusing a consumed sign-in link, a byte-identical
download, unsharing mid-session, a second client's access-isolation check, a blank-message
refusal, a Greek message and a Greek-named client upload, a 390px viewport check, and
cleanup. Accepted limitations carried over: payments from the portal are Phase 2; screen-
reader coverage is the Phase 2 accessibility row.

### R15. Time capture suggestions, and time-entry role scoping
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5976023530 2026-10-04T03:08:00Z

Bot 1's backlog (B1-1 through B1-8) and the sign-off outline (Calendar, Conflict check,
Client portal) are both fully used up, and no code under `app/` changed since R14's pin
(`7c595c7`), so this closes the two items B1-4 left open: "Time suggestions" and "a staff
user's own-time scoping." See the batch body in the comment above (cases 1643-1655): the
whole `/time/suggestions` tool via `/api/v1/capture` (a too-short segment ignored, a Greek
title matched to a matter by its number, a duplicate title merged within the 30-minute
window, a no-match capture built live), the `_own()` cross-user 403 on dismiss, accept-all
and accept/save and dismiss-all with their exact rounding and flashes, and a correction to
the "own-time scoping" framing: `/time` has no per-user filter, only the firm-wide `time`
permission (paralegal full access, billing view-only with its own 403 on write), proven
with a second role rather than the scoping feature the note assumed existed.

### R16. Messages

status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5976202245 2026-10-04T03:33:00Z

Bot 1's backlog and the sign-off outline are both fully used up, and no code under `app/`
changed since R15's pin (`7c595c7`), so this picks up the one Phase 1 client tool neither
bot has functionally tested yet: Messages (`app/blueprints/messages.py`), previously only
probed for HTTP status in a role sweep. See the batch body in the comment above (cases
1656-1670): the SMS-send validation chain refused before ever reaching `send_sms` (no
phone, then an unparseable phone), the email-send validation chain, a real reply sent only
to the sanctioned QA inbox with Greek text and an overlong truncated subject, a portal
reply and a portal reply with no client email on file, and the role matrix (paralegal
reads and replies, billing is refused the whole prefix, readonly reads but cannot POST).

### R17. Retest issue #100's fix: non-Latin text across the document-template, engagement-letter
### and research-memo PDF builders

status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5976494923 2026-10-04T04:15:49Z

Bot 1's sign-off outline and backlog are both fully used up, so this re-proves `e77e6f6` (the fix
for issue #100, still `qa:fixed` and awaiting this re-test) on `doctemplates.py`, `engagements.py`
and `research.py`'s PDF builders, with `statements.py` excluded as invoicing-adjacent. See the
batch body in the comment above (cases 1671-1683): an HTML-kind template with Greek text and a
merge field, back-to-back generation to hit the thread-local reset in both directions
(doctemplates-doctemplates, doctemplates-engagements, engagements-doctemplates), an engagement
draft's PDF and a research memo PDF in the same sequence, an empty-merge-field edge, a second
role (paralegal) reading all three PDFs, and cleanup.

### R18. Retest four already-fixed defects: matter edit validation, blank contact fields,
### long document names, lead audit log
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5976687983 2026-10-04T04:46:00Z

Bot 1's backlog and sign-off outline are both used up and no code under `app/` changed since
R17's pin, so this retests four previously-filed, already-`qa:fixed` defects that have never
been retested on testfirm: #96 (matter edit with no client returns 500 instead of "Pick a
client"), #92 (empty contact fields saved/shown as the text "None"), #87 (a long document
file name returns 500), and #95 (lead status/fields edits not written to the audit log). See
the batch body in the comment above (cases 1684-1695). Read the current code for each fix
before writing the cases (`matters.py`'s `no_autoflush` rollback, `contacts.py`'s stripped
`_fill()` plus the Send-text `tool_on`-style phone gate, `documents.py`'s
`_fit_filesystem_limit`, and `intake.py`'s `audit()` calls in `status()`/`fields()`) and
confirmed each is present at this pin.

### R19. Conflict check: closing the Phase 2 "further checks" caveats (name matching edges)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5976933287 2026-10-04T05:28:28Z

Bot 1's backlog and sign-off outline are both fully used up, no code under `app/` changed
since R18's pin (`f72353c`), and the pool of previously-filed unretested `qa:fixed` defects
is now empty too (the only unverified ones left, #91/#101/#103/#104, all belong to Bot 2).
So this comes from `docs/QA-HANDOFF.md`'s "Further checks" list under Conflict check,
never yet run. See the batch body in the comment above (cases 1696-1709): a suffix/middle-
initial fuzzy hit, a company and an individual sharing a name, a dual-role contact (client
on one matter, adverse on another), the same surname on multiple contacts not deduped,
Latin-diacritic folding (Vietnamese) versus no auto-transliteration on Cyrillic (a
documented limitation, not a bug), a company-only contact matched against a person-shaped
query, whitespace folding, an ALL CAPS query, two same-named contacts with different
emails not deduped, a no-match control built live, and cleanup.

### R20. Documents deep (testfirm): folders, tags, versions, search, sharing, and the billing/readonly guard
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5977103832 2026-10-04T05:49:00Z

Bot 1's backlog, sign-off outline and the conflict-check further-checks list are all used
up again, and `git log b687b0f..HEAD -- app` is empty, so no code changed since R19's pin
either. Documents has never had its own deep pass on testfirm (R1 only retested specific
fixed bugs; Bot 2's S11 ran the equivalent on qa2, a different firm with different
fixtures). See the batch body in the comment above (cases 1710-1722): folder/tag
normalisation (stray spaces, mixed case, dedup), a version-family bulk move/retag,
truncation of an over-300-char folder, a Greek-named and Greek-tagged upload found by
search, two same-named documents with different contents not merged, portal share/unshare,
a temporary billing user refused `/documents` outright and a temporary readonly user that
can open it but not POST, cleanup, and what remains.

### R21. Intake and leads deep pass (testfirm): pipeline, conversion, decline, follow-up
### sequences, and the billing/readonly guard
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5977319752 2026-10-04T06:29:22Z

Bot 1's backlog and sign-off list are both used up again, and `git log d67db0f..HEAD -- app`
is empty, so no code changed since R20's pin either. Intake has never had its own deep pass
on testfirm (Bot 2's S12 covered it on qa2, a different firm with different fixtures). See
the batch body in the comment above (cases 1723-1737): an overlong-name and non-Latin
submission, an empty-name refusal, moving a lead through the pipeline to Won before it is
converted, converting it to a new contact and matter, a refused second conversion, a
converted lead's status staying put, declining a second lead with a reason, follow-up
sequence validation (no name, no steps), starting a sequence and the drafted-vs-sent branch,
a no-email lead refused a sequence, a temporary billing user refused the POST and a
temporary readonly user getting the identical refusal, cleanup, and what remains.
Found #108 (misleading sequence-start flash on an already-converted lead); case 1729's
FAIL was the handoff's own wrong assumption, not filed.

### R22. Tasks deep pass (testfirm): creation, filters, done/reopen, the open-redirect
### guard, and the billing/readonly guard
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5977600876 2026-10-04T07:12:34Z

Bot 1's backlog is fully done again and there is no code drift since R21's pin to
regression-test, so this is a fresh deep pass: `/tasks` has never had one of its own
before (only touched in passing via matter templates in R6). See the batch body in the
comment above (cases 1738-1751): baseline group/SOL/rule-task counts, creating a task,
an empty-title refusal, an overlong-plus-non-Latin title and notes, editing, marking done
and reopening, filtering by kind/priority/assignee, the `next=` open-redirect guard,
a court-date task tied to a matter, deleting it, a temporary billing user refused the
POST and a temporary readonly user getting the identical refusal, a check that the SOL
and rule-task widgets are untouched, cleanup, and what remains.

### R23. Retest issue #102: matter-tagged messages on the matter's own Activity tab
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5977783492 2026-10-04T07:38:00Z

Bot 1's backlog and sign-off outline are both used up again, and `git log 8e8ed20..HEAD -- app`
is empty, so no code changed since R22's pin either. This retests #102 (`qa:fixed`, fixed in
`b687b0f`, never retested): `email_send()`, `send()` (SMS) and `portal_send()` in
`app/blueprints/messages.py` now each write a second `audit("send_message", "matter", ...)`
row whenever the message carries a `matter_id`, so it shows on the matter's own Activity tab
(`a.action.replace('_',' ')` → "send message", by the sending user, with the same detail
string as the message-level audit row) alongside the thread view, not only on the contact's
thread. Use contact 1852 (`QA Day Client 20261003`) is NOT needed; create a fresh contact and
matter instead. Create only records named `QA Messages Retest 20261004`. Use staff user
`QA Tools Staff 20261001` (user id 22, paralegal, active) for the second-role case; create one
temporary billing user for the refusal case and deactivate it at the end. Do not touch the
retained fixtures (contact 1863; matter 3132/M-1108; docs 162/163; lead 33; contact 1862;
matter 3131/M-1107; template 8; docs 157-161; engagement 18; users 22 active, 23-27 and 30-32
inactive; contact 1852; leads 34-37; contact 1864; matter 3136/M-1112 closed; sequence 3
deactivated; users 35/36 inactive).

1. New contact `QA Messages Retest 20261004` with phone `512-555-0199` and an email address,
   and a new matter `QA Messages Retest Matter 20261004` for that contact, office none, no
   template. Expect `Matter M-.... opened.` Record both IDs.
2. Open the matter's Activity tab. Expect exactly one row so far: `create` by the owner,
   detail naming the matter number and name (from the matter-creation audit).
3. From the contact's message thread, send an SMS reply with `matter_id` set to the new
   matter. Report the flash (Twilio is likely not configured on testfirm; either outcome is
   fine as long as the message is stored). Re-open the matter's Activity tab: expect a new
   `send message` row (two rows total now), detail naming the phone number, by the owner.
4. Send an email reply, body `QA Messages Retest email 20261004`, tagged to the same matter.
   Expect `Emailed QA Messages Retest 20261004. The reply is on the thread.` Activity tab:
   three rows now; the newest `send message` row's detail names the contact's email address
   and ends `(sent)`.
5. Send a portal-channel reply (`/messages/portal-send`) tagged to the same matter, body
   `QA Messages Retest portal 20261004`. Expect `Posted to the portal. The client was emailed
   that a message is waiting.` Activity tab: four rows now; the newest `send message` row
   names a portal message to the contact.
6. Send one more email reply tagged to the same matter, body in Greek: `Καλημέρα 20261004`.
   Expect the same `Emailed ...` flash pattern as case 4, with the Greek text exact on the
   thread. Activity tab: five rows; the Greek text is not required in the Activity row
   itself, just the fifth `send message` row existing.
7. Send one more SMS or email reply to the same contact, this time with no `matter_id` (a
   plain thread reply, not tagged to any matter). Confirm it appears on the thread. Re-open
   the matter's Activity tab: still exactly five rows, unchanged, proving an untagged message
   never adds a matter-side row.
8. Signed in as `QA Tools Staff 20261001` (paralegal), send one more reply (any channel) to
   the contact tagged to the matter. Confirm success, then check the matter's Activity tab:
   a sixth `send message` row, this one `by QA Tools Staff 20261001` rather than the owner.
9. Create a temporary user `QA Messages Billing Retest 20261004` (billing role). Signed in as
   that user, POST to `/messages/email-send` with a valid CSRF token, `contact_id` set to the
   new contact and `matter_id` set to the new matter. Expect a refusal (403), nothing sent,
   and the matter's Activity tab unchanged at six rows.
10. Close the matter `QA Messages Retest Matter 20261004`. Expect `M-.... closed.` Activity
    tab now shows a seventh row, `close`, in addition to the six `send message`/`create` rows
    already there (the fix only added a row for tagged sends; it did not disturb the other
    audit actions already on the tab).
11. Deactivate the temporary billing user. Report everything created: the contact id, the
    matter id and number, the message count on the thread, the final Activity-tab row count
    and its action sequence, and the deactivated billing user's id. Report what remains open
    for Bot 1: nothing in the backlog or sign-off outline; the next batch, if code has not
    changed again, will need to come from a fresh area or a new regression.

### R24. Retest issue #108: misleading sequence-start flash on an already-converted/declined/Won lead
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5978071199 2026-10-04T08:19:00Z

Bot 1's backlog and sign-off outline are both used up and no code changed since R23's pin
(`11fb356`), so this retests #108 (`qa:fixed`, fixed in `11fb356`, found by Bot 1 in R21's
case 1734, never retested): `sequence_start()` in `app/blueprints/intake.py` now checks
whether the lead is already converted/declined/Won *before* creating a `LeadSequence` row,
flashing a plain "already converted/declined/marked Won" message instead of the old
unkeepable "drafted/sent the next time ... runs" promise. See the batch body in the comment
above (cases 1-10): creating a fresh sequence, a converted lead's guard plus a repeat-attempt
idempotency check, a declined lead's guard, a Won-but-unconverted lead with a Greek name, the
same guard under a second role (paralegal), a check that the pre-existing no-email guard
still fires ahead of the new state guard, a normal lead proving the ordinary path still
works, cleanup, and what remains.

### R25. Regression: engagement-letter subject-line localization fix (#107) on testfirm
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5978277649 2026-10-04T08:52:00Z

Bot 1's backlog and sign-off outline are both used up again, and the only app-code change
since R24's pin (`11fb356..1262707`) is `1262707`, "Localize the client-facing engagement
letter subject lines, not just their body text (#107)". That fix was found and filed by
Bot 2 on qa2 (its S20 result), so Bot 2 retests it there on its own; this batch instead
regression-tests the same change from testfirm, confirming the English default subject is
byte-identical to the pre-fix text and that the fix itself (localized default subject,
untouched staff-typed subject, localized reminder wrapper) also holds on a second host.
See the batch body in the comment above (cases 1-12): an English baseline send/remind/sign,
a non-Latin staff-typed custom subject sent and reminded under a second role, a fresh
Spanish contact's send/remind/sign with the sign-form's Spanish validation errors and the
overlong-name guard, a check that the firm-side signed notify stays English by design,
cleanup, and what remains.

### R26. Contacts deep pass (testfirm): full CRUD, custom fields, search, the delete guard, and the billing/readonly guard
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5978594966 2026-10-04T09:39:00Z

Bot 1's backlog and sign-off outline are both used up again and no code under `app/`
changed since R25's pin, so this picks an area never given its own deep pass on testfirm:
`/contacts`, touched so far only under CSV-import load (R9) and conflict-check reads
(R13/R19). See the batch body in the comment above (cases 1752-1764): a baseline count and
an empty search, creating a person contact with every field including custom fields,
aliases, language and a LEDES id, editing to add a second custom field, the empty-name
refusal for both person and company kinds, an overlong non-Latin name round-tripping
untruncated (SQLite not enforcing `String(100)`, the same class of behavior as R22's task
titles), a company/`is_client` contact and the `only=clients` filter, the search endpoint
matching on aliases, a note added and an empty note no-op, the delete guard on a contact
with a matter versus a successful delete on one without, the paralegal/billing/readonly
role matrix, cleanup, and what remains.

### R27. Case audit deep pass (testfirm): the rule engine on non-PI matters, the finding
### lifecycle, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5979582413 2026-10-04T11:44:52Z

Neither bot had ever given `/audit` its own batch. This one deliberately uses non-PI
matters to prove `sol_near` and `no_activity` run independent of a PI case, covers the
dismiss/resolve/reopen/run lifecycle including the resolved-vs-dismissed permanence
difference, and the paralegal/billing/readonly role matrix including `run_now()`'s
separate owner-only gate (bare `abort(403)` -> generic "Not allowed", distinct from the
permissions-module role-refusal text). PI-specific rules are S28 on qa2 instead.

### R28. Matters deep pass (testfirm): core CRUD, custom fields, parties, milestones,
### notes, close/reopen, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5980009345 2026-10-04T12:39:23Z

Bot 1's backlog and sign-off outline are fully used up and no code under `app/` changed
since R27's pin (`1b1b954`), so this is the next area never given its own deep pass on
testfirm (Bot 2 already did the equivalent on qa2 as S26). Written from
`app/blueprints/matters.py` and `app/permissions.py`: new-matter validation (no client,
blank name), custom fields with non-Latin text, milestone add/delete and its
empty-description refusal, party add and its empty-name refusal, a note and a blank-note
no-op, the apply-template no-template refusal, close/reopen, the status and
practice-area/billing-type filters, and the billing/readonly role matrix (view-only GET,
403 on write).

### R29. Research, reports and exports deep pass (testfirm): case law search and saved
### authorities, the citation check, every /reports page, and the three non-money /exports
### downloads
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5980289941 2026-10-04T13:09:43Z

Bot 1's backlog and sign-off outline are fully used up again and no code under `app/`
changed since R28's pin (`1b1b954`), so this is the one Phase 1 tool never given its own
batch on testfirm (only read in passing in R3's recert; Bot 2 already did the equivalent on
qa2 as S30). Read `app/blueprints/research.py` in full (`_authority_from_form`'s
matter/case-name checks, `saved_note`/`saved_delete`/`saved_export`'s flashes, and
`cite_check`'s empty-input refusal and its `[internal]` note save gated on a matter being
chosen), `app/blueprints/reports.py` and `app/blueprints/exports.py` for their route lists,
and `app/permissions.py` (`/research` sits in the case-work prefix group mapped to
`matters`, so owner/attorney/paralegal hold it fully and billing/readonly are view-only;
`/reports` and `/exports` are each their own area, and critically different ones: attorney's
set holds `reports` but not `exports`, so an attorney is refused even a GET on `/exports`,
while readonly's view-only mirror of attorney carries `reports_view` but, same reason, no
`exports_view` at all). Every expected flash below was read from the code at this pin,
quoted exactly. Use staff user `QA Tools Staff 20261001` (user id 22, paralegal, already
active) for the positive role-matrix case rather than creating a new paralegal. Create only
records named `QA Research` plus the date (20261004).

1. Baseline: open `/research` (no query), `/reports` and `/exports`. Report what each shows
   (the empty-search prompt, the reports landing page's contents, and the list of downloads
   `/exports` offers). Do not touch anything.
2. Act and check: create contact `QA Research Client 20261004` (person, client) via
   `/contacts/new`. Expect `Contact created.` `POST /matters/new`, that contact as client,
   name `QA Research Case 20261004`, practice area anything other than Personal Injury,
   status `open`, billing type `flat`, opened today. Expect a flash matching `Matter M-....
   opened.` Record the id and number.
3. Act and check: on `/research`, search case law for `Gideon v. Wainwright`. Report the
   first three results (case name, court, date filed). If the outside search service does
   not answer, mark this case and case 4 BLOCKED with the message shown.
4. Act and check: save the first result to the case 2 matter (`POST /research/save`).
   Expect a flash matching `Saved ... to ....` Confirm it appears on
   `/research/saved?matter_id=<the matter's id>`.
5. Act and check, non-Latin text: add the note `QA Research Σημείωση 20261004` (Greek) to
   that saved authority (`POST /research/saved/<id>/note`). Expect flash exactly `Note
   saved.` Confirm it round-trips exactly, with the Greek characters intact, on the
   saved-authorities page.
6. Act and check: export the research memo for that matter (`POST /research/saved/export`).
   Expect a flash matching `Memo saved to the matter's documents in the Research folder.`
   Open the PDF: confirm the case name and the Greek note text both appear correctly.
7. Edge, refused: `POST /research/cite-check` with empty text and no document selected.
   Expect flash exactly `Paste some text or pick a document that has readable text.`
8. Act and check: `POST /research/cite-check` with text `See Gideon v. Wainwright, 372 U.S.
   335 (1963).` and the case 2 matter selected. Report what it finds (resolved/ambiguous/
   not-found counts). Confirm a new note starting `[internal] Citation check` was saved on
   that matter with a matching summary.
9. Role matrix, positive, second role: signed in as `QA Tools Staff 20261001` (user 22,
   paralegal, already active): `GET /research` is 200; `POST /research/saved/<the case 4
   authority's id>/note` with a short new note. Expect flash exactly `Note saved.`
   (paralegal holds `matters` outright, the same area research sits in).
10. Role matrix, negative: create `QA Research Billing 20261004` (billing) and `QA Research
    Readonly 20261004` (readonly). Expect `Added QA Research Billing 20261004.` and `Added
    QA Research Readonly 20261004.` Signed in as billing: `GET /research` is 200 (billing
    holds `matters_view`); `POST /research/saved/<the same authority's id>/note` is HTTP
    403, exactly `Your role (billing) cannot change matters and contacts. Ask the firm owner
    if you need that access.` Signed in as readonly: same GET 200, same POST refused with
    the `(readonly)` wording. Leave both active; case 12 reuses them.
11. Act and check, reports: open every page under `/reports` (A/R aging, work in progress,
    revenue, productivity, origination, realization, profitability, compensation, trust
    balances). Each should open with HTTP 200 and no error page; report any that do not. On
    productivity, pick last month, then this month; both should load. Do not change any
    filter beyond the defaults.
12. Act and check, exports: download `/exports/contacts.csv`, `/exports/matters.csv` and
    `/exports/time.csv`. Each should open as a CSV with a header row. Confirm the case 2
    matter appears in the matters export with its status. Report whether the time export
    has rows beyond the header and, either way, confirm it does not error. Say plainly that
    LEDES, the QuickBooks invoices/payments exports and `trust.csv` stay inside the standing
    Money and trust exclusion and were not touched; only these three contact/matter/time
    downloads were exercised.
13. Role matrix, reports and exports (act and check): create `QA Research Attorney
    20261004` as attorney; expect `Added QA Research Attorney 20261004.` Signed in as them:
    `GET /reports` and `GET /exports`. Report the status of each; confirm `/reports` is
    allowed and `/exports` is refused, with the exact message. Then, still signed in as the
    readonly user from case 10: `GET /reports` and `GET /exports`. Report the same; confirm
    `/reports` is allowed (readonly's view-only set mirrors attorney, which does hold
    reports) and `/exports` is refused. Deactivate the billing, readonly and attorney users
    from cases 10 and 13; expect `User saved.` each.
14. Clean up and what remains: close matter `QA Research Case 20261004` (expect a flash
    matching `M-.... closed.`). Confirm every temporary user created this batch (billing,
    readonly, attorney) is inactive again; user 22 stays active, unchanged. Report every id
    created this batch. Say plainly that the opinion reader's AI-summarise button was not
    exercised here, inside the standing AI exclusion regardless of whether testfirm holds a
    key. Reconfirm the full retained list carried forward from R28, above, is untouched.

### R30. Retest the conflict-check shared-token fix (`1b1b954`, #109's class) on testfirm
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5981355961 2026-10-04T15:02:00Z

`1b1b954` ("Stop shared boilerplate tokens from flooding conflict-check fuzzy hits") has
been the pin since R20 but was never itself retested on testfirm: R19, the last batch to
touch `/conflicts`, ran on `b687b0f`, before this fix landed. Bot 2 confirmed it on qa2 as
S32; this is the testfirm side of that cross-check. Covers: a real exact hit, the
Jr/middle-initial subset case the fix must still allow, a shared-prefix no-match control
(built with the run-time clock per QA-HANDOFF's rule 8, never written in advance), a
duplicate submission, a Greek-name exact hit, a mixed real+no-match submission, waive/undo
on resolve, and the four exact error flashes from `conflicts.py`/`run_check`/`resolve`.

1. Setup (act and check): create contact `QA Conflict Imogen Castellano 20261004` (person,
   client). Expect `Contact created.` `POST /matters/new` with that contact as client, name
   `QA Conflict Case 20261004`, practice area anything other than Personal Injury, status
   `open`, billing type `flat`, opened today, no template. Expect a flash matching `Matter
   M-.... opened.` Record the id and number.
2. Act (no flash on success): add two parties to that matter: `QA Conflict Dakota Reyes Jr
   20261004` (role `witness`) and `QA Conflict Priya Oyelaran 20261004` (role `adverse`).
   Confirm both show on the matter's Parties list.
3. Act and check, baseline real match still works: run a conflict check for `QA Conflict
   Priya Oyelaran 20261004` alone. Expect outcome `unresolved`, one result row, an exact hit
   on that party.
4. Act and check, the subset case the fix must still allow: run a check for `QA Conflict
   Dakota Reyes 20261004` (Jr dropped). Expect one result row hitting the Jr party (nothing
   left over on the query's side, so the subset passes on the shared tokens alone). Report
   the score shown (capped below 100).
5. Act and check, the fix itself, a shared-prefix no-match control: build a name sharing
   only "QA Conflict" and "20261004" with the fixtures above, using the exact wall-clock
   time you run this case as the unique differentiator. Do not write the finished string in
   advance. Run the check for that name alone. Expect outcome `clear`, zero result rows.
6. Duplicate submission edge (act and check): resubmit the exact same query from case 5 a
   second time. Expect a second, separate check record, also `clear` with zero rows.
7. Non-Latin edge (act and check): add a third party, `QA Conflict Σοφία Παπαδοπούλου
   20261004`, role `other`. Run a check for that exact Greek name. Expect one result row,
   an exact hit, Greek characters intact in the label.
8. Act and check, mixed real and no-match in one submission: run one check with two query
   lines, the case 3 name and a freshly-built no-match control (new clock time). Expect
   outcome `unresolved`, exactly one result row, and that row's query is the real name.
9. Undo/redo edge (act and check): resolve the case 5 check `waived`, notes `QA Conflict
   waive reason 20261004`. Expect `Conflict check marked waived.` Resolve it again, outcome
   `clear`, notes blank. Expect `Conflict check marked clear.`
10. Error edges (check only): `POST /conflicts/run` with empty `names`. Expect exactly
    `Enter at least one name to search.` Then with `names` as punctuation only. Expect
    exactly `Enter a name containing letters or numbers before running the conflict check.`
11. Resolve error edges (check only, against the case 3 check): resolve with `outcome=waived`
    and no notes. Expect exactly `Enter a reason before waiving a conflict.` Resolve with an
    invalid outcome value. Expect exactly `Pick an outcome.` Confirm the outcome is
    unchanged (unresolved).
12. Clean up and what remains: close the case 1 matter (expect a flash matching `M-....
    closed.`). Leave the contact, its three parties, and every conflict-check record from
    this batch in place. Report every id created. Reconfirm the full retained list carried
    forward from R29, above, is untouched.

### R31. Calendar deep pass (testfirm): recurrence, DST edges, the ICS feed, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5981601428 2026-10-04T15:33:00Z

Bot 1's backlog and sign-off outline are both fully used up again, and `git log
1b1b954..HEAD -- app` is empty, so there's no code drift to regression-test. Calendar
(`app/blueprints/calendar.py`) has never had its own deep pass on testfirm, only R12's
lighter sign-off. Mirrors Bot 2's S24 deep pass on a different firm/fixtures. See the batch
body in the comment above (cases 1820-1834): a baseline grid read, a timed event created and
its time edited (checked against the ICS feed), an all-day event on a month's last day, a
monthly-repeat series from Jan 31 through Jun 30, a weekly series spanning Chicago's March
2027 spring-forward, the empty-title refusal versus the end-before-start silent correction, a
non-Latin title, a rule-set deadline with a weekend roll-forward, a task done/reopen round
trip, a second role (paralegal, user 22), deleting the recurring series, cleanup, and what
remains. R30's 4 FAILs were recorded as my own batch-authoring mistake (typing fixture names
into the handoff lets testfirm's own GitHub-notification ingestion create a matching
`message` row), not a product defect; not filed.

### R32. Engagement letters: the decline flow, the reminder button, and a contact with no email (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5981874814 2026-10-04T16:01:57Z

Not a backlog item. Bot 1's backlog and sign-off outline are both used up again and
`git log 1b1b954..HEAD -- app` is empty, so no regression batch was possible. R8's own
batch (cases 1551-1565) left three things explicitly open: the decline flow, the reminder
button on an open letter, and a letter sent to a contact with no email. No batch since has
touched any of the three. See the batch body in the comment above (cases 1835-1849): two
new contacts (one with no email), two matters, a letter sent and reminded, a second role
(readonly, user 26) refused on remind, a letter sent to the no-email contact and reminded
without error, a non-Latin decline, a duplicate decline on the same token, a remind refusal
on a declined letter, a void on a still-sent letter, close-out, and what remains.

### R33. Personal injury, criminal defense and discovery deep pass (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5982318564 2026-10-04T16:54:00Z

Not a backlog item. Bot 1's backlog (B1-1 through B1-8) and sign-off outline are both used
up again, and `git log 1b1b954..HEAD -- app` is empty, so no regression batch was possible.
R20, R21, R22, R26, R27, R28, R29 and R31 gave a deep pass to Documents, Intake/leads,
Tasks, Contacts, Case audit, Matters, Research/reports/exports and Calendar; Personal
injury, Criminal defense and Discovery had only R2's light re-certification, never a deep
pass. See the batch body in the comment above (cases 1850-1864): provider/lien/charge
create-edit-delete round trips, the empty-description and empty-name refusals, a demand
package, a leap-day date of loss testing the statute-of-limitations `ValueError` fallback,
duplicate-deadline and duplicate-court-chain guards, a discovery set we propound through
export and delete, non-Latin text, the role matrix, close-out, and what remains. AI buttons
and the settlement worksheet stayed excluded.

### R34. API tokens and webhooks deep pass (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5982659328 2026-10-04T17:36:00Z

Not a backlog item. Bot 1's backlog and sign-off outline are both used up again, and
`git log 1b1b954..HEAD -- app` is still empty, so no regression batch was possible either.
R20-R33 have now given a deep pass to every other major tool; `/settings/api` and
`/settings/webhooks` had only R4's light re-certification from before scopes or
confidentiality modes existed in the UI. See the batch body in the comment above (cases
1865-1879): three tokens (full scopes/full confidentiality, full scopes/redacted, and a
scope-limited one), the missing-header and malformed-token 401s, the redacted-vs-full split
on `/api/v1/me`, `/api/v1/contacts`, `/api/v1/notes` and `/api/v1/calendar`, a scope-missing
403, non-Latin and overlong-input edges, a duplicate/idempotent `/api/v1/leads` POST, a
webhook triggered on `intake_lead.created` only, the private-address and bad-scheme webhook
refusals, cleanup, and what remains. Invoice/payment webhook events stayed excluded as
money-adjacent.

### R35. Document e-signature deep pass (testfirm): full lifecycle, validation edges, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5983004971 2026-10-04T18:21:00Z

Not a backlog item. Bot 1's backlog is fully used up and `git log 1b1b954..HEAD -- app` is
still empty. Document e-signature (`/signatures`, distinct from the engagement-letter flow)
had only ever had one happy-path case, from R1. See the batch body in the comment above
(cases 1880-1893): a new QA matter and document, a signature request saved as a draft then
sent by staff (two different flash wordings for "sent" depending on the route), the
not-yet-sent public status page, the sent-to-viewed transition and view count, an overlong
signer-name refusal, an empty-name refusal, a Cyrillic signer name (a direct regression
check for #47's question-mark bug) and its certificate, the signed-cannot-be-voided guard,
a second request created and sent directly (not via draft), a reminder and decline flow, and
the readonly/billing role matrix (readonly reads but cannot write; billing cannot even read,
holding no documents permission at all).

### R36. Settings > Court rules, Holidays, and the Voice line reminder test (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5983487989 2026-10-04T19:17:48Z

Not a backlog item. Bot 1's backlog is fully used up and `git log 1b1b954..HEAD -- app` is
still empty. `/settings/rules`, `/settings/holidays` and the voice line's owner-only
`/voice/reminders/test` had never been given their own batch. See the batch body in the
comment above (cases 1894-1908): loading and re-loading US federal holidays (idempotency),
a custom holiday add/duplicate/delete, a rule set validation refusal and a non-Latin
jurisdiction create, a rule validation refusal and a calendar-day rule that rolls a
deadline off Thanksgiving once it is loaded as a holiday, the cannot-delete-a-used-rule
and used-rule-set-deactivates-instead-of-deletes guards, a JSON export, and a role-matrix
case contrasting the permissions module's own refusal (attorney denied `/settings/rules`
outright) against a route's separate bare `@owner_required` gate (attorney reaches
`/voice/reminders/test` because it holds `matters`, then gets refused there instead;
billing never reaches it at all).

### R37. Client portal further checks (testfirm): a shared email's client-priority login, the pending-link replace-on-request rule, the silent rate limit, and the closed-matter visibility split
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5983760120 2026-10-04T19:49:00Z

Not a backlog item. Bot 1's backlog and sign-off outline are both used up again, and
`git log 1b1b954..HEAD -- app` is empty, so no regression batch was possible. Drawn instead
from issue #12's own "Further checks" list under Client portal, three items never run by
either bot: two contacts sharing one email address, requesting a link twice then using the
first, and a client whose matter was closed. Read `app/blueprints/portal.py` in full for
this: `login()`'s contact lookup orders by `is_client` descending then id (so a client
record wins a shared email over a non-client one regardless of creation order); the
"replace the pending token" update runs on every new request and only touches a token that
is still unused and unexpired; `RATE_LIMIT_COUNT=3` within `RATE_LIMIT_MIN=15` counts every
token created in the window, used or not, and silently drops any request once that is hit,
still showing the same neutral flash; and `home()` filters the matters table to
open/pending only while the upload dropdown's `all_matters` carries every status, and
`store_upload()` has no matter-status check at all. Every flash below was read from
`app/i18n.py` at this pin, quoted exactly.

1. Setup (act and check): create contact `QA Portal Dup A 20261004` (person, not a client)
   with email `qa-portal-dup-20261004@coil.test`. Expect `Contact created.` Create a second
   contact `QA Portal Dup B 20261004` (person, client) with the exact same email
   `qa-portal-dup-20261004@coil.test`. Expect `Contact created.` New matter
   `QA Portal Dup Matter 20261004` for contact B, office none, no template. Expect a flash
   matching `Matter M-.... opened.` Record both contact ids and the matter id/number.
2. Act and check: on `/portal/login`, submit the shared email (request #1). Expect flash
   exactly `If we have that email on file, we sent you a sign-in link. It works for 30
   minutes.` In `/qa-mail/` (owner session), confirm exactly one new sign-in email to that
   address; do not open its link yet.
3. Act and check, duplicate edge: submit the same email again immediately (request #2).
   Expect the identical flash. Confirm a second sign-in email now sits in `/qa-mail/` for
   that address (two so far).
4. Act and check: submit the same email a third time (request #3). Expect the identical
   flash. Confirm a third email (three so far).
5. Act and check, rate-limit edge: submit the same email a fourth time (request #4), still
   well inside the 15-minute window. Expect the identical neutral flash (it never reveals
   the limit), but confirm no fourth email arrives in `/qa-mail/` for that address: still
   exactly three, proving the fourth request was silently rate-limited.
6. Check: open request #1's link. Expect the expired page, HTTP 410 (its pending token was
   replaced the moment request #2 ran, before it was ever used).
7. Check: open request #2's link. Expect the same expired page, HTTP 410 (replaced by
   request #3).
8. Act and check: open request #3's link, the one request #4 never got the chance to
   replace. Expect it to succeed: redirected to the portal home, signed in. Confirm the page
   identifies contact B (the client) by name, not contact A, proving the shared-email
   lookup's client-first tie-break picked B even though A was created first and holds the
   lower id.
9. Check: open request #3's link again immediately. Expect the expired page, HTTP 410
   (already consumed by case 8).
10. Act and check, closed-matter visibility: without logging out (the case 8 session is
    still signed in as the client), in a separate owner session close
    `QA Portal Dup Matter 20261004`. Expect a flash matching `M-.... closed.` Back in the
    still-open client session, reload `/portal`. Confirm the matter no longer appears in
    the open-matters table, but report whether it is still offered in the "upload a
    document" matter dropdown.
11. Act and check, non-Latin edge: if the closed matter is still offered in that dropdown,
    use it: upload a small text file named `QA Portal Closed Καλημέρα 20261004.txt` to it.
    Report the flash and whether the upload is accepted even though the matter is closed;
    if accepted, expect `Uploaded QA Portal Closed Καλημέρα 20261004.txt. We will take a
    look.` with the Greek filename exact in the matter's document list.
12. Check: sign out of the client session (`POST /portal/logout`). Expect flash exactly
    `You are signed out.` Confirm `/portal` now redirects to the login page.
13. Clean up and what remains: as owner, report the final state (matter closed, the
    document present if case 11 accepted it). Report every id/number created this batch:
    contact A, contact B, the matter, and the document if any. Confirm every fixture
    retained from R36, above, is untouched.

### R38. Client portal accessibility pass (testfirm): keyboard navigation and accessible names
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5984335170 2026-10-04T20:58:00Z

Not a backlog item. Bot 1's backlog and sign-off outline are both used up again, and
`git log 1b1b954..HEAD -- app` is still empty. The register's Phase 2 section carries one
item never run for Bot 1: "Portal accessibility. Keyboard and screen-reader pass on the
invoice done; the portal half was blocked for lack of a session." R14's client-portal
sign-off explicitly carved this out as its own accepted limitation. See the batch body in
the comment above (cases 1922-1934): a fresh QA client and matter, the login field's
label/id pairing read from source, a keyboard-only Tab pass through login and the signed-in
home page, heading structure, the messages page's Regarding-select and body-textarea label
pairing compared against the upload form's correctly paired fields, a Greek-text message
send, an empty-message refusal, a label-click focus test, keyboard-only logout, a second
client account with no matter to check empty-state text is real text, cleanup, and a
findings table that checks against #97 before filing anything new.

### R116. Invoice payments in Stripe test mode: ACH, card payment and decline
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6073244987 2026-10-09T02:50:48+00:00

P2-B1-0, corrected before posting against payments.py and its payment templates.
Use the existing surcharge setting without changing any firm or provider setting.
ACH can remain pending; only settlement permits a paid-invoice expectation.
Only Stripe test mode is allowed. If Checkout does not clearly indicate test mode,
stop the affected payment case and report the blocker. Never connect a real bank.
All records use `QA Pay 20261008`; keep every earlier retained fixture untouched.

1. Create client `QA Pay Client 20261008`, English, email `qa-pay-20261008@coil.test`.
   Create its hourly USD matter `QA Pay Matter 20261008`, rate $100.00, no office or
   template. Report the creation flashes and IDs. Confirm the client and rate persisted.
2. Log 1.00 billable hour at $100.00 on that matter, description `QA Pay ACH 20261008`.
   Draft and send its $100.00 invoice to the new client, reporting the flashes and
   invoice number as INV-ACH. Open the captured message in `/qa-mail/` and follow its
   public invoice link privately. Choose ACH and confirm no surcharge. Use only Stripe's
   hosted test-bank option to complete Checkout; if none is available, report blocked.
3. Report whether ACH is pending or settled. Pending means the invoice may remain unpaid
   with no posted payment; do not call that a failure or resubmit. If settled, expect
   paid status, zero balance and one payment row with method ach and no surcharge.
   Revisit the success page privately and confirm it never creates a duplicate payment.
4. Log another 1.00 billable hour at $100.00, description `QA Pay Card 20261008`.
   Draft and send a second $100.00 invoice, INV-CARD. Report the flashes. Confirm only
   this new hour appears on it, without rebilling the first invoice's time.
5. Open INV-CARD's captured public link. Choose card. Record its displayed surcharge
   and total using the current firm setting; do not enable or disable surcharge.
   In clearly marked Stripe test mode, pay using 4242 4242 4242 4242, any future expiry,
   CVC and ZIP. Expect the success page and eventually a paid invoice with zero balance.
6. Inspect INV-CARD's payment detail. Expect one card payment, applied amount $100.00,
   with any surcharge matching the confirmation page. Revisit its success page and
   reload invoice detail; expect still one payment and unchanged zero balance.
7. Log a third 1.00 billable hour at $100.00, description `QA Pay Decline 20261008`.
   Draft and send a third $100.00 invoice, INV-DECLINE. Follow its captured link to
   Stripe test Checkout and submit decline card 4000 0000 0000 0002 with any future
   expiry, CVC and ZIP. Report Stripe's decline message; expect no successful payment.
8. Cancel that Checkout through its back/cancel control. Expect Coil's cancellation
   page and INV-DECLINE still owing $100.00 with no payment row. Send its reminder
   from invoice detail. Expect `Reminder sent to qa-pay-20261008@coil.test.` Confirm
   the reminder appears in `/qa-mail/` and still names the unpaid invoice.
9. Open `/pay/not-a-real-token-20261008`. Expect HTTP 404. Do not probe private links
   belonging to any retained fixture.
10. Reopen INV-CARD's paid invoice payment link privately. Expect the paid page naming
    INV-CARD and `Nothing is owed on this invoice. Thank you.` No new Checkout opens.
11. Clean up: void only INV-DECLINE. Expect the flash naming its invoice number and
    saying `voided. Its time, expenses and milestones can be billed again.` Confirm
    its time entry is unbilled again. Keep INV-CARD paid and INV-ACH in its actual
    pending or paid state; do not void a pending bank payment. Leave the matter open.
12. What remains: list the contact, matter, three invoices, their statuses and payment
    IDs. State whether ACH is still pending. Confirm the card success, duplicate guard,
    decline/cancel and void behavior. Earlier retained fixtures and all firm/provider
    settings remain unchanged. Give counts and a per-case verdict table, without
    passwords, tokens or private links.

### R117. Invoicing core: time, expense, captured mail, void and statement
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6073578030 2026-10-09T03:21:02+00:00

P2-B1-1, corrected against invoices.py, statements.py and time.py and their forms.
No approval-setting change: that firm-wide test is deferred to Bot 2. All amounts
are USD and all content English. Use the owner. No payments or provider changes.
Use only this batch's records. Report creation flashes where no exact wording is given.

1. Create client `QA Invoice Client 20261008`, email `qa-invoice-20261008@coil.test`,
   and hourly matter `QA Invoice Matter 20261008`, rate $100.00, no office or template.
   Record IDs and confirm the saved rate. All earlier retained fixtures stay untouched.
2. Log 2.00 billable hours at $100.00, description `QA Invoice Time 20261008`, on that
   matter. Add a billable $45.00 expense, description `QA Invoice Expense 20261008`,
   with a small English receipt PDF named `QA Invoice Receipt 20261008.pdf` showing
   that description and $45.00. Expect `Expense saved.` Confirm $200.00 time and $45.00 expense unbilled.
3. Download the attached receipt and confirm it is the uploaded PDF with the same bytes.
4. Submit the invoice builder with no selected time_ids, expense_ids or milestone_ids,
   and no manual amount. Expect `Pick at least one item to invoice, or enter an amount.`
   Confirm no invoice and both items remain unbilled.
5. Draft from exactly the time and expense above, no tax, discount or other adjustments.
   Report the flash and number as INV-A. Expect two lines and total $245.00, draft status,
   and both source entries billed. Download its PDF; confirm number, client and $245.00.
6. As owner, send INV-A to the new client's address. Report the flash. Find the invoice
   message in `/qa-mail/` by recipient and number. Confirm exactly one new invoice message.
7. Send INV-A again. Confirm a second captured invoice message and a second sent event,
   without changing invoice total or creating a second invoice.
8. Remind INV-A. Expect `Reminder sent to qa-invoice-20261008@coil.test.` Confirm one
   new reminder in `/qa-mail/`, in addition to the two earlier invoice messages.
9. Void INV-A, which has no payments. Expect the invoice-number flash ending
   `voided. Its time, expenses and milestones can be billed again.` Confirm both
   source items become unbilled, INV-A is void and has no payment.
10. Draft again from exactly those two source items. Expect a new invoice INV-B for
    $245.00 with the two items billed again. INV-A remains void; its ID is not reused.
11. Open `/statements/<client-id>` with no date or matter filters. Expect INV-A omitted
    because void and INV-B omitted because draft. Do not infer a defect from their absence.
12. Send INV-B to the new client. Report the flash. Reopen that statement with no filters:
    expect INV-B included, INV-A excluded, total owed $245.00 and no payment credits.
13. Download the statement PDF and confirm INV-B and $245.00. Send this statement only
    to the batch's client. Expect `Statement sent to qa-invoice-20261008@coil.test.`
    Confirm a new captured statement message in `/qa-mail/`, without opening payment links.
14. Clean up: void INV-B. Confirm both source items unbilled again. Close the batch's
    matter, report the flash, and reload the client statement: neither void invoice
    contributes to the balance, which is $0.00. Retain both invoice records and receipt.
15. What remains: list contact, closed matter, time, expense and both void invoice IDs.
    Confirm no payments, no changes to approval or provider settings, and earlier
    retained fixtures untouched. Return counts and one verdict per case. No private links.

### R118. Card Checkout cancellation, retry and paid-invoice guards (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6073972925 2026-10-09T03:59:36+00:00

P2-B1-0 follow-up. R116 confirmed ACH settlement. This batch covers cancellation
and retry on a fresh invoice, plus its paid-invoice guards. Read payments.py pay/success/record_from_session and invoices.py void,
time/form.html, invoices/new.html, payment templates and permissions.py before writing.
At posting, replace DATE with the current YYYYMMDD. Use only new QA records and USD.
Do not change surcharge, invoice approval, firm settings or provider settings.
Stripe must visibly be in test mode. Never use a real card or bank. Report a blocker
if test mode cannot be confirmed. Retained fixtures from every earlier batch stay intact.

1. Create client `QA Retry Client DATE`, English, email `qa-retry-DATE@coil.test`, and
   its hourly USD matter `QA Retry Matter DATE`, $100.00 rate, no template or office.
   Report flashes and IDs. Confirm the saved client, rate and open matter status.
2. Log 0.50 billable hours at $100.00 on that matter, description `QA Retry Time DATE`.
   Report the flash. Confirm one unbilled entry worth $50.00 on this matter.
3. Draft an invoice using just that entry, then send it to the batch's client. Report
   the flashes and invoice ID/number. Expect $50.00 due. Find its captured message
   at `/qa-mail/`; keep the invoice and payment links private.
4. Follow its Pay by card path to clearly marked Stripe test Checkout, but enter no
   card. Cancel using Checkout's own control. Expect Coil's cancellation page. Check
   staff invoice detail: balance $50.00, no payment, and the time entry still billed.
5. Return through the same captured invoice link. Confirm card total equals $50.00
   plus any surcharge shown under the existing firm setting. Complete test Checkout
   using 4242 4242 4242 4242, any future expiry, CVC and ZIP. Expect paid status and
   zero invoice balance once the success page/webhook records the payment.
6. Revisit the successful return page twice, using the same private URL. After each,
   inspect invoice detail: exactly one payment and zero balance. Record its payment
   ID and confirm the applied amount is $50.00, separate from any surcharge.
7. As owner, attempt to void this paid invoice. Expect `Payments are recorded against
   INV-NUMBER, so this invoice cannot be voided.` with the actual invoice number.
   Confirm the invoice remains paid, the payment unchanged and the time still billed.
8. Reopen its payment link after payment. Expect the paid-invoice page and
   `Nothing is owed on this invoice. Thank you.` No new Stripe Checkout starts.
   Open an invented `/pay/qa-retry-missing-DATE` token: expect HTTP 404.
9. Clean up by closing only this batch's matter. Report the flash. Retain the contact,
   closed matter, time entry, paid invoice and payment. Confirm the paid invoice can
   still be read after the matter closes. Do not refund or delete the payment.
10. What remains: list every created ID and final status, the observed surcharge,
    cancellation result, retry result, payment count and paid-void refusal. Confirm
    earlier fixtures and all settings were untouched. Return counts and one verdict
    per case. Never post credentials, tokens or private links.

### R119. Public payment guards for draft and void invoices (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6074699563 2026-10-09T05:09:33+00:00

P2-B1-0 reserve batch. Source checked: payments.py pay(), invoices.py void(), the
public payment templates, invoice builder and time-entry form, and permissions.py.
This batch makes no payment and never submits a sent invoice to Stripe. It tests
Coil's guards before Checkout. Do not change firm settings or provider settings.
At posting replace DATE with today's YYYYMMDD. English and USD only; owner session.
All previous retained fixtures stay untouched. Report flashes where not quoted below.

1. Create client `QA Pay Guard Client DATE`, English, email `qa-pay-guard-DATE@coil.test`,
   and hourly matter `QA Pay Guard Matter DATE`, rate $100.00, no template or office.
   Record IDs and confirm the saved client, rate and open status.
2. Log 0.50 billable hours at $100.00, description `QA Pay Guard Time DATE`, on this
   matter. Confirm the one entry is unbilled and worth $50.00. Record its ID.
3. Draft an invoice from just that entry, with no adjustments. Confirm $50.00 total,
   draft status and the time entry billed. Record the invoice ID/number. Obtain only
   this invoice's public link from its staff page; keep the token private. If the UI
   exposes no link before sending, report the next case blocked instead of reading a database.
4. Before sending, privately request `/pay/<this-token>` by GET and POST, once each.
   Expect the draft not-ready page, HTTP 200, no Stripe redirect and no payment on both.
   Do not mistake this designed refusal for a 404 requirement.
5. Send the invoice to the new client's address. Find its message in `/qa-mail/`.
   Confirm the correct recipient, invoice number and $50.00 amount. Obtain the public
   payment link privately from that message or public invoice page.
6. GET that payment link with `method=` blank, then `method=unknown`. Both must choose
   the card confirmation page, matching the normal `method=card` page's amount and
   existing surcharge. Never click Continue or POST while the invoice is sent.
   Inspect staff events: the visits may add link-click events but no payment.
7. Void the unpaid invoice as owner. Expect the invoice-number flash ending
   `voided. Its time, expenses and milestones can be billed again.` Confirm void status,
   no payment and the time entry unbilled again.
8. Repeat the void POST with CSRF. Expect `Already void.` Confirm no new invoice,
   payment or change to the unbilled time entry. Then GET and POST the old payment link,
   once each: expect the cancelled/no-longer-open page and no redirect to Stripe.
9. Clean up: close only this batch's matter. Report the flash and confirm closed
   status. Retain the contact, closed matter, unbilled time and void invoice. Check
   the old payment link still refuses payment after the matter closes.
10. What remains: list every created ID/status and state whether draft/void GET and
    POST guards, blank/unknown method fallback and duplicate void all held. Confirm
    zero payments, no Stripe Checkout started, no settings changes and all prior
    retained fixtures untouched. Return counts and one verdict per case. No private links.

### R120. Payment entry refuses card and ACH outside Stripe (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6075026757 2026-10-09 05:40 UTC

P2-B1-0 boundary follow-up: a manual POST cannot create a fake card or ACH payment.
Source checked: payments.py record, invoices.py void/send, invoice detail's payment
form (invoice_id, amount, method, received_on, reference, note) and permissions.py.
Run as owner on new records only. This batch creates no payment and never opens Stripe.
English and USD only. At posting replace DATE with today's YYYYMMDD. No firm settings
or provider changes. Keep all previous retained fixtures untouched.

1. Create client `QA Method Client DATE`, English, email `qa-method-DATE@coil.test`,
   and hourly matter `QA Method Matter DATE`, $100.00 rate, no office or template.
   Report flashes and IDs; confirm the saved client, rate and open status.
2. Log 1.00 billable hour at $100.00 on this matter, description `QA Method Time DATE`.
   Report the flash and confirm the unbilled time entry is worth $100.00.
3. Draft an invoice from only that time, no adjustments. Record its ID/number and
   confirm total and balance $100.00, draft status and no payments.
4. Directly submit `/payments/record` with a fresh CSRF token, this invoice_id,
   amount=100.00, method=card, today's received_on and reference `QA Method Card DATE`.
   Expect `Method must be check, cash, wire or other. Card and bank payments come in
   through Stripe.` Confirm no payment and unchanged $100.00 balance.
5. Repeat with method=ach and reference `QA Method ACH DATE`. Expect the identical
   method refusal, no payment and unchanged balance. No Stripe request should be started.
6. Submit the same form with method=check and amount=0, then amount=-1.00.
   Expect `Enter a positive amount.` for each, no payment, balance still $100.00.
7. Submit method=check and amount=100.01. Expect `That is more than the invoice balance
   of $100.00. Record the balance and note the overpayment separately.` Confirm no
   payment and no change to the invoice or time entry.
8. Send this invoice to the new client using its staff detail action. Report the flash.
   Confirm a new captured invoice message at `/qa-mail/`, naming this invoice and $100.00.
   Repeat the invalid method=card POST from case 4 on the sent invoice; expect the same
   method refusal. Changing draft to sent must not permit manual card entry.
9. Void the invoice as owner. Expect the invoice-number flash ending `voided. Its time,
   expenses and milestones can be billed again.` Confirm void status and unbilled time.
10. Submit method=check and amount=100.00 against this void invoice with fresh CSRF.
    Expect `This invoice is void. Payments cannot be recorded against it.` Confirm
    it remains void, no payment and time still unbilled.
11. Clean up: close only this matter and report the flash. Keep the contact, closed
    matter, unbilled time and void invoice as evidence. Confirm all earlier fixtures stay.
12. What remains: list the created IDs, final statuses and zero payment count. State
    whether card/ACH refusal, nonpositive amount, overpayment and void guards held.
    Return counts and one verdict per case. No credentials, tokens or private links.

### R121. Manual check, cash and wire payments on one USD invoice (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6075382235 2026-10-09 06:09 UTC

From P2-B1-3, after the already assigned card guards R119/R120 and invoicing core R117.
Firm-wide invoice-template and approval work belongs to Bot 2 and is deferred until
it finishes signatures. Source checked: payments.py record, invoice detail payment
form, Invoice.recalc, invoices.py void and permissions.py. Owner only. These are
synthetic bookkeeping entries, no real cash, wire, bank transfer or processor call.
English and USD; replace DATE with today's YYYYMMDD. New records only, no settings changes.

1. Create English client `QA Manual Client DATE`, email `qa-manual-DATE@coil.test`, and
   hourly USD matter `QA Manual Matter DATE`, $100.00 rate, no office/template.
   Report flashes and IDs; confirm client and rate persisted.
2. Log 1.00 billable hour at $100.00, description `QA Manual Time DATE`. Draft and
   send its $100.00 invoice to that client. Report flashes and IDs. Confirm one captured
   message at `/qa-mail/`, $100.00 balance and no payments. Do not open any payment link.
3. On the manual-payment form submit amount=0, method=check, today's received_on,
   reference `QA Manual Zero DATE`. Expect `Enter a positive amount.` No payment saved.
4. Record $25.00 by check, received today, reference `QA Manual Check DATE`, note
   `QA Manual Check Note DATE`. Expect the recorded-payment flash naming $25.00, check
   and this invoice. Confirm partial status, $25.00 paid, $75.00 due and one payment.
5. Open that payment's detail. Confirm amount $25.00, method check, account operating,
   today's received date, reference and note exactly. The link must belong to this invoice.
6. Record $30.00 by cash, received today, reference `QA Manual Cash DATE`, note
   `QA Manual Cash Note DATE`. Report the flash. Expect two payments totalling $55.00,
   invoice partial and $45.00 due. Time remains billed, not returned to unbilled.
7. Try $45.01 by wire. Expect `That is more than the invoice balance of $45.00.
   Record the balance and note the overpayment separately.` Confirm still only two
   payments, $55.00 paid and $45.00 due.
8. Record exactly $45.00 by wire, received today, reference `QA Manual Wire DATE`,
   note `QA Manual Wire Note DATE`. Report the flash. Expect paid status, $100.00
   total paid, zero balance and exactly three payments: check 25, cash 30, wire 45.
9. Repeat the $45.00 wire form POST with fresh CSRF. Expect the overpayment refusal
   naming $0.00 balance. Confirm payment count remains three and zero balance unchanged.
   This is a full-balance guard, not a claim of general duplicate-reference protection.
10. Attempt to void the paid invoice as owner. Expect the flash naming its invoice
    number and saying `so this invoice cannot be voided.` Confirm paid status, three
    payments and billed time remain unchanged.
11. Clean up: close only this matter, reporting the flash. Retain the contact, closed
    matter, billed time, paid invoice and three payment records. No refund, deletion,
    trust action or external transfer. All earlier retained fixtures stay untouched.
12. What remains: list every ID, method, amount and final status. Confirm zero amount
    and both overpayment refusals, partial-to-paid totals and paid-void refusal. Return
    counts and a Markdown per-case table. No credentials, tokens or private links.

### R122. Manual-payment permissions and invalid-method guards (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6075921308 2026-10-09 06:48 UTC

Continues P2-B1-3 after R121. Source checked: payments.py record/detail,
permissions.py role matrix and denial text, invoice payment form, payment detail,
and settings.py user routes and user form. Only synthetic USD bookkeeping entries.
No processor call, real transfer, trust action or firm configuration change.
Replace DATE with today's YYYYMMDD. Use separate sessions for each role and a fresh
CSRF token from that session for each POST. Preserve every earlier retained fixture.

1. As owner create client `QA Payment Roles Client DATE`, email
   `qa-payment-roles-DATE@coil.test`, and hourly matter `QA Payment Roles Matter DATE`
   at $100.00. Log 1.00 billable hour named `QA Payment Roles Time DATE` and draft
   its $100.00 USD invoice. Send only through the existing captured-mail setup.
   Report flashes and IDs. Confirm one captured message, $100.00 due and no payments.
2. As owner create `QA Payment Attorney DATE` and `QA Payment Billing DATE`, with
   unique matching addresses at coil.test, roles attorney and billing, hourly_rate=100,
   cost_rate=0 and no office. Use private generated passwords of at least 12 characters;
   do not report them. Leave voice fields blank. Report flashes and IDs, then verify roles.
3. Sign in as the new attorney. GET this invoice: expect 200 and $100.00 due.
   GET `/payments`: expect 403 and `Your role (attorney) cannot open payments. Ask the firm owner if you need that access.`
   An invoice payment form or link may still be visible; report it without treating its
   visibility alone as permission to record a payment.
4. As attorney POST `/payments/record` for this invoice, amount=10, method=check,
   received_on=today, reference `QA Payment Denied DATE`. Expect 403 and
   `Your role (attorney) cannot change payments. Ask the firm owner if you need that access.`
   As owner verify no payment appeared and $100.00 remains due.
5. As billing open this invoice and `/payments`, both 200. Submit amount=-1,
   method=check and today's received_on for this invoice. Expect `Enter a positive amount.`
   Verify no payment and $100.00 due. This checks an invalid amount with an authorized role.
6. As billing submit amount=10, method=card directly to `/payments/record`, using
   this invoice and fresh CSRF. Expect `Method must be check, cash, wire or other. Card and bank payments come in through Stripe.`
   Verify no payment or processor action and unchanged $100.00 due.
7. As billing record amount=40, method=other, received_on=today, reference
   `QA Payment Other DATE`, note `QA Payment Other Note DATE`. Report the flash.
   Verify exactly one $40.00 operating payment, partial invoice and $60.00 due.
8. As billing open the new payment detail. Verify method other, amount $40.00,
   operating account, today's date, reference, note and links to this new client,
   matter and invoice. As attorney GET that same payment detail: expect 403 with the
   same cannot-open-payments text from case 3. The invoice remains readable as attorney.
9. As attorney try a second record POST, amount=60, method=cash, today's date,
   reference `QA Payment Denied Again DATE`. Expect the same 403 from case 4.
   As billing confirm still one payment, $40.00 paid and $60.00 due.
10. As billing record $60.00 by cash, received today, reference `QA Payment Cash DATE`.
    Report the flash. Confirm exactly two payments totalling $100.00, paid invoice,
    zero balance and the original time still billed. No external cash movement occurs.
11. Clean up as owner: close only this matter and deactivate both new users using
    their edit forms, preserving their role and other fields. Report flashes and verify
    inactive status. Retain client, closed matter, billed time, paid invoice and both
    payment records. Do not delete payments or change any earlier fixture.
12. What remains: list all new IDs and final statuses, both payment amounts/methods,
    the invalid-amount and invalid-method refusals, and each role's GET/POST outcomes.
    Return counts and a per-case Markdown table. No passwords, tokens or private links.

### R123. Reminder-only payment plan with month-end schedule and cancellation (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6076479090 2026-10-09 07:28 UTC

P2-B1-4, after manual-payment core and roles in R121/R122. Source checked: money.py
plan_new, plan_schedule, advance_date, pause/resume/cancel and remind; invoice plan
form, money/plan_detail.html, and permissions.py (owner can use payments).
Owner only, English and USD. New fixtures only. Replace DATE with today's YYYYMMDD.
No card saved, no auto_charge field submitted, no Charge now, no public pay-link visit,
no processor call or real money. Mail stays in the existing capture inbox.

1. Create client `QA Plan Month Client DATE`, email `qa-plan-month-DATE@coil.test`,
   and hourly USD matter `QA Plan Month Matter DATE` at $100.00. Log 1.00 billable hour,
   description `QA Plan Month Time DATE`, and draft its $100.00 invoice. Report flashes
   and IDs. Confirm draft, $100.00 due, one billed time entry and no payments.
2. POST `/money/plans/new` with this invoice_id, installments=3, frequency=monthly,
   first_charge_on=2027-01-31 and auto_charge omitted. Expect `A payment plan needs a sent invoice with a balance.`
   Confirm no plan exists. Send the invoice to this client, report the flash and verify
   its captured invoice message. Balance remains $100.00.
3. Submit plan creation with installments=1 and otherwise the same valid fields.
   Expect `Installments must be between 2 and 60.` Confirm no plan or payment.
4. Submit installments=3, frequency=daily, first_charge_on=2027-01-31, no auto_charge.
   Expect `Frequency must be weekly, biweekly or monthly.` Confirm no plan.
5. Submit installments=3, frequency=monthly, first_charge_on blank, no auto_charge.
   Expect `Pick the date of the first charge.` Confirm no plan or payment.
6. Create the valid 3-installment monthly plan starting 2027-01-31, auto_charge omitted.
   Report the setup flash and plan ID. Confirm active, email-reminder mode, zero paid
   installments, next amount $33.34, and invoice balance $100.00 with no payments.
7. Inspect its schedule: January 31, February 28 and March 31, 2027, amounts $33.34,
   $33.34 and $33.32, total $100.00. The short February month must not shift March to
   the 28th. Confirm this schedule belongs only to this new invoice.
8. Repeat the valid creation POST with fresh CSRF against this invoice. Expect
   `This invoice already has a payment plan. Cancel it before setting up another.`
   Confirm one plan, same ID and schedule, no payments.
9. Send this plan's manual reminder. Expect `Reminder emailed to qa-plan-month-DATE@coil.test.`
   Confirm exactly one new captured reminder for this invoice and the next $33.34
   installment. Do not open or report its private pay link. No payment is created.
10. Pause the plan. Expect `Plan paused. Nothing will be charged or sent until you resume it.`
    Confirm paused and its next installment displayed as next when resumed. Then resume:
    expect `Plan resumed.` Confirm active and first due date still 2027-01-31.
11. Cancel the plan. Expect `Plan cancelled. The invoice balance stays due.` Confirm
    cancelled, no next charge displayed on the plan list, $100.00 still due and no payments.
    Try its reminder action: expect `The plan is cancelled.` and no captured reminder.
12. Clean up: void this unpaid invoice as owner, report the flash, and confirm time is
    unbilled again. Close only this matter and report the flash. Retain contact, closed
    matter, unbilled time, void invoice and cancelled plan. Earlier fixtures stay untouched.
13. What remains: list all IDs/statuses, exact schedule dates and amounts, reminder count,
    duplicate/validation refusals and zero payment count. Return counts and a per-case
    Markdown table. No credentials, tokens or private links.

### R124. Reminder-plan amounts after manual partial payments (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6076766206 2026-10-09 07:49 UTC

P2-B1-4 follow-up. Source checked: money.py plan_new, plan_schedule,
next_installment_cents, plan_payments, remind/cancel and send_plan_reminder;
payments.py record; invoice plan/manual-payment form fields; plan detail template;
permissions.py. Owner only, new English/USD records. Replace DATE with today's YYYYMMDD.
No cards, auto_charge, Charge now, processor calls, real transfers or public pay-link
visits. Captured mail only. Manual entries are synthetic bookkeeping.

1. Create client `QA Plan Partial Client DATE`, email `qa-plan-partial-DATE@coil.test`,
   and hourly USD matter `QA Plan Partial Matter DATE` at $100.00. Log 1.00 billable
   hour `QA Plan Partial Time DATE`. Draft/send its $100.00 invoice. Report flashes and
   IDs, verify captured invoice mail, $100.00 due and no payments.
2. Create a plan with invoice_id, installments=3, frequency=monthly,
   first_charge_on=2027-01-31 and auto_charge omitted. Report setup flash and P1 ID.
   Confirm active email-reminder mode and schedule $33.34, $33.34, $33.32.
3. Record $40.00 check on this invoice, received_on=today, reference
   `QA Plan Partial Check DATE`, note `QA Plan Partial Check Note DATE`. Report flash.
   Confirm one payment, partial invoice, $40.00 paid and $60.00 due.
4. Open P1 again. Confirm next amount remains $33.34 and schedule amounts now total
   $60.00: $33.34, $26.66, $0.00. Paid-installment count remains zero: an ordinary manual
   payment is not a plan installment receipt. It appears on the invoice, not under
   Payments through this plan. Dates remain Jan 31, Feb 28 and Mar 31, 2027.
5. Send P1's reminder. Expect `Reminder emailed to qa-plan-partial-DATE@coil.test.`
   Confirm one new captured reminder requesting $33.34, not the invoice's full $60.00.
   Keep the private link out of evidence and never visit it.
6. Record another $40.00, method=cash, received_on=today, reference
   `QA Plan Partial Cash DATE`. Report flash. Confirm two payments totalling $80.00,
   invoice partial and $20.00 due. Time remains billed.
7. Reopen P1 and send another reminder. Confirm next amount $20.00, schedule amounts
   $20.00, $0.00, $0.00, and one new captured reminder requesting $20.00. Report flash.
   Paid-installment count remains zero; no card or online payment was created.
8. Edit only this client's email to blank, preserving other fields. Report flash.
   Try P1's reminder: expect `The client has no email address.` No new captured message.
   Restore qa-plan-partial-DATE@coil.test, report flash and verify it persisted.
9. Cancel P1. Expect `Plan cancelled. The invoice balance stays due.` Verify $20.00
   due and both manual payments unchanged. Create P2 on the same invoice with
   installments=2, frequency=weekly, first_charge_on=2027-02-01, no auto_charge.
   Report setup flash. Confirm a new active plan, two $10.00 rows on Feb 1 and Feb 8.
10. Repeat P2 creation with fresh CSRF. Expect `This invoice already has a payment plan. Cancel it before setting up another.`
    Confirm only P1 cancelled and P2 active, no third plan, and unchanged $20.00 due.
11. Clean up: cancel P2, expecting `Plan cancelled. The invoice balance stays due.`
    Close only this matter, report flash. Retain client, closed matter, billed time,
    partial invoice owing $20.00, two manual payments and two cancelled plans. Do not
    void an invoice carrying payments or leave an active reminder plan. Older fixtures stay.
12. What remains: list IDs/statuses, both payments, invoice balance, both cancelled
    plans, schedule/next-amount checks and captured reminder counts. Return counts and
    a per-case table. Never include credentials, tokens or private payment links.

### R125. Credits complete a reminder plan and undo does not restart it (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6077043263 2026-10-09 08:09 UTC

P2-B1-4 remaining credit-to-zero coverage (#54), after R123/R124. Source checked:
invoices.py credit/void_credit, money.py plan_new/remind/_plan_action, invoice credit
and plan form fields, permissions.py. Owner only, English/USD, new fixtures only.
Replace DATE with today's YYYYMMDD. No payment, refund, card, auto_charge or processor
call. Do not run the scheduler or visit public payment links. Captured invoice mail only.

1. Create client `QA Plan Credit Client DATE`, email `qa-plan-credit-DATE@coil.test`,
   and hourly USD matter `QA Plan Credit Matter DATE` at $100.00. Log 1.00 billable
   hour `QA Plan Credit Time DATE`. Draft/send its $100.00 invoice. Report flashes/IDs.
   Confirm one captured invoice message, $100.00 due and no payments or credit notes.
2. Create reminder plan P1: invoice_id, installments=2, frequency=monthly,
   first_charge_on=2027-01-31, auto_charge omitted. Report flash/ID. Confirm active,
   zero paid installments, $50.00 next amount and no payment.
3. POST the invoice's credit form with amount=0, reason=other, note `QA Plan Credit Zero DATE`.
   Expect `Enter a positive amount to credit.` Confirm no credit and unchanged plan/balance.
4. Issue credit C1 for $40.00, reason=other, note `QA Plan Credit Partial DATE`.
   Report the flash naming the credit/invoice and $60.00 outstanding. Confirm C1 issued,
   credited total $40.00, paid total $0.00, balance $60.00 and P1 still active.
5. Issue credit C2 for exactly $60.00, reason=other, note `QA Plan Credit Remaining DATE`.
   Report the flash naming $0.00 outstanding. Confirm two issued credits totalling
   $100.00, zero balance, zero payment records, and P1 completed. This is credit, not cash collected.
6. Attempt P1's reminder. Expect `The plan is completed.` Confirm no new captured
   reminder and no change to credits or completed status.
7. Attempt P1's resume action with fresh CSRF. Expect
   `The plan is completed; it cannot be resumed from there.` Confirm completed and no payment.
8. Void only C2 using `/invoices/credit/<C2-ID>/void`. Report the flash; it must say
   $60.00 is owed again and that the payment plan stays completed. Confirm C1 issued,
   C2 void, $40.00 credited, $60.00 balance, zero payments and P1 still completed.
9. Repeat void C2. Expect `That credit note is already void.` Confirm no extra credit,
   $60.00 balance unchanged and P1 still completed. No reminder should be sent.
10. Set up replacement reminder plan P2 on this invoice, installments=2, frequency=weekly,
    first_charge_on=2027-02-01, auto_charge omitted. Report setup flash and new ID.
    Confirm P2 active with $30.00 installments and P1 completed. Cancel P2: expect
    `Plan cancelled. The invoice balance stays due.` Confirm P2 cancelled and $60.00 due.
11. Clean up: close only this matter, report the flash. Retain client, closed matter,
    billed time, invoice with $60.00 due, C1 issued $40.00, C2 void $60.00, P1 completed
    and P2 cancelled. No active plan remains. Do not erase the credit history or alter
    earlier fixtures. Record invoice status as displayed without treating credit as payment.
12. What remains: list all IDs/statuses, credits, zero payments and invoice balance.
    Confirm credit-to-zero completed P1, voiding C2 did not restart it, duplicate void
    changed nothing, and only a newly created plan could become active. Return counts
    and a per-case table. No tokens, credentials or private links.

### R126. Split-payer invoice rounding and group void (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6077474615 2026-10-09 08:39 UTC

P2-B1-5 split-payer core after the queued plan checks. Interest remains for a later
batch. Source checked: matters.py add_payer/delete_payer, matter payer form fields;
invoices.py payers_total_ok, split_cents, create_invoices, builder and group void;
permissions.py. Owner only. English/USD. Replace DATE with today's YYYYMMDD.
New fixtures only, no shared settings, mail, payments, plans, cards or processor calls.

1. Create clients `QA Split First Client DATE` and `QA Split Second Client DATE`, with
   respective emails qa-split-first-DATE@coil.test and qa-split-second-DATE@coil.test.
   Open hourly USD matter `QA Split Matter DATE` for the first client, rate $100.01,
   no office/template. Report flashes/IDs and confirm no payers or invoices yet.
2. Log 1.00 billable hour, rate $100.01, description `QA Split Time DATE`. Report flash
   and ID. Confirm unbilled value $100.01. This odd cent tests line-level split rounding.
3. POST the new matter's payers form with contact_id blank, percent=50, label
   `QA Split Missing DATE`. Expect `Pick a contact to bill.` Confirm no payer created.
4. Submit first client's contact_id with percent=0 and label `QA Split Zero DATE`.
   Expect `Percent must be between 0 and 100.` Confirm no payer created.
5. Add first client with percent=50, label `QA Split First DATE`. Expect
   `Payers now total 50%. Invoices for this matter cannot be built until they total 100%.`
   This warning accompanies a saved payer. Record payer ID and confirm one row at 50%.
6. Attempt to draft the new matter's invoice using its single time entry. Expect HTTP
   400 and `Split payers on this matter do not add up to 100%. Fix the payers on the matter first.`
   Confirm no invoice and time still unbilled.
7. Try adding the first client again at 50%. Report the flash saying the client is
   already a payer and must be removed/re-added to change the share. Confirm one row,
   unchanged 50% total and no duplicate payer.
8. Add second client at 50%, label `QA Split Second DATE`. Report any flash. Confirm
   two distinct payer rows, total 100%, each tied to its intended new contact.
9. Draft the invoice from the $100.01 time entry. Report the split-build flash and
   both invoice IDs/numbers. Expect exactly two drafts, one for each payer, sharing a
   split group. Amounts are $50.01 and $50.00, sum $100.01. Time is billed once, not twice.
   Record which payer receives each rounding share; do not assume ID order from page rows.
10. Void either unpaid draft. Report the flash naming both invoices. Expect both void,
    time unbilled again, no payments and no orphaned billable source link.
11. Remove only the second payer through its own remove action. Confirm one 50% row.
    Re-add the same second contact at 50% with the same label and confirm 100% again.
    Rebuild the single time entry: exactly two new drafts, again $50.01 plus $50.00,
    with the same payer allocation. Earlier two invoices remain void. Record all IDs.
12. Clean up: void the new pair through either member and confirm both void, time
    unbilled again and zero payments across all four invoices. Close only this matter,
    report the flash. Retain both clients, closed matter, two payer rows, unbilled time
    and four void invoices. Leave all earlier retained fixtures untouched.
13. What remains: list IDs/statuses, payer percentages, both pairs' rounded totals and
    zero payment count. Confirm invalid inputs, incomplete-total refusal, duplicate
    payer refusal, group void and remove/re-add behavior. Return counts and a per-case
    table. No private links, credentials or tokens.

### R127. Bulk invoice selection, empty matters and closed-matter exclusion (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6078070237 2026-10-09 09:19 UTC

P2-B1-7 USD core. P2-B1-5 interest needs firm settings and stays deferred to Bot 2;
P2-B1-6 non-USD remains parked. Source checked: invoices.py bulk_row/bulk_rows/bulk,
create_invoices and void; invoices/bulk.html matter_ids/issued_on/due_on fields;
permissions.py. Owner only, English/USD. Replace DATE with today's YYYYMMDD.
No send, payment, card, provider or firm-setting changes. Never submit the separate
monthly-invoicing form: it can change other matters. Bulk POSTs must contain ONLY
this batch's named matter IDs, never the default selection of all visible matters.

1. Create client `QA Bulk Client DATE`, email qa-bulk-DATE@coil.test, and three hourly
   USD matters `QA Bulk First DATE`, `QA Bulk Second DATE`, `QA Bulk Empty DATE`, each
   $100.00, no office/template/payers. Report flashes and IDs, calling them A/B/C.
2. Log 1.00 billable hour on A, description `QA Bulk First Time DATE`, rate $100.00.
   Report flash and ID. Confirm $100.00 unbilled on A and no invoice.
3. Log 0.50 billable hour on B, description `QA Bulk Second Time DATE`, rate $100.00.
   Report flash and ID. Confirm $50.00 unbilled on B. Leave C with no billable records.
4. Open `/invoices/bulk`. Confirm A shows $100.00 and B $50.00; C is absent from the
   billable table. Other retained matters may appear: do not select or modify them.
   Deselect every row, then select A/B only; selected total must be $150.00 USD.
5. POST `/invoices/bulk` with CSRF, issued_on=today, due_on=2027-01-31 and no matter_ids.
   Expect `No invoices were built. Tick at least one matter.` Confirm A/B still unbilled
   and no invoice created. Do not submit any monthly_ids or monthly form.
6. POST the same date fields with only A's matter_ids value. Report the build flash.
   Expect one draft for A, total $100.00, issue date today and due date Jan 31, 2027.
   A's time becomes billed; B's time remains unbilled and C remains empty.
7. Repeat the POST selecting A only, fresh CSRF. Expect `No invoices were built. Tick at least one matter.`
   Confirm no duplicate invoice and B still unbilled. The generic flash is designed
   even though the supplied A ID no longer has anything billable.
8. Close only B via its normal matter action, report flash. Reload bulk: B is absent.
   POST selecting closed B only, same dates. Expect the same no-invoices-built flash,
   no invoice on B and its original time still unbilled.
9. Reopen B through its matter edit form, preserving other fields; report flash and
   confirm open. POST bulk with B and empty C only. Expect one draft for B at $50.00,
   not an empty invoice for C. Report the build flash and new invoice ID/number.
10. Inspect both drafts and sources. A has only its $100.00 time and B only its $50.00
    time; each entry is billed once. Both invoices use the explicit issue/due dates,
    correct client/matter, zero payments and no sent mail. C has zero invoices.
11. Clean up: void A's and B's new invoices separately, report flashes, and confirm
    both time entries unbilled again. Close A/B/C and report flashes. Retain client,
    three closed matters, two unbilled time entries and two void invoices. No monthly
    preferences or earlier retained fixtures changed.
12. What remains: list IDs/statuses, totals, date checks, empty/duplicate/closed-matter
    refusals and zero payments/mail. Return counts and a per-case table. Never include
    credentials, tokens or private links.

### R128. Draft invoice stale edits and released time (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6078362106 2026-10-09 09:39 UTC

P2-B1-1 draft-edit coverage. Source checked: invoices.py edit, _unlink_line,
builder and void; invoices/edit.html version, desc_ID, amount_ID, remove_ID,
adj_amount, adj_description, issued_on, due_on and notes; permissions.py.
Owner only, English/USD, new records only. Replace DATE with today's YYYYMMDD.
No send, mail, payment, plan, card, provider or shared-setting changes. Use current
CSRF on every POST. Preserve all current form fields unless the case changes them.

1. Create client `QA Draft Edit Client DATE` and hourly USD matter
   `QA Draft Edit Matter DATE`, rate $100.00, no office/template/payers. Log 1.00
   billable hour `QA Draft Edit Time DATE`. Report flashes and IDs. Confirm $100 unbilled.
2. Draft a $100 invoice from only that time entry. Report flash, invoice and line IDs.
   Confirm one time line, billed source and zero payments. Open its edit form twice,
   as tabs A and B, and record the same hidden version V from both.
3. In A change the line description to `QA Draft Edited DATE`, its amount to 90.00,
   notes to `QA Draft Notes A DATE`, due_on to 2027-01-31; preserve issue date.
   Save with version V. Expect `Invoice updated.` Confirm draft total $90, saved
   description/notes/date, quantity 1.00, billed source and version V+1.
4. Submit B with its stale version V, fresh CSRF, amount 80.00 and notes
   `QA Draft Stale DATE`. Report the stale-edit refusal saying another save occurred.
   Confirm A's $90 total and notes survived, version unchanged and no extra line.
5. Reload the current form and submit with amount for the time line blank, preserving
   other fields and current version. Expect `Invoice updated.` Confirm the blank
   amount leaves $90 unchanged, rather than turning the line into a zero-dollar item.
6. Add adj_amount=-10.00 and adj_description `QA Draft Discount DATE` using the fresh
   form version. Expect `Invoice updated.` Confirm two lines totalling $80, one
   $90 time line and one negative $10 discount, still zero payments.
7. Replay that saved adjustment POST with its now-stale version and fresh CSRF.
   Report stale-edit refusal. Confirm only one discount and $80 total, no duplicate.
8. Reload, check remove_ID for the discount line only and save. Expect
   `Invoice updated.` Confirm just the $90 time line remains and source stays billed.
9. Reload and remove the time line using its own remove_ID. Expect `Invoice updated.`
   Confirm draft now has zero lines and zero total, and the original time entry is
   unbilled again. This draft edit permits an empty draft; do not attempt to send it.
10. Draft a second invoice from the released time entry. Report flash and new ID.
    Expect its original recorded time value $100.00, not the first invoice's edited
    $90 line amount. Confirm one source association to the new draft, no duplicate
    time record, and the old draft still empty. Do not send either invoice.
11. Clean up: void both new drafts and report flashes. Confirm both void, original
    time unbilled and zero payments. Attempt to open the second invoice's edit route;
    expect `Only draft invoices can be edited. Void it and rebuild if the lines are wrong.`
    Close the new matter and report the flash. Retain client, closed matter, unbilled
    time and both void invoices. All earlier retained fixtures stay unchanged.
12. What remains: list IDs, version checks, stale replay refusals, blank-amount behavior,
    discount add/remove, released source and the second invoice's $100 value. Confirm
    zero mail/payments and unchanged earlier fixtures. Return counts and a per-case
    table. No tokens, credentials or private links.

### R129. Split-payer payment isolation and whole-group void refusal (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6078654677 2026-10-09 09:59 UTC

P2-B1-3/P2-B1-5 intersection after R126. Source checked: invoices.py create_invoices,
edit and void; payments.py record; invoices/detail.html manual payment fields;
permissions.py. Owner only, English/USD. Replace DATE with today's YYYYMMDD.
Only simulated manual check/cash records on this batch's new invoices. No mail,
card, Stripe, refunds, plans, shared settings or actual movement of money.

1. Create clients `QA Split Pay First DATE` and `QA Split Pay Second DATE`, and hourly
   USD matter `QA Split Pay Matter DATE` for First, rate $100.00, no office/template.
   Report flashes/IDs. Add both new clients as 50% payers; confirm total 100%.
2. Log 1.00 billable hour `QA Split Pay Time DATE`, rate $100.00. Draft its split
   invoices. Report flashes and IDs. Confirm two $50 drafts, one per payer, a shared
   split group and one billed source. Call First's invoice A and Second's invoice B.
3. GET A's edit route, then POST to it with valid CSRF and changed notes. Expect
   `This invoice is one share of a split group. Void the group and rebuild it to change the lines.`
   Confirm both drafts, amounts, notes and source association unchanged.
4. POST `/payments/record` for A with amount=0, method=check, received_on=today and
   reference `QA Split Pay Zero DATE`. Expect `Enter a positive amount.` No payment.
5. Record $20.00 check against A, reference `QA Split Pay Check DATE`, today's date.
   Report success flash and payment ID. Confirm A paid total $20, balance $30,
   payment's client First and shared matter; B remains $50 due with no payment.
6. Try to void unpaid B. Report the refusal naming A's invoice and explaining that
   voiding a member would void the group. Confirm neither invoice void, time still
   billed, A still $30 due, B still $50 due and exactly one payment.
7. Try to void A. Expect the same group payment refusal. Confirm all IDs, balances
   and status values unchanged. Record displayed statuses without assuming that a
   manual payment sends an invoice or produces captured mail.
8. Attempt $30.01 cash against A with reference `QA Split Pay Over DATE`. Report the
   over-balance refusal naming $30.00. Confirm no extra payment and unchanged B.
9. Record exactly $30.00 cash on A, reference `QA Split Pay Finish DATE`. Report
   success flash/new payment ID. Confirm A paid with zero balance and $50 paid total;
   B remains $50 due and no payments. Source remains billed, not released.
10. Attempt to record $0.01 check on fully paid A. Report the over-balance refusal
    naming $0.00; no third payment. Try void B again and confirm the group still
    refuses because A has payments. No reversal, refund or source release occurs.
11. Clean up: close only this new matter and report flash. Retain both contacts,
    closed matter, two payer rows, billed time, paid A, unpaid B owing $50 and A's
    two manual payments ($20 check/$30 cash). Do not try to erase paid history.
    No active plan, mail or card exists. Earlier fixtures remain untouched.
12. What remains: list all IDs, invoice statuses, balances and payment-client links.
    Confirm payment isolation, edit refusal, group void protection from either side,
    zero/over-balance refusals and billed source preserved. Return counts and a
    per-case table. No credentials, tokens or private links.

### R130. Manual payment month boundaries and list reconciliation (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6079378384 2026-10-09 10:49 UTC

P2-B1-3 receipt-date coverage. Source checked: payments.py index/record/detail,
payments/index.html month form and totals, invoices/detail.html manual form;
permissions.py. Owner only, English/USD. Replace DATE with today's YYYYMMDD.
Manual test bookkeeping only, no actual money, card, processor, plans or settings.
Invoice email only to the existing capture inbox. Preserve all older records.

1. Record payment IDs and USD totals currently shown for month=2028-01, 2028-02,
   2028-03 and all. Create client `QA Payment Dates Client DATE`, email
   qa-payment-dates-DATE@coil.test, and hourly matter `QA Payment Dates Matter DATE`
   at $100.00, no office/template/payers. Report flashes and IDs.
2. Log 1.00 billable hour `QA Payment Dates Time DATE`, draft and send its $100
   invoice to the capture address. Report flashes/IDs. Confirm one captured message,
   $100 due, no payments and no active plan. Do not open any public payment link.
3. Record $20 check through `/payments/record`, invoice_id=this invoice,
   received_on=2028-01-31, reference `QA Payment Jan DATE`. Report flash/payment ID.
   Confirm $80 due and payment detail shows January 31, $20 and the intended client.
4. Record $30 cash, received_on=2028-02-29, reference `QA Payment Leap DATE`.
   Report flash/ID. Confirm $50 due and detail preserves February 29, 2028.
5. Record $40 wire, received_on=2028-03-01, reference `QA Payment March DATE`.
   Report flash/ID. Confirm $10 due, three distinct payments totalling $90, operating
   account, zero surcharge and processor fee, correct client/matter/invoice links.
6. GET `/payments?month=2028-01`. Among this batch's IDs, only the $20 check appears.
   Confirm USD total equals case 1's January baseline plus $20. Do not mistake older
   retained payments for newly created duplicates; compare IDs and baseline totals.
7. GET month=2028-02 and month=2028-03. Confirm only the leap-day $30 cash in February
   and only the $40 wire in March, with baseline increases of $30 and $40 respectively.
   February must include its leap day and exclude March 1.
8. GET month=all. Confirm all three IDs exactly once, ordered March 1 then February 29
   then January 31 relative to one another, and USD baseline increased by $90.
   GET month=not-a-month: expect the All time fallback and the same three records.
9. POST a $1 manual payment with method=invalid, today's date and reference
   `QA Payment Bad Method DATE`. Expect `Method must be check, cash, wire or other. Card and bank payments come in through Stripe.`
   Confirm no fourth payment, unchanged $10 balance and unchanged month totals.
10. POST $10.01 check, received_on=2028-03-01, reference `QA Payment Over DATE`.
    Report the over-balance refusal naming $10.00. Confirm three payments only,
    $10 still due and March/all totals unchanged. Do not record the remaining balance.
11. Clean up: close the new matter and report flash. Retain client, closed matter,
    billed time, invoice owing $10 and three manual payments with their specified
    receipt dates. No refund or history deletion. Confirm older fixtures unchanged.
12. What remains: list IDs, receipt dates, balances and before/after USD totals for
    each filter. Confirm leap-day inclusion, month separation, invalid-month fallback,
    invalid-method and over-balance refusals. Return counts and a per-case table.
    Never include tokens, credentials or private links.

### R131. WIP, receivables and revenue through invoice payment (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6079961039 2026-10-09T11:28:49.710048+00:00

P2-B1-3 reporting reconciliation. Source checked: reports.py wip/ar_aging/revenue,
_range and CSV schemas; reports/revenue.html from/to form; invoices.py builder/send/
void and payments.py record; manual-payment form and permissions.py. Owner only,
English/USD. Replace DATE with today's YYYYMMDD. Captured invoice email and manual
check/cash bookkeeping only. No actual money, cards, processors, plans or settings.
Compare this batch's rows by IDs; older records may contribute to firm totals.

1. Create client `QA Report Flow Client DATE`, email qa-report-flow-DATE@coil.test,
   and hourly USD matter `QA Report Flow Matter DATE`, $100.00, no office/template.
   Report flashes/IDs. Record existing USD totals for WIP, A/R and revenue for today.
2. Log 1.00 billable hour `QA Report Flow Time DATE`, rate $100.00, date today.
   Report flash/ID. GET `/reports/wip` and its format=csv variant. Expect this
   matter's row with 1.00 unbilled hour, $100 time and $100 WIP, no expenses.
3. Draft the invoice from that time only. Report flash/ID. Confirm time billed and
   matter absent from WIP HTML/CSV. The draft must not add a client row to A/R aging
   or revenue. Neither sending nor payment occurred.
4. Void that unpaid draft and report flash. Confirm original time unbilled and the
   same $100 WIP row returns once. No A/R or revenue row for this new client/matter.
5. Rebuild a new draft from the same time, due date today, then send to capture.
   Report flashes/ID and confirm one captured invoice message. Expect WIP row gone;
   `/reports/ar-aging` and format=csv show this client's USD Current=100.00,
   Total=100.00, other aging buckets zero. Revenue still has no new matter row.
6. POST zero check payment against this invoice with today's receipt date and
   reference `QA Report Zero DATE`. Expect `Enter a positive amount.` Confirm no
   payment and A/R still $100, no revenue contribution from this matter.
7. Record $40 check, received_on=today, reference `QA Report Check DATE`. Report
   flash/payment ID. Confirm invoice $60 due; this client's A/R Current/Total is
   $60 in HTML/CSV. GET revenue with from=today and to=today: this matter contributes
   $40 and one payment. The CSV matter row matches USD, count 1, amount 40.00.
8. Attempt to void the partially paid invoice. Report payment refusal. Confirm
   invoice still $60 due, source still billed, A/R $60 and revenue $40 unchanged.
9. Record remaining $60 cash today, reference `QA Report Cash DATE`. Report flash/ID.
   Confirm paid invoice, zero balance, no client A/R row, and this matter's revenue
   $100 with two payments in HTML and CSV. WIP remains absent for this matter.
10. Request revenue with from=tomorrow and to=yesterday, dates computed at runtime.
    Confirm it normalizes to yesterday through tomorrow and includes both payment
    IDs' $100 contribution. Compare HTML/CSV matter row rather than the whole-firm
    total. Both payment detail pages link this invoice/client/matter and show $40/$60.
11. Clean up: close only the new matter and report flash. Confirm paid history still
    contributes $100 to today's revenue, with no WIP/A/R row from this batch. Retain
    client, closed matter, billed time, first void invoice, second paid invoice and
    two manual payments. Preserve every older fixture; no refund or deletion.
12. What remains: list IDs, WIP transitions 100 to 0 to 100 to 0, A/R 100 to 60 to 0,
    revenue 0 to 40 to 100, date normalization and CSV agreement. Return counts and
    a per-case table. No tokens, credentials or private links.

### R132. Invoice PDF follows draft edits and rejected stale saves (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6080401826 2026-10-09T11:59:07.445846+00:00

P2-B1-1 PDF regression, without the shared template editor assigned to Bot 2.
Source checked: invoices.py edit/build_pdf/render_invoice_pdf/pdf, stale version
check and void; invoices/edit.html fields; permissions.py. Owner only,
English/ASCII/USD. Replace DATE with today's YYYYMMDD. No mail, payments, plans,
cards, processor calls or shared settings. Keep downloaded PDFs local; they may
contain a private payment link that must never be pasted in results.

1. Create client `QA PDF Edit Client DATE` and hourly matter `QA PDF Edit Matter DATE`,
   $100.00, no office/template/payers. Log one billable hour `QA PDF Original DATE`.
   Report flashes/IDs and confirm $100 unbilled, no invoices or payments.
2. Draft its $100 invoice with notes `QA PDF Original Notes DATE`, due_on=2028-02-29.
   Report flash/ID. Download `/invoices/<id>/pdf` locally: HTTP 200, application/pdf,
   parsable PDF, correct invoice/client/matter, $100 total, original description,
   notes and February 29 due date. Save this baseline before any later downloads.
3. Open edit twice and record version V. With the first form and current CSRF,
   change line amount to 75.00, description `QA PDF Revised DATE`, notes
   `QA PDF Revised Notes DATE`, due_on=2028-03-01. Preserve other fields. Expect
   `Invoice updated.` Confirm $75 draft, revised fields and version V+1.
4. Download a second PDF separately. Confirm revised description/notes, March 1
   due date and $75 total match invoice detail. Original description/notes must not
   survive as invoice content. The saved first download must still contain its
   original $100 and original text; don't overwrite that local evidence file.
5. Submit the stale second edit form with version V and fresh CSRF, amount 60.00,
   description `QA PDF Stale DATE`, notes `QA PDF Stale Notes DATE`. Report stale
   save refusal. Confirm saved amount/text/version unchanged from the valid edit.
6. Download a third PDF. Confirm it still describes the $75 revised invoice, with
   no stale description/notes. Compare extracted content, not byte hashes: PDF
   metadata can change between renders. No payment or email should have been made.
7. Add a -$5 adjustment `QA PDF Discount DATE` through a fresh versioned edit form.
   Expect `Invoice updated.` Confirm two lines and $70 total, zero payments.
8. Download PDF again. Confirm $75 time line, negative $5 adjustment and $70 total,
   with revised notes/date still present. Inspect rendering for overlapping totals
   or clipped line text, and report concrete page evidence if anything is wrong.
9. Remove only this discount line and restore original line amount 100.00,
   description/notes and due_on=2028-02-29 using current version and CSRF. Expect
   `Invoice updated.` Confirm one line, $100 total and original fields restored.
10. Download final PDF. Confirm restored $100, original description/notes and leap
    date, no discount or stale text. Report semantic comparisons across the five
    saved PDFs. Do not include any private pay URL, QR content or token in evidence.
11. Clean up: void only this draft and close the new matter, report flashes.
    Confirm time unbilled and zero payments/mail. Retain client, closed matter,
    time, void invoice and local PDF evidence. Earlier fixtures remain untouched.
12. What remains: list IDs, versions, PDF field/total comparisons and stale-save
    refusal. Confirm no shared template changes and no mail/payment. Return counts
    and a per-case table, with only safe text excerpts if needed.

### R133. USD QuickBooks exports follow invoice and payment lifecycle (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6081207068 2026-10-09T12:48:53.154611+00:00

P2-B1-3 export reconciliation, USD only. Source checked: exports.py qb_invoices,
qb_payments, time_csv, CSV schemas and formatting; exports/index.html links;
payments.py record, invoices/detail.html fields and permissions.py. Owner only.
Replace DATE with today's YYYYMMDD. No QuickBooks connection or upload, just local
CSV downloads. No settings, cards, processors or real money. Invoice email only
through the existing capture inbox. Compare batch rows by IDs/numbers, not global totals.

1. Create client `QA Export Flow Client DATE`, email qa-export-flow-DATE@coil.test,
   and hourly USD matter `QA Export Flow Matter DATE`, $100, no office/template.
   Report flashes/IDs. Confirm no invoices or payments on the new matter.
2. Log 1.00 billable hour dated today, description `QA Export Flow Time DATE`.
   Report flash/ID. Download `/exports/time.csv`, parse as UTF-8 with BOM and CSV.
   Match Id: Hours=1.00, Rate=100.00, Amount=100.00, Currency=USD, Billable=yes,
   InvoiceNo empty, Date=today in YYYY-MM-DD. Preserve this downloaded snapshot.
3. Draft a $100 invoice from that time. Report flash/number. Download time.csv again:
   same time ID now links the draft number. Download `/exports/quickbooks/invoices.csv`:
   no row for this draft. Do not expect an invoice export to include drafts.
4. Void the unpaid draft. Report flash. Confirm its number remains absent from the
   QuickBooks invoice CSV and the time row's InvoiceNo becomes empty again.
5. Rebuild from that same time, due 2028-02-29, send only to the capture address.
   Report flashes/new number; confirm one captured invoice email. Invoice CSV now
   has exactly one matching line: Customer is the new client, DueDate=02/29/2028,
   InvoiceDate equals actual issued date in MM/DD/YYYY, Item(Product/Service)=Legal
   Services, ItemDescription equals time description, ItemQuantity=1,
   ItemRate=100.00 and ItemAmount=100.00. First void invoice stays excluded.
6. Record $25 check via `/payments/record`, invoice_id=new invoice,
   received_on=2028-02-29, reference `QA Export Check DATE`. Report flash/ID.
   Download `/exports/quickbooks/payments.csv`: one matching row for new InvoiceNo,
   PaymentDate=02/29/2028, Customer matches, Amount=25.00, Method=check and exact
   Reference. Invoice balance is $75; invoice export line remains $100.
7. Attempt a zero cash payment on this invoice. Expect `Enter a positive amount.`
   Confirm no extra payment row, $75 balance and exported invoice amount unchanged.
8. Record remaining $75 cash, received_on=2028-03-01, reference `QA Export Cash DATE`.
   Report flash/ID. Payment CSV has two rows for this invoice in receipt-date order:
   February 29 check 25.00 then March 1 cash 75.00. Total 100.00; invoice paid.
9. Download invoice CSV after payment. Confirm one $100 line, not a zero-balance
   line or a second invoice row. Time CSV still links the new paid invoice number.
   Compare headers with the export schemas; parse quoted values with a CSV parser.
10. Download payments CSV twice without mutations. Confirm the two batch rows and
    values are identical, with no duplicated bookkeeping. The original unbilled
    time snapshot from case 2 is unchanged on disk despite subsequent downloads.
11. Clean up: close the new matter and report flash. Confirm exports retain the paid
    invoice, two payments and billed time after closure. Retain client, closed
    matter, time, first void invoice, second paid invoice and two manual payments.
    No refunds, deletion, external uploads or changes to older records.
12. What remains: list IDs/numbers, draft/void exclusions, time linkage transitions,
    invoice line values, both payment CSV rows, date formats and retained snapshots.
    Return counts and a per-case table. No credentials, tokens or private links.

### R134. USD receivables aging at exact day boundaries (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6083296752 2026-10-09T14:49:33.753196+00:00

P2-B1-3 aging boundary regression. Source checked: reports.py ar_aging/_bucket and
CSV schema; invoices.py builder/_lines_from_form, invoices/new.html adjustment and
date fields; payments.py record/manual form; permissions.py. Owner only, English/USD.
Replace DATE with today's YYYYMMDD. No settings, interest run, plans, cards or actual
money. Email only through the existing capture inbox. Preserve all earlier fixtures.
Use the report's displayed as-of date T, not the browser timezone, for offsets below.
If the report date changes mid-batch, recompute expected bucket placement and report it.

1. Create client `QA Aging Edge Client DATE`, email qa-aging-edge-DATE@coil.test,
   and hourly USD matter `QA Aging Edge Matter DATE`, $100, no office/template.
   Report flashes/IDs. Read report as-of date T and confirm no row for this client.
   Do not create time or expenses. Each invoice below uses only a positive $10
   adjustment via adjustment_amount=10.00 and its named adjustment_description.
2. Build invoice A with description `QA Aging Current DATE`, issued_on=T minus 100
   days, due_on=T. Send to capture; report flash/number. Confirm $10 due and new
   client Current=10.00, Total=10.00 in `/reports/ar-aging` and format=csv.
3. Build/send invoice B identically except description `QA Aging Thirty DATE` and
   due_on=T minus 30 days. Confirm B's $10 is in 1-30; client total $20.
4. Build/send C, description `QA Aging Thirty One DATE`, due_on=T minus 31 days.
   Confirm C's $10 is in 31-60; client total $30. B must remain in 1-30.
5. Build/send D, description `QA Aging Sixty DATE`, due_on=T minus 60 days.
   Confirm D is also in 31-60, that bucket $20 and client total $40.
6. Build/send E, description `QA Aging Sixty One DATE`, due_on=T minus 61 days.
   Confirm E's $10 is in 61-90 and client total $50.
7. Build/send F, description `QA Aging Ninety DATE`, due_on=T minus 90 days.
   Confirm F is also in 61-90, that bucket $20 and client total $60.
8. Build/send G, description `QA Aging Ninety One DATE`, due_on=T minus 91 days.
   Confirm G's $10 is in 90+, client total $70. Capture inbox has one invoice
   message per new invoice, seven total. No public payment link opened.
9. Record a $5 check only on G with today's receipt date and reference
   `QA Aging Partial DATE`. Report flash/payment ID. Confirm G $5 due, 90+ $5,
   total $65; other buckets unchanged. No interest or fee should be generated.
10. Compare HTML and CSV for only this client's USD row: Current=10.00, 1-30=10.00,
    31-60=20.00, 61-90=20.00, 90+=5.00, Total=65.00. Check all seven invoice
    numbers against their due dates and bucket placement; source amounts total $70
    with exactly $5 paid. Repeat read and confirm no extra payment or invoice.
11. Clean up: close the new matter and report flash. Confirm its outstanding
    invoices remain in A/R with the same client totals after closure. Retain client,
    closed matter, seven sent/partial invoices, one check payment and seven captured
    messages. No refund, void, deletion or modification of older records.
12. What remains: list IDs/numbers, report date T, exact due dates and offsets,
    bucket values before/after the partial payment and HTML/CSV agreement. Return
    counts and a per-case table. No credentials, tokens or private links.

### R135. Invoice builder discount boundaries and refused source consumption (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6084492818 2026-10-09T15:59:40.765736+00:00

P2-B1-1 draft builder regression. Source checked: invoices.py builder and
_lines_from_form, invoices/new.html time_ids/adjustment_amount/date fields,
and permissions.py. Owner only, English/USD. Replace DATE with today's YYYYMMDD.
No sending, payments, plans, cards, credits, processors or shared settings.
Use only new records. A zero-total draft with real offsetting lines is permitted.

1. Create client `QA Builder Edge Client DATE` and hourly USD matter
   `QA Builder Edge Matter DATE`, $100, no office/template/payers. Report flashes/IDs.
   Confirm no invoice, time or payment on this new matter.
2. Log 1.00 billable hour `QA Builder Edge Time DATE`, rate $100, date today.
   Report flash/time ID and confirm $100 unbilled. Use this same time ID throughout.
3. Submit the invoice builder with matter_id, valid CSRF, issued_on=today,
   due_on=2028-02-29, no selected time_ids and adjustment_amount blank.
   Expect HTTP 400 and `Pick at least one item to invoice, or enter an amount.`
   Confirm no invoice and the time still unbilled.
4. Select the $100 time and set adjustment_amount=-100.01, description
   `QA Builder Negative DATE`. Submit. Expect HTTP 400; report the exact negative
   total refusal. Confirm no invoice, the time remains unbilled and still selectable.
5. Re-submit selected time with adjustment_amount=-100.00, description
   `QA Builder Zero DATE`, due_on=2028-02-29. Expect a draft created with two lines,
   $100 time and negative $100 discount, total $0.00, no payments, time billed once.
   Report flash/invoice number and verify due date. Do not send the zero draft.
6. Void that unpaid draft and report flash. Confirm the original time becomes
   unbilled again, one void invoice remains and no payment was created.
7. Rebuild from the same time with adjustment_amount=-99.99, description
   `QA Builder Cent DATE`, same leap-day due date. Expect second draft with two
   lines, total $0.01, time billed to this draft only. Report flash/number.
8. While that time is billed, submit a new builder request without selectable items
   and adjustment_amount=-0.01, description `QA Builder Alone DATE`.
   Expect HTTP 400; report negative-total refusal. Confirm no third invoice,
   second draft still $0.01 and its time linkage unchanged.
9. Void only the one-cent draft. Report flash. Confirm two void invoices, original
   time unbilled again and zero payments. Earlier retained invoices are untouched.
10. Rebuild same time with adjustment_amount blank and no other selections. Expect
    third draft with one $100 time line, total $100, no leftover discount from prior
    requests. Confirm exactly one linkage to this draft and no duplicate time row.
11. Clean up: void third draft, close new matter and report flashes. Retain client,
    closed matter, one unbilled $100 time entry and three void invoices ($0, $0.01,
    $100). Confirm zero mail/payments and no extra invoice from refused requests.
12. What remains: list IDs, invoice counts/totals, source linkage after every refusal,
    build and void, leap due date and zero/negative boundary behavior. Return counts
    and a per-case table. No credentials, tokens or private links.

### R136. Large draft invoice confirmation threshold (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6085614379 2026-10-09T17:09:35.546435+00:00

P2-B1-1 builder guard regression. Source checked: helpers.py UNUSUAL_INVOICE_CENTS
(100000000 cents), invoices.py builder/_lines_from_form and invoices/new.html
confirm_unusual, adjustment and date fields; permissions.py. Owner only, English/USD.
Replace DATE with today's YYYYMMDD. These are unsent test drafts only. No mail,
payments, plans, cards, real money, processor calls, exports or shared settings.
Preserve every earlier fixture. Report exact guard flashes rather than guessing format.

1. Create client `QA Large Draft Client DATE` and hourly USD matter
   `QA Large Draft Matter DATE`, $100, no office/template/payers. Report flashes/IDs.
   Confirm no invoices or payments. All builder requests use this matter, valid
   CSRF, issued_on=today, due_on=2028-02-29 and only the source/adjustment stated.
2. Log one billable hour `QA Large Draft Time DATE`, $100. Record time ID and
   confirm unbilled. It must remain unbilled through each refused builder request.
3. Select this time and adjustment_amount=999900.01, description
   `QA Large Draft Above DATE`, with confirm_unusual omitted. Total $1,000,000.01.
   Expect HTTP 400, a flash requiring confirmation and the checkbox offered.
   Confirm no invoice, time unbilled and no financial transaction.
4. Repeat the same request with fresh CSRF, still without confirm_unusual.
   Expect the same refusal, no invoice and no consumed time. Do not click Send.
5. Select time plus adjustment_amount=999900.00, description
   `QA Large Draft Exact DATE`, no confirm_unusual. Total exactly $1,000,000.00.
   Expect a draft created: the guard uses strictly greater than the threshold.
   Confirm two lines, exact total, $100 time billed to this draft, zero payments.
6. Void that draft and report flash. Confirm time released, one void invoice,
   no mail/payment and no live receivable from this unsent invoice.
7. Re-submit time plus adjustment_amount=999900.01, description
   `QA Large Draft Confirmed DATE`, this time confirm_unusual=1. Expect a second
   draft created at $1,000,000.01, two lines and time billed once to this draft.
   Confirm it remains draft, not sent; zero payments. Report flash/number.
8. Void second draft and report flash. Confirm original time unbilled and two
   void invoices. No implicit send or payment resulted from confirming the amount.
9. Select time plus adjustment_amount=999899.99, description
   `QA Large Draft Below DATE`, omit confirm_unusual. Expect third draft created
   at $999,999.99 without guard, time billed and due February 29, 2028.
10. Void third draft. Report flash; confirm three void invoices with totals
    $1,000,000.00, $1,000,000.01 and $999,999.99, original time unbilled, no extra
    invoice from either refusal. Check zero payments and no captured invoice email.
11. Clean up: close new matter and report flash. Retain client, closed matter,
    one unbilled $100 time entry and three void invoices. Do not delete history or
    create refunds/credits. Confirm all earlier retained fixtures unchanged.
12. What remains: list IDs, exact cent totals, both refused requests, checkbox
    behavior and source release after each void. Return counts and a per-case
    table. No credentials, tokens or private links.

### R137. Manual payment normalization and text limits (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6086277196 at 2026-10-09T17:51:02Z

P2-B1-3 manual bookkeeping regression. Source checked: payments.py record,
invoices.py _lines_from_form, Invoice.recalc, invoices/detail.html payment fields,
payments/detail.html and permissions.py. Owner only. English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No real money, mail, cards, bank processor,
plans, provider settings, public payment links or changes to older fixtures.
All payment requests below POST /payments/record with fresh CSRF and this invoice_id.
Manual payments on a draft are permitted; its status deliberately remains draft.

1. Create client `QA Payment Text Client DATE` and hourly USD matter
   `QA Payment Text Matter DATE`, $100, no office/template/payers. Report flashes/IDs.
   Confirm no time, expenses, invoices or payments on this new matter.
2. Build one unsent USD invoice with adjustment_amount=10.00, description
   `QA Payment Text Charge DATE`, issued_on=today, due_on=2028-02-29, no other items.
   Report flash/number. Confirm total/balance $10, draft status and zero payments.
3. Submit amount=0.00, method=check, received_on=2028-02-29. Expect redirect and
   `Enter a positive amount.` Confirm no payment and balance still $10.
4. Submit amount=1.00, method=invalid, same date. Expect redirect and
   `Method must be check, cash, wire or other. Card and bank payments come in through Stripe.`
   Confirm no payment and balance still $10. Do not invoke a processor endpoint.
5. Submit amount=1.00, method containing spaces around uppercase CHECK, leap date.
   Reference: two spaces, `QA Payment Text Ref DATE ` padded with R to exactly
   125 ASCII characters, then two spaces. Note: two spaces, `QA Payment Text Note DATE `
   padded with N to exactly 305 characters, then two spaces. Include note in the POST
   even though the visible manual form has no note input. Report flash/payment ID.
   Expect check, operating, $1, balance $9. Payment detail stores stripped reference's
   first 120 characters and stripped note's first 300, exactly, with no outer spaces.
6. Submit amount=2.00 with method omitted, received_on=2028-03-01, whitespace-only
   reference and note. Expect second payment, default check, operating, balance $7.
   Report flash/ID. Detail has no Reference or Note field; no prior text leaks in.
7. Submit amount=7.01, method=other, same March date. Expect refusal; report exact
   balance flash. Confirm still two payments totalling $3 and $7 balance.
8. Submit amount=7.00, method containing spaces around uppercase OTHER, March date,
   reference `QA Payment Text Final DATE`, note `QA Payment Text Complete DATE`.
   Expect third payment, method other, operating, total paid $10, balance zero.
   Report flash/ID. Draft badge remaining draft is designed behavior, not a failure.
9. Submit amount=0.01, method=check on the zero-balance invoice. Expect refusal;
   report exact balance flash. Confirm three payments, paid $10, balance zero.
10. Reopen all three payment details and invoice. Confirm amounts $1/$2/$7, methods
    check/check/other, leap/March dates, client/matter/invoice links, text truncation
    and empty-field omission. No surcharge, processor fee or trust entry was made.
11. Clean up: close the new matter and report flash. Retain client, closed matter,
    one unsent draft with $10 paid and zero balance, three operating manual payments.
    No void, refund, credit or deletion. Confirm no captured invoice email and all
    older fixtures unchanged.
12. What remains: list IDs/counts, exact text lengths, method normalization/default,
    refused requests and unchanged balances, date values and draft-status behavior.
    Return counts and a per-case table. No credentials, tokens or private links.

### R138. Invoice builder source IDs stay scoped to their matter (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6086734359 at 2026-10-09T18:19:34Z

P2-B1-1 builder selection regression. Source checked: invoices.py _builder_context,
_lines_from_form/new/void, invoices/new.html time_ids fields and permissions.py.
Owner only, English/USD. Replace DATE with today's YYYYMMDD. Unsent drafts only.
No payments, mail, plans, cards, credits, processors or shared settings. Requests
POST /invoices/new with matter_id in the form, no conflicting query parameter,
fresh CSRF, issued_on=today, due_on=2028-02-29 and no adjustment or other items.
Use only IDs created here. Foreign or already-billed IDs are ignored by the builder.

1. Create client `QA Source Scope Client DATE` and two hourly USD matters
   `QA Source Scope A DATE` and `QA Source Scope B DATE`, both $100 with no
   office/template/payers. Report flashes/IDs and label matters A and B.
2. Log one billable hour on A named `QA Source Scope Time A DATE`, $100;
   log two billable hours on B named `QA Source Scope Time B DATE`, $200.
   Report flashes/time IDs TA/TB, both unbilled. No other source rows.
3. Submit builder for A selecting only TB. Expect HTTP 400 and
   `Pick at least one item to invoice, or enter an amount.` No invoice anywhere;
   TA/TB remain unbilled. A foreign source is not billed to the target matter.
4. Submit A with time_ids containing TA twice and TB once. Expect one draft IA,
   one $100 time line linked only to TA. TB stays unbilled on B. Repeated TA
   values do not duplicate its line. Report flash/number and leap-day due date.
5. Submit A again with stale TA and foreign TB, no other items. Expect HTTP 400
   and the same pick-at-least-one flash. IA remains $100 with one line, TA billed
   to IA once, TB unbilled and no extra invoice.
6. Submit B selecting TB and TA. Expect one draft IB, one $200 time line linked
   only to TB; IA/TA unchanged. Report flash/number. No cross-matter source link.
7. Void IA only and report flash. Confirm TA unbilled, TB still billed to IB,
   IA void and IB still draft $200. Source release must stay on A.
8. Repeat void IA. Expect `Already void.` and no changed source linkage or
   invoice count. TB remains billed to IB; TA remains unbilled.
9. Rebuild A with TA twice and TB once. Expect new draft IA2 at $100, one TA
   line and same leap due date. TB and IB unchanged; no duplicated time rows.
10. Void IB only. Confirm TB unbilled while TA remains billed to IA2. Report flash.
    Three invoices total: IA void, IB void, IA2 draft. Zero payments or mail.
11. Clean up: void IA2, close both matters, report flashes. Retain client, two
    closed matters, TA/TB unbilled ($100/$200), three void invoices ($100/$200/$100).
    Confirm source ownership and all older retained fixtures unchanged.
12. What remains: all IDs/counts, foreign/stale selection refusals, deduplication,
    source linkage after each void/rebuild and leap dates. Return counts and a
    per-case table. Never disclose credentials, tokens or private links.

### R139. Expense billability and invoice locks (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6087048050 at 2026-10-09T18:40:02Z

P2-B1-1 expense-source regression. Source checked: time.py expense_new/edit/delete
and _expense_from_form, time/expense_form.html; invoices.py _builder_context,
_lines_from_form and void; permissions.py. Owner only, English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No receipt upload, mail, payment, cards,
AI, processor calls, plans or shared settings. Preserve all older fixtures.
Expense routes start /time/expenses. All POSTs need fresh CSRF. Expense fields:
matter_id, date, category=Other, amount, description, billable=1 when stated;
omit billable when not billable. No expense_code or receipt. Builder requests
POST /invoices/new with this matter_id, issued_on=today, due_on=2028-02-29,
only the stated expense_ids and no other source or adjustment.

1. Create client `QA Expense Lock Client DATE` and hourly USD matter
   `QA Expense Lock Matter DATE`, $100, no office/template/payers. Report IDs/flashes.
   Confirm no time, expenses, invoices or payments.
2. POST /time/expenses/new for this matter: date=2028-02-29, amount=12.34,
   description `QA Expense Lock Source DATE`, billable omitted. Expect
   `Expense saved.` Record expense E; $12.34, Other, leap date, not billable.
3. Submit builder selecting E. Expect HTTP 400 and
   `Pick at least one item to invoice, or enter an amount.` No invoice; E unbilled.
4. Edit E with identical fields plus billable=1. Expect `Expense saved.`
   Confirm same E, billable and $12.34. Builder now offers this expense once.
5. Submit builder selecting E twice. Expect one unsent draft I, one expense
   line at $12.34, quantity 1, leap source date and description
   `Other: QA Expense Lock Source DATE`. E billed to I once. Report number/flash.
6. GET E edit page: expect read-only invoice link. POST edit E attempting
   amount=99.99 and description `QA Expense Lock Refused DATE`, other fields
   unchanged. Expect `This expense is on an invoice and cannot be changed.`
   E remains $12.34 with original description; I unchanged, no second expense.
7. POST /time/expenses/E/delete using the actual E ID. Expect
   `This expense is on an invoice and cannot be deleted. Void the invoice first.`
   Confirm E still exists and I still has its single $12.34 line.
8. Void I, report flash. Confirm E released and editable, invoice void $12.34.
   Edit E amount=23.45, description `QA Expense Lock Revised DATE`, same date,
   billable omitted. Expect `Expense saved.` Same E now not billable, $23.45.
9. Submit builder selecting E. Expect HTTP 400 and the pick-at-least-one flash.
   Confirm no second invoice and E remains unbilled, not billable, $23.45.
10. Edit E with billable=1, other fields unchanged. Expect `Expense saved.`
    Build again selecting E once. Expect new draft I2, one $23.45 expense line,
    `Other: QA Expense Lock Revised DATE`, quantity 1, leap date. I stays void;
    E links only to I2. Report number/flash. No payments or mail.
11. Clean up: void I2 and close matter, reporting flashes. Retain client,
    closed matter, one billable unbilled expense $23.45, two void invoices
    $12.34/$23.45. Do not delete E. All earlier retained fixtures unchanged.
12. What remains: list IDs, source billability/link transitions, refusal flashes,
    deduplication, exact dates/totals and unchanged historical invoice line.
    Return counts and per-case table. No credentials, tokens or private links.

### R140. Expense amount refusals preserve source and invoice text (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6087515101 at 2026-10-09T19:09:59Z

P2-B1-1 expense validation regression. Source checked: time.py _expense_from_form,
expense_new/edit and time/expense_form.html; invoices.py _lines_from_form/void;
permissions.py. Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD.
No receipt uploads, mail, payments, processors, plans, AI or shared settings.
Preserve every earlier fixture. All requests use fresh CSRF and only this matter.
Expense POST fields: matter_id, date=2028-02-29, billable=1, category and amount
as stated, no receipt or expense_code. Report exact flashes and record IDs.

1. Create client `QA Expense Guard Client DATE` and hourly USD matter
   `QA Expense Guard Matter DATE`, $100, no office/template/payers. Confirm
   no time, expenses, invoices or payments; report create flashes/IDs.
2. POST /time/expenses/new with amount=-0.01, category=Other, description
   `QA Expense Guard Source DATE`. Expect HTTP 400 and `Amount cannot be negative.`
   Confirm zero expenses and invoices, no financial record created.
3. Repeat with amount=0.00 and no receipt. Expect HTTP 400 and
   `Enter an amount, or attach a receipt to fill the amount in later.`
   Confirm still zero expenses. Do not attach a receipt to evade this check.
4. Create amount=0.01, category=invalid, description with two outer spaces around
   `QA Expense Guard Source DATE`. Expect `Expense saved.` One expense E:
   one cent, category Other by fallback, stripped description, billable, leap date.
5. POST /time/expenses/E/edit with amount=-1.00, category=Other and description
   `QA Expense Guard Refused DATE`. Expect HTTP 400 and negative-amount flash.
   Fresh GET E must show original one cent, original description/date, billable.
6. Repeat edit with amount=0.00 and no receipt. Expect HTTP 400 and receipt-or-amount
   flash. Fresh GET E still original. Failed form contents are not saved state.
7. Edit E to amount=12.34, category=Other, description
   `QA Expense Guard Other Source DATE`. Expect `Expense saved.` Same E, $12.34,
   billable, leap date. Description already contains exact category word Other.
8. Build unsent draft via POST /invoices/new, selecting only E in expense_ids,
   issued_on=today, due_on=2028-02-29, no adjustment or other sources. Expect one
   $12.34 expense line with description exactly `QA Expense Guard Other Source DATE`,
   no extra `Other:` prefix. Quantity 1, leap source date, E billed once. Report I.
9. Void I, report flash; E becomes unbilled. Edit E to description
   `QA Expense Guard Revised DATE`, same amount/date/category/billable. Expect
   `Expense saved.` Same E, original void I line text remains its earlier text.
10. Build again selecting only E, same invoice dates. Expect new draft I2 $12.34,
    one line `Other: QA Expense Guard Revised DATE`. Category is prepended when
    absent. E billed to I2, I remains void with original line, zero payments/mail.
11. Clean up: void I2, close matter and report flashes. Retain client, closed
    matter, one billable unbilled expense E $12.34 on leap day with revised text,
    two void invoices $12.34 each with their respective original descriptions.
    No deletion, refund or credit. Confirm all older retained fixtures unchanged.
12. What remains: list IDs/counts, negative/zero refusal evidence, saved-state
    preservation, category fallback, trimming and both invoice descriptions.
    Return counts and a per-case table. No credentials, tokens or private links.

### R141. Expense invoice ordering follows source dates and IDs (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6087981134 at 2026-10-09T19:39:57Z

P2-B1-1 invoice source-order regression. Source checked: invoices.py
_builder_context/_lines_from_form/void, Invoice.lines order_by in models.py,
invoices/new.html expense_ids and date fields; time.py expense_new/edit,
time/expense_form.html; permissions.py. Owner only, English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No mail, payments, plans, cards, processors,
receipts, AI or shared settings. Preserve all older fixtures. Expense POSTs use
/time/expenses/new or /time/expenses/ID/edit, fresh CSRF, this matter_id,
category=Other, billable=1, no receipt/expense_code, stated date/amount/description.
Builder POST /invoices/new: this matter_id, issued_on=today, due_on=2028-03-31,
only stated expense_ids; no time, flat fee or adjustment. Retain original invoices.

1. Create client `QA Expense Order Client DATE` and hourly USD matter
   `QA Expense Order Matter DATE`, $100, no office/template/payers. Report
   IDs/flashes; confirm zero expenses and invoices.
2. Create expense A, description `QA Expense Order A DATE`, date=2028-03-01,
   amount=3.33. Expect `Expense saved.`, billable and unbilled. Record A ID.
3. Create B, description `QA Expense Order B DATE`, date=2028-02-29, amount=2.22.
   Expect same flash, leap date and unbilled. Record B ID, greater than A ID.
4. Create C, description `QA Expense Order C DATE`, date=2028-02-29, amount=1.11.
   Expect same flash, unbilled, C ID greater than B ID. Three distinct expenses.
5. Build with expense_ids in order A,C,B,A. Expect one draft I, three lines
   ordered B,C,A, total $6.66. Source dates sort first; equal dates use source ID;
   request order and repeated A do not override that. Quantity 1 each, unit/line
   amounts $2.22/$1.11/$3.33, descriptions prefixed Other:. Report number/flash.
6. Void I, report flash. Confirm all three expenses unbilled, I void $6.66.
   Rebuild with expense_ids C,B,A. Expect new draft I2, same B,C,A line order,
   amounts/dates/descriptions/total; each expense billed once to I2.
7. Void I2 and edit A date to 2028-02-28, all other A fields unchanged.
   Expect `Expense saved.`, A same ID now February 28; B/C remain leap day.
   Both void invoices preserve original B,C,A order and original dates.
8. Rebuild with expense_ids C,B,A. Expect new draft I3, order A,B,C and total
   $6.66; A now February 28, B/C February 29. All three billed to I3 only.
9. Void I3 and edit C date to 2028-02-28, all other C fields unchanged.
   Expect `Expense saved.` Same C ID, A/C equal dates, A ID lower than C.
   I3 preserves A,B,C and its old C date. All sources unbilled.
10. Rebuild with expense_ids C,B,A,C. Expect new draft I4, order A,C,B,
    amounts $3.33/$1.11/$2.22, total $6.66, no duplicate C. A/C February 28,
    B leap day; due March 31. Four invoices, three expenses, zero payments/mail.
11. Clean up: void I4, close matter, report flashes. Retain client, closed matter,
    three billable unbilled expenses (A/C February 28, B February 29), four void
    $6.66 invoices with historical order/date snapshots. Older fixtures unchanged.
12. What remains: IDs, chronological/tied-date/request-order comparisons, exact
    cents, all four invoice snapshots and final source states. Return counts and
    per-case table. Never disclose credentials, tokens or private links.

### R142. Matter-filtered expense totals track billability and voids (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6088585439 at 2026-10-09T20:19:49Z

P2-B1-1 expense summary regression. Source checked: time.py expenses,
_expense_from_form/expense_new/edit; time/expenses.html and expense_form.html;
invoices.py builder/void and permissions.py. Owner only, English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No payments, mail, receipts, AI, cards, plans,
processors or shared settings. Preserve older fixtures. Expenses use fresh CSRF,
category=Other, date=2028-02-29, no receipt/code. Expense routes /time/expenses/new
and /time/expenses/ID/edit. Filter list via /time/expenses?matter_id=ID.
Total includes every expense; Unbilled includes only billable rows without invoice.
Do not confuse Receipt column none with Status non-billable or unbilled.

1. Create client `QA Expense Totals Client DATE` and two hourly USD matters
   `QA Expense Totals A DATE`, `QA Expense Totals B DATE`, $100, no office/template/
   payers. Report IDs/flashes. Both filtered expense lists start empty.
2. Create E1 on A, amount=10.01, billable=1, description `QA Expense Totals One DATE`.
   Expect `Expense saved.` A: one row, total $10.01, unbilled $10.01; B empty.
3. Create E2 on A, amount=20.02, billable omitted, description
   `QA Expense Totals Two DATE`. A: two rows, total $30.03, unbilled $10.01.
   E2 status non-billable. Same-date display orders newer E2 before E1.
4. Create E3 on B, amount=30.03, billable=1, description
   `QA Expense Totals Three DATE`. B: one row, total/unbilled $30.03.
   A remains two rows, total $30.03, unbilled $10.01. No cross-matter counts.
5. Edit E2 on A adding billable=1, all other fields unchanged. Expect
   `Expense saved.` A total $30.03, unbilled $30.03, both unbilled; B unchanged.
6. Build unsent invoice I on A selecting only E1, issued_on=today,
   due_on=2028-03-31, no adjustment/other sources. Expect $10.01 draft.
   A total still $30.03, unbilled $20.02, E1 links to I; B unchanged.
7. Edit unbilled E2 amount=25.02, other fields unchanged. Expect `Expense saved.`
   A total $35.03, unbilled $25.02, two rows. I remains $10.01; B unchanged.
8. Void I, report flash. A total $35.03, unbilled $35.03, E1/E2 unbilled.
   Repeated void gives `Already void.` and preserves these totals; B unchanged.
9. Edit E1 with billable omitted, same amount/date/description. Expect
   `Expense saved.` A total $35.03, unbilled $25.02; E1 non-billable.
   Builder A must offer E2 and exclude E1. B still $30.03 total/unbilled.
10. Build A selecting E2 only, same dates as I. Expect I2 draft $25.02.
    A total $35.03, unbilled $0.00; E1 non-billable, E2 linked to I2.
    B still one unbilled expense $30.03. No payments or mail.
11. Clean up: void I2, close A/B, report flashes. Reopen both filtered lists.
    A two rows total $35.03, unbilled $25.02; B one row total/unbilled $30.03.
    Retain client, two closed matters, E1 non-billable $10.01, E2 billable unbilled
    $25.02, E3 billable unbilled $30.03, two void invoices $10.01/$25.02.
    Closing a matter must not remove its filtered expense history. Older fixtures intact.
12. What remains: IDs, row counts, totals at each transition, same-date ordering,
    status labels and unchanged other-matter evidence. Return counts and per-case
    table. Never disclose credentials, tokens or private links.

### R143. Expense code normalization and invalid-code clearing (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6089023849 at 2026-10-09T20:49:53Z

Source checked: app/blueprints/time.py _code, _expense_from_form, expense_new,
expense_edit and _open_matters; ledes.py choices/valid_code; expense_form.html;
permissions.py owner access. Owner only, English/ASCII/USD. Replace DATE with
 today's YYYYMMDD. Preserve all older fixtures. No invoices, payments, mail,
cards, AI, receipts, exports or shared settings in this batch. Use fresh CSRF
for POST /time/expenses/new and /time/expenses/ID/edit. Every save supplies
matter_id, date=2028-02-29, category=Copies, amount=4.56, billable=1,
description=`QA Expense Code DATE`, plus stated expense_code. Reopen edit after
each save and inspect selected option value, not merely submitted form data.
Malformed values use authenticated form POSTs because the select offers only
valid choices. Blank code is allowed; do not expect category fallback to be
persisted into the code field. That fallback belongs to LEDES export.

1. Create client `QA Expense Code Client DATE` and hourly USD matter
   `QA Expense Code Matter DATE`, $100, no office/template/payers. Report IDs
   and flashes. Filtered expense list starts empty.
2. Create one expense with expense_code=E101. Expect `Expense saved.`
   Reopened edit selects E101 Copying, amount $4.56, leap date, billable.
3. Edit with expense_code=`  e108  `. Expect `Expense saved.` and selected
   value E108, label E108 Postage. Category stays Copies; amount stays $4.56.
4. Edit with expense_code=`E112 Court fees`. Expect successful save and
   selected value E112 only. No description or category change.
5. Edit with expense_code=E999. Expect successful save with blank selected
   value, label (none), not a validation error. One expense still $4.56.
6. Edit with expense_code=E124. Expect E124 Other selected on fresh GET.
   Billable, date, description and category stay unchanged.
7. Edit with expense_code=A101, a code from a different set. Expect successful
   save but blank expense code. No new expense, no amount change.
8. Edit with expense_code=`e101 Copying`. Expect E101 selected on fresh GET.
   Then reload the filtered list: one row, total and unbilled $4.56.
9. Edit with expense_code consisting only of three spaces. Expect blank
   selection and successful save. Category Copies does not populate E101.
10. Restore expense_code=E101 through the ordinary select and Save changes.
    Expect `Expense saved.` and E101 persisted. Reload twice, same expense ID,
    one row, total and unbilled $4.56, no invoices or payments created.
11. Clean up: close only this matter, report flash. Reopen expense edit and
    confirm closed matter remains selected and available, E101 still selected.
    Retain client, closed matter and this billable unbilled expense $4.56.
    All earlier retained fixtures remain untouched; no deletion needed.
12. What remains: report IDs, selected values for each submitted code,
    unchanged category/description/date/amount evidence, counts and per-case
    PASS/FAIL table. Never disclose credentials, tokens or private links.

### R144. Expense matter moves preserve validation and invoice history (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6089576849 at 2026-10-09T21:30:00Z

Source checked: time.py _expense_from_form/expense_edit/expenses;
time/expense_form.html; invoices.py _builder_context/_lines_from_form/void;
permissions.py owner access. Owner only, English/ASCII/USD. Replace DATE with
 today's YYYYMMDD. Preserve all older fixtures. No mail, payments, cards, AI,
receipts, plans, processors or shared settings. Expense form routes
/time/expenses/new and /time/expenses/E/edit with fresh CSRF, matter_id as
stated, amount=7.89, date=2028-02-29, category=Other, billable=1,
description=`QA Expense Move DATE`, no code or receipt. After refusal use a
fresh GET to verify persisted fields, not the echoed submitted form.

1. Create client `QA Expense Move Client DATE` and two hourly USD matters
   `QA Expense Move A DATE`, `QA Expense Move B DATE`, $100, no office/template/
   payers. Record IDs/flashes; both filtered expense lists start empty.
2. Create expense E on A with the specified fields. Expect `Expense saved.`
   One billable unbilled $7.89 row, A total/unbilled $7.89, B empty. Record E.
3. Edit E changing only matter_id to B. Expect `Expense saved.` Same E on B,
   A empty with zero totals, B total/unbilled $7.89. Builder A excludes E;
   builder B offers it. Leap date, description and amount unchanged.
4. POST edit E with blank matter_id. Expect HTTP 400 and `Pick a matter.`
   Fresh GET still has B selected and $7.89; A remains empty. No duplicate.
5. Attempt move to A with amount=-1. Expect HTTP 400 and
   `Amount cannot be negative.` E stays on B at $7.89 with unchanged text/date.
6. Repair with A and amount=7.89. Expect successful save, same E back on A,
   A total/unbilled $7.89, B empty. Reopen both builders to verify eligibility.
7. Build unsent invoice I on A via /invoices/new: matter_id=A, expense_ids=E,
   issued_on=today, due_on=2028-03-31, no other sources/adjustment. Expect draft
   $7.89, one expense line. A total $7.89, unbilled zero; B empty.
8. Attempt authenticated edit POST moving billed E to B. Expect redirect with
   `This expense is on an invoice and cannot be changed.` Locked GET still
   shows A and I. E stays on A, I remains $7.89, B empty.
9. Void I, report flash. Move E to B with ordinary edit. Expect successful
   save, same E now unbilled on B, total/unbilled $7.89, A empty. Original void
   I still belongs to A and retains its original $7.89 line/date/description.
10. Build unsent I2 on B selecting E only with same issue/due dates. Expect
    draft $7.89 on B, E linked to I2, B unbilled zero. Original I remains void
    on A with its original snapshot. Exactly two invoices, one expense.
11. Clean up: void I2 and close A/B, report flashes. Retain client, two closed
    matters, E billable unbilled on B at $7.89, and two void $7.89 invoices on
    their original respective matters. B total/unbilled $7.89, A empty.
    No payments or mail. All older fixtures untouched.
12. What remains: IDs, matter-link transitions, both refusal messages,
    persisted-field evidence, invoice snapshots and counts. Return per-case
    table. Never disclose credentials, tokens or private links.

### R145. Expense receipt replacement and zero-amount preservation (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6089962227 at 2026-10-09T21:59:53Z

Source checked: time.py _save_receipt/_expense_from_form/expense_new/edit/
expense_receipt; expense_form.html multipart receipt input; permissions.py.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
older fixtures. No invoices, payments, mail, cards, plans, AI, providers or
shared settings. Receipt upload/download only, never invoke extraction or AI.
Prepare two tiny valid one-page PDFs A/B with distinct ASCII text and bytes,
filenames `QA Receipt A DATE.pdf` and `QA Receipt B DATE.pdf`. Record SHA256
hashes locally. Each save uses fresh CSRF, matter_id=M1, date=2028-02-29,
category=Other, billable=1, description=`QA Receipt Expense DATE`, no code,
stated amount and optional receipt. Routes /time/expenses/new and
/time/expenses/E/edit. Download /time/expenses/E/receipt to compare exact bytes;
random filename prefix is expected, not a bug. Do not publish private links.

1. Create client `QA Receipt Client DATE` and hourly USD matter
   `QA Receipt Matter DATE`, $100, no office/template. Record IDs and flashes;
   filtered expense list empty. Prepare the two PDFs without real information.
2. Submit new expense amount=0 with no receipt. Expect HTTP 400 and
   `Enter an amount, or attach a receipt to fill the amount in later.`
   No saved expense and filtered list still empty.
3. Submit new expense amount=0 with receipt A. Expect `Expense saved.`
   One billable unbilled expense E at $0.00, leap date. Download matches A hash.
4. Edit E amount=12.34, omit receipt. Expect `Expense saved.`, same E at
   $12.34, existing A still downloadable with matching bytes. One expense.
5. Edit E amount=0, omit receipt. Expect successful save because A already
   exists. Same E at $0.00, A unchanged. No receipt-free zero refusal here.
6. Edit E amount=0 with receipt B. Expect successful save, same E; download
   now matches B exactly and differs from A. Current receipt link reflects B.
7. Edit E amount=-1 with receipt A. Expect HTTP 400 and
   `Amount cannot be negative.` Fresh GET still $0.00 and current receipt B;
   download still matches B. Refused save must not replace the current file.
8. Edit E amount=23.45, no receipt. Expect successful save, B preserved;
   filtered list one row total/unbilled $23.45, same leap date and description.
9. Replace receipt with A at amount=23.45. Expect successful save; download
   matches A again, one expense and unchanged amount/date/category/billability.
10. Save same fields with receipt omitted once more. Expect successful save,
    A preserved. GET receipt with inline=1 and ordinary download both return
    the same A bytes; ordinary response is attachment, inline response inline.
11. Clean up: close M1, report flash. Retain client, closed matter, one
    billable unbilled $23.45 expense with current receipt A. Confirm download
    still works and filtered list unchanged. Do not delete server receipt
    files or older fixtures. No invoices/payments/mail created.
12. What remains: IDs, hashes/byte counts, zero/negative outcomes, receipt
    replacement and preservation evidence, retained records and per-case table.
    No credentials, tokens or private links in the result.

### R146. Expense deletion respects invoice locks and released sources (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6090460045 at 2026-10-09T22:39:51Z

Source checked: time.py expense_new/edit/delete/receipt and _expense_from_form;
time/expense_form.html; invoices.py _builder_context and void; permissions.py.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
all older fixtures. No payments, mail, cards, receipts, AI, plans, providers or
shared settings. Create only this batch's records. Fresh CSRF on every POST.
Expense fields: matter_id=M1, date=2028-02-29, category=Other, amount=6.54,
billable=1, description as stated, blank expense_code, no receipt. Use
/time/expenses/new, /time/expenses/E/edit and /time/expenses/E/delete.
Invoice builder /invoices/new uses matter_id=M1, expense_ids as stated,
issued_on=today, due_on=2028-03-31, no other sources or adjustments.

1. Create client `QA Expense Delete Client DATE` and hourly USD matter
   `QA Expense Delete Matter DATE`, $100, no office/template/payers. Report
   IDs/flashes and confirm its filtered expense list is empty.
2. Create E1 description `QA Expense Delete A DATE` with stated fields.
   Expect `Expense saved.`, one unbilled $6.54 expense, leap date persisted.
3. Create E2 description `QA Expense Delete B DATE` with same fields.
   Expect successful save, two distinct IDs, total/unbilled $13.08.
4. Delete E2 through its own edit form. Expect `Expense deleted.`, filtered
   list has E1 only, total/unbilled $6.54. Fresh GET E2 edit returns 404.
5. Repeat authenticated POST to E2 delete with fresh CSRF. Expect 404,
   E1 unchanged, no duplicate deletion effect and no server error.
6. Build unsent draft I from E1 only. Expect one $6.54 expense line,
   E1 linked to I, total $6.54 and unbilled zero. Record invoice ID/number.
7. Attempt authenticated POST delete E1 while linked. Expect redirect and
   `This expense is on an invoice and cannot be deleted. Void the invoice first.`
   E1 and draft I remain; locked edit identifies I and has no delete form.
8. Void I via /invoices/I/void. Expect `Invoice NUMBER voided. Its time,
   expenses and milestones can be billed again.` with its actual number.
   E1 becomes editable/unbilled, total/unbilled $6.54; I retains its line.
9. Delete released E1 using its form. Expect `Expense deleted.`, filtered
   list empty, totals zero, E1 edit 404. Void I still opens with its original
   $6.54 line/description/date. No surviving source expense is required.
10. Create E3 description `QA Expense Delete Survivor DATE`, amount=8.76,
    other stated fields. Expect successful save and one unbilled $8.76 row;
    builder offers E3 only. I remains void $6.54, no new invoice created.
11. Clean up: close only M1, report flash. Retain client, closed matter,
    E3 billable unbilled $8.76 on leap day and void I with its original line.
    E1/E2 remain deleted. No payments/mail. All older fixtures untouched.
12. What remains: IDs, delete/refusal/repeat outcomes, list totals, locked
    form evidence and surviving invoice snapshot, per-case PASS/FAIL table.
    Never disclose credentials, tokens or private links.

### R147. Expense categories use exact choices and safe fallback (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6090705769 at 2026-10-09T22:59:51Z

Source checked: time.py EXPENSE_CATEGORIES/_expense_from_form/expense_new/edit;
time/expense_form.html and permissions.py owner access. Owner only,
English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve older fixtures.
No invoices, payments, mail, receipts, cards, AI, providers or shared settings.
Use /time/expenses/new and /time/expenses/E/edit, fresh CSRF and multipart.
Every save supplies matter_id=M1, date=2028-02-29, amount=9.87, billable=1,
description=`QA Category Expense DATE`, blank expense_code, stated category.
After every save reopen edit and inspect the selected category and persisted
fields. Invalid choices require authenticated POST, not a fabricated select.

1. Create client `QA Category Client DATE` and hourly USD matter
   `QA Category Matter DATE`, $100, no office/template. Record IDs/flashes;
   filtered expense list empty.
2. Create E with category=Travel. Expect `Expense saved.`, selected Travel,
   one billable unbilled $9.87 row on leap date. Record E ID.
3. Edit category=Expert. Expect successful save and Expert selected; same E,
   unchanged amount/date/description, total/unbilled $9.87.
4. Edit category=travel (lowercase). Expect successful save and Other selected,
   not Travel. Exact category choices are case-sensitive; no new expense.
5. Edit category=` Travel ` with spaces. Expect successful save and Other
   selected. Category values are not trimmed before choice validation.
6. Edit category=Postage. Expect successful save and Postage selected;
   blank expense_code remains blank, unchanged amount/date/description.
7. Edit category empty. Expect successful save and Other selected. One row
   remains $9.87, billable and unbilled; blank is allowed with fallback.
8. Edit category=Filing fee. Expect successful save and exact choice selected,
   same E. Reload filtered list and verify displayed category.
9. Edit category=Unknown. Expect successful save and Other selected,
   no validation error. Fresh GET confirms original amount and leap date.
10. Restore category=Copies, then repeat identical save. Expect successful
    saves, Copies selected, same E and one row, total/unbilled $9.87.
    No invoices, payments or mail created.
11. Clean up: close M1, report flash. Retain client, closed matter and E,
    billable unbilled $9.87, Copies, blank code and leap date. Closed matter
    remains selected on edit. No deletion; older fixtures untouched.
12. What remains: IDs, submitted categories and selected values, unchanged
    fields, counts and per-case PASS/FAIL table. No credentials or private links.

### R148. Expense description whitespace, blank fields and refused edits (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6091018762 at 2026-10-09T23:29:55Z

Source checked: time.py _expense_from_form/expense_new/expense_edit;
time/expense_form.html description input and permissions.py owner access.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
older fixtures. No invoices, payments, mail, receipts, cards, AI, providers or
shared settings. Routes /time/expenses/new and /time/expenses/E/edit, fresh
CSRF and multipart POST. Every save supplies matter_id=M1, date=2028-02-29,
category=Other, amount=5.43, billable=1, blank expense_code, no receipt,
description as stated. Reopen edit after every save; inspect decoded input
value, not rendered whitespace or HTML source entities.

1. Create client `QA Expense Text Client DATE` and hourly USD matter
   `QA Expense Text Matter DATE`, $100, no office/template. Record IDs/flashes;
   filtered list empty.
2. Create E description `QA Expense Text Original DATE`. Expect
   `Expense saved.`, one unbilled $5.43 expense, leap date; record E.
3. Edit description with three leading and trailing spaces around original.
   Expect successful save; reopened input is original without outer spaces.
4. Edit description `QA Expense Text A  B DATE` with two spaces between A/B.
   Expect successful save; internal double space retained, same E and amount.
5. Edit description `QA Expense Text A & B "quoted" DATE`. Expect successful
   save; decoded input preserves ampersand and quotes exactly. No extra row.
6. Edit description empty. Expect successful save, empty persisted input;
   amount $5.43 and billability unchanged. Description is optional.
7. Restore original description. Expect successful save and original value
   on fresh GET; one row, total/unbilled $5.43.
8. Edit description consisting only of spaces and tabs. Expect successful
   save and empty persisted input. Other fields remain unchanged.
9. Restore original, then attempt description `QA Expense Text Refused DATE`
   with amount=-1. Expect HTTP 400 `Amount cannot be negative.` Fresh GET
   still has original description and $5.43, not the echoed refused form.
10. Omit description entirely in an otherwise valid edit POST. Expect
    successful save and empty input. Restore original with ordinary form,
    then reload twice: same E, original text, total/unbilled $5.43.
11. Clean up: close M1, report flash. Retain client, closed matter, one
    billable unbilled $5.43 expense with original description and leap date.
    Closed matter remains selected. Older fixtures untouched; no deletion.
12. What remains: IDs, exact submitted/persisted text, refusal preservation,
    list totals and per-case table. No credentials, tokens or private links.

### R149. Expense checkbox values and rejected billability changes (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6091348239 2026-10-10T00:01:15Z

Source checked: time.py _expense_from_form/expenses/expense_edit;
expense_form.html billable checkbox value 1; invoices.py _builder_context;
permissions.py owner access. Owner only, English/ASCII/USD. Replace DATE with
today's YYYYMMDD. Preserve older fixtures. No invoices created, payments,
mail, receipts, cards, AI, providers or shared settings. Read builders only.
Routes /time/expenses/new and /time/expenses/E/edit, fresh CSRF, multipart.
Every save uses M1, amount=4.32, date=2028-02-29, category=Other,
description=`QA Billable Flag Expense DATE`, blank expense_code, no receipt.
Specify billable as below. This HTML checkbox uses presence/nonempty string,
not the CSV importer's boolean parser. Inspect fresh persisted edit fields.

1. Create client `QA Billable Flag Client DATE` and hourly USD matter
   `QA Billable Flag Matter DATE`, $100, no office/template. Record IDs/flashes;
   filtered expense list empty.
2. Create E with billable=1. Expect `Expense saved.`, checkbox checked,
   status unbilled, total/unbilled $4.32, builder offers E. Record ID.
3. Edit through ordinary form with checkbox unchecked (field omitted).
   Expect successful save, unchecked, non-billable, total $4.32/unbilled zero,
   builder excludes E. Date, description and amount unchanged.
4. POST billable empty string. Expect successful save and still non-billable,
   same E, builder excludes E, unchanged total.
5. POST billable=0 (nonempty text). Expect successful save and checked,
   billable unbilled, builder offers E, unbilled $4.32. Do not expect CSV rules.
6. POST billable=false (nonempty text). Expect successful save and checked,
   same billable state, one expense, total/unbilled $4.32.
7. Ordinary form uncheck again. Expect non-billable, builder excludes E,
   total $4.32/unbilled zero; one expense still.
8. Attempt billable=1 with amount=-1. Expect HTTP 400
   `Amount cannot be negative.` Fresh GET remains unchecked at $4.32,
   non-billable and absent from builder. Refused edit must not change state.
9. Repair amount=4.32, billable=1. Expect successful save, checked,
   unbilled $4.32 and eligible builder row, same E.
10. Repeat ordinary checked save. Expect successful save and one expense,
    same amount/date/text; total/unbilled $4.32, no invoice created.
11. Clean up: close M1, report flash. Retain client, closed matter and E,
    billable unbilled $4.32 on leap day. Reopen edit, checkbox checked and
    closed matter selected. All older fixtures untouched.
12. What remains: submitted values versus persisted checkbox/status,
    builder eligibility, refusal preservation and per-case table. No secrets.

### R150. Expense dates use ISO prefixes and firm-local fallback (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6091632998 2026-10-10T00:30:24Z

Source checked: helpers.py parse_date/firm_today; time.py _expense_from_form,
expense_new/edit; expense_form.html date input; owner permissions. English/USD.
Replace DATE with today's YYYYMMDD. Preserve older fixtures. No invoices,
payments, mail, receipts, cards, AI, providers or shared settings. Read the
firm timezone without changing it. Record firm-local today T at each fallback
save, allowing an actual midnight rollover. Default new-expense date should
agree with T. Use fresh CSRF/multipart /time/expenses/new and /time/expenses/E/edit.
Every save supplies M1, amount=7.65, category=Other, billable=1, blank code,
no receipt, description=`QA Expense Date DATE`, date as stated. Malformed dates
use authenticated POST; verify fresh GET persisted date, not echoed form.

1. Create client `QA Expense Date Client DATE` and hourly USD matter
   `QA Expense Date Matter DATE`, $100, no office/template. Record IDs/flashes,
   timezone and T; new form defaults to T, filtered list empty.
2. Create E date=2028-02-29. Expect `Expense saved.`, one billable unbilled
   $7.65 expense and exact leap date. Record E ID.
3. Edit date=2028-01-31. Expect successful save, month-end date persists,
   same E and unchanged amount/text/category/billability.
4. Edit date=2028-02-29T23:59:00. Expect successful save and Feb 29 2028;
   parser uses first ten characters, no time or timezone conversion.
5. Edit date empty. Expect successful save, date defaults to T at save time,
   same E. Empty required browser input is bypassed only for this form POST.
6. Restore date=2028-02-29 through ordinary date input. Expect successful
   save and leap date back; one row, total/unbilled $7.65.
7. Edit date=2027-02-29. Expect successful save with fallback T, not 400;
   invalid leap date is not persisted. Other fields unchanged.
8. Edit date=not-a-date. Expect successful save and fallback T again,
   no duplicate and no server error. Fresh edit confirms persisted value.
9. Restore leap date, then submit date=2028-01-31 with amount=-1.
   Expect HTTP 400 `Amount cannot be negative.` Fresh GET still leap date
   and $7.65; refused save does not persist the submitted month-end date.
10. Omit date in a valid edit POST. Expect successful save and T. Restore
    leap date with ordinary form, then reload twice: exact leap date, same E,
    original amount/text/category and total/unbilled $7.65.
11. Clean up: close M1, report flash. Retain client, closed matter and one
    billable unbilled $7.65 expense dated Feb 29 2028. Closed matter remains
    selected; all older fixtures untouched. No deletion.
12. What remains: IDs, submitted and persisted dates, timezone/T evidence,
    refusal preservation and per-case table. No credentials or private links.

### R151. Expense invalid matter edits preserve the stored row (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6092562987 2026-10-10T02:10:33Z

Source checked: time.py _expense_from_form, expense_new/edit and expenses;
time/expense_form.html required matter selector; permissions.py owner access.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD.
Preserve every older fixture. No invoices, payments, receipts, mail, cards,
AI, providers or shared settings. Use fresh CSRF and multipart POST to
/time/expenses/new or /time/expenses/E/edit. Unless stated otherwise supply
matter_id=M1, amount=6.78, date=2028-02-29, category=Other, billable=1,
blank expense_code, no receipt, description=`QA Matter Guard Expense DATE`.
Invalid matter values require authenticated POST, bypassing required select.
After refusals inspect fresh GET, not echoed submitted fields.

1. Create client `QA Matter Guard Client DATE` and hourly USD matter
   `QA Matter Guard Matter DATE`, $100, no office/template. Record IDs/flashes;
   filtered expense list empty.
2. Submit new expense with matter_id empty and otherwise valid fields.
   Expect HTTP 400 `Pick a matter.` and filtered list still empty.
3. Submit new expense with matter_id=not-an-id. Expect HTTP 400
   `Pick a matter.` and no expense created.
4. Create valid E on M1. Expect `Expense saved.`, billable unbilled $6.78,
   leap date, Other, original description. Record ID and total/unbilled $6.78.
5. Edit E with matter_id empty and description `QA Matter Guard Refused DATE`.
   Expect HTTP 400 `Pick a matter.` Fresh GET still M1 and original text.
6. Edit E omitting matter_id, amount=9.99. Expect HTTP 400 `Pick a matter.`
   Fresh GET still $6.78 on M1, same date/text and one row.
7. Edit E with matter_id=not-an-id and date=2028-01-31. Expect HTTP 400
   `Pick a matter.` Fresh GET still M1 and leap date, amount $6.78.
8. Edit E with matter_id empty and amount=-1. Expect `Pick a matter.`
   with HTTP 400 because matter validation runs first. Stored row unchanged.
9. Repair all fields with valid M1 and original values. Expect `Expense saved.`
   and one billable unbilled $6.78 row, total/unbilled $6.78.
10. Close M1, report flash. Ordinary edit still offers the selected closed
    matter. Save original values against this closed M1; expect `Expense saved.`
    and unchanged row. Closed status does not prohibit an expense edit here.
11. Cleanup: retain client, closed M1 and E with original fields. Reload
    twice and confirm same ID, leap date, billable unbilled $6.78. Do not delete
    or reopen the matter; all older fixtures untouched.
12. What remains: IDs, invalid-value/refusal table, persisted fields after
    each refusal, final totals and per-case results. No secrets or private links.


### R152. Expense amount formatting and sub-cent truncation (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6092761775 2026-10-10T02:30:24Z

Source checked: helpers.py parse_money; time.py _expense_from_form/new/edit,
expenses; expense_form.html amount text field and owner permissions.
English/ASCII/USD, owner only. Replace DATE with today's YYYYMMDD.
Preserve older fixtures. No invoices, payments, mail, receipts, cards, AI,
providers or shared settings. Fresh CSRF/multipart at /time/expenses/new or
/time/expenses/E/edit. Every save supplies M1, date=2028-02-29, Other,
billable=1, blank expense_code, no receipt, original description
`QA Amount Format Expense DATE`, amount as below. Inspect fresh persisted
amount and filtered totals, not echoed rejected input. Parser truncates
fractional text after two digits; do not expect rounding.

1. Create client `QA Amount Format Client DATE` and hourly USD matter
   `QA Amount Format Matter DATE`, $100, no office/template. Record IDs/flashes;
   filtered expense list empty.
2. Create E amount=12.34. Expect `Expense saved.`, one billable unbilled
   expense $12.34, leap date and original text. Record E ID.
3. Edit amount=` $1,234.56 `. Expect successful save, persisted 1234.56,
   total/unbilled $1,234.56, same E and other fields.
4. Edit amount=12.349. Expect successful save and $12.34, not $12.35.
   Fresh edit and total/unbilled agree, exactly one row.
5. Edit amount=.50. Expect successful save and $0.50, same E, unchanged
   description/date/category/billability.
6. Edit amount=12.3. Expect successful save and $12.30; one row and matching
   total/unbilled. A single fractional digit is padded on the right.
7. Edit amount=(1.23). Expect HTTP 400 `Amount cannot be negative.`
   Fresh GET remains $12.30 with original fields.
8. Edit amount=0.009. Expect HTTP 400
   `Enter an amount, or attach a receipt to fill the amount in later.`
   Truncation makes zero cents and this expense has no receipt. Stored $12.30
   survives; do not attach anything.
9. Edit amount empty. Expect the same zero-amount HTTP 400 error and
   preserved $12.30. Original date/text/category/billability remain intact.
10. Restore amount=12.34, then repeat that valid save. Expect `Expense saved.`
    each time, same E, one row, total/unbilled $12.34 and original fields.
11. Clean up: close M1, report flash. Retain client, closed matter and E,
    billable unbilled $12.34 on leap day with original description. Fresh edit
    selects closed M1. All older fixtures untouched; no deletion.
12. What remains: IDs, input-to-persisted amount table, refusal preservation,
    final totals and per-case results. No secrets or private links.


### R153. Expense date sorting and totals after edits and deletion (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093088440 2026-10-10T03:00:22Z

Source checked: time.py expenses date/id descending order, _expense_from_form,
expense_new/edit/delete; expense_form.html and owner permissions. Owner only,
English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve all older fixtures.
No invoices, payments, mail, receipts, cards, AI, providers or shared settings.
Fresh CSRF and multipart create/edit; CSRF POST deletion only for this batch's B.
Use /time/expenses?matter_id=M1 and /time/expenses/new or /time/expenses/E/edit.
All expenses Other, blank code, no receipt, named `QA Sort A DATE`, B and C.
Check only the filtered M1 rows, excluding global older fixtures.

1. Create client `QA Sort Client DATE` and hourly USD matter `QA Sort Matter DATE`,
   $100, no office/template. Record IDs/flashes; filtered list empty.
2. Create A amount=1.11, date=2028-02-29, billable=1. Expect `Expense saved.`,
   one row, total/unbilled $1.11. Record A ID.
3. Create B amount=2.22, date=2028-01-31, billable=1. Expect successful save,
   order A then B despite B's newer ID; total/unbilled $3.33.
4. Create C amount=3.33, date=2028-02-29, billable omitted. Expect successful
   save, order C,A,B (same-date newer ID first), total $6.66, unbilled $3.33.
5. Edit B date=2028-03-01 with other B fields unchanged. Expect successful
   save, order B,C,A; same IDs and total $6.66/unbilled $3.33.
6. Edit B date=2028-02-29. Expect successful save, order C,B,A by descending
   ID on tied dates; totals unchanged, exactly three rows.
7. Edit A amount=4.44 preserving billable/date/text. Expect successful save,
   order C,B,A, total $9.99 and unbilled $6.66.
8. Edit C billable=1 with original amount/date/text. Expect successful save,
   total/unbilled $9.99, same order and three rows.
9. Attempt B amount=-1 and date=2028-04-01. Expect HTTP 400
   `Amount cannot be negative.` Fresh filtered list retains C,B,A, total/unbilled
   $9.99; B still $2.22 and Feb 29. Refused edit cannot reorder the list.
10. Delete only B via /time/expenses/B/delete. Expect `Expense deleted.`,
    order C,A, two rows, total/unbilled $7.77. Fresh GET B/edit is 404.
11. Clean up: close M1, report flash. Retain client, closed matter, A $4.44
    and C $3.33, both billable unbilled on leap day. Reload list twice:
    C,A and total/unbilled $7.77. No new expense after B deletion; older
    fixtures untouched and no other deletion.
12. What remains: IDs, date/order transitions, exact totals, refused edit
    preservation and deleted B ID, per-case results. No secrets/private links.


### R154. Expense code normalization and invalid-kind clearing (testfirm)
status: posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-6093332595 2026-10-10T03:32:32Z

Source checked: time.py _code/_expense_from_form/new/edit; ledes.py valid_code,
UTBMS expense choices; expense_form.html expense_code select; owner permissions.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve older
fixtures. No invoices, payments, mail, receipts, cards, AI, providers or settings.
Fresh CSRF/multipart at /time/expenses/new or /time/expenses/E/edit. Every save
uses M1, amount=8.91, date=2028-02-29, category=Other, billable=1, no receipt,
description=`QA Code Normalize Expense DATE`, expense_code as stated.
Non-option values use authenticated POST. Inspect fresh persisted select value.

1. Create client `QA Code Normalize Client DATE` and hourly USD matter
   `QA Code Normalize Matter DATE`, $100, no office/template. Record IDs/flashes;
   filtered expense list empty.
2. Create E with expense_code=E101. Expect `Expense saved.`, selected E101,
   category Other unchanged, billable unbilled $8.91. Record E ID.
3. Edit code=e102. Expect successful save, selected E102 (uppercased),
   same E and Other category, unchanged amount/date/text.
4. Edit code=` E101 Copying `. Expect successful save, E101 selected.
   Outer trim and first-space token extraction accept this older label format.
5. Edit code=A103. Expect successful save and blank expense code, because
   an activity code is invalid for an expense. Other fields unchanged.
6. Edit code=E999. Expect successful save and blank code, not an error;
   same E, one row and total/unbilled $8.91.
7. Restore E102 using ordinary select. Expect successful save and E102.
   Then fresh GET confirms code, Other category and original fields.
8. Attempt code=E101 with amount=-1. Expect HTTP 400
   `Amount cannot be negative.` Fresh GET still E102 and $8.91;
   refused save cannot change code or other fields.
9. Valid edit omitting expense_code entirely. Expect successful save and
   blank selected code. One row remains with Other category and original fields.
10. Restore E101; repeat ordinary E101 save. Expect successful saves, E101
    selected, same E and total/unbilled $8.91 with no duplicate.
11. Clean up: close M1, report flash. Retain client, closed matter and E,
    billable unbilled $8.91, Other, E101, leap date and original description.
    Closed M1 remains selected on edit; all older fixtures untouched.
12. What remains: IDs, submitted-to-stored codes, invalid-kind and refusal
    preservation, exact totals, per-case results. No secrets/private links.


### R155. Expense matter reassignment updates filtered totals (testfirm)
status: retired by Ian October 9 finite acceptance direction

Source checked: time.py expenses, _expense_from_form and expense_new/edit;
expense_form.html matter select and billable checkbox; owner permissions.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve older
fixtures. No invoices, payments, mail, receipts, cards, AI, providers or settings.
Fresh CSRF/multipart create/edit. All rows use Other, blank code, no receipt,
date=2028-02-29. Check /time/expenses?matter_id=M1 and M2, not global totals.
Descriptions `QA Move Totals A DATE` and `QA Move Totals B DATE`.
Preserve all fields on edits except explicitly changed fields.

1. Create client `QA Move Totals Client DATE`, two hourly USD matters
   `QA Move Totals One DATE` and `QA Move Totals Two DATE`, $100 each,
   no office/template. Record IDs/flashes; both filtered lists empty.
2. Create A on M1, amount=2.34, billable=1. Expect `Expense saved.`,
   M1 total/unbilled $2.34; M2 empty. Record A.
3. Create B on M2, amount=5.67, billable omitted. Expect successful save,
   M2 total $5.67/unbilled zero, M1 unchanged. Record B.
4. Edit A matter_id=M2, preserving billable and other fields. Expect
   successful save; M1 empty/zero totals, M2 two rows total $8.01/unbilled
   $2.34. Fresh A edit selects M2 and keeps leap date/text/amount.
5. Edit B billable=1. Expect successful save, M2 total/unbilled $8.01,
   M1 still empty; same A/B IDs and two rows.
6. Attempt move A to M1 with amount=-1. Expect HTTP 400
   `Amount cannot be negative.` Fresh A remains M2 at $2.34; M1 empty,
   M2 total/unbilled $8.01. Failed move must not transfer the expense.
7. Move A back to M1 with valid amount=2.34. Expect successful save,
   M1 total/unbilled $2.34, M2 total/unbilled $5.67, one row each.
8. Move B to M1 and omit billable. Expect successful save, B non-billable;
   M1 two rows total $8.01/unbilled $2.34, M2 empty, same B ID.
9. Move B back to M2 with billable omitted. Expect successful save,
   original distribution restored: M1 A billable $2.34, M2 B non-billable
   $5.67/unbilled zero. Reload each list twice and confirm exact IDs/totals.
10. Clean up: close both matters, report flashes. Retain client, closed
    M1/M2, A on M1 billable unbilled $2.34 and B on M2 non-billable $5.67,
    both leap date with original descriptions. Older fixtures untouched.
    Report IDs, per-case results, movement and totals table; no secrets.


## Bot 2 (#89, QA Bot 2, qa2.coil.legal)

### S1. Security sweep: clients cannot reach each other, roles cannot climb
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5972084478 2026-10-03T18:17:22Z

A deliberate attempt to break the walls between clients and between roles, on your own clean firm. Create only records named `QA2 Sec ... 20261003`, emails ending `@example.test`. Portal sign-in links are in the owner-only `/dev/outbox`; open them there in a separate browser session and never paste them. Every refused request must actually be sent: a request that never left the browser is BLOCKED, not PASS.

1. As owner, create client contacts `QA2 Sec X 20261003` (`qa2-sec-x-20261003@example.test`) and `QA2 Sec Y 20261003` (`qa2-sec-y-20261003@example.test`), each with This contact is a client ticked, and a matter for each, `QA2 Sec MX 20261003` and `QA2 Sec MY 20261003`. Record all four IDs.
2. Upload a small text file to each matter and share both to the portal. Record both document IDs.
3. Client X signs in to the portal. X sees MX and its document only; nothing of Y's.
4. As X, request Y's document at `/portal/documents/<Y doc id>/download`. Expect 404.
5. As X, open the staff pages `/matters/<MY id>`, `/contacts` and `/settings`. Each sends X to the staff login page and shows no firm data.
6. As X, POST to `/portal/upload` with `matter_id` set to MY's ID and a small file. Expect `Pick one of your matters.` and no file on MY.
7. As X, open `/portal/invoices/1` (invoice 1 belongs to client 1 and is a draft). Expect 404.
8. Signed out completely, open `/documents/<X doc id>/download` and `/matters/<MX id>`. Each redirects to login; no file or data.
9. As owner, add users `QA2 Sec Paralegal 20261003` (paralegal) and `QA2 Sec Readonly 20261003` (readonly). As the paralegal, POST `/settings/users/new` with a valid CSRF token and a new user's details. Expect 403 and no new user.
10. As the readonly user, POST `/contacts/new` with a valid CSRF token and a name. Expect a refusal (403) and no contact.
11. As owner, POST `/contacts/new` with no `_csrf` field. Expect a refusal (400 or 403) and no contact. Then send the paralegal's CSRF token with the owner's session cookie. Expect a refusal and no contact.
12. As X in the portal, send a message with an extra form field `contact_id` set to Y's ID. Expect the message to appear only on X's thread for the firm, never on Y's.
13. Clean up: unshare both documents, close both matters, deactivate both new users. Report everything created and its final state.

### S2. Security sweep: public endpoints and tokens
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5972515133 2026-10-03T19:02:56Z

Public doors and bearer tokens. Same naming and the same rule that an unsent request is BLOCKED.

1. POST `/webhooks/stripe` with any JSON and no signature. qa2 has no Stripe webhook secret, so expect HTTP 503 `webhook verification not configured`, and no payment or invoice change. Invoice 1 stays a draft.
2. POST `/webhooks/twilio` with `From=+15125550100` and `Body=QA2 Sec spoof 20261003`, no Twilio signature. Report the HTTP status and whether any message appears anywhere in the firm. A stored message from an unsigned request is a finding.
3. Open `/p/<made-up 40-character token>` and `/sign/doc/<made-up token>`. Each returns 404 or an expired page, never a document.
4. Submit the public intake form with the hidden `website` field filled. Expect the thank-you page and no new lead.
5. Submit the public intake form six times within a minute with names `QA2 Sec Rate 1 20261003` to `6`. Expect the sixth to get HTTP 429. Then decline the leads that were created, reason `QA2 Sec cleanup 20261003`.
6. As owner, create an API token `QA2 Sec token 20261003`. `GET /api/me` with it: 200. With the token wrong by one character: 401. With no Authorization header: 401.
7. As the readonly user from S1 (reactivate it), create an API token if the page allows it, and report whether a readonly user can. If it can, `POST /api/time` with it must be refused.
8. Revoke the owner token. `GET /api/me` with it: 401.
9. Send `GET /matters/<MX id>?tab=../../settings` and `GET /contacts?q=%27%20OR%201%3D1--` as owner. Both return normal pages or a clean 404, never an error page or another firm's data.
10. Deactivate the readonly user again. Report everything created and its final state.

### S3. Security sweep: hostile text and hostile files
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5973249473 2026-10-03T20:36:00Z

Stored script injection and dangerous uploads, on your own firm. Create only records named `QA2 Sec ... 20261003`. A refused request must actually be sent. Never open a file you uploaded in a way that could run it on your own machine; read headers and page source instead.

1. Create contact `QA2 Sec <b>bold</b> 20261003` with notes `<script>alert(1)</script> QA2 Sec 20261003` and a tag `"><img src=x onerror=alert(2)>`. Open the contact page, the contacts list and the conflict check on that name. The text shows literally; view source shows it escaped (`&lt;script&gt;`), and no script runs.
2. Give that contact client status and a matter `QA2 Sec XSS Matter <svg onload=alert(3)> 20261003`. The matter page, the matters list, the dashboard and the audit log show the name as text, escaped in source.
3. Portal: share a document on that matter and sign in as that client (link from `/dev/outbox`, not pasted). The portal shows the matter name and the contact name escaped. Send a portal message `<script>alert(4)</script>`; the staff thread shows it as text.
4. Public intake form: submit name `QA2 Sec <script>alert(5)</script> 20261003` and description `<iframe src=//example.test>`. The owner's lead page, the pipeline and the `/dev/outbox` notice show both as text.
5. Upload `qa2-sec-20261003.html` containing `<script>alert(6)</script>` to the matter. Download it from the staff page and from the portal. Report the `Content-Type`, `Content-Disposition` and `X-Content-Type-Options` headers on each. Expect `attachment` and `nosniff`; the browser must not render it as a page on the Coil origin.
6. Upload `qa2-sec-20261003.svg` containing `<svg xmlns="http://www.w3.org/2000/svg" onload="alert(7)"/>`. Same header check. If any page shows a preview of it inline, report the page and whether the script runs.
7. Upload a file named `../../qa2-sec-20261003.txt` and one named `qa2-sec-20261003.txt.exe`. Report the stored names; neither may escape the matter's folder, and Coil may keep or refuse the `.exe` but must never serve it inline.
8. Upload a file of exactly 25 MB plus one byte. Expect a refusal naming the 25 MB limit and nothing stored.
9. Response headers on the dashboard: report `Content-Security-Policy`, `X-Frame-Options` (or `frame-ancestors`), `Referrer-Policy` and `Strict-Transport-Security`.
10. Clean up: unshare the documents, close the matter, delete the uploaded files. Leave the contact. Report everything created and its final state.

### S4. Security sweep: every role against every area, and the session itself
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5973636927 2026-10-03T21:27:00Z

A systematic map rather than spot checks. Use the inactive users 10 (paralegal) and 11 (readonly) from S1, reactivated for this batch, and create `QA2 Sec Attorney 20261003` (attorney) and `QA2 Sec Billing 20261003` (billing). Deactivate all four at the end.

1. For each of the four roles, GET each of these and record the HTTP status: `/`, `/contacts`, `/matters`, `/intake`, `/conflicts`, `/tasks`, `/calendar`, `/documents`, `/messages`, `/time`, `/reports`, `/exports`, `/trust`, `/invoices`, `/payments`, `/settings`, `/settings/users`, `/settings/tools`, `/settings/api`, `/audit`, `/dev/outbox`, `/import`. Present it as one table, role by route. Compare it with the role descriptions on `/settings/users`; any route a role can open that its description says it cannot is a finding.
2. For readonly, send a POST with a valid CSRF token to `/contacts/new`, `/matters/new`, `/tasks/new` and `/calendar/new`. Each must be refused with nothing saved.
3. For billing, send a POST with a valid CSRF token to `/contacts/new` and to a closed matter's edit URL. Each must be refused (billing reads matters and contacts but does not change them).
4. Owner signs in, copies the session cookie value into a second client, then logs out in the first. The second client's next request must go to the login page.
5. The session cookie has `Secure`, `HttpOnly` and `SameSite=Lax` (or stricter). Report the flags.
6. Five wrong passwords for user 10 in a row, then the right one. Report what happens at each step (lockout, delay or nothing). Then sign in normally after any lockout clears, or record that it did not.
7. Password reset (if offered on the login page) for `qa2-sec-x-20261003@example.test`, a client contact, not a user: expect the same neutral message as for a real user and no email in `/dev/outbox`.
8. Deactivate the four users. Report the final state.

### S5. Settings > Tools deeper
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5973871484 2026-10-03T21:57:31Z

See the batch body in the comment above (cases 5148-5160): Intake, Tasks, Documents,
Calendar and Messages switched off one or two at a time, checking the sidebar, dashboard
card, a matter tab, the direct URL's 404 message, and that the matching `/api/` route
stays unaffected; the non-owner 404 wording; and the calendar feed's open question.

### S6. Spanish: the client portal, its emails, and the anti-leak check
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5974096727 2026-10-03T22:21:00Z

See the batch body in the comment above (cases 5161-5173): a Spanish-language contact
through the portal (login, home, messages with Greek text, upload, logout), the sign-in
email's Spanish strings in `/dev/outbox`, a second staff session confirming the firm side
stays English, the rate-limit duplicate case, and the check that `/portal/login`'s neutral
message never changes language based on whether the email matched (anti-enumeration).

### S7. Firm settings (Settings > Firm profile)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5974419377 2026-10-03T23:03:45Z

See the batch body in the comment above (cases 5174-5186): the Firm profile card only
(name, address, phone, email, website, timezone, client-facing language, currency, daily
agenda checkbox) plus matter prefix / next matter number, since the rest of `/settings`
(invoice template/logo, invoice numbering, surcharge, bank accounts, invoice
approval/interest, AI, CourtListener/LEDES) is parked under the standing exclusions.
Non-Latin text, an empty-name edge, an invalid timezone string, a duplicate save, an
invalid next-matter-number that must discard the whole submission, and a readonly-role
403 check on both GET and POST. No date-format setting exists in the Firm model, so that
part of the original backlog note (B2-3) was dropped rather than guessed at.

### S8. Importer at scale (contacts) on a clean firm
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5974624814 2026-10-03T23:40:00Z

See the batch body in the comment above (cases 5187-5199): a 2,000-row generic-CSV
contact import with embedded in-file duplicates, non-Latin scripts, a no-name/no-company
error row, an invalid-email warning row and an overlong name; preview's 200-row dry-run
sample versus the true total; driving the >100-row background job to completion;
verifying final counts, the failed-rows CSV, and that duplicates land as updates, not
new contacts; a readonly 403 check on the importer; the contacts.csv export round trip;
and a second identical run to confirm re-import doesn't double the client base.

### S9. Users at scale (Settings > Users, Offices, Audit)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5974996237 2026-10-04T00:29:07Z

Backlog item B2-5. See the batch body in the comment above (cases 5200-5213): a login
sanity check first (re-confirming owner login on qa2 after the `7c595c7` pin move, since
the S8 result flagged stored owner passwords appearing not to authenticate post-deploy),
creating a second office and 20 users spread across all four non-owner roles and both
offices, rate edits, office reassignment, a role change and its token-revocation path,
deactivate/reactivate at scale, duplicate-email and weak-password creation edges, the
owner self-deactivation guard, the office delete-guard while still in use, and the audit
log (filtered view and CSV export) covering all of it.

S9's result was 0 PASS / 1 FAIL / 13 BLOCKED: the bot's own login attempt in case 5200
failed, blocking everything after it. Verified from the server: the account is active and
a direct HTTP login with the password on file succeeds (302, live dashboard). Not a
product defect; the bot's own harness held a stale or wrong credential. None of
5201-5213's actual ground (offices, 20 users, rates, role change, deactivate/reactivate,
duplicate/weak-password edges, self-protection, delete-guard, audit log) got exercised, so
it is retried below as S10 rather than marked covered.

### S10. Users at scale, retry (Settings > Users, Offices, Audit)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5975193702 2026-10-04T00:51:00Z

Retry of B2-5/S9. See the batch body in the comment above (cases 5214-5227): same ground
as S9, cases renumbered, opening with a plain login re-check rather than one that burns the
whole batch BLOCKED a second time if it fails again.

### S11. Documents deep (folders, tags, versions, search, sharing, a closed matter)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5975629917 2026-10-04T02:05:00Z

B2-6. Written by the coordinator since the queue was empty. Covers nested folders, tag
dedup, an overlong folder value, Greek folder/tag/search text (including an ASCII-only
case-folding edge on the Greek search, not treated as a bug), multi-word search AND logic,
new-version upload, a version delete-then-reupload (undo/redo), bulk move+tag on several
documents at once, bulk with nothing ticked, share/unshare on several documents checked
against the client portal, and a closed matter's documents (read access plus a direct
upload that bypasses the UI's closed-matter dropdown filter). All fixtures created fresh
and named `QA2 Docs ... 20261003` / `QA2-*.txt`, cleaned up at the end. Case body is in the
comment this status line is updated to point at.

### S12. Intake and leads (sign-off)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5975904828 2026-10-04T02:41:00Z

Not a backlog item. `docs/QA-HANDOFF.md`'s "Sign-off batches" section lists Intake and
leads as the one Phase 1 tool for #89 still without its sign-off batch, reopened by the
`7acb3a4` stale-decline fix, with the regression batch planned in
`docs/PHASE1-READINESS.md`. See the batch body in the comment above (cases 5257-5271):
normal decline/status/stage controls and undo-redo, a conflict-free conversion, the stale
converted-decline/status/stage guard (the regression itself), a duplicate-name conflict hit
refused then waived, linked-ID and audit-trail invariants on the conversion, a paralegal
decline (allowed) and a billing decline (403 refused), and non-Latin/overlong submit and
decline text.

### S13. Voice line (sign-off)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5976202113 2026-10-04T03:33:00Z

Not a backlog item by name, but B2-1 and B2-3 both left "Voice line" explicitly open, and
no batch on either bot has touched it. Picked since Bot 2's backlog and sign-off outline
(Intake) are both otherwise used up and no code under `app/` changed since S12's pin
(`7c595c7`). See the batch body in the comment above (cases 5272-5286): `/settings/voice`
baseline and configure, the test-call box's bad-input and Twilio-unconfigured paths, a
Voice-scoped API token from the owner and from a disposable paralegal, billing refused the
token page entirely, `/api/v1/voice/config`/`lookup`/`verify` over the bearer API including
a name-mismatch refusal and a built-live non-match, the PIN lockout and success path, a
Greek dictated note and a rounded phone time entry, the never-PIN-verified guard, and
cleanup restoring the voice line back off. qa2 has no Twilio keys, so no real call is ever
placed.

### S14. Settings > Tools deeper, part 3: Signatures, Conflict check and Engagement letters
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5976495094 2026-10-04T04:15:51Z

Continues B2-1's still-open note (Signatures, Conflict check and Engagement letters, left
over from S5). See the batch body in the comment above (cases 5287-5296): the 5287
baseline including a read-only note on the case-type tools and the whole Money section
(both still left open after this), Conflict check switched off and on alone with the
contact page's button and a non-owner role check, Signatures and Engagement letters
switched off and on together, a non-Latin-named signing link proving the already-sent-link
exception survives the tool being off, the `tools_changed` audit trail, and cleanup.

S14's result was 7 PASS / 3 FAIL, all three real (filed by the bot as #103, #104, #105):
`contacts/detail.html`'s Conflict check button and `documents/index.html`'s Request
signature button are not gated by `tool_on()`, unlike the sidebar/tab/route guards, and
signature send on qa2 flashes a delivery failure while the mail still reaches `/dev/outbox`.

### S15. Settings > Tools deeper, part 4: Personal injury, Criminal defense and Discovery
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5976688768 2026-10-04T04:46:00Z

Continues B2-1's last open item besides Money (deferred, too close to the parked
invoicing/payments/trust exclusions). See the batch body in the comment above (cases
5297-5306): the sidebar/dashboard/route guards for Personal injury, Criminal defense and
Discovery switched off alone and together, a non-owner role check, and a direct look at
`app/templates/matters/detail.html`'s matter-overview action bar, which read of the code
showed is not gated by `tool_on()` for Personal injury, Criminal defense, Discovery,
Depositions or Voice calls, the same class of gap as #103/#104 on different pages. The
batch asks the bot to confirm rather than refile a near-duplicate if it is the same pattern.

### S16. Session cookie invalidation (#101) and Settings > Tools button guards (#103, #104), retested on qa2
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5976933410 2026-10-04T05:28:29Z

No code under `app/` changed since S15's pin (`f72353c`). Of the open, unverified
`qa:fixed` issues (#91, #101, #103, #104), all filed by Bot 2, three can be retested
without touching the deferred Money section; #91 needs Invoices switched off to
reproduce, so it stays with Ian. See the batch body in the comment above (cases
5307-5320): a session cookie copied before logout then refused after it (#101), a
double-logout edge, three simultaneous copies invalidated by one logout, a second role
run through the same check, Conflict check's button hidden and restored on a contact
page (#103), Signatures' Request signature button hidden and restored on a document row
(#104), the `tools_changed` audit trail, cleanup, and a note that #91 was skipped this
batch.

### S17. Engagement letters, the Spanish sign flow (B2-2, engagement-letter half)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5977215591 2026-10-04T06:09:00Z

Bot 2's full backlog (B2-1 through B2-6) is used up and no code under `app/` changed
since S16's pin (`b687b0f`), so this closes B2-2's still-open note on engagement-letter
and document e-signature Spanish strings, engagement-letter half only. See the batch
body in the comment above (cases 5321-5332): a Spanish-language client and matter, a
sent engagement letter with its sign page's labels confirmed Spanish, an empty-input
edge expected to surface a hardcoded English validation string against a Spanish page,
an overlong-input edge expected to surface the one validation string on that route that
is localized, a non-Latin decline reason and the Spanish declined page, a duplicate
reload of a declined link, a second letter's reminder and signed-copy emails read from
`/dev/outbox` and compared against `engagements.py`'s `send_engagement`,
`send_engagement_reminder` and `_email_signed_copies` (none call `t()`/`lang_for()`), a
non-Latin signer name, a second-role read confirming the firm side stays English, and
cleanup. Document e-signature's half stays open: #105 (open, `qa:needs-ian`) means a
signature request with an email on file never leaves draft when SMTP is unset, so its
sign page cannot be reached live on qa2 to run the same comparison.

### S18. Settings > Integrations (closing B2-3's still-open note)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5977411572 2026-10-04T06:40:00Z

Bot 2's backlog had nothing queued, so this batch comes from the first still-open backlog
item in order: B2-3's "Settings > Integrations" note. See the batch body in the comment
above (cases 5333-5345): baseline reads of the integrations cards and the firm settings
form's CourtListener token field, setting that token and reading the card flip to
"configured", an overlong-value edge and a non-Latin-value edge on the same field, a
second role (a QA attorney) refused both `/settings/integrations` and `/settings`, the
dev-outbox link and webhook URLs checked against the page's own public intake URL, the
AI workbench (Mike) card confirmed off, cleanup back to baseline, and an audit-log and
retained-fixture check. Still open after this: B2-1's Money section (deliberately left
for Ian) and B2-4's other importers (matters/activities/bills/trust/tasks/calendar/notes,
the documents ZIP importer, resuming an interrupted job).

### S19. Importer deep (qa2): Matters, Calendar, Notes, and the background-job cursor
### (B2-4, part 1)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5977601049 2026-10-04T07:12:34Z

B2-3 and B2-2 are both closed now, so this moves to B2-4, the importer, which had only
its contacts entity (S8) exercised so far. See the batch body in the comment above (cases
5346-5355): a baseline read of every entity listed, a small Matters import with a
non-Latin name and a no-name error row, a duplicate re-run landing as updates not new
matters, a Calendar import linked to one of those matters with a missing-start-date error
row, a Notes import with a non-Latin body, a 110-row Matters import that crosses the
`CSV_BATCH_ROWS=100` background-job threshold, continuing that job once, reopening its
page fresh to confirm the cursor survived (standing in for "interrupted mid-batch") and
driving it to completion, cleanup of what has a delete/close action, and what remains.
Still open after this: the activities (time/expense) importer, the documents ZIP
importer, and the bills/trust importers (left for Ian, per the standing exclusions).

### S20. Retest issue #107: engagement-letter emails and sign() validation errors, Spanish contact
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5977783667 2026-10-04T07:38:00Z

Bot 2's backlog is fully used up again and `git log 8e8ed20..HEAD -- app` is empty, so no
code changed since S19's pin either. This retests #107 (`qa:fixed`, fixed in `8e8ed20`,
never retested): `send_engagement`, `send_engagement_reminder` and the client half of
`_email_signed_copies` in `app/blueprints/engagements.py` now route through new
`email.engagement_request.*` / `email.engagement_reminder.*` / `email.engagement_signed.*`
keys in `app/i18n.py`, and the two `sign()` validation branches (empty name, agree unticked)
now call the existing `sign.err_name` / `sign.err_agree_letter` keys instead of hardcoded
English, so all of it should now be Spanish for a Spanish-language contact, matching the
sign page's labels, which were already correct. Create only records named `QA2 Retest ES
20261004`. Do not touch the retained fixtures (contacts 5, 6, 7; matters 6, 7, 8 closed,
13, 14 open, 15 closed, 16; conflicts 4, 5; signature 1 draft; doc 4; contacts 1968, 1969,
1970, 1972, 1973; matter 17/M-1017 closed; engagements 1 declined, 2 signed; users 10, 11,
34-37 inactive; leads 33-37).

1. New client contact `QA2 Retest ES 20261004` with `language` set to Spanish and an email
   address, and a new matter `QA2 Retest Matter 20261004` for that contact, office none, no
   template. Expect `Matter M-.... opened.` Record both IDs.
2. Open `/engagements/new?matter_id=<id>` with the default template and the default scope
   text, then submit with `action=send`. Expect `Engagement letter sent to
   qa2-retest-es-20261004@example.test.` (or whatever delivery status actually shows; report
   it exactly if it differs). Record the engagement id.
3. Open `/dev/outbox` and read that email. Report its exact subject and opening line. Expect
   both in Spanish, not the English `Hello QA2 Retest ES,` from before the fix.
4. Open the sign link from that email (do not paste it). Confirm the page's labels are
   Spanish (already known correct; this just proves no regression).
5. Submit the sign form with an empty name and the agree box unticked. Report the exact
   error text and its language. Expect Spanish, not the English `Type your full name and
   tick the box to confirm you agree.` from before the fix.
6. Submit again with a name typed but the agree box still unticked. Report the exact error
   text. Expect Spanish.
7. Sign properly: type the name `QA2 Retest Cliente Muñoz 20261004` (non-Latin diacritics),
   tick the box, submit. Expect a Spanish signed-confirmation page.
8. Open `/dev/outbox` again for the signed-copy email. Report its exact subject and opening
   line. Expect Spanish for the client-facing copy. If a separate firm-side notification
   email appears in the same outbox, report whether it stayed English (by design, not a
   defect either way).
9. New matter `QA2 Retest Matter B 20261004` for the same contact, a second engagement letter
   sent on it (`action=send`), then POST its `/remind`. Expect `Reminder sent.` Open
   `/dev/outbox` for the reminder email and report its exact subject and opening line. Expect
   Spanish, not the English `Reminder: Engagement letter: ...` / `Hello ...,` from before.
10. Try to void the signed letter from case 7. Expect `A signed letter cannot be voided.`
11. Void the still-open (sent, not signed) letter from case 9 instead. Expect `Letter
    voided.`
12. Close both matters (`QA2 Retest Matter 20261004` and `QA2 Retest Matter B 20261004`).
13. Report everything created: the contact id, both matter ids and numbers, both engagement
    ids and their final statuses (signed / void), and confirm the three email subjects/
    openings recorded in cases 3, 8 and 9 were all Spanish. Report what remains open for Bot
    2: document e-signature's Spanish half of B2-2 is still blocked on #105 (`qa:needs-ian`);
    nothing else is open in the backlog besides the Money section and the importers
    deliberately left for Ian.

### S21. Importer deep (qa2): Activities (time/expense) import, closing B2-4
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5977966093 2026-10-04T07:59:00Z

Bot 2's queue was empty again with nothing changed since S20's pin, so this closes the
last open piece of B2-4: the activities (time/expense) importer, the only importer entity
in the backlog not reserved for Ian. See the batch body in the comment above (cases
5369-5382): a baseline read of the Activities entity's guide text, a new QA2 contact and
matter, a 5-row CSV (a non-Latin time entry with an overlong task code to check
truncation, an expense that falls back to its category label, a blank-date error row, a
nonexistent-matter error row, and a billed-flag row that forces billable off and prefixes
the description), two duplicate re-runs (update, then skip), a required-field guard with
`date` left unmapped, a temporary billing-role user proving `/import` is owner-only
(403), cleanup of everything created with a delete/close action, and what remains.

### S22. Tasks deep pass (qa2): creation, filters, done/reopen, the open-redirect guard, and the billing/readonly guard
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5978171301 2026-10-04T08:34:00Z

Bot 2's full backlog (B2-1 through B2-6) is used up, `git log 11fb356..HEAD -- app` is empty
(no code drift to regression-test), and the pool of previously-filed-but-unretested
`qa:fixed` defects on #89 is empty too (#101/#103/#104 already retested clean in S16; #91
stays deferred for Ian). So this picks an area never given its own deep pass on qa2:
`/tasks`, touched so far only as an HTTP-status row in S4's role matrix. See the batch body
in the comment above (cases 5383-5396): baseline group/SOL/rule-task counts, creating a
task, an empty-title refusal, an overlong-plus-non-Latin title and notes, editing, marking
done and reopening, filtering by kind/priority/assignee, the `next=` open-redirect guard, a
court-date task tied to one of the retained open matters (13/14/16), deleting it, a
temporary billing user refused the POST and a temporary readonly user getting the identical
refusal, cleanup, and what remains. Mirrors Bot 1's R22 on a different firm/fixtures.

### S23. Messages deep pass (qa2): SMS/email refusal chains, non-Latin send, matter tagging, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5978393235 2026-10-04T09:10:05Z

Bot 2's full backlog (B2-1 through B2-6) is used up, no code under `app/` changed since
S22's pin (`1262707`), and the `qa:fixed` retest pool is empty too, so this picks up the one
area never given its own deep pass on qa2: `/messages`, previously only probed for HTTP
status in S1/S4's role sweeps. Mirrors Bot 1's R16 on a different firm/fixtures, adapted for
qa2 having no SMTP (every email case lands on one deterministic flash into `/dev/outbox`
instead of testfirm's two-sided outcome) and no Twilio (no case completes a real SMS send
either way). See the batch body in the comment above (cases 5397-5409): the SMS and email
refusal chains stopping before any real send, a non-Latin reply landing in `/dev/outbox`,
subject truncation at 300 characters, matter-tagging onto the Activity tab (the #102 fix),
a portal reply with and without a client email on file, and the paralegal/billing/readonly
role matrix read exactly from `app/permissions.py`.

### S24. Calendar deep pass (qa2): recurrence, DST edges, the ICS feed, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5978595090 2026-10-04T09:39:00Z

Bot 2's full backlog and sign-off outline are both used up, and no code under `app/`
changed since S23's pin, so this picks the one area never given its own batch on qa2:
`/calendar`, previously only probed for HTTP status in S4's role sweep. Mirrors Bot 1's
R12 sign-off on a different firm/fixtures. See the batch body in the comment above (cases
5410-5424): a baseline grid read, a timed event created and its time edited (checked
against the ICS feed), an all-day event on a month's last day, a monthly-repeat series
from Jan 31 through Jun 30, a weekly series spanning Chicago's March 2027 spring-forward,
the empty-title refusal versus the end-before-start silent correction, a non-Latin title,
a rule-set deadline with a weekend roll-forward, a task done/reopen round trip, a second
role (paralegal), deleting the recurring series, cleanup, and what remains.

### S25. Conflict check deep pass (qa2): fuzzy matching, accents, content-only matches, the resolve/waive workflow, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5978839308 2026-10-04T09:56:00Z

Bot 2's full backlog and sign-off outline are both used up, and no code under `app/`
changed since S24's pin, so this picks the one area never given its own functional batch
on qa2: conflict check has only ever been toggled on/off in Settings > Tools (S14, S16),
never run as a tool itself. Mirrors Bot 1's R13 sign-off and R19 phase-2 edges on a
different firm/fixtures. See the batch body in the comment above (cases 5425-5438): a
baseline history read, an exact-name self-hit, a matter-party hit with its role label,
a dual-role name not deduped across a contact and a party, case/whitespace folding, a
content field (a note) that never fuzzy-matches despite high token overlap, a suffix
fuzzy hit capped at 99, Latin-diacritic folding versus no Cyrillic transliteration, the
empty-input and all-punctuation refusals, the resolve/waive workflow's three flashes, a
no-match control built live, a second and third role (paralegal allowed, billing and
readonly refused on the write route), cleanup, and what remains.

### S26. Matters deep pass (qa2): core CRUD, custom fields, parties, milestones, notes, close/reopen, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5979127321 2026-10-04T10:39:00Z

Bot 2's backlog is used up again and no code under `app/` changed since S25's pin, so
this picks `/matters` itself, the hub blueprint, which has never had its own deep pass on
either firm (S8/S19 only exercised it under the importer, R6 only touched matter
templates, S25/R19 only used it as a conflict-check party source). See the batch body in
the comment above (cases 5439-5452): a baseline count by status, the client/name refusals,
a full create with a custom field and an hourly rate, an edit adding a non-Latin custom
field, an overlong name (SQLite does not enforce the `String(300)` limit), parties
including the `co_counsel` label rendering, the party-name refusal, two milestones added
and one deleted, the milestone-description refusal, a note added and an empty one
refused, close then reopen, the paralegal/billing/readonly role matrix, cleanup, and what
remains. Money- and trust-adjacent matter fields (currency, evergreen trust
minimum/replenish-to, auto-invoice, split-billing payers) stayed untouched per the
standing exclusions.

### S27. Case audit deep pass (qa2): the rule engine, the finding workflow, rescoring, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5979438073 2026-10-04T11:26:00Z

Bot 2's backlog is used up again and no code under `app/` changed since S26's pin, so this
picks `/audit` (Case audit), which has never had its own batch on either firm. It is a
distinct tool from the parked AI assistant (its own `case_audit` switch in `app/tools.py`,
separate from `ai`/"Ask Coil"), and qa2 holds no AI key, so every finding this batch
produces comes from the deterministic rule engine, never the AI-origin rules. See the
batch body in the comment above (cases 5453-5465): a baseline read, creating a PI matter
with a near statute-of-limitations date and starting its PI case, running the audit and
confirming the `sol_near` finding's exact message, dismiss then reopen (undo/redo), the
paralegal/billing/readonly role matrix on the finding routes and the owner-only `/run`
route, adding a deadline task and confirming the finding resolves and stays resolved
(suppressed) on the next run, rescoring with and without the AI refine flag (confirmed
rules-only since qa2 holds no AI key), 404 guards, a second matter stale past the
30-day activity window to trigger the `no_activity` rule, cleanup, and what remains. The
PI-specific provider/lien/demand/imaging rules and the AI-origin findings are left open
for a follow-up batch, needing medical-provider/lien/chronology fixtures this one does
not build.

### S28. Case audit deep pass, part 2 (qa2): the PI-specific provider, lien, demand and
### imaging rules
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5979582577 2026-10-04T11:44:52Z

S27's follow-up: builds a PI matter with medical providers, a lien and chronology entries
to exercise every rule in `_pi_rules()` (`missing_records` at both severities,
`bills_missing`, `treatment_gap`, `imaging_not_obtained`, `lien_no_contact`,
`demand_unanswered`, `limits_unknown`), plus one role/undo-redo case. AI-origin findings
stay untested on qa2 by design (no AI key).

### S29. Time and expenses deep pass (qa2): the timer lifecycle, expenses with receipts,
### editing/deleting, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5979694863 2026-10-04T11:59:00Z

Bot 2's backlog and both case-audit follow-ups (S27, S28) are used up, and no code under
`app/` changed since S28's pin. `/time` has never had its own batch on qa2: testfirm
covered it in R7/R15, but qa2's only contact with it was incidental, inside S4's
role-matrix sweep. See the batch body in the comment above (cases 5481-5494): a baseline
read, a fresh QA2 matter, a logged entry with Greek description text, the matter/duration/
zero-duration refusals, the over-a-day confirm step, edit and delete, the full timer
lifecycle (start, the already-running guard, pause/resume, stop with its rounding), two
expenses including a receipted one, the zero-amount and negative-amount refusals, edit and
delete, and the paralegal/billing/readonly role matrix. The invoice-lock guard on editing
or deleting a billed entry/expense is left untested here, since exercising it means
creating an invoice, inside the standing Money-section exclusion; R7/R15 already cover it
on testfirm.

### S30. Research, reports and exports deep pass (qa2): case law search and saved
### authorities, the citation check, every /reports page, and the three non-money /exports
### downloads
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5979892396 2026-10-04T12:24:00Z

Bot 2's backlog, both case-audit follow-ups and S29 are all used up, and no code under
`app/` changed since S29's pin. Research, together with reports and exports, had never had
its own batch on qa2, only a GET-status table inside S4's role sweep. See the batch body in
the comment above (cases 5495-5508): a baseline read, a fresh QA2 matter, a case-law search
and save, a Spanish-language note on the saved authority, a research-memo export, the
cite-check empty-input refusal, a real citation check with its `[internal]` note, the
paralegal/billing/readonly role matrix on `/research`, every page under `/reports`, the
three non-money `/exports` downloads (contacts/matters/time), and a role matrix on
`/reports` versus `/exports` that confirms attorney and readonly can read reports but not
exports. LEDES, the QuickBooks invoice/payment exports and `trust.csv` stay inside the
standing Money/trust exclusion and were not touched.

### S31. Contacts deep pass (qa2): full CRUD, custom fields, search, the delete guard, and
### the billing/readonly guard
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5980152930 2026-10-04T12:51:00Z

Bot 2's backlog (B2-1 through B2-6) and S30 are all used up, and no code under `app/`
changed since S30's pin. Contacts had never had its own deep pass on qa2, only CSV-import
load in S8. See the batch body in the comment above (cases 5509-5521): full CRUD with
custom fields and aliases, the empty-name refusal, an overlong non-Latin name, the
`?only=clients` filter, search matching on aliases, notes, the delete guard on a contact
with a matter versus a successful delete on one without, and the paralegal/billing/readonly
role matrix. Mirrors Bot 1's R26 on testfirm, same commit.

### S32. Retest #109 (conflict-check fuzzy matching, shared boilerplate tokens)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5980432017 2026-10-04T13:24:00Z

Not a backlog item. Issue #109, filed from this bot's own S25 conflict-check deep pass,
was fixed in `1b1b954` (already S31's pin) and never retested. See the batch body in the
comment above (cases 5522-5530): re-runs #109's four exact queries against the same S25
fixtures (Meridian Textiles, Dana Okafor, the no-match control, Harrison Boyle, Renée
Dupont, Чехов) confirming the false positives are gone, plus three regression guards
(the Jr/Sr subset fuzzy hit, accent folding, and a fresh one-letter-off typo) confirming
the fix did not also swallow genuine fuzzy matches, and a resolve/cleanup case.

### S33. Retest #107's subject-line fix (`1262707`) on qa2: Spanish contact send/reminder/sign subjects
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5980705359 2026-10-04T13:49:00Z

Not a backlog item. Issue #107's final fix (`1262707`) carried its own re-test instruction
("Re-test on qa2 with a Spanish contact's default-titled engagement letter...") that was
never followed up: S17/S20 tested #107 before that commit landed, and no later qa2 batch
exercised it, only adopted it as a pin. Bot 2's full backlog and every area already given
its own deep pass are used up, and `git log 1b1b954..HEAD -- app` is empty, so there was no
code drift to regression-test instead. See the batch body in the comment above (cases
5531-5541): a baseline read, a Spanish-language contact's default-subject send/reminder/sign
confirming the localized `Carta de contratación: .../Recordatorio: .../Firmado: ...`
subjects and the firm copy's deliberate English-only `Signed: Engagement letter: ...`, a
second matter on the same contact with a staff-customized subject confirming it still
bypasses localization on send and reminder, an English-contact control confirming the fix
is per-contact rather than firm-wide, the billing role refused `POST /engagements/new`, a
void cleanup, and a final ids/retained-list case.

### S34. Retest #91's fix (Settings > Tools "still off" dependency notice) on qa2
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5980968707 2026-10-04T14:16:00Z

Not a backlog item. #91 (`QA2: Time suggestions off-flash also names Payments and Plans`)
is labeled `qa:fixed` but never `qa:verified`, and is the only open, on-topic, unblocked
item for qa2: Bot 2's full backlog is used up, `git log 1b1b954..HEAD -- app` is empty, and
the Money section, document e-signature's Spanish strings (#105) and the ZIP/bills/trust
importers are all parked or blocked on Ian. See the batch body in the comment above (cases
5542-5552): a baseline read of every tool's tick state, unticking Invoices alone to
legitimately hold Payments and Plans off, then the #91 repro itself, unticking Time
suggestions on a later unrelated save and expecting the flash to name only Time
suggestions, a 404 check, a duplicate-submission edge expecting `No change.`, an
undo/redo edge turning Time suggestions back on, restoring Invoices and expecting Payments
and Plans to come back in the same flash, a `/payments`/`/money` sanity check, an audit-log
check, a non-owner 403 check, and a final state-matches-baseline case.

### S35. Retest four already-fixed defects (matter edit validation, blank contact fields, long document names, lead audit log) on qa2
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5981217298 2026-10-04T14:46:00Z

Not a backlog item. Bot 2's full backlog and sign-off outline are both used up, there is no
code drift since S34's pin, and the `qa:fixed`-but-unverified pool on #89 is now empty
(#91 closed out in S34; #101/#103/#104 already clean since S16). So this mirrors Bot 1's
R18 on qa2's own firm and data: four already-`qa:fixed` defects that were only ever
retested on testfirm, never on qa2. See the batch body in the comment above (cases
5553-5564): a matter edit with no client selected and with a blank name (#96), a real save
to confirm no corruption, a contact created with blank email/phone/address (#92), the
Send-text button's phone gate, a 223-byte and a 320-byte document filename (#87), a lead's
status and fields changed and audited including an undo (#95), a decline as the audit
control, cleanup, and what remains.

### S36. Engagement letters deep pass (qa2): full lifecycle, sign-page validation, duplicate-sign guard, decline flow, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5981765316 2026-10-04T15:39:00Z

Not a backlog item. Bot 2's full backlog (B2-1 through B2-6) is used up and everything each
one left "still open" is either the parked Money section or blocked on Ian (#105); the
`qa:fixed`-but-unverified pool on #89 is empty (S32-S35 cleared it); and `git diff
1b1b954..HEAD` is empty, so there was no code drift to regression-test. Engagement letters
had only had visibility/localization coverage (S14, S17), never a full functional deep pass
the way Tasks/Calendar/Conflict check/Matters got. Read `app/blueprints/engagements.py` in
full (`new`/`send`/`remind`/`void`/`sign`/`decline`, every flash and the three `sign()`
validation branches) and `app/permissions.py` (`/engagements` sits in the case-work prefix
group mapped to `matters`; owner/attorney/paralegal hold it, billing/readonly are view-only
and get a 403 on any write). Every expected flash/error below was read from the code and
`app/i18n.py` at this pin, quoted exactly. See the batch body in the comment above (cases
5565-5579): a contact and matter created, an engagement drafted then sent then resent then
reminded, the public sign page's three validation errors (empty name, Greek name without
agreeing, a 201-character name), a Greek-named signature that succeeds, a duplicate-sign
visit that changes nothing, a void-after-signed refusal, a second engagement used for the
readonly role's void refusal and a decline/double-decline check, cleanup, and what remains.

### S37. Criminal defense and Discovery deep pass (qa2): case facts, charges, court-chain
### and speedy-trial deadlines, a discovery set we propound, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5982205340 2026-10-04T16:36:00Z

Not a backlog item. Bot 2's full backlog (B2-1 through B2-6), the Users/offices sign-off
(S10) and the Intake sign-off (S12) are all done; `/health` is unchanged since S36's pin and
`git log 1b1b954..HEAD -- app` is empty, so there was no code drift to regression-test.
Criminal defense and Discovery had only ever had the tool-visibility gate checked on qa2
(S15) plus bot 1's own recertification on testfirm (R2), never a full functional pass on
qa2 the way Tasks/Calendar/Conflict check/Matters/Engagement letters got. Read
`app/blueprints/criminal.py` in full and `app/blueprints/discovery.py`'s non-AI routes
(`tailor`/`draft` stay excluded, standing AI exclusion) and `app/permissions.py`. Every
expected flash/error was read from the code at this pin, quoted exactly. See the batch body
in the comment above (cases 5580-5594): a contact and matter opened, a criminal case
started, the court-chain action refused before a setting date then run twice (success then
duplicate), an empty and a 310-character charge description (truncation edge), case facts
saved with a Greek prosecutor name, the speedy-trial deadline run twice (success then
duplicate), the disposition PDF, a discovery set we propound from the general starter set,
a hand-typed Greek item added, a "respond" set refused with no source document, its
deadline task run twice (success then duplicate), its PDF export, a readonly-role refusal
on the speedy-trial action, cleanup, and what remains.

### S38. Client portal deep pass (qa2): the sign-in link's rate limit and
### replace-invalidates-pending behavior, single-use tokens, messages threading, and upload
### validation edges
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5982444110 2026-10-04T17:07:00Z

Not a backlog item. Bot 2's full backlog, the Users/offices and Intake sign-offs, and the
Criminal defense/Discovery deep pass (S37) are all done; `/health` is unchanged since S37's
pin and `git log 1b1b954..HEAD -- app` is empty, so there was no code drift to
regression-test. The client portal (`app/blueprints/portal.py`) had only ever had its
Spanish strings checked (S6, S17) and the cross-client/role security sweep run against it
(S1), never a functional deep pass on its own mechanics. Read `app/blueprints/portal.py` in
full and the `portal.*` strings in `app/i18n.py`. See the batch body in the comment above
(cases 5595-5609): a client contact and two matters (one closed), a shared and an unshared
document, the sign-in link requested four times in a row to exercise the 15-minute/3-request
rate limit and the replace-invalidates-pending-token behavior, single-use token reuse after
logout, the not-shared download guard on one's own document, a Greek general message, an
empty-body message, a matter-tied message's thread filter, an empty-file/blocked-extension/
non-Latin upload sequence, and a close/report case.

### S39. API tokens and webhooks deep pass (qa2): full vs redacted confidentiality, scope
### limits, leads idempotency, and webhook delivery/refusal edges
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5982775492 2026-10-04T17:53:00Z

Not a backlog item. Bot 2's backlog and sign-off outline are both used up again, and
`git log 1b1b954..HEAD -- app` is still empty, so no regression batch was possible either.
Mirroring Bot 1's R34 on testfirm: `/settings/api` and `/settings/webhooks` on qa2 have only
ever had S2's light security-sweep pass (an owner token created/revoked, a readonly 403) and
one scoped-token case from an earlier Settings > Tools batch (a Voice-only token, a
billing-role 403), never a full confidentiality-mode and webhook-delivery deep pass. Read
`app/blueprints/api.py` in full (scopes, confidentiality redaction, the leads idempotency
key, the notes/calendar validation) and `app/blueprints/webhooks_out.py` (event names, the
private-address and scheme refusals) at this pin; every expected message is quoted from the
code. See the batch body in the comment above (cases 5610-5624): a full-scope/full-
confidentiality token, a full-scope/redacted token, an overlong token-name truncation check,
a scope-limited token, the missing-header and malformed-token 401s, the redacted-vs-full
split on `/api/v1/me`, `/api/v1/contacts`, `/api/v1/matters` and `/api/v1/notes`, a
scope-missing 403 on `/api/v1/calendar`, a non-Latin/idempotent `/api/v1/leads` POST, a
webhook that only fires on its subscribed event, the private-address and bad-scheme webhook
refusals, and cleanup. Invoice scopes and webhook events stayed excluded as money-adjacent.

### S40. Settings > Templates role-matrix deep pass (qa2): matter templates (owner-gated), document templates (documents-gated), and engagement letter templates (matters-gated)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5983005518 2026-10-04T18:21:00Z

Not a backlog item. Bot 2's backlog is fully used up and `git log 1b1b954..HEAD -- app` is
still empty. The three places a template lives sit behind three different permission areas
in `app/permissions.py` (`settings` for matter templates, `documents` for document
templates, `matters` for engagement letter templates), which gives each role a different
boundary that neither bot had checked directly. See the batch body in the comment above
(cases 5625-5637): one template of each kind created by owner, attorney and paralegal
confirmed able to write document and engagement templates but refused on matter templates,
billing refused document templates entirely (no documents permission at all) but allowed to
read the other two, readonly able to read all three but write none, a non-Latin merge-field
letter generation, applying the matter template, and cleanup.

### S41. Personal injury deep pass (qa2): providers, liens, medical chronology entries, the demand package, the standard-task statute-of-limitations leap-day fallback, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5983326728 2026-10-04T19:00:00Z

Not a backlog item. Bot 2's full backlog, the Users/offices and Intake sign-offs are all
done, `/health` was unchanged since S40's pin, and `git log 1b1b954..HEAD -- app` is empty,
so there was no code drift to regression-test. Personal injury (`app/blueprints/pi.py` and
the manual, non-AI routes of `app/blueprints/records.py`) had never had a functional pass
on qa2, only the tool-visibility gate (S15); Bot 1 gave it one on testfirm in R33, but that
firm and its fixtures are separate. Read `app/blueprints/pi.py` in full, the chronology
routes in `app/blueprints/records.py`, and `app/permissions.py`. See the batch body in the
comment above (cases 5638-5651): a PI case auto-started from a fresh matter, case facts
saved with a Feb 29 2024 date of loss and Greek liability notes, the empty-name provider
refusal then two providers (one Greek), a records-request letter advancing the stage, a
chronology entry round trip (add, the blank-entry refusal, confirm, recalc-specials,
confirm-all's zero-unconfirmed edge, link/unlink, delete), the empty-holder lien refusal
then a lien, an out-of-range and then a valid reduction-letter percentage, the
already-agreed-figure branch overriding the percentage box, the empty-amount demand-package
refusal then a demand and a sent package, the standard-task statute-of-limitations
leap-day fallback and its duplicate-run guard, the role matrix (billing and readonly refused
the exact 403 text), close-out, and what remains. The settlement worksheet and every
AI-touching route (`extract`, `overview`, `demand-draft`) stayed excluded.

### S42. Dashboard deep pass (qa2): card customization, the permission-gated card set, tool-off hiding, and the order/reset flow
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5983622096 2026-10-04T19:28:00Z

Not a backlog item. Bot 2's full backlog, the Users/offices and Intake sign-offs, and
S41's personal injury pass are all done; `/health` is unchanged since S41's pin and
`git log 1b1b954..HEAD -- app` is still empty, so there is no code drift to regression-test.
The dashboard (`app/blueprints/dashboard.py`) has never had its own pass on either bot: every
sign-off and sweep so far opened `/dashboard` only incidentally, as a login landing page.
Read `app/blueprints/dashboard.py` in full (the `CARDS`/`CARD_PERMISSIONS`/`CARD_TOOLS`
tables and the `customize` route) and `app/permissions.py`'s role matrix before writing a
single expectation. Every flash below was read from the code at this pin and is quoted
exactly. Money-card content itself (the actual A/R, WIP and trust figures) is read-only
background on this pass, not the point of it; do not open `/invoices`, `/payments`,
`/trust` or `/accounting` or change anything there. Do not touch the Money section of
Settings > Tools (Invoices, Statements, Payments, Plans, Trust, Accounting, Reports) —
that toggle stays parked for Ian, same as B2-1.

1. As owner, open `/dashboard/customize`. Expect all 16 cards listed as available rows
   (`open_matters`, `ar`, `wip`, `trust`, `my_hours_week`, `pending_approvals`, `tasks`,
   `deadlines`, `leads`, `engagements`, `overdue`, `evergreen`, `unsigned_documents`,
   `portal_messages`, `recent_matters`, `case_audit`), the default 12 pre-checked and the
   other 4 (`my_hours_week`, `pending_approvals`, `evergreen`, `unsigned_documents`,
   `portal_messages` — report the exact set) unchecked. Record which ones start checked.

2. Submit the customize form with every card unchecked. Expect `Pick at least one card.`
   and the dashboard's own saved selection unchanged (reload `/dashboard` and confirm the
   default cards are still the ones showing, not zero).

3. Submit the form picking exactly three cards (`open_matters`, `tasks`, `case_audit`) with
   their order fields set in reverse (`case_audit`=1, `tasks`=2, `open_matters`=3). Expect
   `Dashboard saved with 3 cards.` Open `/dashboard` and confirm exactly those three cards
   render, in the order Case audit, Tasks, Open matters (the order field drives the sort,
   not the table's natural order).

4. On the same page, submit a POST with one more card added (`leads`) but its order field
   left as a non-numeric string (`abc`). Expect the save to succeed (`Dashboard saved with
   4 cards.`, no 500) with `leads` sorted last (the code's `except ValueError: pos = 1000`
   fallback).

5. Click reset. Expect `Dashboard reset to the default cards.` and `/dashboard` back to
   showing exactly `DEFAULT_CARDS` (`open_matters`, `ar`, `wip`, `trust`, `tasks`,
   `deadlines`, `leads`, `engagements`, `overdue`, `recent_matters`, `my_hours_week`,
   `case_audit`), 12 cards, in that order.

6. Create one disposable user per role (paralegal, billing, readonly; attorney already
   covered implicitly by owner's superset in case 1) named `QA2 Dashboard <Role>
   20261004`. As **paralegal**, open `/dashboard/customize`. Expect the six money-gated
   cards (`ar`, `wip`, `trust`, `pending_approvals`, `overdue`, `evergreen`) absent from
   the row list entirely (paralegal holds no `billing` or `trust` permission), and the
   other 10 present. Open `/dashboard` with the default selection and confirm those same
   six cards do not render there either, with no error in their place.

7. As **billing**, open `/dashboard/customize`. Expect `unsigned_documents` and
   `portal_messages` absent (billing holds no `documents` or `messages` permission) and
   every money card (including `trust` and `evergreen`, which billing holds via `trust`)
   present. Confirm on `/dashboard` with the default selection.

8. As **readonly**, open `/dashboard/customize`. Expect `trust` and `evergreen` absent
   (readonly's view-only mirror of attorney excludes trust) but everything else, including
   `ar`/`wip`/`overdue`/`pending_approvals`/`unsigned_documents`/`portal_messages`,
   present. Confirm on `/dashboard`.

9. As paralegal, forge a direct POST to `/dashboard/customize` including a hidden
   `card_trust=on` field alongside an allowed card. Expect it silently ignored (trust is
   not in paralegal's `allowed` set, so the code never adds it) — the flash names only the
   allowed cards' count, and `trust` does not appear on the resulting `/dashboard`.

10. As owner, open Settings > Tools and switch off Signatures only (leave every other tool,
    including the whole Money section, exactly as it is now). Expect a flash starting
    `Switched off: Signatures. Everything in them is kept.` Open `/dashboard` as owner with
    `unsigned_documents` in the saved selection (re-pick it via customize if case 5's reset
    dropped a custom selection). Confirm the `unsigned_documents` card is gone even though
    it is still in the user's saved list. Switch Signatures back on. Expect a flash
    starting `Switched on: Signatures.` and confirm the card reappears.

11. Clean-up and what remains. Reset the owner's dashboard to defaults again (so it is not
    left on the case 3/4 custom pick), deactivate the three disposable role users from case
    6-8, and confirm Settings > Tools shows Signatures on and every other tool, especially
    the whole Money section, exactly as it was before case 10. Say what remains: the actual
    money-card figures (A/R, WIP, trust balance, overdue list) were not exercised for
    correctness, since that needs invoicing/trust fixtures and stays with that parked
    exclusion; do not touch the fixtures retained from S41 or earlier.

### S43. Criminal defense further checks (qa2): statutory maxima across charges, a plea to a lesser charge, the disposition PDF, and the billing role
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5984202646 2026-10-04T20:03:00Z

Not a backlog item. Bot 2's backlog (B2-1 through B2-6) is used up, and
`git log 1b1b954..HEAD -- app` is still empty, so there is no code drift to
regression-test. Issue #12's own "further checks" note under Criminal defense lists
"three charges with different statutory maximums" and "a disposition after a plea to a
lesser charge"; S37 ran only one charge on qa2 and never revisited it after a
disposition, so neither has been run on either firm. Read `app/blueprints/criminal.py`
in full at this pin (`_fill_charge`, `charge_new`/`charge_edit`/`charge_delete`,
`court_chain`, `speedy_trial`, `build_disposition_pdf`, `SPEEDY_TRIAL_NOTE`) and
confirmed the disposition PDF's table has only five columns (Statute, Charge, Degree,
Disposition, Sentence): `range_text` and `fine_max_cents` are captured on the charge but
never rendered anywhere. Every expected flash below was read from the code at this pin,
quoted exactly.

## Cases 5663 to 5676: Criminal defense further checks (qa2) — statutory maxima across charges, a plea to a lesser charge, the disposition PDF, and the billing role

1. Baseline: open `/criminal`. Report the total case count and how many sit in each
   stage column. Do not touch anything yet.

2. Act and check: create contact `QA2 Criminal2 Client 20261004`, email
   `qa2-crim2-20261004@coil.test`. Expect flash `Contact created.`

3. Act and check: open a new matter `QA2 Criminal2 Matter 20261004` for that contact,
   office none, no template. Expect a flash matching `Matter M-.... opened.` Record the
   id and number. `POST /criminal/start` with that matter id. Expect flash `Criminal case
   started on <the matter number>.`

4. Act and check, non-Latin: save the case facts: arrest date Aug 1 2026, stage
   `Charged`, court `QA2 Criminal2 County Court 20261004`, prosecutor `Εισαγγελέας
   Κωνσταντίνου 20261004`, notes `Υπόθεση δοκιμής 20261004`. Expect flash `Case facts
   saved.` Reload the case page and confirm the arrest date, stage and the Greek
   prosecutor name and notes all show back exactly.

5. Edge, refused: `POST` a new charge with description blank (everything else blank
   too). Expect flash exactly `Describe the charge.` and confirm no charge exists on the
   matter yet.

6. Act and check: add charge 1: statute `Tex. Penal Code §22.01(a)(1)`, description `QA2
   Criminal2 Assault causes bodily injury 20261004`, degree `Class A misdemeanor`, range
   `0-365 days county jail`, fine max `$4,000.00`, disposition `Pending`. Expect flash
   `Charge added.` Record its id.

7. Act and check, non-Latin: add charge 2: statute `Tex. Penal Code §30.02(c)(2)`,
   description `QA2 Criminal2 Burglary of a habitation 20261004`, degree `2nd degree
   felony`, range `2-20 years TDCJ`, fine max `$10,000.00`, enhancement `Προηγούμενη
   καταδίκη 20261004`, disposition `Pending`. Expect flash `Charge added.` Record its id.

8. Act and check: add charge 3: statute `Tex. Health & Safety Code §481.115(b)`,
   description `QA2 Criminal2 Possession of a controlled substance 20261004`, degree
   `State jail felony`, range `180 days-2 years state jail`, fine max `$10,000.00`,
   disposition `Pending`. Expect flash `Charge added.` Record its id.

9. Act and check: generate the disposition summary PDF with all three charges pending.
   Expect flash exactly `Disposition summary saved to the Criminal folder: Disposition
   summary <the matter number> <today, YYYY-MM-DD>.pdf.` Open the PDF and confirm its
   charges table lists all three rows (statute, description, degree, disposition
   `Pending`) in the order added. Confirm it has no column for the sentencing range or
   maximum fine typed into cases 6-8: both are stored on the charge but neither is
   rendered on this PDF or the case page. Not a bug; report it as confirmed-as-written,
   since `RANGE_NOTE` already tells the reader ranges are attorney-entered and not looked
   up anywhere. Record this document's id.

10. Act and check: edit charge 3 to a plea to a lesser charge: description `QA2
    Criminal2 Possession reduced to Class A 20261004`, degree `Class A misdemeanor` (down
    from State jail felony), disposition `Plea`, disposition date today, sentence `QA2
    Criminal2 180 days county jail, probated 20261004`. Expect flash `Charge saved.`

11. Act and check: generate a second disposition summary PDF. Confirm charge 3's row now
    reads disposition `Plea <today's date, MM/DD/YYYY>` with the updated description and
    degree (`Class A misdemeanor`), and that charges 1 and 2 are unchanged, still
    `Pending`. Record this second document's id.

12. Edge, overlong, then duplicate: add charge 4 with description set to `QA2 Criminal2
    Overlong 20261004 ` followed by the letter `Ω` repeated to roughly 310 characters.
    Expect flash `Charge added.` Open it and confirm the stored description is cut to
    exactly the first 300 characters, not 310. Then run the speedy-trial action. Expect
    flash exactly `Deadline added for Jan 28, 2027 (arrest + 180 days). Confirm the
    jurisdiction's rule.` and confirm the new task's notes contain the full tolling
    disclaimer verbatim: "Placeholder at arrest + 180 days, unadjusted for tolling. Coil
    does not model tolling periods (continuances, competency proceedings, interlocutory
    appeals, etc.), so any tolled time is not subtracted from this count. Confirm the
    jurisdiction's speedy-trial rule, any tolling that applies, and the charging
    limitations period for these charges; Coil does not ship statute tables." Run the
    same action again immediately. Expect flash exactly `That deadline already exists.`
    and confirm there is still only one such task on the matter.

13. Second role, act and check: reactivate user 42 (billing); expect `User saved.`
    Signed in as it, `GET /criminal/<the matter id>`: expect HTTP 200 (billing holds
    `matters_view`). `POST` the speedy-trial action again: expect HTTP 403, exactly `Your
    role (billing) cannot change matters and contacts. Ask the firm owner if you need
    that access.`, and confirm the matter still has exactly one speedy-trial deadline
    task, not a second. Deactivate user 42 again; expect `User saved.`

14. Clean up and what remains: delete charge 4 (the overlong one); expect flash `Charge
    removed.` Close the matter; expect a flash matching `<the matter number> closed.`
    Report every id created this batch: the contact, the matter and its number, the
    criminal case, charges 1-3 (charge 4 deleted), both disposition-summary document ids,
    and the speedy-trial deadline task id. Confirm user 42 is inactive again, and
    reconfirm the full retained list (contacts 5/6/7/1968-1992/1995/1999/2001; matters
    6/13/14/23/132/133/145/149-152/155/161/162/164; docs 1/2/4/5/6/7/8/9; engagements
    1-9; leads 33/37/38; conflicts 4/5; signature 1; users 10/11/50/55-65 inactive;
    matter template 4 and doc template 3 deactivated; engagement template 2 deleted; the
    owner's dashboard at defaults; Signatures on) is untouched.

### S44. Discovery deep pass (qa2): propounding and responding to a served set, the response deadline, the PDF export's Unicode font selection, and the role matrix
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5984463789 2026-10-04T21:17:00Z

Not a backlog item. Bot 2's backlog (B2-1 through B2-6) is used up, and
`git log 1b1b954..HEAD -- app` is still empty, so there is no code drift to
regression-test. Filing #110 (disposition PDF turns non-Latin prosecutor/notes/charge
text into `?`) turned up the same `enable_unicode` gap in `build_set_pdf`
(`app/blueprints/discovery.py`): it scans `ds.party` and the firm/matter/client names but
never an item's request or response text. This batch is a normal discovery deep pass with
case 5681 as a direct, planned retest of that same bug class in a second PDF builder.
AI-dependent discovery routes (`/tailor`, `/draft`) are out of scope: AI extraction in
discovery is paused per Ian's 2026-10-02 direction.

## Cases 5677 to 5687: Discovery deep pass (qa2) — propounding and responding to a served set, the response deadline, the PDF export's Unicode font selection, and the role matrix

1. Baseline: open `/discovery` with no matter filter. Report the total discovery-set
   count and how many belong to each matter shown. Do not touch anything yet.

2. Act and check: create contact `QA2 Discovery Client 20261004` (person, client), email
   `qa2-discovery-20261004@coil.test`. Expect flash `Contact created.` New matter `QA2
   Discovery Matter 20261004` for that contact, practice area left blank, office none, no
   template. Expect a flash matching `Matter M-.... opened.` Record the contact id and
   the matter id/number.

3. Act and check: on that matter, start a new discovery set we propound: kind
   Interrogatories, party `QA2 Discovery Defendant 20261004`, served date left blank.
   Expect flash matching `Started from the general civil starter set (<N> items).`
   Record N and the set's id.

4. Act and check, non-Latin: edit that set, add one item with request text `Απάντησε
   στην ερώτηση 20261004` (Greek). Expect flash `Saved.` Reload the set and confirm the
   Greek text round-trips exactly as item N+1.

5. Act and check: export that set to PDF. Expect flash matching `PDF filed under
   Documents in the Discovery folder: <the set's title> <today, YYYY-MM-DD>.pdf.` Open
   the PDF and report whether the Greek item text from case 4 renders as Greek or as `?`
   characters. Read `build_set_pdf` first: `enable_unicode` is called with the firm name,
   address, the PDF heading, `ds.party`, the matter name and the client's display name,
   never with any item's request or response text. If this prints as `?`, it's the same
   bug as #110 in a second PDF builder; add it as a new finding referencing #110 rather
   than filing a duplicate issue, unless it in fact renders correctly, in which case
   report that and say so plainly.

6. Edge, refused: on the same matter, try to start a new discovery set we respond to,
   with no source document picked. Expect flash exactly `Pick the served set from the
   matter's documents.` and confirm no new set was created by this attempt.

7. Act and check: upload a small plain-text document to the matter named `QA2 Discovery
   Served Set 20261004.txt` with this exact body (so the server's extracted text has two
   labelled requests):
   ```
   INTERROGATORY NO. 1: State your full name.
   INTERROGATORY NO. 2: Περιγράψτε το περιστατικό 20261004.
   ```
   Then start a new discovery set we respond to: kind Interrogatories, party `QA2
   Discovery Plaintiff 20261004`, source document that upload. Expect flash matching
   `Found 2 numbered requests in QA2 Discovery Served Set 20261004.txt.` Confirm the two
   parsed items appear in order and item 2's Greek text is intact.

8. Act and check, duplicate edge: on that responded-to set, set today as the served date
   (editor's `served_on` field, then Save) then run the deadline-task action. Expect
   flash matching `Deadline task created, due <served date + 30 days, formatted like "Nov
   3, 2026">.` Run the same action again immediately. Expect flash matching `That
   deadline task already exists (due ...).` and confirm there is still exactly one such
   task.

9. Second role, act and check: reactivate user 42 (billing, currently inactive); expect
   `User saved.` Signed in as it, `GET` the responded-to set's detail page: expect HTTP
   200 (billing holds `matters_view`). `POST` the deadline-task action again on the same
   set: expect HTTP 403, flash exactly `Your role (billing) cannot change matters and
   contacts. Ask the firm owner if you need that access.`, and confirm the set still has
   exactly one deadline task. Deactivate user 42 again; expect `User saved.`

10. Act and check: delete the propounded set from case 3. Expect flash exactly
    `Discovery set deleted.` Confirm `/discovery?matter_id=<the matter id>` now shows
    only the responded-to set from case 7, and that set (with its deadline task) is
    unaffected.

11. Clean up and what remains: close the matter from case 2; expect a flash matching
    `<the matter number> closed.` Report every id created this batch: the contact, the
    matter and its number, the deleted propounded-set id, the surviving responded-to set
    id and its document source, the uploaded text document's id, the exported PDF's
    document id, and the deadline-task id. Confirm user 42 is inactive again, and
    reconfirm the full retained list (contacts 5/6/7/1968-1992/1995/1999/2001/2002;
    matters 6/13/14/23/132/133/145/149-152/155/161/162/164/165; docs
    1/2/4/5/6/7/8/9/21/22; engagements 1-9; leads 33/37/38; conflicts 4/5; signature 1;
    users 10/11/42/50/55-65 all inactive; matter template 4 and doc template 3
    deactivated; engagement template 2 deleted; the owner's dashboard at defaults;
    Signatures on; speedy-trial task 22 on matter 165) is untouched.

### S45. Mail round trip on qa2 (P2-B2-1): signature requests and engagement letters actually
### deliver via the capture inbox, sign from the captured link, and the no-mail-server edge
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-5984637110 2026-10-04T21:33:00Z

Backlog item P2-B2-1. qa2 got its own Mailpit capture inbox on 2026-10-04 (commit
`b26aad0`), so the signature and engagement-letter send flows that previously stuck at
"Email delivery failed" for lack of any SMTP server should now actually deliver and be
signable end to end, the same way testfirm's already work.

## Cases 5688 to 5701: Mail round trip on qa2 (P2-B2-1)

1. Setup (act and check): create contact `QA2 Mail Roundtrip Client 20261004` (person,
   client), email `qa2-mailrt-20261004@coil.test`. Expect `Contact created.` New matter
   `QA2 Mail Roundtrip Matter 20261004` for that contact, practice area blank, office
   none, no template. Expect a flash matching `Matter M-.... opened.` Upload a small text
   document named `QA2 Mail Roundtrip Doc 20261004.txt` to it. Expect `Uploaded QA2 Mail
   Roundtrip Doc 20261004.txt.` Record the contact id, the matter id/number, and the
   document id.

2. Act and check: from that document, request a signature (default title, no message)
   addressed to the matter's client. Expect flash matching `Signature request sent to
   qa2-mailrt-20261004@coil.test.` — specifically NOT `Email delivery failed. The
   signature request remains a draft; check mail settings and try again.` If the
   delivery-failed flash still appears, say so plainly as a regression of the
   capture-inbox fix, do not refile #105, and skip ahead to case 6 (the no-email edge)
   plus cleanup.

3. Check (owner session, read-only): open https://qa2.coil.legal/qa-mail/ and confirm
   exactly one new message to `qa2-mailrt-20261004@coil.test`, sent since case 2, with a
   subject naming the document. Open its sign link from inside that captured email and
   confirm it lands on the public sign page for this document.

4. Act and check, non-Latin: on that signing page, type signer name `Ελένη
   Παπαδοπούλου 20261004`, tick the agree box, submit. Expect the signed/done page.
   Reload the signature's detail page as owner: confirm status `signed`, the signer name
   is exactly that Greek text, and the certificate download opens.

5. Check: reload https://qa2.coil.legal/qa-mail/ and confirm two more new messages since
   case 3: one to `qa2-mailrt-20261004@coil.test` (the client's signed copy) and one to
   the firm's own email. Confirm the client copy carries the signed PDF as an attachment.

6. Edge, no email on file: create a second contact `QA2 Mail Roundtrip No-Email 20261004`
   (person, client) with no email. Request a signature on the same document for this
   contact. Expect flash matching `Signature request sent to nobody (no email on
   file).` Confirm /qa-mail/ gets no new message for this one, and the signature's own
   detail page still shows a working sign link.

7. Edge, blocked role: reactivate user 42 (billing, inactive per the retained list);
   expect `User saved.` Signed in as it, `GET /signatures` and the signature detail page
   from case 2. Expect HTTP 403 on both, flash exactly `Your role (billing) cannot open
   documents. Ask the firm owner if you need that access.` Deactivate user 42 again;
   expect `User saved.`

8. Act and check: on the matter from case 1, create and send an engagement letter (any
   template, default scope) to the client. Expect flash matching `Engagement letter sent
   to qa2-mailrt-20261004@coil.test.` — not `Saved, but the email to ... could not be
   delivered. The sign link is still active; check the firm's email settings and
   resend.`

9. Check: https://qa2.coil.legal/qa-mail/ shows one new message for the engagement
   letter since case 8. Open its sign link from the captured email.

10. Act and check, empty-input edge: on the engagement sign page, submit with the name
    field blank and the agree box ticked. Expect flash exactly `Type your full name and
    tick the box to confirm you agree.` and the letter still `sent`, not signed. Submit
    again with a real name and the box ticked. Expect the signed/done page.

11. Check: /qa-mail/ shows two more new messages since case 9 (the client's and firm's
    signed copies). Confirm the client's carries the signed PDF as an attachment.

12. Act and check, duplicate edge: submit that same engagement's sign form a third time
    (the same token, already signed). Confirm it shows the already-signed status page,
    not a second signature, and no third round of signed-copy emails in /qa-mail/.

13. Act and check: create and send a third, fresh signature request on the document from
    case 1, to the original client contact. From its public sign page, decline it with
    reason `QA2 decline 20261004`. Confirm the signature's detail page shows status
    `declined` with that reason, and /qa-mail/ gets one new message addressed to the firm
    noting the decline.

14. Clean up and what remains: void any signature request from this batch that is not
    already signed or declined, close the matter from case 1. Report every id created
    this batch: both contacts, the matter and its number, the document, all three
    signature ids and their final statuses, and the engagement id and its final status.
    Reconfirm user 42 is inactive and that the full retained list above this batch is
    untouched.

### S124. Evergreen trust targets and dashboard role checks (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6073578251 2026-10-09T03:21:02+00:00

Reviewed against matters.py _fill, trust.py evergreen_shortfalls, matters/form.html,
dashboard.html and permissions.py. Monthly invoicing cases are deferred while Bot 1
works on invoicing. No invoice, payment or trust deposit is created here. Do not touch
provider settings. Keep the monthly invoice flag off throughout. English and USD only.
Use only new records. Record the owner's dashboard card selection before enabling the
evergreen card; restore that selection at cleanup. Create private random passwords
for the new role-test users; never put them in reports. Retained fixtures stay untouched.

1. Setup (act and check): create contact `QA2 Evergreen Client 20261008` (person, client).
   Expect `Contact created.` New matter `QA2 Evergreen Matter 20261008` on it (Hourly, rate
   $100.00, office none, no template, open). Expect a flash matching `Matter M-.... opened.`
   Record its id/number as M-ID/M-NN. Open its edit form: confirm "Evergreen retainer
   minimum" and "Replenish to" are both blank and "Invoice this matter automatically each
   month" is unticked.
2. Act and check: edit M-ID, set "Evergreen retainer minimum" to $500.00, leave "Replenish
   to" blank, save. Expect flash exactly `Matter saved.` Re-open the edit form: confirm the
   minimum reads $500.00 and "Replenish to" is still blank.
3. Act and check, the dashboard card picks up a real shortfall: as owner, open `/dashboard`
   with the evergreen card ticked (enable it under `/dashboard/customize` first if it is not
   already). Expect M-NN listed with "In trust" $0.00 and "Short by" $500.00 (no replenish
   target set, so the shortfall falls back to the minimum). Confirm the row links to M-ID.
4. Act and check, replenish-to under the minimum is clamped up: edit M-ID again, set
   "Replenish to" to $300.00 (below the $500 minimum), save. Expect `Matter saved.` Re-open
   the edit form and confirm "Replenish to" now reads $500.00, not $300.00. Confirm the
   dashboard card's "Short by" is still $500.00.
5. Act and check, a replenish-to above the minimum takes as entered: edit again, set
   "Replenish to" to $750.00 (above the $500 minimum), save. Expect `Matter saved.` Confirm
   the dashboard card now reads "Short by" $750.00, "In trust" still $0.00.
6. Edge, blanking the minimum turns evergreen off even with a replenish target still set:
   edit M-ID, clear "Evergreen retainer minimum" only (leave "Replenish to" at $750.00),
   save. Expect `Matter saved.` Confirm the dashboard evergreen card no longer lists M-NN at
   all (`evergreen_shortfalls()` filters on `trust_minimum_cents > 0`). Restore the minimum
   to $600.00 (a new value, not the original $500, so case 7 does not read as a no-op).
7. Edge, a second role that can write the field but never see its effect: create a
   paralegal user `QA2 Evergreen Paralegal 20261008` if none exists this batch (expect
   `Added QA2 Evergreen Paralegal 20261008.`). Signed in as it, `POST /matters/<M-ID>/edit`
   changing nothing but confirming the minimum still reads $600.00 from case 6 (paralegal
   holds the full `matters` permission, so this plain save succeeds with `Matter saved.`,
   even though paralegal holds no `trust` permission at all). Still as paralegal, open
   `/dashboard`: confirm the evergreen card itself does not render (gated on `trust_view`).
   Sign back in as owner and confirm the card now reads $600.00 minimum, $750.00 short.
8. Create billing user `QA2 Evergreen Billing 20261008`. Report its creation flash.
   As billing, GET this matter's edit form: expect 200 and minimum $600.00. Submit the
   unchanged complete form with CSRF: expect HTTP 403 and `Your role (billing) cannot
   change matters and contacts. Ask the firm owner if you need that access.` As owner,
   confirm the saved fields are unchanged. Do not open invoicing for this batch.
9. As owner, set the batch matter's minimum to -1.00 and target to -2.00, save.
   Expect `Matter saved.` Both stored fields render blank (the server clamps negatives
   to zero). Confirm this matter disappears from the evergreen dashboard card.
10. Restore minimum $600.00 and target $750.00 on the complete edit form. Expect
    `Matter saved.` Confirm the dashboard row returns with $0.00 in trust and $750.00
    short. Keep monthly invoicing unticked; do not create a deposit request.
11. Close only this matter using its edit form, preserving both trust target fields.
    Expect `Matter saved.` Confirm the row disappears because closed matters are
    excluded. Reopen it with the same fields; expect `Matter saved.` and the row returns.
12. Clean up: deactivate the two users created here; expect `User saved.` each. Close
    the batch matter again and confirm no evergreen shortfall row remains for it.
    Restore the owner's dashboard card selection to its original value.
13. What remains: report contact, closed matter and both inactive user IDs. The matter
    retains minimum $600.00, target $750.00, no trust balance and monthly invoicing off.
    Confirm save/clamp, blanking, dashboard math, role refusals and close/reopen behavior.
    Earlier retained fixtures and firm/provider settings stay unchanged. Return counts
    and one verdict per case, without credentials or private links.

### S125. Captured mail and signing: document request and engagement letter (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6073777562 2026-10-09T03:39:45+00:00

From P2-B2-1. Run after S124. Source checked: `app/blueprints/signatures.py`,
`app/blueprints/engagements.py`, their new/sign forms, and `app/permissions.py`.
Use only qa2's capture inbox at `/qa-mail/`; do not change mail or provider settings.
The no-mail-server configuration edge remains open for an operator test. This batch
checks English mail and signing only. No invoice, payment, trust entry or card action.
At posting, replace DATE with that day's YYYYMMDD in every record name and email.
Use a fresh suffix if any name already exists. All earlier retained fixtures stay untouched.
The coordinator adds the live pin, standard exclusions and continuing case numbers.

1. As owner, create client contact `QA2 Mail Client DATE`, English, email
   `qa2-mail-DATE@coil.test`. Create matter `QA2 Mail Matter DATE`, hourly in USD,
   rate $100.00, no template and no office. Report the flashes and both IDs. Confirm
   the matter names this contact and remains open.
2. Upload `QA2 Mail Document DATE.txt` with exactly `QA2 Mail Document DATE` as its
   contents to that matter. Report the flash and document ID. Download it and confirm
   the bytes match. Use only this document in the signature cases below.
3. Create a document signature request using that document, the new client as
   `contact_id`, title `QA2 Mail Signature DATE`, and message `QA2 Mail Review DATE`.
   Choose `action=draft`. Expect `Signature request saved as a draft.` Record S-ID;
   confirm draft status. No delivery is expected at this step.
4. Send S-ID from its detail page. Expect `Sent to qa2-mail-DATE@coil.test.`
   As owner, find its message in `/qa-mail/` by recipient and title. Confirm the message
   is in English and names this document. Open its signing link privately without
   copying it into any report. Confirm the correct document and signing form appear.
5. From the staff detail page, remind S-ID. Expect `Reminder sent.` Find the new
   reminder in the capture inbox and confirm its recipient and document title. Report
   only the message ID, never its link or token.
6. On the public signing form, submit an empty `signer_name`, the client's email as
   `signer_email`, and consent `agree=1`. Expect refusal with no signature recorded;
   report the validation text. If native validation stops submission, record that
   separately and use a direct form submission to verify the server returns HTTP 400.
7. Submit `QA2 Mail Client DATE` as signer_name, the same email, and `agree=1`.
   Expect signed status. In the staff view confirm signer name and a signed event.
   Download `/signatures/<S-ID>/certificate`; expect a PDF naming the document and signer.
8. Submit the same signed form once more. Expect the signed-status page, no new signature
   and the original signed timestamp unchanged. Confirm the staff event list contains
   only one signed event. Report any extra view events separately.
9. On `/engagements/new` choose the new matter. Set subject `QA2 Mail Letter DATE`,
   scope `QA2 Mail Scope DATE`, and body_html to `<p>QA2 Mail Letter DATE. Review of
   the QA2 Mail Matter DATE file only. No payment is requested.</p>`. Choose
   `action=draft`. Expect `Draft saved.` Record E-ID and confirm its saved subject/body.
10. Send E-ID from its detail page. Expect `Sent to qa2-mail-DATE@coil.test.`
    Find the new engagement email in `/qa-mail/`. Confirm English text, correct recipient
    and subject. Open the captured link privately; confirm it shows the exact body saved
    in case 9 and refers to the batch's matter.
11. Sign E-ID with `signer_name=QA2 Mail Client DATE`, the client's email and `agree=1`.
    Expect signed status. Download `/engagements/<E-ID>/pdf`; confirm the PDF opens,
    includes the saved body and names the signer. Any courtesy emails must remain in
    qa2's capture inbox; report their count and recipients without private links.
12. As owner, attempt to void each signed record. S-ID must refuse with
    `A signed document cannot be voided.` E-ID must refuse with
    `A signed letter cannot be voided.` Confirm both remain signed, with their original
    signed timestamps and downloadable certificate/PDF.
13. Clean up: close only the new matter using its edit form, reporting the flash.
    Retain the new contact, closed matter, document, signed request and signed letter as
    evidence. Do not delete captured messages belonging to other batches.
14. What remains: list the contact, matter, document, S-ID and E-ID, with final statuses.
    State whether request delivery, reminder delivery, blank-name refusal, signing,
    duplicate protection and signed-record void refusals passed. Confirm earlier retained
    fixtures and all firm/provider settings remain unchanged. Report counts and one
    verdict per case; no passwords, tokens, feed URLs or signing links in the result.

### S126. Captured signature mail: decline, duplicate decline and void guards (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6074174195 2026-10-09T04:19:42+00:00

P2-B2-1 follow-up, after S125. Source checked: signatures.py new/send/remind/void,
public decline/file/certificate routes, signatures/new.html and sign.html, and
permissions.py. This tests English captured mail only, with no provider changes.
The no-mail-server configuration edge stays open for an operator; do not change SMTP.
At posting replace DATE with today's YYYYMMDD. Use only this batch's records.

1. As owner create client `QA2 Decline Client DATE`, English, email
   `qa2-decline-DATE@coil.test`, and its hourly USD matter `QA2 Decline Matter DATE`,
   $100.00 rate, no office or template. Report flashes and IDs; confirm the saved client.
2. Upload `QA2 Decline Document DATE.txt`, containing `QA2 Decline Document DATE`.
   Report the flash and ID. Download it and compare bytes with the original.
3. Create signature A on this document with the new client as contact_id, title
   `QA2 Decline Draft DATE`, message `QA2 Decline Draft Note DATE`, action=draft.
   Expect `Signature request saved as a draft.` Then POST its remind action with CSRF:
   expect `Only sent requests can be reminded.` No captured email should be added.
4. Void A. Expect `Signature request voided.` Try its send action with CSRF: expect
   `Cannot send a request with status void.` A remains void and no email is added.
5. Create signature B on the same new document and client, title `QA2 Decline Sent DATE`,
   message `QA2 Decline Sent Note DATE`, action=send. Expect the signature-request-sent
   flash naming the new client's address. Find the captured email at `/qa-mail/` and
   privately open its link. Confirm the correct document and client; keep its token private.
6. Decline B with reason left blank. Expect declined status: an empty reason is allowed.
   In staff detail confirm one declined event with empty detail. The capture inbox should
   receive a new decline notification naming B. Report its message ID, no private links.
7. Submit B's decline form again, this time with reason `QA2 Decline Repeat DATE`.
   Expect the declined-status page without a second declined event, changed original
   reason or second decline notification. Compare the event and captured-message counts.
8. As owner try send and remind on B. Expect `Cannot send a request with status declined.`
   and `Only sent requests can be reminded.` respectively. B remains declined; no new mail.
9. In the same private public context, request B's file and certificate endpoints using
   its existing token privately. Expect HTTP 404 on each. No signed certificate exists.
10. Create signature C on the same document and client, title `QA2 Decline Void DATE`,
    message `QA2 Decline Void Note DATE`, action=send. Find its captured email, open its
    link and confirm the file can be read. As owner void C; expect `Signature request
    voided.` Reload its public file URL: expect 404. Its signing page now shows void status.
11. Clean up: close this batch's matter, reporting the flash. Keep the contact, closed
    matter, document and requests A (void), B (declined), C (void). Do not delete another
    batch's captured mail or alter any earlier retained fixture.
12. What remains: list all IDs and statuses, notification counts, and results of blank
    reason, duplicate decline, send/remind refusals and public file/certificate guards.
    Confirm no signed request, payment, provider change or external delivery. Return
    counts and one verdict per case; never include credentials, tokens or private links.

### S127. Signature signer selection and title limits (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6074375565 2026-10-09T04:39:27+00:00

P2-B2-1 follow-up after S126. Source checked: signatures.py signer_choices/new/send/void,
signatures/new.html form fields and permissions.py. This batch checks the request
before mail is sent, then one captured request. No provider changes or money operations.
At posting replace DATE with today's YYYYMMDD. English and USD only; use the owner.
Only the records below may be changed. Prior retained fixtures stay untouched.

1. Create client `QA2 Sign Guard Client DATE`, English, email
   `qa2-sign-guard-DATE@coil.test`. Create its hourly USD matter `QA2 Sign Guard Matter
   DATE`, $100.00 rate, no template or office. Record IDs and confirm saved client/rate.
2. Create unrelated contact `QA2 Sign Guard Other DATE`, email
   `qa2-sign-guard-other-DATE@coil.test`. Do not attach it to the matter as a party.
   Upload `QA2 Sign Guard Document DATE.txt` containing that exact filename as text
   to the new matter. Record IDs and confirm the document is on this matter.
3. Open `/signatures/new` for this document. Confirm the new client appears in the
   signer choices and the unrelated contact does not. Submit the form directly with
   CSRF and the unrelated contact's ID as contact_id, title `QA2 Sign Guard Refused DATE`,
   action=draft. Expect `Pick a signer from the matter's client or parties.` and no
   new request. Report HTTP status; a rendered validation page need not be HTTP 400.
4. Repeat with action=send and the same unrelated contact. Expect the same refusal,
   no request and no captured message to that address. This must fail before delivery.
5. Submit with the correct client and a blank title using a direct CSRF form submission
   (the browser's required attribute normally stops this). Choose action=draft.
   Expect `Signature request saved as a draft.` and the title defaults to the document
   filename. Record A-ID; no email should have been sent.
6. Submit a second draft with the correct client, title built from `QA2 Sign Guard DATE `
   followed by enough ASCII Q characters to make exactly 350 characters, and message
   `QA2 Sign Guard Long DATE`. Expect `Signature request saved as a draft.` Record B-ID;
   verify the stored title is exactly the first 300 submitted characters. Report browser
   maxlength=300 separately from this direct server validation check.
7. Send A-ID. Expect the send flash naming `qa2-sign-guard-DATE@coil.test`. In `/qa-mail/`
   confirm exactly one new request to the correct client and none to the unrelated one.
   Open its signing link privately: the title is the document filename and its bytes match.
   Do not sign, decline or copy the private URL into the report.
8. As owner void A-ID and B-ID. Expect `Signature request voided.` for each. A's public
   signing page now shows void status. Try B's send action: expect `Cannot send a request
   with status void.` No new captured request is sent.
9. Clean up: close the new matter and report the flash. Retain the two contacts, closed
   matter, document and two void requests. Confirm the unrelated contact still has no
   connection to this matter and all earlier fixtures remain untouched.
10. What remains: list all IDs, final statuses and title lengths. Confirm both invalid
    signer attempts failed before creating a request, blank-title fallback and server
    truncation held, and mail went only to the intended client in qa2's capture inbox.
    Return counts and one verdict per case. No credentials, tokens or private links.

### S128. Engagement letter decline and terminal-state mail guards (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6074593221 2026-10-09T04:59:34+00:00

P2-B2-1 follow-up. Source checked: engagements.py new/send/remind/void/sign/decline,
engagements/new.html and sign.html, and permissions.py. Use the owner and only new
records below. English and USD; mail only in qa2's capture inbox. No provider changes.
Replace DATE with today's YYYYMMDD at posting. Never probe with a retained matter,
document or letter. No invoice, payment or trust action. Report unquoted flashes.

1. Create English client `QA2 Letter Guard Client DATE`, email
   `qa2-letter-guard-DATE@coil.test`, and its hourly USD matter `QA2 Letter Guard Matter
   DATE`, rate $100.00, no office/template. Record IDs; confirm saved client and rate.
2. Create engagement A for this matter with subject `QA2 Letter Guard Draft DATE`,
   scope `QA2 Letter Guard Scope DATE`, body_html `<p>QA2 Letter Guard Draft DATE.
   Review only; no payment requested.</p>` and action=draft. Expect `Draft saved.`
   Confirm saved body and draft status; record A-ID.
3. POST A's remind action with CSRF. Expect `Only sent letters can be reminded.`
   No captured reminder and no change to draft status. Void A: expect `Letter voided.`
4. Attempt A's send action with CSRF. Expect `Cannot send a letter with status void.`
   Confirm no request email and A still void.
5. Create letter B on the same new matter, subject `QA2 Letter Guard Sent DATE`,
   scope `QA2 Letter Guard Scope DATE`, body_html `<p>QA2 Letter Guard Sent DATE.
   Review only; no payment requested.</p>`, action=send. Report the flash, confirm
   sent status and its captured message. Open its private link; verify the exact body.
6. Submit the public signing form with signer_name blank, client email, and agree=1.
   If native required validation blocks it, report that and test a direct form POST.
   Expect HTTP 400 and unsigned status. Report validation text; do not sign B.
7. Decline B with reason `QA2 Letter Guard Decline DATE`. Confirm declined status and
   exactly one declined event with that reason. Find one new captured decline notice
   naming B. Record its message ID only.
8. Repeat B's decline POST with reason `QA2 Letter Guard Repeat DATE`. Expect the
   declined-status page, one declined event with the original reason, and no extra
   decline notification. Count rows labelled declined, not every activity row.
9. As owner attempt B's send and remind actions. Expect `Cannot send a letter with
   status declined.` and `Only sent letters can be reminded.` No mail is added.
10. Create letter C on this matter with subject `QA2 Letter Guard Void DATE`, scope
    `QA2 Letter Guard Scope DATE`, body_html `<p>QA2 Letter Guard Void DATE.
    Review only; no payment requested.</p>`, action=send. Confirm captured delivery.
    Void C as owner: expect `Letter voided.` Open its captured link privately; it must
    show void status. A direct signing POST with name/email/agree must not sign it.
11. Clean up: close only the new matter and report the flash. Keep A void, B declined
    and C void. Retain the contact and closed matter. Leave prior fixtures untouched.
12. What remains: list all IDs and statuses, captured message counts, and results of
    blank-name validation, duplicate decline and terminal-state send/remind/sign guards.
    Return a Markdown per-case table and counts. No credentials, tokens or private links.

### S129. Signature and engagement mail permissions by role (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6074811147 2026-10-09T05:19:31+00:00

P2-B2-1 role coverage. Source checked: permissions.py (signatures use documents,
engagements use matters), signatures.py new/send/void, engagements.py new/send/void,
and their form fields, plus settings/user_form.html. English and USD only. Replace
DATE with today's YYYYMMDD. Only new fixtures below, no probe on retained records.
No invoices, payments, trust operations, provider changes or external email.

1. As owner create English client `QA2 Mail Role Client DATE`, email
   `qa2-mail-role-DATE@coil.test`, and hourly USD matter `QA2 Mail Role Matter DATE`,
   $100.00 rate, no office or template. Report flashes and IDs, confirm the saved client.
2. Upload `QA2 Mail Role Document DATE.txt`, containing `QA2 Mail Role Document DATE`,
   to this matter. Confirm its bytes on download and record its ID.
3. Create attorney `QA2 Mail Role Attorney DATE`, email `qa2-mail-role-attorney-DATE@coil.test`,
   and billing user `QA2 Mail Role Billing DATE`, email `qa2-mail-role-billing-DATE@coil.test`.
   Use private random passwords, no voice phone or PIN. Report flashes and IDs only.
4. As billing GET `/signatures/new?document_id=<new-document-id>`: expect HTTP 403
   with the role refusal for opening documents. POST that endpoint with CSRF and valid
   document/client/title fields: expect HTTP 403 for changing documents, no request.
5. Still as billing GET `/engagements/new?matter_id=<new-matter-id>`: expect HTTP 200.
   POST a draft with matter_id, subject `QA2 Mail Role Refused DATE`, body_html
   `<p>QA2 Mail Role Refused DATE</p>`, action=draft and CSRF. Expect HTTP 403 for changing
   matters and contacts, no letter and no captured mail. The read/write difference is expected.
6. As attorney create a signature draft on the new document for the new client,
   title `QA2 Mail Role Signature DATE`, message `QA2 Mail Role Review DATE`.
   Expect `Signature request saved as a draft.` Record S-ID, confirm draft status.
7. As attorney send S-ID. Expect the send flash naming the new client's address.
   As owner inspect `/qa-mail/` and confirm one captured signature request with this title.
   Do not open or print its private signing link.
8. As attorney create engagement draft on the new matter, subject `QA2 Mail Role Letter
   DATE`, scope `QA2 Mail Role Scope DATE`, body_html `<p>QA2 Mail Role Letter DATE.
   Review only; no payment requested.</p>`, action=draft. Expect `Draft saved.` Record E-ID.
9. As attorney send E-ID. Expect the send flash naming the new client's email. As owner
   confirm one captured engagement message with the saved subject, in addition to the
   earlier signature request. No message should go to either staff user's test address.
10. As attorney void S-ID and E-ID, neither signed. Expect `Signature request voided.`
    and `Letter voided.` Confirm both void. No extra request email should be sent.
11. Clean up as owner: deactivate both role-test users and close the new matter.
    Report flashes. Retain the contact, closed matter, document, two void requests and
    inactive users. Confirm all prior fixtures unchanged.
12. What remains: list all created IDs, role outcomes, statuses and captured-message
    counts. Confirm billing could read engagement creation but could not write it,
    billing could not access signatures, and attorney could create/send/void both.
    Return a Markdown per-case table and counts. Never include passwords or private links.

### S130. Sent signature keeps its document version after later uploads (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6075138835 2026-10-09 05:48 UTC

P2-B2-1 document-mail integrity follow-up. Source checked: documents.py new_version,
version_family and store_upload; documents/versions.html file field; signatures.py
new/send/sign and _verified_file_bytes; signatures forms; permissions.py.
New versions are new Document rows, so an existing request must keep the bytes and ID
it was sent with. Use owner, English and USD, captured qa2 mail only. No provider changes.
Replace DATE with today's YYYYMMDD at posting. Every fixture below is new; never probe
using retained files. Do not delete or replace on disk any signed file.

1. Create English client `QA2 Version Sign Client DATE`, email
   `qa2-version-sign-DATE@coil.test`, and hourly USD matter `QA2 Version Sign Matter DATE`,
   $100.00 rate, no template or office. Record IDs, report flashes, confirm saved client.
2. Upload `QA2 Version Sign DATE.txt` containing exactly `QA2 Version Sign Original DATE`.
   Record document D1. Download and compare bytes. Keep a local SHA-256 for comparison.
3. Create and send a signature request for D1 to this client, title `QA2 Version Sign
   Request DATE`, message `QA2 Version Sign Review DATE`. Report the flash, record S1.
   Confirm a captured request in `/qa-mail/`; keep its public link private.
4. POST D1's new-version form with CSRF but no file. Expect `Choose a file for the new
   version.` Confirm its history still contains only version 1 and S1 is unchanged.
5. Upload through D1's new-version form (field file) the same filename but bytes
   `QA2 Version Sign Revised DATE`. Expect a version-2 upload flash. Record D2.
   History shows v2 current and v1 still downloadable. Download each and compare bytes.
6. Repeat that upload through the current version's new-version form with the same
   filename and revised bytes. Expect version 3, not an overwrite. Record D3; history
   has v1, v2, v3 with only v3 current. D2 and D3 downloads have equal revised bytes.
7. Open S1's captured signing link and its file link privately. Expect the original D1
   bytes and original SHA-256, even though v3 is now current. Record no token or URL.
8. Sign S1 with the new client's full name and email and agree=1. Expect signed status,
   one event specifically labelled signed and a certificate naming D1's original hash.
   The newer document bytes must not be substituted into the signed request.
9. As owner create and send a separate request S2 explicitly selecting D3, title
   `QA2 Version Sign Latest DATE`, message `QA2 Version Sign Latest Review DATE`.
   Find its captured message; its public file download must match the revised bytes.
   Void S2 without signing. Expect `Signature request voided.`
10. Reopen S1's signed page and certificate: still signed, same original hash and one
    signed event. S2 remains void. Confirm D1 is still downloadable and unchanged;
    v3 remains current with revised bytes. Do not delete any version.
11. Clean up: close only this batch's matter and report the flash. Retain all three
    document versions, signed S1, void S2, contact and closed matter. Earlier fixtures stay.
12. What remains: list all IDs, versions, statuses and original/revised hash comparisons.
    Confirm missing-file refusal, repeated-upload versioning and old-request byte binding.
    Return counts and a Markdown per-case table. No passwords, tokens or private links.

### S131. Signature mail with no initial email and later contact edits (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6075384821 2026-10-09 06:09 UTC

P2-B2-1 recipient handling. Source checked: signatures.py send_signature and
send_signature_reminder, new/send/remind/void routes, contacts.py edit, signature
and contact forms, permissions.py. Initial send with no email is deliberately marked
sent without email; reminders refuse until an address exists. Once sent_to is set,
reminders prefer that saved recipient over later contact edits. Test this as designed.
Replace DATE with today's YYYYMMDD. Owner only, English and USD. No provider changes;
mail stays in qa2's capture inbox. No invoice, payment or trust action. New fixtures only.

1. Create English client `QA2 Recipient Client DATE` with email blank and hourly USD
   matter `QA2 Recipient Matter DATE`, $100.00 rate, no office/template. Report flashes
   and IDs. Confirm the stored email is blank, not an old retained address.
2. Upload `QA2 Recipient Document DATE.txt` containing `QA2 Recipient Document DATE`.
   Confirm download bytes match; record document ID.
3. Create and send signature A on this document for the new client, title `QA2 Recipient
   Empty DATE`, message `QA2 Recipient Review DATE`. Expect `Signature request sent to
   nobody (no email on file).` It is sent with blank sent_to, not draft. Confirm zero
   captured messages for this title. This status is designed, not proof of email delivery.
4. Attempt to remind A. Expect `No signer email address is on file.` Confirm no captured
   message, no new reminder event and unchanged sent status.
5. Edit the batch contact to email `qa2-recipient-a-DATE@coil.test`, preserving its other
   fields. Expect `Contact saved.` Confirm the saved address.
6. Remind A. Expect `Reminder sent.` Find exactly one new captured reminder for A,
   addressed to qa2-recipient-a-DATE@coil.test. Record message ID only. Do not sign A.
7. Edit the same contact to `qa2-recipient-b-DATE@coil.test`, then remind A again.
   Expect `Contact saved.` and `Reminder sent.` The new captured reminder goes to B,
   because A's original sent_to was blank. Confirm prior captured messages remain.
8. Create and send signature B on the same batch document/client, title `QA2 Recipient
   Fixed DATE`, message `QA2 Recipient Fixed Review DATE`. Report its send flash.
   Confirm its captured initial request goes to qa2-recipient-b-DATE@coil.test.
9. Edit the contact back to qa2-recipient-a-DATE@coil.test and remind B. Expect
   `Contact saved.` then `Reminder sent.` The reminder still goes to B's original
   qa2-recipient-b-DATE@coil.test, from its saved sent_to. Confirm the recipient exactly.
10. As owner void A and B. Expect `Signature request voided.` for each. Remind B again:
    expect `Only sent requests can be reminded.` and no additional captured message.
11. Clean up: close the new matter, report the flash. Keep contact email at A, the
    closed matter, document and two void requests. Leave all earlier fixtures untouched.
12. What remains: list IDs and statuses plus each captured message's recipient and
    request title. Confirm no-email send state, reminder refusal, blank sent_to fallback
    and saved-recipient preference. Return counts and Markdown per-case table. No private links.

### S132. Engagement reminder recipient fallback and repeated send (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6075773839 2026-10-09 06:38 UTC

P2-B2-1 final recipient coverage after S131. Source checked: engagements.py new,
send_engagement, send_engagement_reminder, send/remind/void; engagements/new.html
fields; contacts.py edit; permissions.py. Owner only, English and USD. All mail stays
in qa2's capture inbox. No firm/provider settings, invoices, payments or trust.
Replace DATE with today's YYYYMMDD. Use fresh CSRF for each POST, new fixtures only.

1. Create client `QA2 Letter Recipient Client DATE` with email blank and hourly USD
   matter `QA2 Letter Recipient Matter DATE`, rate $100.00, no office/template.
   Report flashes and IDs. Confirm email is blank and the matter uses this client.
2. Create engagement A with matter_id, subject `QA2 Letter Recipient Empty DATE`,
   scope `QA2 Letter Recipient Scope DATE`, body_html `<p>QA2 Letter Recipient Empty DATE.</p>`
   and action=send. Expect `Engagement letter sent to nobody (no email on file).`
   Confirm sent status, blank recipient and no captured message for this subject.
3. POST A's remind action. Expect `Reminder sent.` but zero captured messages and
   one new reminder event with detail `no email`. This is the current designed behavior:
   that flash does not prove delivery when the client has no address. Report it plainly.
4. Edit this contact to `qa2-letter-recipient-a-DATE@coil.test`, preserving other fields.
   Expect `Contact saved.` Remind A again: expect `Reminder sent.` and exactly one new
   captured reminder addressed to that address. A remains sent with its original body.
5. Edit this contact to `qa2-letter-recipient-b-DATE@coil.test`. Expect `Contact saved.`
   POST A's send action again. Expect `Sign link re-sent.` and one new captured reminder
   addressed to B, with a reminder event whose detail names `resent by staff`.
   This reuses A, does not create a second engagement and keeps its original body hash.
6. Create engagement B on the same matter with subject `QA2 Letter Recipient Fixed DATE`,
   scope `QA2 Letter Recipient Fixed Scope DATE`, body_html `<p>QA2 Letter Recipient Fixed DATE.</p>`
   and action=draft. Expect `Draft saved.` Confirm draft and no captured message for B.
7. Send B through its detail action. Expect `Sent to qa2-letter-recipient-b-DATE@coil.test.`
   Confirm sent status, saved recipient B and one captured initial message for B's subject.
8. Edit the client back to qa2-letter-recipient-a-DATE@coil.test. Expect `Contact saved.`
   Remind B: expect `Reminder sent.` and a new captured message still addressed to B's
   saved original address, not the contact's current A address. Preserve both messages.
9. Repeat B's send action. Expect `Sign link re-sent.` and one new reminder to the saved
   B address. Confirm the same engagement ID, unchanged body hash and no second sent
   event. Count event rows by event name, not labels elsewhere on the page.
10. Void A and B. Expect `Letter voided.` for each. Try reminding B afterward:
    expect `Only sent letters can be reminded.` and no additional captured message.
    Do not open either private signing link and do not sign these letters.
11. Clean up: close only this matter, report the flash. Retain the client with email A,
    closed matter and two void engagements. All older retained fixtures stay untouched.
12. What remains: list IDs and final statuses, each initial/reminder recipient and
    captured-message count, blank-email event behavior, fallback and saved-recipient
    preference, and repeated-send hash/event checks. Return counts and a per-case table.
    Never include a password, token or private signing link.

### S133. Engagement template edits and deletion preserve saved letters (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6076067950 2026-10-09 06:58 UTC

P2-B2-1 saved-letter integrity, after recipient checks. Source checked: engagements.py
_fill_template, _validate_template, template_new/edit/delete, new, send and void;
engagement template and new-letter form fields; permissions.py. Owner only, English
and USD. Use only a new nondefault template; never edit an existing template or default.
Replace DATE with today's YYYYMMDD. Mail stays in qa2's capture inbox. No invoices,
payments, trust, cards, provider changes or private-link disclosure.

1. Record the existing engagement template IDs and default flags without changing them.
   Create client `QA2 Template Snapshot Client DATE`, email `qa2-template-snapshot-DATE@coil.test`,
   and hourly USD matter `QA2 Template Snapshot Matter DATE` at $100.00, no office or
   matter template. Report flashes and IDs. Confirm client and matter persisted.
2. POST `/engagements/templates/new` with name blank, kind=engagement, is_default=0,
   subject `QA2 Template Snapshot DATE`, body_html `<p>QA2 Template Snapshot DATE.</p>`.
   Expect `A name is required.` Confirm no new template and unchanged default flags.
3. Repeat with name `QA2 Template Snapshot DATE` but body_html `{{ client_name`.
   Report the exact template-syntax flash rather than guessing its parser text. Expect
   rejection with no template saved and no change to existing templates.
4. Create the valid template with name `QA2 Template Snapshot DATE`, kind=engagement,
   is_default=0, subject `QA2 Template Original DATE: {{ matter_name }}`, and body_html
   `<p>QA2 Template Original DATE.</p><p>{{ client_name }}</p><p>{{ scope }}</p>`.
   Expect `Template created.` Record T-ID and confirm nondefault. If it is the only
   template and becomes default automatically, record that designed behavior; do not
   alter another template to compensate. Cleanup deletes only this new template.
5. Create draft A via `/engagements/new` with matter_id, template_id=T-ID,
   scope `QA2 Scope Original DATE`, action=draft, and subject/body_html omitted so the
   saved content comes from the template. Expect `Draft saved.` Record A. Confirm the
   original marker, new client's name, original scope and merged matter name in subject.
6. Edit only T-ID, keeping name/kind/is_default as saved in case 4. Change subject to
   `QA2 Template Revised DATE: {{ matter_name }}` and body_html to
   `<p>QA2 Template Revised DATE.</p><p>{{ client_name }}</p><p>{{ scope }}</p>`.
   Expect `Template saved.` Reload A: still the original subject/body/scope, no revised marker.
7. Create draft B with this same T-ID and new matter, scope `QA2 Scope Revised DATE`,
   action=draft, subject/body_html omitted. Expect `Draft saved.` Confirm revised marker,
   revised scope and merged subject on B. A remains unchanged with its original content.
8. Send A through its detail action. Report its send flash. Confirm one new captured
   message with A's original merged subject. Open the signing page privately to verify
   the original body and scope remain. Do not sign it or print its token or URL.
9. Delete only T-ID through `/engagements/templates/<T-ID>/delete`. Expect
   `Deleted template QA2 Template Snapshot DATE.` Confirm template absent, existing
   template IDs/default flags restored to their initial set, and A/B still accessible.
   Saved letters retain their bodies even though their template reference is removed.
10. Send B after template deletion. Report its send flash. Confirm one captured message
    with B's revised subject and verify its signing page privately shows the revised
    body and scope. A's signing page still shows original content. Do not sign either.
11. Void both A and B as owner. Expect `Letter voided.` for each. Confirm both void
    and their saved bodies remain available in staff detail. No new request mail.
12. Clean up: close only this matter, report the flash. Retain client, closed matter
    and two void letters. Confirm this batch's template is deleted, every earlier
    template/default is unchanged, and all prior fixtures stay untouched.
13. What remains: list IDs/statuses, deleted template ID, original versus revised
    subjects and markers, captured-message counts, blank-name and syntax refusals.
    Return counts and a per-case table without private links or credentials.

### S134. Engagement signed-copy delivery and duplicate-sign completion check (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6076341826 2026-10-09 07:19 UTC

Final P2-B2-1 engagement completion sweep after S132/S133. Source checked:
engagements.py new/send/sign/_email_signed_copies/sign_pdf/void, engagement creation
and signing form fields, permissions.py. Owner only, English and USD, new fixtures.
Replace DATE with today's YYYYMMDD. Capture inbox only; no provider changes, invoice,
payment, trust or card actions. Private signing links stay out of evidence.

1. Create client `QA2 Letter Complete Client DATE`, email `qa2-letter-complete-DATE@coil.test`,
   and hourly USD matter `QA2 Letter Complete Matter DATE`, rate $100.00, no office or
   matter template. Report flashes and IDs; verify contact and matter values persisted.
2. Create draft engagement with matter_id, action=draft, subject `QA2 Letter Complete DATE`,
   scope `QA2 Letter Complete Scope DATE`, body_html `<p>QA2 Letter Complete DATE.</p><p>Review and signature only.</p>`.
   Expect `Draft saved.` Record E-ID and verify draft plus exact saved subject/body.
3. Send this letter. Report the send flash, confirm sent state and one captured initial
   request to the new client's address. Store its signing URL privately for these cases.
4. GET the private signing page. Confirm the saved letter body and signing form.
   Request its public signed-PDF endpoint before signing: expect 404, not a signed PDF.
5. POST signer_name blank, signer_email equal to the new client, agree=1. Expect HTTP
   400; report the displayed error. Confirm no signed event, no signed-copy mail and
   letter remains unsigned. Do not treat a viewed state as a failure.
6. POST the new client's full name and email with agree omitted. Expect HTTP 400;
   report the error. Confirm still unsigned, no signed event and no signed-copy mail.
7. POST the valid full name, client email and agree=1. Expect successful completion,
   signed status, the exact signer name/email, a nonempty document/signature hash and
   exactly one event named signed. Count event rows rather than all text matches.
8. In `/qa-mail/`, find the signed-copy message to the client and the firm's signed
   notification. Confirm both refer to this letter and each has an application/pdf
   attachment named `engagement-<E-ID>-signed.pdf`. Report message IDs only. The firm's
   configured recipient stays unchanged; capture delivery does not send externally.
9. Download the public signed PDF privately and the attachments from case 8. Confirm
   each is a readable PDF with the original letter marker and signer name, and compare
   their SHA-256 values: they should be copies of the same stored signed PDF.
10. Repeat the valid signing POST with the same signer fields. Expect the signed-status
    page, unchanged hashes and exactly one signed event. Confirm no extra signed-copy
    messages since case 8. Download again: same signed PDF bytes.
11. As owner attempt to void E-ID. Expect `A signed letter cannot be voided.` Confirm
    signed state and PDF unchanged. Attempt its reminder action: expect
    `Only sent letters can be reminded.` and no new captured reminder.
12. Clean up: close only this matter, report the flash. Retain client, closed matter,
    signed engagement and stored signed PDF. Preserve captured evidence and every
    earlier fixture; do not remove the signed letter or change any shared template.
13. What remains: list IDs/statuses, signer fields, signed-event count, signed-copy
    recipients/counts and PDF hash comparisons. Return counts and a per-case table.
    No tokens, passwords or private links. This concludes the queued mail completion
    coverage; report any remaining operator-only limitation separately.

### S135. Document ZIP import, folder mapping and safe repeat (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6076768383 2026-10-09 07:49 UTC

B2-4 remaining document-ZIP import, after S134 closes the queued mail sweep.
P2-B2-2/3/5/6 overlap Bot 1's current money tools; defer them until that seat changes
areas. P2-B2-4 is parked currency work. This batch touches no money tool.
Source checked: importer.py upload/preview/_zip_plan/_zip_rows/_apply_zip/_start_zip_job,
importer index and preview_zip fields, documents.py blocked extensions, permissions.py.
Owner only. English, ASCII filenames and new fixtures only. Replace DATE with today's
YYYYMMDD. No provider or shared-template changes, external email or private-link output.

1. Create client `QA2 Zip Client DATE` and hourly USD matter `QA2 Zip Matter DATE` at
   $100.00, no office/template. Report flashes and IDs, including the generated matter
   number. Confirm zero documents on this newly created matter. Record the current
   importer source selection so it can be restored during cleanup.
2. POST `/import/documents/upload` with source=generic and CSRF but no file. Expect
   `Choose a file to upload.` Confirm no document or import job created by this request.
3. Upload `QA2 Invalid DATE.zip` containing plain text `QA2 Not A ZIP DATE` as field file,
   source=generic. Expect `That file is not a ZIP archive.` Confirm no document created.
4. Upload valid `QA2 Root Only DATE.zip` containing only root file `QA2 Root DATE.txt`
   with nonempty text `QA2 Root DATE`. Expect `No files found inside matter folders. The ZIP needs one top-level folder per matter.`
   Confirm no document imported.
5. Build `QA2 Documents DATE.zip` with six entries. Under a top-level folder equal to
   the new matter number, include `QA2 First DATE.txt` with bytes `QA2 First DATE`,
   `Notes/QA2 Second DATE.txt` with bytes `QA2 Second DATE`, and `QA2 Third DATE.txt`
   with bytes `QA2 Third DATE`. Add root `QA2 Root DATE.txt` with nonempty text, an empty
   `<matter-number>/QA2 Empty DATE.txt`, and `<matter-number>/QA2 Blocked DATE.exe`
   containing harmless plain text `QA2 Blocked DATE` (never executable code).
   Upload with source=generic. Preview should show one folder, three accepted files,
   mapped to the new matter, plus three skipped entries with reasons `Not inside a matter folder.`,
   `Empty file.` and `.exe files are not allowed.` No documents exist before commit.
6. In that preview set the folder's matter-number field to a unique nonexistent ASCII
   value constructed at run time, then Save folder choices. Report the exact refusal
   flash. Expect rejection and no import. Never substitute a retained matter number.
7. Set the same field to this batch's actual matter number and Save folder choices.
   Use the field name supplied in the form, `folder_number_<folder-hash>`. Confirm its
   saved mapping is this new matter and preview still lists exactly three accepted files.
8. Click Import all files and let the normal progress page finish. Record job ID and
   terminal status. Expect 3 created, 3 skipped, 0 updated, 0 errors across 6 rows.
   Only this matter gains three documents; no new matter/contact is created by the import.
9. Download each new document and compare exact bytes to the three inputs. Confirm
   first/third files are in `Imported`, second in `Imported/Notes`. Record document IDs.
   Root, empty and blocked filenames must not be stored as documents on this matter.
10. Upload the same six-entry ZIP again with source=generic and the same mapping,
    commit, and let the job finish. Expect 0 created, 6 skipped, 0 updated, 0 errors.
    Confirm still exactly three document IDs and unchanged bytes, with no new versions.
11. Clean up: close only this matter, report the flash. Retain contact, closed matter,
    three imported documents and both completed import jobs. Restore the importer source
    selection to its initial value through the normal form if it changed. Earlier fixtures stay.
12. What remains: list IDs/statuses, document folder/byte checks, both job counts and
    upload/mapping refusals. Return counts and a per-case table. No upload tokens,
    credentials or private URLs. Do not delete import history or retained documents.

### S136. Document ZIP duplicate paths and long-path identity (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6077045932 2026-10-09 08:09 UTC

B2-4 ZIP boundary coverage after S135. Source checked: importer.py _zip_plan,
_apply_zip path identity and source deduplication, preview mapping fields and job flow;
documents.py store_bytes; permissions.py owner-only import. English, ASCII, new
fixtures only. Replace DATE with today's YYYYMMDD. No money tools or shared settings.
Use source=generic consistently. Never map to an earlier retained matter.

1. Create client `QA2 Zip Identity Client DATE` and hourly USD matter `QA2 Zip Identity Matter DATE`
   at $100.00, no office/template. Report flashes and IDs; confirm zero documents.
   Record the importer source selection for restoration during cleanup.
2. Build `QA2 Zip Identity DATE.zip` with five file entries under the new matter-number
   folder: `QA2 Unique DATE.txt` containing `QA2 Unique DATE`; two entries with exactly
   the same archive path `QA2 Duplicate DATE.txt`, one containing `QA2 Duplicate A DATE`
   and the other `QA2 Duplicate B DATE`; and two long-path entries described next.
   The long entries share one subfolder named `QA2 Long DATE ` plus 125 ASCII X characters,
   then filenames `QA2 Long A DATE.txt` and `QA2 Long B DATE.txt`, with distinct contents
   `QA2 Long A DATE` and `QA2 Long B DATE`. Confirm both archive paths exceed 120 characters
   and their first 120 characters match, while their full paths differ.
3. Upload that ZIP via `/import/documents/upload`, field file, source=generic, CSRF.
   Preview should show three accepted files and two skipped duplicate entries, each
   with `Ambiguous duplicate path. Rename the files and upload again.` Confirm the
   selected matter is this batch's new matter and no documents exist before commit.
4. Commit through the preview and let the progress page finish. Expect 3 created,
   2 skipped, 0 updated and 0 errors across 5 rows. Record job ID. Confirm neither
   ambiguous duplicate was silently chosen or imported.
5. Download all three documents. Compare bytes exactly: unique, long A and long B.
   Long A/B must have distinct IDs and contents despite the shared 120-character prefix.
   Confirm they belong to this new matter, with their nested Imported folder preserved.
6. Upload the identical ZIP again with source=generic and identical mapping, then commit.
   Expect 0 created, 5 skipped, 0 updated and 0 errors. Same three IDs and bytes remain.
7. Build another ZIP with only the already-imported unique file path, but change its
   bytes to `QA2 Unique Changed DATE`. Upload/commit with source=generic and the same
   mapping. Expect 0 created, 1 skipped, 0 updated, 0 errors. The existing unique file
   retains its original bytes: path identity does not update content on a repeat import.
8. Rename that changed entry to `QA2 Unique Renamed DATE.txt`, leaving changed bytes
   intact. Upload/commit as generic. Expect 1 created, 0 skipped, 0 errors. Download its
   new document ID and confirm changed bytes; the original unique file is unchanged.
9. Build a repaired ZIP containing `QA2 Duplicate A DATE.txt` and `QA2 Duplicate B DATE.txt`
   under the same new matter-number folder, with their original A/B contents. Import
   as generic. Expect 2 created, 0 skipped, 0 errors and two distinct correct downloads.
10. Re-upload that repaired ZIP unchanged, same source and mapping. Expect 0 created,
    2 skipped, 0 errors and unchanged IDs/bytes. Total documents on this matter: six.
11. Clean up: close only this matter and report the flash. Retain client, closed matter,
    six documents and all six completed import jobs. Restore importer source selection
    to its original value if changed. Do not delete import history or older fixtures.
12. What remains: list IDs, job counts, duplicate refusal and long-path comparisons.
    Confirm repeat imports did not replace bytes or add versions and renamed paths
    created separate documents. Return counts and a per-case table. No upload tokens,
    credentials or private URLs. All earlier retained fixtures stay untouched.

### S137. Document ZIP explicit skips and changed folder mappings (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6077477456 2026-10-09 08:39 UTC

B2-4 mapping coverage after S135/S136. Source checked: importer.py preview,
_zip_rows and _apply_zip; preview_zip.html folder_number fields and do actions;
permissions.py. Owner only. English/ASCII, new fixtures only. No money tools, mail,
shared settings or provider changes. Replace DATE with today's YYYYMMDD.

1. Create client `QA2 Zip Map Client DATE` and two hourly USD matters
   `QA2 Zip Map First DATE` and `QA2 Zip Map Second DATE`, each $100.00, no office/template.
   Report flashes and IDs; record their matter numbers as M1 and M2. Both start with
   zero documents. Record the importer source selection for restoration.
2. Build `QA2 Zip Map DATE.zip` with four distinct top-level folders A/B/C/D, each
   named with `QA2 Zip Map DATE` plus its letter and a run-time clock suffix, and each
   containing one file `QA2 Map <letter> DATE.txt` with bytes `QA2 Map <letter> DATE`.
   Upload via `/import/documents/upload`, field file, source=generic, CSRF. Record the
   preview folder names; do not commit or rely on automatically inferred mappings.
3. Use the preview fields to map A to M1, B to M2, C to blank and D to a nonexistent
   matter number generated at run time. Save folder choices. Report the exact unknown-
   number refusal. Confirm no import job/documents and no partial save of these choices.
4. Submit all four fields again: A=M1, B=M2, C blank, D blank, do=recheck. Reload preview.
   Confirm A/B saved to the intended new matters and C/D explicitly saved as skip.
   Blank here means intentional skip, not an unresolved folder that should fail import.
5. Commit and let the normal progress page finish. Expect 2 created, 2 skipped,
   0 updated, 0 errors across 4 rows. Record job ID and both created document IDs.
6. Download the two documents. Confirm A bytes only on M1, B bytes only on M2, each
   under Imported; no C/D documents on either matter. Record exact byte comparisons.
7. Upload the identical ZIP again with source=generic. Map A=M2, B=M1, C/D blank,
   Save folder choices and reload. Confirm the preview persisted the swapped mapping.
   No existing document moves simply from saving a preview.
8. Commit that second upload. Expect 0 created, 4 skipped, 0 errors: source+archive-path
   deduplication keeps A on M1 and B on M2 despite the new mapping. Confirm original IDs,
   matter associations and bytes remain. This is repeat-import behavior, not a move tool.
9. Make a third ZIP containing only the earlier skipped C/D folders and original files.
   Upload as generic, map C=M1 and D=M2, commit and finish. Expect 2 created, 0 skipped,
   0 errors: explicitly skipping earlier did not reserve their external paths.
10. Download C and D and compare exact bytes. Confirm M1 now has A/C and M2 has B/D,
    four distinct document IDs total; A/B unchanged. No document lands on another matter.
11. Clean up: close both new matters and report flashes. Retain client, two closed
    matters, four documents and all three completed import jobs. Restore the importer
    source selection if it changed. Do not delete import history or earlier fixtures.
12. What remains: list IDs, mappings, job counts and byte checks; confirm invalid mapping
    rejected the save, explicit blanks skipped, changed mappings did not move previously
    imported paths, and previously skipped paths could be imported later. Return counts
    and a per-case table. No upload tokens, credentials or private URLs.

### S138. Document ZIP saved progress and stale cursor replay (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6077911817 2026-10-09 09:08 UTC

B2-4 progress coverage after S135/S136/S137. Source checked: importer.py
_start_zip_job, _apply_zip, _csv_progress and continue_csv; progress.html cursor
field and automatic continue loop; permissions.py and owner guards. Owner only.
English/ASCII, USD, new fixtures only. No money tools, mail or shared settings.
Replace DATE with today's YYYYMMDD.

1. Create client `QA2 Zip Progress Client DATE` and an hourly USD matter
   `QA2 Zip Progress Matter DATE`, rate $100.00, no office/template. Report flashes,
   IDs and actual matter number. Confirm zero documents. Record importer source selection.
2. Build `QA2 Zip Progress DATE.zip` with one top-level folder matching that actual
   matter number and 25 small ASCII text files. Names are `QA2 Progress 01 DATE.txt`
   through `QA2 Progress 25 DATE.txt`; each contains its matching name without `.txt`.
   Upload via `/import/documents/upload`, field file, source=generic, CSRF. Confirm
   preview has 25 accepted rows mapped only to the new matter, with no documents yet.
3. Commit once using authenticated HTTP requests. Read the progress page without
   executing its JavaScript, which otherwise runs every batch automatically. Record
   job ID, running status and saved cursor 0 of 25. Confirm still zero documents.
   Use this job only throughout; do not stop processes or change server configuration.
4. POST `/import/jobs/<job_id>/continue` with valid CSRF and Accept application/json
   but omit cursor. Expect HTTP 400 with `The import position is missing. Reopen this
   import to continue.` Report the response text. Saved progress stays 0; no documents.
5. POST continue once with cursor=0, valid CSRF and Accept application/json. Expect
   processed=20, total=25, created=20, updated=0, skipped=0, errors=0, done=false.
   The file batch limit is 20. Record the 20 document IDs now on the new matter.
6. Replay continue with the stale cursor=0 and valid CSRF. Expect the same progress
   and counts, still done=false, with the same 20 document IDs and no duplicates.
7. Reload the progress page without executing JavaScript. Confirm saved progress is
   20 of 25 and the resume form has hidden cursor=20. This checks a saved checkpoint
   across requests; it does not claim a server-crash recovery test.
8. POST continue with cursor=20, valid CSRF and Accept application/json. Expect
   processed=25, total=25, created=25, updated=0, skipped=0, errors=0, done=true.
   Confirm committed job and exactly five additional document IDs, 25 total.
9. Replay continue with cursor=20 after completion, then again with cursor=25.
   Both should return the same completed counts, no missing-source error and no new
   documents. Refresh the job detail and confirm the final counts remain unchanged.
10. Download all 25 documents and compare bytes to the matching generated originals.
    Confirm 25 distinct paths in Imported, each current version 1, with no duplicates
    and no files on another matter. Report any mismatch individually.
11. Clean up: close the new matter and report the flash. Restore the prior importer
    source selection if changed. Retain the client, closed matter, 25 documents and
    completed import job. Do not delete history or touch any earlier retained fixture.
12. What remains: list client/matter/job IDs, all document IDs, byte-check counts and
    the 0 to 20 to 25 checkpoints. Confirm missing cursor refused, stale cursor did
    nothing, reload preserved progress, and completed replay did nothing. Return counts
    and a per-case table. Never include upload tokens, credentials or private URLs.

### S139. Document ZIP mapping across preview pages (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6078215706 2026-10-09 09:28 UTC

B2-4 final preview paging coverage after S138. Source checked: importer.py
_zip_plan, preview, _zip_rows and continue_csv; preview_zip.html folder_number fields,
do=page:N, recheck and commit; permissions.py owner-only importer. English/ASCII,
USD, owner only. Replace DATE with today's YYYYMMDD. No money tools, mail or shared
settings. Use only new fixtures. This checks the 25-folder preview page boundary.

1. Create client `QA2 Zip Pages Client DATE` and two hourly USD matters
   `QA2 Zip Pages First DATE` and `QA2 Zip Pages Second DATE`, each $100.00,
   no office/template. Report flashes and IDs; call their matter numbers M1/M2.
   Confirm zero documents and record the importer source for restoration.
2. Build `QA2 Zip Pages DATE.zip` with 26 distinct top-level folders named
   `QA2 Zip Pages DATE <clock> 01` through `26`, where clock is generated at run time.
   Each contains one `QA2 Page NN DATE.txt` with matching ASCII content
   `QA2 Page NN DATE`. Keep a manifest of paths and bytes. Upload field file with
   source=generic to `/import/documents/upload`, using CSRF. No commit yet.
3. Confirm preview has 26 folders and 26 files, page 1 of 2 with 25 folder rows.
   Record actual folder order. Assign the first 25 visible folders to M1 and submit
   the form with do=page:2. Confirm page 2 shows the remaining one folder and no
   documents or import job was created by saving choices.
4. On page 2 submit that folder's field with a nonexistent matter number generated
   at run time and do=page:1. Report the unknown-number refusal. Confirm it stays
   on page 2, no document/job exists, and the invalid choice was not persisted.
5. Replace the page 2 value with M2 and submit do=page:1. Confirm page 1 still shows
   all 25 choices saved as M1. Return to page 2 with Save and next page and verify
   the final folder's saved value is M2. Do not submit hidden or invented folder keys.
6. Clear the final folder's number, save do=recheck, and reload. Confirm its Saved
   label is skip. Then restore M2, save and reload again. Confirm M2 persisted and
   no document/job was created. The first 25 saved choices must remain M1.
7. Return to page 1 with the form's previous-page action. Commit from page 1 using
   its current fields and do=commit. Let normal progress finish. Expect all 26 files
   imported across both pages: 26 created, 0 updated, 0 skipped and 0 errors.
8. Confirm exactly 25 document IDs on M1 and one on M2, matching the preview's actual
   folder order. Download all 26 and compare bytes to the manifest. Every document
   has current version 1 in Imported. No document belongs to another matter.
9. Re-submit the same original preview commit with fresh CSRF after completion.
   Expect a redirect to the existing job, not a second job or duplicate documents.
   Confirm original job ID/counts and all 26 document IDs unchanged. Keep the preview
   token private; never include it or its URL in the result.
10. Reload that preview URL with GET. Expect the same completed job again. Download
    the M2 document once more and confirm identical bytes and version 1. Record
    that the second page was included when commit originated from page 1.
11. Clean up: close both new matters and report flashes. Restore original importer
    source selection if changed. Retain client, two closed matters, 26 documents and
    the single completed import job. Do not delete import history or earlier fixtures.
12. What remains: list IDs, per-matter document counts, byte checks and job totals.
    Confirm invalid mapping refused, choices survived page switches, skip could be
    undone before commit, all pages imported and duplicate commit reused the job.
    Return counts and a per-case table. No tokens, credentials or private URLs.

### S140. Document importer owner boundary on preview and progress (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6078514699 2026-10-09 09:49 UTC

B2-4 closing role check after S139, not another archive-shape batch. Source checked:
importer.py index/upload/preview/job/continue_csv/failed_csv owner guards;
settings.py user_new/user_edit, settings/user_form.html fields; permissions.py.
Owner and two new non-owner sessions only. English/ASCII/USD. Replace DATE with
today's YYYYMMDD. No money tools, mail, provider or shared-setting changes.

1. As owner create client `QA2 Import Access Client DATE` and hourly USD matter
   `QA2 Import Access Matter DATE`, $100.00, no office/template. Report flashes and
   IDs; confirm no documents. Record importer source selection for restoration.
2. Create active users `QA2 Import Attorney DATE` and `QA2 Import Billing DATE`,
   roles attorney and billing, respective emails qa2-import-attorney-DATE@coil.test
   and qa2-import-billing-DATE@coil.test, hourly_rate=100, no office. Use strong
   temporary passwords kept private. Report flashes/IDs and sign into isolated
   sessions. Do not alter existing users, generate API tokens or configure voice.
3. Owner submits `/import/documents/upload` with source=generic and CSRF but no file.
   Expect `Choose a file to upload.` Confirm no job/document. Then upload a valid
   `QA2 Import Access DATE.zip` containing one file `QA2 Import Access DATE.txt`
   under the new matter's actual number, with bytes `QA2 Import Access DATE`.
   Confirm owner preview maps to the new matter and no job/document exists yet.
4. Attorney requests `/import` and the owner's exact preview URL, then POSTs a
   valid ZIP to `/import/documents/upload` with their own session CSRF. Expect
   HTTP 403 for all. Confirm no job or document appeared. A missing-CSRF refusal
   does not prove the role check; use a valid token from that session.
5. Billing repeats the same GETs and upload POST with its own CSRF. Expect 403
   throughout despite billing's exports permission. Confirm no imported document.
6. Both non-owner sessions POST do=commit to the owner's existing preview URL with
   their own valid CSRF. Expect 403 for each. Owner reloads preview and confirms
   mapping unchanged, no job/document created. Never print the preview token or URL.
7. Owner commits that preview once using HTTP without running progress-page JavaScript.
   Record running job ID, saved cursor 0 of 1 and zero documents. Keep this request
   controlled so the next case tests a genuinely unfinished job.
8. Both non-owner sessions GET `/import/jobs/<job_id>` and its `/failed.csv`, then
   POST `/continue` with cursor=0, their own CSRF and Accept application/json.
   Expect 403 for every request. Owner confirms cursor remains 0 and no documents.
9. Owner POSTs continue with cursor=0 and valid CSRF. Expect processed=1, total=1,
   created=1, updated=0, skipped=0, errors=0, done=true. Download the one new document
   and confirm exact bytes, version 1, Imported folder and intended matter.
10. Both non-owners repeat job GET, failed.csv GET and continue POST after completion.
    Expect 403 throughout. Owner repeats continue with cursor=0: expect unchanged
    completed counts and same document ID. Confirm no duplicate document or job.
11. Clean up as owner: deactivate only the two new users through their edit forms,
    preserving other fields and omitting is_active. Expect `User saved.` and confirm
    both inactive. Close the new matter and report flash; restore importer source.
    Retain client, closed matter, document, completed job and inactive test users.
    All earlier fixtures remain untouched.
12. What remains: list IDs and per-role HTTP status matrix for upload, preview, job,
    error export and continue before/after completion. Confirm zero writes by the
    refused roles, exact owner download and duplicate continuation unchanged.
    Return counts and a per-case table. No credentials, tokens or private links.

### S141. Notes CSV failed-row repair and duplicate policy (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6078942866 2026-10-09 10:19 UTC

B2-4 importer regression after the ZIP completion/role checks. Money importers
remain deferred while Bot 1 holds billing. Source checked: importer.py prep_notes,
apply_notes, mapping/options, _commit and failed_csv; _importmap.py note fields;
importer/preview.html map_FIELD, duplicates and do fields; permissions.py.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. No mail,
money, provider changes or earlier fixtures. Keep source=generic throughout.

1. Create client `QA2 Note Import Client DATE` and hourly USD matters
   `QA2 Note Import First DATE` and `QA2 Note Import Second DATE`, $100.00,
   no office/template. Report flashes/IDs and matter numbers M1/M2. Confirm no notes
   on either. Record importer source selection for cleanup.
2. Build `QA2 Note Import DATE.csv` with headers external_id,matter_number,body,date,
   subject,author and three rows. IDs are `QA2 Note DATE A`, B and C. A: M1, body
   `QA2 Note Body A DATE`, date 2028-02-29 12:00, subject/author blank. B: M1,
   empty body, same date, subject/author blank. C: a nonexistent matter number
   generated at run time, body `QA2 Note Body C DATE`, same date, subject/author blank.
   Upload file to `/import/notes/upload` as generic with CSRF. Explicitly map each
   header to its matching field using map_FIELD, set duplicates=update and recheck.
3. Confirm preview has one create and two errors. B says `Note is empty.` and C
   names the missing matter. No notes have been created by preview. Commit this
   small import; report flash/job ID. Expect 1 created, 0 updated, 0 skipped and
   2 errors. Confirm only A exists on M1, with exact body and the supplied leap date.
4. Download this job's failed.csv as owner. Parse CSV and confirm exactly the two
   failed original rows B/C plus their Import error messages. A must not appear.
   Preserve the generated unknown number privately for comparison, no existing ID reuse.
5. Build a repair CSV with just B and C using the same external IDs. B now has body
   `QA2 Note Body B DATE` on M1; C now uses M2 with its original body. Keep the date.
   Upload, map, preview and commit. Expect 2 created, no errors. Confirm A/B on M1,
   C on M2, three distinct note IDs total. Report new job ID and exact bodies.
6. Re-upload the repaired B/C CSV unchanged, explicitly choose duplicates=skip,
   recheck and commit. Expect 0 created, 0 updated, 2 skipped, no errors. IDs, dates,
   bodies and matter associations remain unchanged.
7. Build a CSV with only B's existing external ID, M1 and body
   `QA2 Note Changed B DATE`, same date. Upload/map with duplicates=skip and commit.
   Expect one skipped row; B keeps its original body and ID.
8. Upload the same changed B CSV again, but choose duplicates=update. Commit.
   Expect 0 created, 1 updated, 0 skipped, no errors. Confirm B has the changed body
   under the same note ID on M1, with A/C unchanged and only three notes overall.
9. Build another B-only CSV restoring its original body `QA2 Note Body B DATE` and
   retaining M1/date. Import with duplicates=update. Expect one updated row and B's
   original body restored, same ID. Confirm no duplicate note from undoing the edit.
10. Reopen the first failed job and download failed.csv again. Confirm historical
    errors still contain original B/C failed rows even though later jobs repaired
    them. Check all six job IDs and counts; no unrelated notes or matters changed.
11. Clean up: close both new matters and report flashes. Restore importer source
    selection if changed. Retain client, two closed matters, notes A/B/C and six
    completed import jobs, including the original job with two errors. Do not delete
    history or alter earlier fixtures.
12. What remains: list all IDs/counts, failed-row checks, bodies and leap-date values.
    Confirm preview wrote nothing, repair created only failed rows, skip preserved
    existing content and update/restore kept B's ID. Return counts and a per-case
    table. Never include tokens, credentials or private URLs.

### S142. Notes importer required mapping and safe failed-row CSV (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6079229186 2026-10-09 10:38 UTC

B2-4 failed-row export boundary after S141. Source checked: importer.py prep_notes,
_mapping_from_form, _commit and failed_csv; _importmap.py required Note field;
helpers.py csv_safe; importer/preview.html map_FIELD/duplicates/do; permissions.py.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. No money,
mail, providers or shared settings. Examine CSV as text, never execute cell formulas.

1. Create client `QA2 CSV Safety Client DATE` and hourly matter
   `QA2 CSV Safety Matter DATE`, $100, no office/template. Report flashes/IDs and
   matter number M1; confirm no notes. Record importer source selection.
2. Build `QA2 CSV Safety DATE.csv` with external_id,matter_number,body,subject headers.
   Four IDs are `QA2 CSV Safety DATE A` through D. Give every row the same nonexistent
   matter number generated at run time. Bodies A/B/C/D are respectively `=1+1`,
   `+QA2 Text DATE`, `@QA2 Text DATE`, `-QA2 Text DATE`; subjects blank. Upload to
   `/import/notes/upload`, source=generic, file field and CSRF. These are inert text
   samples only, with no links, commands or external references.
3. Explicitly map external_id and matter_number but clear map_body. Submit do=commit
   with duplicates=update and CSRF. Expect `Map these required fields first: Note`.
   Confirm no job or note created. Do not count disabled UI alone as the refusal.
4. Restore all matching field mappings including map_body=body, recheck and commit.
   Expect 0 created, 0 updated, 0 skipped, 4 errors, each naming the missing matter.
   Report flash/job ID. Confirm no notes created on any of this batch's records.
5. Download this job's failed.csv as text and parse it with a CSV parser. Expect
   four original failed rows plus Import error. Each formula-like body must have
   one leading apostrophe before its original text. IDs and missing matter values
   remain intact. Do not open the file in a spreadsheet that evaluates formulas.
6. Build a corrected CSV from the original, not the escaped export: change each
   matter_number to M1 and bodies to `QA2 CSV Safe Body <letter> DATE`. Keep IDs.
   Upload/map/commit as generic. Expect 4 created, no errors; record all note IDs
   and verify exact English bodies on the new matter.
7. Repeat that corrected CSV with duplicates=skip. Expect 0 created, 0 updated,
   4 skipped, no errors. Confirm original four note IDs/bodies unchanged.
8. Import one A-only row with the same external ID/M1 and body
   `QA2 CSV Revised A DATE`, duplicates=update. Expect 1 updated, no creation/error.
   Confirm A changed under its existing ID; B/C/D remain unchanged.
9. Download the original failed.csv again. Confirm the same four escaped bodies
   remain in its historical errors despite the later repair/update. The successful
   repair job's failed.csv should contain its header and no failed data rows.
10. Upload an A-only row with the same external ID/M1 but empty body, duplicates=update.
    Commit after mapping. Expect 1 error `Note is empty.`, 0 updated and 0 created.
    Confirm the saved revised A body was not erased and four note IDs still exist.
11. Clean up: close the new matter and report flash; restore importer source.
    Retain client, closed matter, four notes and five completed import jobs (original
    four-error job, repair, repeat-skip, A-update and empty-body error). Earlier
    fixtures remain untouched. Do not delete error history.
12. What remains: list all IDs/counts, required-mapping refusal, escaped failed cells,
    unchanged historical export and empty-body update refusal. Return counts and a
    per-case table. No credentials, upload tokens or private links.

### S143. Notes importer subject merge and matter reassignment (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6079569978 2026-10-09T11:01:57.296432+00:00

B2-4 note identity coverage after S141/S142. Source checked: importer.py prep_notes,
apply_notes, external refs and mapping/options; _importmap.py fields;
importer/preview.html form; permissions.py. Owner only. English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No money tools, mail or shared settings.
Use only this batch's records; source=generic and explicit external IDs throughout.

1. Create client `QA2 Note Move Client DATE` and hourly USD matters
   `QA2 Note Move First DATE` and `QA2 Note Move Second DATE`, $100 each,
   no office/template. Report flashes/IDs and numbers M1/M2. Confirm zero notes on
   both and record importer source for restoration.
2. Create `QA2 Note Move DATE.csv` with headers external_id,matter_number,body,subject,
   author,date. One row: ID `QA2 Note Move DATE A`, M1, body `QA2 Body A DATE`,
   subject `QA2 Subject A DATE`, author blank, date 2028-02-29 12:00. Upload via
   `/import/notes/upload`, source=generic/file/CSRF. Map each header to its same field,
   choose duplicates=update, recheck then commit. Expect one created and no errors.
3. Inspect the note on M1: subject followed by two newlines and body, date February
   29, 2028, attributed to current owner. Record note ID. No note on M2.
4. Import the same ID/M1/date with body containing the full subject once, followed
   by `QA2 Revised Body DATE`, and the same subject field. Choose update. Expect
   one updated, no creation; same note ID and no duplicate subject prefix.
5. Import same ID with M2 and body `QA2 Moved Body DATE`, subject/author blank,
   date unchanged, duplicates=skip. Expect one skipped: note remains on M1 with
   the previously saved body, nothing on M2. Preserve its existing ID.
6. Re-upload that same M2 row with duplicates=update. Expect one updated, no creation.
   Confirm same note ID now on M2 and absent from M1, exact new body, date preserved.
   This importer can update the association of a note identified by external ID.
7. Attempt same-ID update back to M1 with whitespace-only body, subject/author blank.
   Commit using the body mapping. Expect one error `Note is empty.`, zero updates.
   Confirm the existing note remains on M2 with its saved body/date unchanged.
8. Import the same ID back to M1 with body `QA2 Restored Body DATE`, blank subject,
   date unchanged, duplicates=update. Expect one update. Confirm original ID moves
   back to M1, M2 empty and exactly one note across the two matters.
9. Upload this restored row twice in a single CSV, same ID and identical content,
   duplicates=skip. Expect two skipped rows, no creation/update/error. Confirm just
   one note and unchanged body/date. No duplicate note is created by repeated rows.
10. Reopen all seven completed jobs and compare counts: initial create; three earlier
    operations (subject update, move skip, move update); empty-body error; restore
    update; duplicate skip. Confirm error history remains and final note ID matches
    the initial one. Do not infer count from the whole firm's import history.
11. Clean up: close both new matters and report flashes; restore importer source.
    Retain client, two closed matters, the one note on M1 and seven completed jobs.
    Leave all earlier retained notes, documents, users and matters untouched.
12. What remains: list IDs, subject/body comparisons, leap date, move/skip/restore
    transitions and job counts. Return counts and a per-case table. No credentials,
    tokens or private preview links.

### S144. Notes CSV progress with a failed row at the batch boundary (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6079816563 2026-10-09T11:18:44.733974+00:00

B2-4 CSV checkpoint coverage. Source checked: importer.py CSV_BATCH_ROWS=100,
_start_csv_job, continue_csv, prep_notes, run_import and failed_csv;
importer/progress.html cursor and automatic JavaScript loop; preview mapping fields
and permissions.py. Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD.
No money, mail, provider or shared-setting changes. No server interruption tests.

1. Create client `QA2 CSV Progress Client DATE` and hourly matter
   `QA2 CSV Progress Matter DATE`, $100.00, no office/template. Report flashes/IDs,
   actual matter number M1 and zero notes. Record importer source for restoration.
2. Build `QA2 CSV Progress DATE.csv` with 105 data rows and headers external_id,
   matter_number,body. IDs `QA2 CSV Progress DATE 001` through 105; all use M1.
   Bodies `QA2 CSV Progress Body DATE NNN`, except data row 100 has an empty body.
   Upload to `/import/notes/upload`, source=generic/file/CSRF. Explicitly map headers,
   choose duplicates=update, recheck. Confirm no notes created by preview. Preview
   may show only its bounded sample; do not require all 105 rows to be displayed.
3. Commit using HTTP and read progress without executing its JavaScript. Confirm
   running job, saved cursor 0, total 105 and zero notes. Record job ID. Keep manual
   control of continuation requests so every checkpoint can be inspected.
4. POST its continue route with valid CSRF and cursor=not-a-number, Accept
   application/json. Expect HTTP 400 with `The import position is missing. Reopen this import to continue.`
   Confirm cursor 0 and no note written.
5. POST continue once with cursor=0. Expect processed=100, total=105, created=99,
   updated=0, skipped=0, errors=1, done=false. Confirm 99 notes with IDs 001 through
   099 from the CSV, and the error for external ID 100 says `Note is empty.`
6. Replay cursor=0 with fresh CSRF. Expect unchanged 100/105 checkpoint, 99 created
   and one error, with no duplicate notes or repeated error. Reload progress without
   JavaScript; confirm hidden cursor 100 and saved progress 100 of 105.
7. POST continue with cursor=100. Expect processed=105, total=105, created=104,
   updated=0, skipped=0, errors=1, done=true and committed status. Confirm notes
   101 through 105 added, no note for 100 and no duplicate of the first 99.
8. Replay cursor=100 after completion. Expect unchanged completed counts and same
   104 note IDs. Download failed.csv and confirm exactly one failed row, original
   external ID 100 with empty body and `Note is empty.` No successful row included.
9. Build a one-row repair CSV using original ID 100, M1 and body
   `QA2 CSV Progress Body DATE 100`. Upload/map/commit as generic/update. Expect
   one created, no errors; record second job and new note ID. Total notes now 105.
10. Verify every note body against the generated manifest and all 105 IDs distinct.
    Reopen the first job: it must still report 104 created and one historical error,
    despite the repair. Second job reports one created. No additional job was made
    by stale or completed continuation requests.
11. Clean up: close the new matter and report flash; restore importer source.
    Retain client, closed matter, 105 notes and the two completed jobs. Do not erase
    the failed-row history or touch any older fixtures.
12. What remains: list client/matter/job IDs and note IDs, checkpoint counts, one
    historical error, repair count and 105 body comparisons. Return counts and a
    per-case table. No credentials, upload tokens or private links.

### S145. Calendar CSV end-date defaults and failed-update preservation (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6080104990 2026-10-09T11:38:43.370174+00:00

B2-4 importer regression, extending completed calendar coverage while money importers
and shared invoice settings remain deferred. Source checked: importer.py upload,
prep_calendar, _calendar_datetime, apply_calendar and preview; _importmap.py calendar
fields; calendar.py _event_error; importer/preview.html; permissions.py. Owner only.
English/ASCII/USD. Replace DATE with today's YYYYMMDD. No mail, reminders, feeds,
provider settings or money tools. Use only new records and source=generic.

1. Create client `QA2 Calendar CSV Client DATE` and hourly USD matter
   `QA2 Calendar CSV Matter DATE`, $100, no office/template. Report flashes, IDs and
   matter number M1. Record importer source for restoration and confirm no events.
2. Build `QA2 Calendar CSV DATE.csv` with headers external_id,title,starts_at,ends_at,
   all_day,matter_number,location,description. Row A: ID `QA2 Calendar CSV DATE A`,
   title `QA2 Calendar A DATE`, start 2028-02-29 12:00, end blank, all_day=false,
   M1, location `QA2 Room A DATE`, description `QA2 Calendar Body A DATE`.
   Upload to `/import/calendar/upload` using source, file and CSRF. Explicitly map
   each matching header, duplicates=update, recheck. Confirm preview writes no event.
3. Commit with do=commit. Expect one created, no errors. Inspect A's ID, matter,
   title/location/description and local wall-clock start noon, end 13:00 on leap day.
   A missing timed end defaults to one hour. Report the flash.
4. Upload same ID with start 2028-03-01 12:00 and earlier end 2028-03-01 11:00,
   title `QA2 Calendar Revised A DATE`, otherwise unchanged, duplicates=update.
   Commit and expect one updated, same ID. The importer replaces the earlier end
   with its one-hour default: March 1 noon to 13:00. This is designed behavior.
5. Attempt same-ID update with ends_at=not-a-date, start unchanged. Commit after
   mapping and expect one row error `Could not read end 'not-a-date'.`, zero updates.
   Inspect A and confirm all saved values from the prior case remain intact.
6. Download this failed job's CSV as text. Expect one failed row with the unchanged
   external ID, invalid end and Import error column. Do not expose upload tokens.
7. Repair that original row to start 2028-03-01 12:00, end 2028-03-01 14:00.
   Upload/map/commit with update. Expect one updated, same A ID, noon to 14:00.
   Reopen the earlier failed job and confirm its error history remains unchanged.
8. Import same A ID with title `QA2 Calendar Skipped A DATE` and end 15:00,
   duplicates=skip. Expect one skipped, no update/create/error. Confirm A retains
   its revised title and 14:00 end under its original ID.
9. Import row B with new ID `QA2 Calendar CSV DATE B`, title `QA2 Calendar B DATE`,
   start 2028-02-29, end blank, all_day=true, M1, location/description blank.
   Expect one created, no errors. Confirm an all-day event on February 29 with no
   explicit end, separate from timed A. Record B ID; do not open a calendar feed.
10. Attempt B update with whitespace-only title, otherwise unchanged. Map title and
    commit. Expect one error `Event has no title.`, zero updates. Confirm B's saved
    title and all-day date remain intact, and only two batch events exist.
11. Clean up: close the new matter and report flash; restore importer source.
    Retain client, closed matter, events A/B and seven completed jobs: create A,
    update default, invalid end, repair, skip, create B, invalid title.
    Leave every earlier fixture untouched. Do not create reminders or send messages.
12. What remains: list client/matter/event/job IDs, counts, missing/earlier-end
    defaults, failed-update preservation, skip evidence and all-day leap date.
    Return counts and a per-case table. No credentials, tokens or private links.

### S146. Task CSV completion undo and duplicate preservation (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6080405134 2026-10-09T11:59:08.077869+00:00

B2-4 task importer regression while money importers and shared settings remain deferred.
Source checked: importer.py prep_tasks/apply_tasks/upload/preview/_commit;
_importmap.py task fields; importer/preview.html mappings and options; permissions.py.
Owner only. English/ASCII/USD. Replace DATE with today's YYYYMMDD. No mail, reminders,
feeds, provider settings or money tools. Use source=generic and only new batch records.

1. Create client `QA2 Task CSV Client DATE` and hourly USD matter
   `QA2 Task CSV Matter DATE`, $100, no office/template. Report flashes and IDs,
   matter number M1, zero tasks and importer source for restoration.
2. Build `QA2 Task CSV DATE.csv` with external_id,title,matter_number,due_on,assignee,
   done,priority,notes headers. Row A: ID `QA2 Task CSV DATE A`, title
   `QA2 Task Deadline DATE`, M1, due 2028-02-29, assignee blank, done=false,
   priority=urgent, notes `QA2 Task Body DATE`. Upload to `/import/tasks/upload`
   with source=generic/file/CSRF. Explicitly map each header, duplicates=update,
   recheck. Confirm preview writes no task.
3. Commit. Expect one created, no errors. Inspect task A ID, leap-day due date,
   incomplete state, high priority, deadline kind, no assignee and exact notes.
   Report flash. If a field is not exposed in UI, report that evidence limitation.
4. Import same A ID with done=true, otherwise unchanged. Expect one updated, no
   creation. Confirm same task now completed and completion time recorded where
   exposed. Do not infer a missing field from an API response that redacts it.
5. Import same ID with done=false and priority=low, duplicates=skip. Expect one
   skipped, no update. Confirm A stays completed/high under its original ID.
6. Repeat that same row with duplicates=update. Expect one updated, same ID, now
   incomplete and low priority, with completion time cleared where exposed.
   Due date, matter and notes stay intact.
7. Attempt same-ID update with whitespace-only title, done=true and priority=urgent.
   Commit after mapping title. Expect one row error `Task has no title.`, zero
   updates. Confirm A remains incomplete/low with its saved title and notes.
8. Repair that original row with title `QA2 Task Hearing DATE`, done=true,
   priority=critical, same ID/M1/date/notes. Expect one updated, no creation.
   Confirm same task is complete/high, kind court_date, still due February 29.
9. Import same ID with title `QA2 Task Ordinary DATE`, done=false, priority=normal.
   Expect one updated. Confirm original ID, incomplete/normal, kind task, and
   unchanged M1, leap-day date and notes. The importer recalculates kind from title.
10. Upload two identical copies of the final row with duplicates=skip. Expect two
    skipped, no creation/update/error, one batch task. Reopen seven completed jobs:
    create, complete, skip, undo, title error, repair and ordinary update; then this
    eighth job. Original title-error history must remain unchanged.
11. Clean up: close the new matter and report flash; restore importer source.
    Retain client, closed matter, one incomplete task and eight completed jobs.
    Do not send reminders, delete history or change any earlier fixtures.
12. What remains: list IDs, job counts, complete/skip/undo transitions, failed-update
    preservation, priority/kind changes and leap-day evidence. Return counts and
    a per-case table. Never include credentials, tokens or private links.

### S147. Task CSV unresolved references and repair by external ID (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6080729714 2026-10-09T12:19:05.707595+00:00

B2-4 importer regression after task completion coverage. Source checked: importer.py
prep_tasks/apply_tasks/resolve_user/upload/preview, _importmap.py task fields,
importer/preview.html mapping/options and permissions.py. Owner only. English/USD.
Replace DATE with today's YYYYMMDD. No money tools, mail, reminders, provider or
shared settings. Use source=generic and explicit external IDs. Warnings below are
accepted importer behavior, not refusals. Do not change any existing user.

1. Create client `QA2 Task Link Client DATE` and hourly USD matter
   `QA2 Task Link Matter DATE`, $100, no office/template. Report flashes/IDs and M1.
   Record importer source and the current owner's exact existing name for assignment.
2. Build nonexistent matter number and nonexistent assignee name at runtime, each
   with QA2/date and a fresh suffix; confirm neither matches an existing record.
   Build `QA2 Task Link DATE.csv` with external_id,title,matter_number,due_on,assignee,
   done,priority,notes. Row A: ID `QA2 Task Link DATE A`, title `QA2 Task Link A DATE`,
   nonexistent matter and assignee, due 2028-02-29, done=false, priority=normal,
   notes `QA2 Task Link Body DATE`. Upload to `/import/tasks/upload` with source,
   file and CSRF, explicitly map headers, update, recheck. No task created yet.
3. Commit. Expect one created with warnings, no row error. Report exact warnings
   about missing matter and unknown assignee. Confirm A exists once, without a
   matter or assignee, with its leap-day due date and exact title/notes. Record ID.
4. Re-import same external ID with M1 and current owner's exact name, update.
   Expect one updated, no new task. Confirm original task ID now links M1 and owner,
   preserving due date, incomplete state and notes. Report flash and job ID.
5. Re-import same ID with the original nonexistent references, duplicates=skip.
   Expect one skipped, no creation/update. Report warnings if shown. Confirm saved
   M1 and owner links remain intact. Skip must not detach the existing task.
6. Repeat that row with duplicates=update. Expect one updated with warnings.
   Confirm same ID now has neither matter nor assignee. This importer deliberately
   replaces unresolved associations with empty values; record this as designed.
7. Repair again with M1 and owner, same external ID/update. Expect one updated,
   no creation and original ID linked correctly again. Exactly one task exists.
8. Attempt same-ID update with whitespace-only title and blank matter/assignee.
   Commit with title mapping. Expect one error `Task has no title.`, zero updates.
   Confirm refusal preserves saved title, M1, owner, due date and body.
9. Download failed.csv for that error job as text. Expect one original failed row
   with matching external ID and Import error. Earlier successful warning jobs
   must have no failed data rows; warnings do not make a row a failed import.
10. Upload two identical repaired rows using the same external ID, duplicates=skip.
    Expect two skipped, no creation/update/error. Confirm one task with original
    ID and repaired links. Reopen all seven jobs and preserve warning/error history.
11. Clean up: close the new matter, report flash and restore importer source.
    Retain client, closed matter, one incomplete task assigned to current owner,
    seven completed jobs and their histories. Leave all older fixtures unchanged.
12. What remains: list IDs/counts, unresolved-reference warnings, skip preservation,
    detach/repair transitions, title refusal and CSV distinction between warnings
    and errors. Return counts and a per-case table. No credentials or private links.

### S148. Notes CSV external IDs stay separate by source (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6083683073 2026-10-09T15:11:40.100836+00:00

B2-4 source identity regression. Source checked: importer.py ref_get/ref_set,
_source_from_form, prep_notes/apply_notes/upload/preview; _importmap.py note fields;
importer/index.html and preview.html; permissions.py. Owner only, English/USD.
Replace DATE with today's YYYYMMDD. No money tools, mail, provider settings or feeds.
The Clio selector here only labels a local CSV source; never connect to a provider.
Use only this batch's external ID and matter, preserving all earlier fixtures.

1. Create client `QA2 Source Note Client DATE` and hourly USD matter
   `QA2 Source Note Matter DATE`, $100, no office/template. Report flashes/IDs and
   M1, confirm zero notes, and record importer source for restoration.
2. Build `QA2 Source Note DATE.csv` with external_id,matter_number,body,date headers.
   One row: ID `QA2 Source Note DATE A`, M1, body `QA2 Generic Body DATE`,
   date 2028-02-29 12:00. Upload to `/import/notes/upload` with source=generic,
   file and CSRF. Explicitly map all four fields, duplicates=update, recheck;
   confirm preview writes no note.
3. Commit and report flash/job ID. Expect one created, no error. Record note G ID,
   exact body and leap date. The note belongs to M1 and current owner.
4. Upload the same external ID/M1/date with source=clio and body
   `QA2 Clio Body DATE`. Explicitly map the same headers, update, commit.
   Expect one created, not updated: record distinct note C ID. Both notes remain
   on M1 with their respective bodies. Source is part of external-ID identity.
5. Repeat the clio row with body `QA2 Clio Skipped DATE`, duplicates=skip.
   Expect one skipped, no update/create. C retains its original body; G unchanged.
6. Repeat with source=generic, body `QA2 Generic Revised DATE`, duplicates=update.
   Expect one updated, original G ID changes body; C's ID/body remain unchanged.
7. Import source=clio same ID with body `QA2 Clio Revised DATE`, update.
   Expect one updated, original C ID changes body; G retains its revised body.
8. Attempt generic same-ID update with whitespace-only body. Commit with body mapped.
   Expect one error `Note is empty.`, zero updates. Both saved IDs and revised bodies
   remain intact. Download failed.csv as text: exactly one failed original row.
9. Restore generic same-ID body to `QA2 Generic Body DATE`, update. Expect one
   updated under G's original ID, C unchanged, exactly two notes on M1.
10. Repeat the restored generic row twice in one CSV with duplicates=skip. Expect
    two skipped, no create/update/error. Confirm G original body, C revised body,
    distinct original IDs and dates preserved. Reopen all eight completed jobs:
    generic create, clio create, clio skip, generic update, clio update, empty error,
    generic restore and double skip. Their source labels/counts must agree.
11. Clean up: close the new matter and report flash; restore original importer source.
    Retain client, closed matter, both notes and eight completed jobs including error
    history. Leave all earlier notes and source mappings untouched.
12. What remains: list IDs, job sources/counts, independent same-ID notes, skip/update
    isolation, empty-body refusal and restore evidence. Return counts and a per-case
    table. Never disclose credentials, upload tokens or private links.

### S149. Notes CSV quoted multiline text and delimiter round trips (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6084495930 2026-10-09T15:59:54.945132+00:00

B2-4 CSV parser regression. Source checked: importer.py _parse_csv/upload,
prep_notes/apply_notes and mapping/options; importer/index.html and preview.html;
permissions.py. Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD.
No money, mail, settings or provider connections. Use source=generic throughout.
Construct files with a CSV writer, not hand-built escaping; compare stored body text
with the original manifest, allowing only removal of leading/trailing whitespace.

1. Create client `QA2 Quoted Note Client DATE` and hourly USD matter
   `QA2 Quoted Note Matter DATE`, $100, no office/template. Report flashes/IDs and
   number M1. Confirm zero notes; record importer source for restoration.
2. Generate UTF-8 with BOM comma CSV `QA2 Quoted Note DATE.csv`, headers
   external_id,matter_number,body,date. Row A ID `QA2 Quoted Note DATE A`, M1,
   date 2028-02-29 12:00. Its body has two lines: first `QA2 He said "Hello", DATE`,
   second `QA2 Second line; still one note DATE`. Add one completely empty data row.
   Upload to `/import/notes/upload`, source/file/CSRF; explicitly map all headers,
   update, recheck. Confirm preview creates no notes and ignores the blank row.
3. Commit. Expect one created, no errors. Inspect A ID and exact body: embedded
   quotes, comma, semicolon and internal newline preserved, leap date correct.
   No quote escapes or extra row should become a second note. Report flash/job ID.
4. Write the same original row with a semicolon CSV writer, retaining comma and
   quotes inside the body. Upload/map/commit with duplicates=skip. Expect one
   skipped, no create/update/error, unchanged A ID/body.
5. Write tab-delimited CSV with the same ID/M1/date and two-line revised body:
   `QA2 Revised "Hello", DATE` then `QA2 Revised second; line DATE`.
   Upload/map/commit with update. Expect one updated, original A ID and exact new
   body, including internal newline and quotes. No extra note.
6. Import comma CSV row B with new ID `QA2 Quoted Note DATE B`, M1, same date,
   body `QA2 Plain Body DATE`. Expect one created; B ID distinct from A.
   Confirm A's multiline revised body remains unchanged.
7. Import same A ID with whitespace-only body, update. Commit with body mapping.
   Expect one error `Note is empty.`, zero updates. Confirm A/B saved content remains.
8. Repair A to its original two-line body using the original BOM comma CSV and update.
   Expect one updated, same A ID and exact original body. B stays unchanged.
9. Upload both valid A and B rows plus an entirely empty row, duplicates=skip.
   Expect two skipped, no create/update/error. Exactly two notes with original IDs.
   Empty CSV records are ignored; do not count physical lines inside quoted fields.
10. Reopen all seven completed jobs: create A, semicolon skip, tab update, create B,
    empty-body error, restore A and combined skip. Counts match the logical rows.
    The empty-body error job still retains its failed row after repair.
11. Clean up: close new matter, report flash and restore importer source. Retain
    client, closed matter, two notes and seven completed jobs. Keep safe local CSV
    manifests; leave earlier records and job histories untouched.
12. What remains: list IDs/counts, delimiter and BOM handling, exact quoted multiline
    body comparisons, blank-row skip and failed-update preservation. Return counts
    and a per-case table. Never include credentials, tokens or private links.

### S150. Notes CSV date preservation and author fallback (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6084983842 2026-10-09T16:29:35.843442+00:00

B2-4 importer regression while shared money tools remain deferred. Source checked:
importer.py prep_notes/apply_notes/resolve_user/upload/preview; _importmap.py note
fields and parse_any_datetime; importer/preview.html; permissions.py. Owner only.
English/USD. Replace DATE with today's YYYYMMDD. No money, mail, users changes,
provider settings or feeds. Use source=generic and explicit external IDs throughout.
Invalid or blank dates on an existing note deliberately preserve its saved date.

1. Create client `QA2 Note Date Client DATE` and hourly USD matter
   `QA2 Note Date Matter DATE`, $100, no office/template. Report flashes and IDs/M1.
   Record importer source, current owner's exact name/ID, and confirm zero notes.
2. Create `QA2 Note Date DATE.csv`, headers external_id,matter_number,body,date,author.
   Row A: ID `QA2 Note Date DATE A`, M1, body `QA2 Note Date Original DATE`,
   date 2028-02-29 12:00, current owner's exact name. Upload /import/notes/upload
   with source/file/CSRF, map every header, update, recheck. No note written yet.
3. Commit and report flash/job ID. Expect one created, no error. Record note A ID,
   exact body, owner and leap-day timestamp. Use this ID for all subsequent checks.
4. Same-ID update: body `QA2 Note Date Blank DATE`, date blank, author blank.
   Commit, expect one updated. Same ID has new body, same saved leap-day timestamp
   and current owner. A blank imported date does not clear an existing timestamp.
5. Same-ID update: body `QA2 Note Date Invalid DATE`, date `not-a-date`, author blank.
   Expect one updated and unchanged timestamp, not a row error. Confirm same ID/body.
6. Same-ID update: body `QA2 Note Date March DATE`, date 2028-03-01 09:30,
   author current owner's exact name in uppercase. Expect one updated, same ID,
   exact new timestamp/body and same owner. User-name matching ignores case.
7. Build nonexistent author `QA2 Missing Note Author DATE` with a fresh suffix;
   confirm it matches no user. Update A with that author, body
   `QA2 Note Date Fallback DATE`, date blank. Expect one updated with an author
   warning, no row error. Report exact warning. Owner falls back to current user;
   saved March timestamp remains. Do not create or modify any user.
8. Same-ID row with date 2028-02-29 12:00 and body `QA2 Note Date Skip DATE`,
   duplicates=skip. Expect one skipped, no update; March timestamp and fallback
   body/owner remain. Use current owner's name as author.
9. Same-ID update with whitespace-only body, original leap date and owner name.
   Expect one error `Note is empty.`, zero updates. Saved March timestamp, fallback
   body and owner remain unchanged. Download failed.csv: exactly one failed row.
10. Restore original body, leap-day timestamp and exact owner name using update.
    Expect one updated, same A ID, no error. Confirm exactly one note on M1.
    Reopen all eight jobs: create, blank date, invalid date, March date, unknown
    author, skip, empty-body error and restore. Warning job has no failed row;
    error job retains its original failed row after repair.
11. Clean up: close new matter, report flash, restore importer source. Retain
    client, closed matter, original restored note and eight jobs with histories.
    Leave every older fixture and all users untouched.
12. What remains: IDs/counts, date preservation, case-insensitive author resolution,
    fallback warning, skip/refusal preservation and restored values. Return counts
    and a per-case table. Never disclose credentials, tokens or private links.

### S151. Task CSV repeated IDs and row ordering (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6085617318 2026-10-09T17:09:49.855050+00:00

B2-4 importer regression while money tools remain with Bot 1. Source checked:
importer.py prep_tasks/apply_tasks/run_import/ref_get/ref_set/upload/preview,
_importmap.py task fields, importer/preview.html and permissions.py. Owner only.
English/USD. Replace DATE with today's YYYYMMDD. No money, mail, reminders,
provider connections or shared settings. Use source=generic, explicit IDs under
120 characters and only this batch's new matter. Report flashes for every commit.

1. Create client `QA2 Task Order Client DATE` and hourly USD matter
   `QA2 Task Order Matter DATE`, $100, no office/template. Report flashes/IDs/M1.
   Record importer source for restoration; confirm zero tasks on M1.
2. Build `QA2 Task Order DATE.csv`, headers external_id,title,matter_number,due_on,
   done,priority,notes. Two rows in order, both ID `QA2 Task Order DATE A`, M1,
   due 2028-02-29, done=false. First title `QA2 Task Order First DATE`, priority=low,
   notes `QA2 Order First Body DATE`; second title `QA2 Task Order Last DATE`,
   priority=high, notes `QA2 Order Last Body DATE`. Upload /import/tasks/upload
   with source/file/CSRF, explicitly map fields, update, recheck. Preview expects
   one create and one update; confirm it has written no task yet.
3. Commit that file. Expect one created, one updated, zero errors, just one task A.
   Record original A ID. Its title/body/priority equal the second row, due leap day,
   incomplete on M1. Counts describe rows, not two distinct saved tasks.
4. Re-import both original rows with duplicates=skip. Expect two skipped, no
   create/update; A's ID and second-row state remain unchanged.
5. Create a new file of two rows with ID `QA2 Task Order DATE B`, using the same
   first/last values but titles `QA2 Task Order B First DATE` and
   `QA2 Task Order B Last DATE`. Set duplicates=skip. Expect one created and one
   skipped: B keeps the FIRST row's low priority/body and leap date. A unchanged.
6. Re-import those B rows with update. Expect zero created, two updated, same B ID
   now holding LAST row's title/high priority/body. Exactly two tasks on M1.
7. Import three rows, all A's ID with update: first original first-row values;
   second whitespace-only title and otherwise original values; third original
   last-row values. Expect zero created, two updated, one `Task has no title.`
   error. Valid rows continue around the refused row; A ends in original last-row
   state, same ID. B unchanged. Save job ID and download failed.csv as text.
8. Repair only the failed row using A's ID and first-row values with update.
   Expect one updated, no error. Same A ID now has first-row title/body/low priority.
   The earlier mixed-result job still has its one failed row and original counts.
9. Restore A to its last-row values with update. Expect one updated, no creation,
   original A ID with last title/body/high priority. Confirm B also remains in its
   last-row state and exactly two incomplete tasks exist, both due February 29.
10. Reopen all seven completed jobs: A create/update, A skip twice, B create/skip,
    B update twice, A mixed rows, A repair, A restore. Confirm row counts and that
    failed.csv from mixed rows contains only the whitespace-title original row.
11. Clean up: close new matter and report flash; restore importer source. Retain
    client, closed matter, two incomplete tasks with last-row values and seven jobs.
    Leave all earlier fixtures and job histories untouched.
12. What remains: IDs, row order, per-job counts, first-row versus last-row outcomes,
    failed-row isolation and repair. Return counts and a per-case table. Never
    include credentials, upload tokens or private links.

### S152. Task CSV blank and invalid due dates with repair (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6086082928 2026-10-09T17:39:53.831545+00:00

B2-4 importer regression. Source checked: importer.py prep_tasks/apply_tasks,
_importmap.py parse_any_date/task fields, importer/preview.html mapping/options
and permissions.py. Owner only. English/USD. Replace DATE with today's YYYYMMDD.
No money, mail, reminders, provider connections or shared settings. Use generic
source and one explicit external ID. Task import updates deliberately clear a due
date when the supplied date is blank or unreadable; record that as designed.

1. Create client `QA2 Task Date Client DATE` and hourly USD matter
   `QA2 Task Date Matter DATE`, $100, no office/template. Report flashes/IDs/M1,
   confirm zero tasks and record importer source for restoration.
2. Build `QA2 Task Date DATE.csv` with external_id,title,matter_number,due_on,
   done,priority,notes. One row: ID `QA2 Task Date DATE A`, title
   `QA2 Task Date Item DATE`, M1, due 2028-02-29, done=false, priority=normal,
   notes `QA2 Task Date Original DATE`. Upload /import/tasks/upload with source,
   file and CSRF. Explicitly map each header, update, recheck. No task written yet.
3. Commit. Expect one created, no error; report flash/job/task ID. Confirm one
   incomplete normal task on M1, leap due date and exact title/body.
4. Re-import same ID with blank due_on and notes `QA2 Task Date Blank DATE`, update.
   Expect one updated, same task ID, no due date, new body, otherwise unchanged.
5. Repair same ID to 2028-02-29 and original notes, update. Expect one updated,
   original task and date restored, no duplicate task.
6. Re-import same ID with due_on=not-a-date and notes `QA2 Task Date Invalid DATE`,
   update. Expect one updated, no row error, due date cleared, original ID retained.
   This is the task importer's designed handling of unreadable dates.
7. Repair again to 2028-02-29 and original notes, update. Expect one updated,
   same task ID with restored date, body and incomplete state.
8. Repeat invalid-date row with duplicates=skip. Expect one skipped, no update,
   restored leap date and original body preserved. A skipped row must not clear it.
9. Attempt same-ID update with whitespace-only title and blank due_on. Expect
   one `Task has no title.` error, zero updates. Saved title, leap date and original
   body remain. Download failed.csv as text: one original failed row only.
10. Re-import valid original row twice with duplicates=skip. Expect two skipped,
    no creation/update/error, one task with original ID/date/body. Reopen all eight
    jobs: create, blank date, repair, invalid date, repair, invalid-date skip,
    title error, double skip. Only the title-error job has a failed data row.
11. Clean up: close new matter, report flash and restore importer source. Retain
    client, closed matter, one incomplete task due February 29 and eight jobs.
    Leave older fixtures and job histories untouched.
12. What remains: IDs/counts, blank/invalid date clearing, both repairs, skip and
    failed-title preservation. Return counts and a per-case table. Never disclose
    credentials, upload tokens or private links.

### S153. Task CSV title whitespace and length boundaries (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6086425279 at 2026-10-09T17:59:29Z

B2-4 importer regression while money tools remain with Bot 1. Source checked:
importer.py prep_tasks/apply_tasks/upload/preview; _importmap.py clean_name/task
fields; importer/preview.html and permissions.py. Owner only. English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No mail, reminders, money, provider connections
or shared settings. Use source=generic, one explicit external ID and CSV writer.
Task titles collapse whitespace and are truncated to 300 characters by design.

1. Create client `QA2 Title Edge Client DATE` and hourly USD matter
   `QA2 Title Edge Matter DATE`, $100, no office/template. Report flashes/IDs/M1.
   Record importer source for restoration; confirm zero tasks on M1.
2. Build `QA2 Title Edge DATE.csv` with external_id,title,matter_number,due_on,
   done,priority,notes. One row ID `QA2 Title Edge DATE A`, M1, due 2028-02-29,
   done=false, priority=normal, notes `QA2 Title Edge Body DATE`. Title has leading
   and trailing spaces, with three spaces between QA2 and Title, a tab between
   Title and Edge, then one space and DATE. Upload /import/tasks/upload with
   source/file/CSRF; map each field, update, recheck. Confirm no task written yet.
3. Commit. Expect one created, no error, title exactly `QA2 Title Edge DATE`,
   one space between words. Record task/job IDs, leap date, body and incomplete state.
4. Build title L300 as `QA2 Title Edge DATE ` followed by enough X characters to
   total exactly 300 ASCII characters. Same-ID update. Expect one updated, same
   task ID with all 300 characters preserved. Other fields remain original.
5. Same-ID update with title L300 followed by Y, total 301. Expect one updated,
   no error; saved title exactly L300, length 300, no trailing Y. No second task.
6. Same-ID update using `QA2 Title Edge DATE ` padded with Z to exactly 299
   characters. Expect one updated, original ID with all 299 characters intact.
7. Re-import L300 with duplicates=skip. Expect one skipped, no update/create;
   saved 299-character Z title and all original fields remain unchanged.
8. Attempt same-ID update with title consisting only of spaces and a tab, update.
   Expect one `Task has no title.` error and zero updates. Saved 299-character
   title, body, leap date and original ID remain. failed.csv has one failed row.
9. Restore short title `QA2 Title Edge DATE`, update. Expect one updated, same ID,
   exact short title, original body/date and one incomplete normal task on M1.
10. Re-import restored valid row twice with duplicates=skip. Expect two skipped,
    no create/update/error. Reopen all eight jobs: create, 300, 301, 299, skip,
    whitespace error, restore, double skip. Error history stays after repair.
11. Clean up: close new matter, report flash and restore importer source. Retain
    client, closed matter, one restored task and eight jobs with histories. Leave
    all older fixtures untouched. Save safe local title manifests for comparison.
12. What remains: IDs/counts, normalized title, exact 299/300/301 input and stored
    lengths, skip/refusal preservation and restore. Return counts and a per-case
    table. Never disclose credentials, upload tokens or private links.

### S154. Import external IDs stay separate between tasks and notes (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6086734978 at 2026-10-09T18:19:36Z

B2-4 entity identity regression. Source checked: importer.py ref_get/ref_set,
prep_tasks/apply_tasks/prep_notes/apply_notes; _importmap.py fields;
importer/preview.html mapping/options; permissions.py. Owner only, English/USD.
Replace DATE with today's YYYYMMDD. No money, mail, reminders, provider connections
or shared settings. Use source=generic and identical external_id
`QA2 Entity Link DATE A` for this batch's task and note. Identity includes entity;
do not compare numeric task and note IDs for inequality, since tables are separate.
All uploads use file/source/CSRF, explicit field mapping, recheck then commit.

1. Create client `QA2 Entity Link Client DATE` and hourly USD matter
   `QA2 Entity Link Matter DATE`, $100, no office/template. Report flashes/IDs/M1.
   Record importer source; confirm zero tasks and zero notes on M1.
2. Upload task CSV to /import/tasks/upload: external_id as above, title
   `QA2 Entity Task DATE`, matter_number=M1, due_on=2028-02-29, done=false,
   priority=normal, notes `QA2 Entity Task Body DATE`. Use update. Preview writes
   nothing; commit creates one task T. Report flash/job/T ID and fields.
3. Upload note CSV to /import/notes/upload: SAME external_id, M1,
   body `QA2 Entity Note Body DATE`, date=2028-02-29 12:00. Use update.
   Expect one new note N, no task update. Record N ID/job/flash; T unchanged.
4. Update the task using same ID with title `QA2 Entity Task Revised DATE`,
   priority=high and original remaining fields. Expect one updated, same T ID.
   Note N's body/date/ID must remain unchanged.
5. Update the note using same ID with body `QA2 Entity Note Revised DATE` and
   original date/M1. Expect one updated, same N ID. Revised T remains unchanged.
6. Re-import original task row with duplicates=skip. Expect one skipped,
   T keeps revised title/high priority; N keeps revised body. No new record.
7. Re-import original note row with duplicates=skip. Expect one skipped,
   N keeps revised body; T keeps revised state. Exactly one task and one note.
8. Attempt note update with whitespace-only body. Expect one `Note is empty.`
   error, zero updates. Both records' IDs and revised state remain unchanged.
   Download failed.csv as text: exactly the single refused note row.
9. Restore original task row with update. Expect one updated, original T ID,
   original title/normal priority/body/date. N remains revised, original N ID.
10. Restore original note row with update. Expect one updated, original N ID/body
    and leap-day timestamp, T unchanged. Reopen all nine jobs: task create,
    note create, task update, note update, task skip, note skip, note error,
    task restore, note restore. Counts and entity labels must match each action.
11. Clean up: close new matter, report flash and restore importer source. Retain
    client, closed matter, one incomplete task, one note and nine jobs including
    error history. Leave all older fixtures and mappings untouched.
12. What remains: IDs/counts, shared external ID with separate entity identities,
    independent update/skip/refusal/restore evidence and job labels. Return counts
    and a per-case table. Never disclose credentials, tokens or private links.

### S155. Note CSV subject composition and empty-body guard (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6087197478 at 2026-10-09T18:49:55Z

B2-4 importer regression. Source checked: importer.py prep_notes/apply_notes,
upload/preview; _importmap.py note fields; importer/preview.html; permissions.py.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. No mail,
money, reminders, providers or shared settings. Preserve all earlier fixtures.
Use source=generic and explicit external_id `QA2 Subject Edge DATE A` throughout.
CSV writer must quote multiline values. Columns external_id,matter_number,body,
subject,date. Map explicitly; recheck then commit. Date always 2028-02-29 12:00.
Subject is prepended with two newlines only when absent as a case-insensitive
substring of body. Empty body is refused even when subject is nonempty.

1. Create client `QA2 Subject Edge Client DATE` and hourly USD matter
   `QA2 Subject Edge Matter DATE`, $100, no office/template. Report IDs/flashes/M1.
   Record importer source for restoration; confirm zero notes on M1.
2. Upload /import/notes/upload with source/file/CSRF. One row for M1 with body
   `QA2 Subject Edge Body DATE`, subject `QA2 Subject Edge Heading DATE`, date
   above and explicit ID. Recheck with update. Confirm no note written in preview.
3. Commit. Expect one created, zero errors. Note N body is heading, two newlines,
   original body exactly. Record N/job ID and leap timestamp.
4. Same-ID update with body `QA2 Subject Edge Heading DATE already present`,
   subject `QA2 Subject Edge Heading DATE`. Expect one updated, same N, body
   unchanged from supplied text, no extra heading, no second note.
5. Same-ID update with body `QA2 Subject Edge DATE contains mixed CASE heading`,
   subject `case`. Expect one updated, supplied body unchanged: matching is case
   insensitive, including a subject occurring inside the sentence.
6. Same-ID update with body `QA2 Subject Edge DATE embedded substring`, subject
   `string`. Expect one updated, supplied body unchanged: substring containment,
   not word boundaries, is designed behavior. Same N/date, no duplicate note.
7. Same-ID update with body containing two outer spaces around
   `QA2 Subject Edge Trim DATE` and subject containing two outer spaces around
   `QA2 Subject Edge New DATE`. Expect one updated, body exactly trimmed subject,
   two newlines, trimmed body. Internal spacing stays unchanged. Same N/date.
8. Same-ID update with body `QA2 Subject Edge Plain DATE`, whitespace-only subject.
   Expect one updated, body exactly supplied plain text without blank heading.
   Save this plain state for the next two preservation checks.
9. Re-import original row using duplicates=skip. Expect one skipped, no update
   or creation; plain state and original N/date remain. No prepended heading.
10. Same-ID update with whitespace-only body and nonempty subject
    `QA2 Subject Edge Refused DATE`. Expect one `Note is empty.` error, zero
    updates. Plain state/N/date remain; failed.csv contains that one failed row.
11. Restore original row using update. Expect one updated, original composed
    heading plus two newlines plus body, same N/date. Close matter, report flash,
    restore importer source. Retain client, closed matter, one note, nine jobs
    (create, exact, case, substring, trim, blank subject, skip, error, restore).
    Confirm all older fixtures unchanged and no mail or reminders.
12. What remains: list IDs/counts, exact body text/newlines for each update,
    subject containment decisions, skip/error preservation and restored source.
    Return counts and per-case table. No credentials, tokens or private links.

### S156. Task CSV keyword boundaries and priority aliases (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6087673805 at 2026-10-09T19:19:57Z

B2-4 importer regression. Source checked: importer.py prep_tasks/apply_tasks,
upload/preview; _importmap.py clean_name; importer/preview.html; tasks/form.html
and tasks/index.html; permissions.py. Owner only, English/ASCII/USD.
Replace DATE with today's YYYYMMDD. No mail, reminders, money, providers or shared
settings. Preserve all older fixtures. Use source=generic, explicit external ID
`QA2 Kind Edge DATE A`, columns external_id,title,matter_number,due_on,done,priority,
notes. All rows use M1, due_on=2028-02-29, done=false, notes `QA2 Kind Body DATE`.
Upload /import/tasks/upload with source/file/CSRF, map, recheck then commit.
Inspect kind/priority via task edit form or list badges, not an API that omits fields.

1. Create client `QA2 Kind Edge Client DATE` and hourly USD matter
   `QA2 Kind Edge Matter DATE`, $100, no office/template. Report IDs/flashes/M1.
   Record importer source; confirm zero tasks on M1.
2. Upload one row, title `QA2 Kind Edge DATE courthouse overdue`, priority=1,
   duplicates=update. Recheck only: preview must write no task. Whole-word matching
   means courthouse and overdue must not count as court or due.
3. Commit. Expect one created, no errors, kind task, priority high, incomplete,
   leap due date and exact notes. Record task T and job ID.
4. Same-ID update with title `QA2 Kind Edge DATE due`, priority=3. Expect one
   updated, same T, kind deadline and priority low. Other fields unchanged.
5. Same-ID update with title `QA2 Kind Edge DATE court deadline`, priority=minor.
   Expect one updated, kind court_date (court overrides deadline), low priority,
   same T/M1/date/body. No second task and no event created by this import.
6. Same-ID update with title `QA2 Kind Edge DATE COURT DUE`, priority=CRITICAL.
   Expect one updated, kind court_date/high: matching is case insensitive.
   Same T and original remaining fields.
7. Same-ID update with title `QA2 Kind Edge DATE trial-run`, priority=unexpected.
   Expect one updated, court_date because hyphen gives a word boundary; unknown
   priority falls back to normal. No row error, same T and fields.
8. Same-ID update with title `QA2 Kind Edge DATE trial_run`, priority=2.
   Expect one updated, kind task (underscore is part of the word), normal priority.
   Same T, incomplete, leap date/body. Save this state for preservation checks.
9. Import original courthouse/overdue row, priority=1, duplicates=skip. Expect
   one skipped, no update/create. T keeps trial_run title/task/normal and fields.
10. Attempt same-ID update with whitespace-only title and priority=critical.
    Expect one `Task has no title.` error and zero updates. Saved trial_run state
    remains. failed.csv contains that one refused row; no second task.
11. Restore original courthouse/overdue row using update. Expect one updated,
    same T, kind task/high and original fields. Close matter and restore importer
    source, report flashes. Retain client, closed matter, one incomplete task,
    nine jobs (create, due, combined, uppercase, hyphen, underscore, skip, error,
    restore). All earlier fixtures unchanged; no reminders or mail.
12. What remains: IDs/counts, whole-word and underscore/hyphen decisions, court
    precedence, priority alias/fallback states and skip/error preservation.
    Return counts and per-case table. No credentials, tokens or private links.

### S157. Calendar CSV location limits and blank-field replacement (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6087981911 at 2026-10-09T19:40:00Z

B2-4 importer regression. Source checked: importer.py prep_calendar/apply_calendar,
upload/preview; _importmap.py calendar fields; calendar.py _event_error;
calendar/form.html and importer/preview.html; permissions.py owner import rule.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. No mail,
reminders, feeds, money, providers or shared settings. Preserve older fixtures.
CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,location,
description. All rows use explicit ID `QA2 Cal Text DATE A`, M1, starts_at
2028-02-29 10:00, ends_at 2028-02-29 11:00, all_day=false. Use source=generic,
file/CSRF at /import/calendar/upload, explicit mapping, recheck then commit.
Location truncates to 300 characters; description becomes event notes.

1. Create client `QA2 Cal Text Client DATE` and hourly USD matter
   `QA2 Cal Text Matter DATE`, $100, no office/template. Report IDs/flashes/M1.
   Record importer source and confirm no batch event exists.
2. Prepare one row title `QA2 Cal Text Event DATE`, location `QA2 Cal Text Room DATE`,
   description `QA2 Cal Text Notes DATE`. Recheck update preview; confirm no event
   is written. CSV must preserve quoted text exactly.
3. Commit. Expect one created, no error, event E with original title/location/notes,
   M1, leap-day 10:00 to 11:00, timed not all-day. Report E/job IDs and flash.
4. Build L300 as `QA2 Cal Text Room DATE ` padded with X to exactly 300 characters.
   Same-ID update location=L300. Expect one updated, same E with all 300 characters,
   other original fields unchanged. Inspect edit form's full location value.
5. Same-ID update location=L300 followed by Y. Expect one updated, saved location
   exactly L300, length 300 with no trailing Y. Same E, no second event.
6. Same-ID update location=`QA2 Cal Text Short DATE`, description with two lines:
   `QA2 Cal Text First DATE` then `QA2 Cal Text Second DATE`. Expect one updated,
   short location and exactly one newline in saved notes, same dates/title/E.
7. Same-ID update location blank, description blank. Expect one updated, location
   and notes both empty by design. Original E/title/M1/times retained.
8. Re-import original row with duplicates=skip. Expect one skipped, zero updates
   or creates. Location and notes stay empty; original E/times unchanged.
9. Attempt same-ID update with whitespace-only title and original location/notes.
   Expect one `Event has no title.` error, zero updates. Empty location/notes and
   saved original title remain. failed.csv contains the single refused row.
10. Restore original valid row using update. Expect one updated, same E with
    original location/notes/title and leap times. No second event.
11. Clean up: close matter, report flash and restore importer source. Retain
    client, closed matter, one restored timed event and eight jobs (create,
    300, 301, multiline, clear, skip, error, restore). Do not delete event/history
    or send reminders. Confirm all older fixtures unchanged.
12. What remains: IDs/counts, exact 300/301 input and stored location lengths,
    multiline notes, blank replacement, skip/error preservation and restore.
    Return counts and per-case table. No credentials, tokens or private links.

### S158. Calendar CSV all-day inference and timed conversion (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6088133834 at 2026-10-09T19:49:54Z

B2-4 importer regression. Source checked: importer.py prep_calendar,
_calendar_datetime/apply_calendar/upload/preview; _importmap.py calendar fields;
calendar.py _event_error, calendar/form.html and importer/preview.html;
permissions.py owner import rule. English/ASCII/USD, owner only.
Replace DATE with today's YYYYMMDD. No mail, reminders, feeds, money, providers
or shared settings. Preserve older fixtures. Use source=generic, explicit ID
`QA2 Day Mode DATE A`, title `QA2 Day Mode Event DATE`, M1, location
`QA2 Day Mode Room DATE`, description `QA2 Day Mode Notes DATE` throughout.
CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,location,
description. Upload /import/calendar/upload with source/file/CSRF, explicit
mapping, recheck then commit. Examine event edit fields without saving them.

1. Create client `QA2 Day Mode Client DATE` and hourly USD matter
   `QA2 Day Mode Matter DATE`, $100, no office/template. Report IDs/flashes/M1.
   Record importer source and confirm no batch event exists.
2. Upload row with starts_at=2028-02-29, ends_at blank, all_day blank, update.
   Recheck preview and confirm it writes no event.
3. Commit. Expect one created, no errors, event E inferred all-day on leap day,
   start midnight and no explicit end. Record E/job IDs and original other fields.
4. Same-ID update starts_at=2028-02-29, ends_at blank, all_day=false. Expect one
   updated, same E now timed at midnight to 01:00 local wall time. Explicit false
   overrides date-only inference; missing timed end defaults to one hour.
5. Same-ID update starts_at=2028-02-29 10:00, ends_at=2028-02-29 11:30,
   all_day blank. Expect one updated, same E timed 10:00 to 11:30, unchanged
   title/M1/location/notes. Time-bearing input does not infer all-day.
6. Same-ID update starts_at=2028-03-01, ends_at blank, all_day=true. Expect one
   updated, same E all-day March 1 with no end. Earlier timed end must be cleared.
7. Re-import prior timed 10:00 to 11:30 row using duplicates=skip. Expect one
   skipped, zero updates/create; E stays all-day March 1 with no end.
8. Attempt update starts_at=not-a-date, ends_at blank, all_day=true. Expect one
   error `Could not read start 'not-a-date'.`, zero updates. E remains all-day
   March 1, original fields intact; failed.csv contains that single refused row.
9. Repair same ID starts_at=2028-02-29, ends_at blank, all_day blank, update.
   Expect one updated, same E restored to inferred all-day leap date, no end.
10. Re-import repaired row twice with duplicates=skip. Expect two skipped,
    zero updates/create/errors, exactly one batch event under original E ID.
    Reopen eight jobs: create, false, timed, true, skip, error, repair, double skip.
11. Clean up: close matter, report flash and restore importer source. Retain
    client, closed matter, one all-day leap-date event with original text fields
    and eight jobs including refusal history. No deletion, mail or reminders.
    Confirm all older fixtures unchanged.
12. What remains: IDs/counts, inferred versus explicit all_day decisions, timed
    defaults and end clearing, skip/refusal preservation and repair. Return
    counts and per-case table. No credentials, tokens or private links.

### S159. Calendar CSV matter reassignment and missing-reference recovery (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6088736793 at 2026-10-09T20:29:48Z

Source checked: importer.py prep_calendar/apply_calendar/upload/preview;
_importmap.py calendar fields; calendar/form.html; permissions.py owner rule.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve all
older fixtures. No money, mail, reminders, feeds, AI, provider or shared settings.
CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,location,
description. Source generic, explicit external_id `QA2 Cal Matter DATE A`, title
`QA2 Cal Matter Event DATE`, leap start 2028-02-29 10:00, end 2028-02-29 11:00,
all_day=false, location `QA2 Cal Matter Room DATE`, description
`QA2 Cal Matter Notes DATE`. Each run: authenticated /import/calendar/upload with
source/file/fresh CSRF, explicit mapping, recheck, then commit. Inspect event
edit fields without saving. Keep external ID, text and dates unchanged except
where specified. Do not infer a failed row from a warning about a missing matter.

1. Create client `QA2 Cal Matter Client DATE` and two hourly USD matters
   `QA2 Cal Matter One DATE` and `QA2 Cal Matter Two DATE`, $100, no templates
   or offices. Record IDs, numbers M1/M2, flashes and original importer source.
2. Upload original row pointing to M1 with duplicates=update. Recheck preview,
   expect one create, no errors and no event written before commit.
3. Commit: one created, no errors. Record E/job IDs; E belongs to M1 with
   original title, location, notes and leap times. Exactly one batch event.
4. Same-ID update pointing to M2: one updated, same E now belongs to M2.
   Reopen edit, verify selected matter and unchanged other fields.
5. Same-ID update with matter_number blank: one updated, same E has Matter
   None. Absence of a reference clears the previous M2 link, no duplicate event.
6. Build a nonexistent matter number at run time using QA2 plus the date and
   clock time, confirm it matches no matter. Update same ID with that number.
   Expect warning `Matter '<number>' not found; event kept without a matter.`
   and one updated, zero errors. E remains without a matter; text/times intact.
7. Repair same ID with M1, update: one updated, same E linked to M1 again.
   No warning and no duplicate. Capture selected matter evidence.
8. Re-import valid M2 row with duplicates=skip: one skipped, zero updates.
   E remains linked to M1 with original text/times, despite submitted M2.
9. Attempt update with M2 and whitespace-only title. Expect one error
   `Event has no title.`, no update. E stays linked to M1 and retains its title;
   failed.csv contains the refused row. No second event created.
10. Restore valid title and M2, update: one updated, same E linked to M2.
    Reopen all eight jobs: create, move, blank, missing, repair, skip, error,
    restore. Counts match, exactly one batch event, no mail or reminders.
11. Clean up: close both matters, report flashes; restore importer source.
    Reopen E's edit page: closed M2 still selected. Retain client, two closed
    matters, one timed leap event on M2 and eight jobs. All older fixtures intact.
12. What remains: IDs, matter-selection transitions, warning versus error
    evidence, failed-row preservation, duplicate counts and retained records.
    Return counts and per-case table. No credentials, tokens or private links.

### S160. Calendar CSV title normalization and length boundaries (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6089024533 at 2026-10-09T20:49:56Z

Source checked: importer.py prep_calendar/apply_calendar/upload/preview;
_importmap.py clean_name and calendar fields; calendar.py _event_error;
calendar/form.html. Import routes are owner-only. English/ASCII/USD.
Replace DATE with today's YYYYMMDD. Preserve older fixtures. No money, mail,
reminders, feeds, AI, providers or shared settings. Source generic, explicit
external_id `QA2 Cal Title DATE A` throughout. CSV columns external_id,title,
matter_number,starts_at,ends_at,all_day,location,description. Use M1, leap start
2028-02-29 10:00, end 2028-02-29 11:00, all_day=false, location
`QA2 Cal Title Room DATE`, description `QA2 Cal Title Notes DATE` throughout.
Each upload uses /import/calendar/upload, file/source/fresh CSRF, explicit
mapping, recheck, commit, duplicates=update unless stated. Inspect persisted
/calendar/E/edit fields without saving. Quote CSV titles containing newlines.

1. Create client `QA2 Cal Title Client DATE` and hourly USD matter
   `QA2 Cal Title Matter DATE`, $100, no office/template. Report IDs, M1,
   flashes and original importer source. No event with batch prefix yet.
2. Upload original title `QA2 Cal Title Event DATE`. Recheck preview: one
   create, no errors, no event written. Commit and record E/job IDs. One timed
   leap-date event, exact original title, location, notes and M1.
3. Update same ID with original title surrounded by spaces, with three spaces
   between each word. Expect one updated and original single-space title on
   fresh edit GET, same E, unchanged other fields.
4. Update same ID with a quoted title whose words are separated by tabs and
   newlines. Expect one updated, original single-space title persisted again.
   No extra event, location and notes unchanged.
5. Build T300 from `QA2 Cal Title DATE ` followed by enough X characters to
   make exactly 300 ASCII characters. Update same ID. Expect all 300 characters
   persisted, one updated, same E. Record input/stored lengths.
6. Update same ID with T300 followed by Y, length 301. Expect one updated,
   title exactly T300, no trailing Y, same E and unchanged leap times/M1.
7. Update same ID with title containing only spaces and tabs. Expect one error
   `Event has no title.`, zero updates. T300 and all other E fields remain;
   failed.csv has exactly the refused row.
8. Re-import original title with duplicates=skip. Expect one skipped, zero
   updates/create/errors. E retains T300, not the submitted original title.
9. Repair with original title and duplicates=update. Expect one updated,
   same E with original title restored; original room/notes/M1/times intact.
10. Re-import original row twice in one CSV with duplicates=skip. Expect two
    skipped, zero created/updated/errors and still exactly one batch event.
    Nine jobs total: create, spaces, multiline, 300, 301, error, skip, repair,
    double skip. Check their summaries and record IDs.
11. Clean up: close only M1, report flash; restore importer source. Retain
    client, closed matter, original timed leap event E and nine jobs. Reopen E
    and verify original title and selected closed matter. Older fixtures intact.
12. What remains: title values and lengths at each transition, duplicate and
    error counts, unchanged fields, retained IDs and per-case PASS/FAIL table.
    Never disclose credentials, tokens or private links.

### S161. Calendar CSV external IDs stay separate by source (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6089306857 at 2026-10-09T21:09:45Z

Source checked: importer.py ImportContext.ref_get/ref_set, prep_calendar,
apply_calendar, _source_from_form and job creation; _importmap.py calendar
mapping; calendar/form.html. Owner import routes only, English/ASCII/USD.
Replace DATE with today's YYYYMMDD. Preserve all older fixtures. No mail,
reminders, feeds, money, AI, providers or shared settings. CSV columns
external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Use the SAME explicit external_id `QA2 Cal Source DATE A` in generic and clio.
Use M1, starts_at=2028-02-29 10:00, ends_at=2028-02-29 11:00, all_day=false,
location=`QA2 Cal Source Room DATE`, description=`QA2 Cal Source Notes DATE`.
Every upload: /import/calendar/upload with specified source, file, fresh CSRF;
explicit mapping (do not trust source presets), recheck, then commit. Update
unless stated. Read persisted /calendar/E/edit fields without saving.

1. Create client `QA2 Cal Source Client DATE` and hourly USD matter
   `QA2 Cal Source Matter DATE`, $100, no office/template. Report IDs/M1/flashes
   and original importer source. No batch events initially.
2. Source generic: upload title `QA2 Cal Source Generic DATE`. Preview one
   create, no errors; commit. Record event G and job. Exact original fields.
3. Source clio: same external ID, title `QA2 Cal Source Clio DATE`.
   Expect one created, different event C ID, not an update to G. Both events
   retain their own titles, same M1/leap times. Two batch events total.
4. Generic same-ID update title `QA2 Cal Source Generic Revised DATE`.
   Expect one updated, G only. C retains original clio title and fields.
5. Clio same-ID update title `QA2 Cal Source Clio Revised DATE`.
   Expect one updated, C only. G retains revised generic title.
6. Generic original row, duplicates=skip. Expect one skipped, zero updates
   or creates. G and C both retain revised titles; two events still.
7. Clio original row, duplicates=skip. Expect one skipped, zero updates or
   creates. Both revised titles remain unchanged, original IDs preserved.
8. Generic update with whitespace-only title. Expect one error
   `Event has no title.`, zero updates; failed.csv contains the refused row.
   Both G and C preserve revised titles and all other fields.
9. Restore generic original row, update. Expect one updated, G restored to
   original generic title, C still revised. No extra event.
10. Restore clio original row, update. Expect one updated, C restored to
    original clio title; G unchanged. Nine jobs total: two creates, two edits,
    two skips, one error, two restores. Verify source on each job.
11. Clean up: close M1, report flash, restore original importer source.
    Retain client, closed matter, G and C with original respective titles,
    leap times/room/notes, and nine jobs. All older fixtures untouched.
12. What remains: both event IDs, shared external ID, per-source changes and
    skips, refusal evidence and job counts. Return per-case PASS/FAIL table.
    Never disclose credentials, tokens or private links.

### S162. Calendar CSV repeated IDs and failed-row ordering (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6089708075 at 2026-10-09T21:39:51Z

Source checked: importer.py _ordered_rows/run_import, Ctx.ref_get/ref_set,
prep_calendar/apply_calendar, owner upload/preview routes; calendar/form.html.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
older fixtures. No mail, reminders, feeds, money, AI or provider/shared settings.
Use source generic and one explicit external_id `QA2 Cal Rows DATE A` for every
row. CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,
location,description. Use M1, leap start 2028-02-29 10:00, end 11:00 same date,
all_day=false, location `QA2 Cal Rows Room DATE`, notes `QA2 Cal Rows Notes DATE`.
Define row A title `QA2 Cal Rows First DATE`; row B identical except title
`QA2 Cal Rows Second DATE`. Row X has a whitespace-only title. Upload each file
at /import/calendar/upload with fresh CSRF/file/source, explicit mapping,
recheck then commit. Each numbered import below is ONE upload/job. Inspect
persisted event edit fields without saving; duplicate policy as specified.

1. Create client `QA2 Cal Rows Client DATE` and hourly USD matter
   `QA2 Cal Rows Matter DATE`, $100, no office/template. Record IDs/M1/flashes,
   original importer source and absence of batch events.
2. Upload two rows A then B, duplicates=update. Preview one create and one
   update with no errors; verify preview alone creates no event.
3. Commit that file. Expect one created, one updated, one event E with B's
   title and original M1/leap times/room/notes. Record E/job IDs.
4. Upload B then A, update. Expect two updates, no creates/errors. Same E
   now has A's title; row order controls final title, no second event.
5. Upload A then B, skip. Expect two skipped, zero updates/creates/errors.
   Same E retains A's title despite B appearing last.
6. Upload B then X, update. Expect one update and one error
   `Event has no title.` E retains B's title; failed.csv contains X only.
   Later failure does not undo the earlier successful row.
7. Upload X then A, update. Expect one error and one update. E ends with A's
   title; failed.csv contains X only. Earlier failure does not block later row.
8. Upload A then A, update. Expect two updates, no creates/errors. E still
   has A's title and unchanged other fields. Exactly one batch event.
9. Upload B then B, skip. Expect two skipped, no updates/errors. E still A.
   Verify original event ID, M1, times, room and notes unchanged.
10. Upload single B, update. Expect one update, E now B. Reopen all eight
    jobs: initial, reverse, skip, trailing error, leading error, repeated
    update, repeated skip, final update. Verify row counts and failed files.
11. Clean up: close M1, report flash; restore importer source. Retain client,
    closed matter, one timed leap event E with B title and original fields,
    eight jobs and their refusal history. Older fixtures untouched.
12. What remains: IDs, row-order outcomes, counts, isolated failed rows and
    retained records. Return per-case table; no credentials or private links.

### S163. Calendar CSV generated identity without external IDs (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6090202360 at 2026-10-09T22:19:52Z

Source checked: importer.py prep_calendar/_hash_key/apply_calendar and owner
upload/preview; _importmap.py clean_name; calendar/form.html. Owner only,
English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve older fixtures.
No mail, reminders, feeds, money, AI, providers or shared settings. Source generic.
CSV columns title,matter_number,starts_at,ends_at,all_day,location,description.
Do NOT map or supply external_id. Original row A: title `QA2 Cal Key Event DATE`,
M1, starts_at=2028-02-29 10:00, ends_at=2028-02-29 11:00, all_day=false,
location=`QA2 Cal Key Room DATE`, description=`QA2 Cal Key Notes DATE`.
Every run is one upload/job at /import/calendar/upload with file/source/fresh
CSRF, explicit mapping, recheck then commit. Update unless stated. Inspect
persisted edit fields without saving. Generated identity uses normalized title
and parsed start; changing title or start can create a new event intentionally.

1. Create client `QA2 Cal Key Client DATE` and hourly USD matter
   `QA2 Cal Key Matter DATE`, $100, no office/template. Record IDs/M1/flashes,
   original importer source and absence of batch events.
2. Upload original A with no external ID mapping. Recheck preview, one create,
   no errors; commit. Record E1/job. One timed leap event with original fields.
3. Upload A again, update. Expect one updated, same E1, not a second event.
   Original title/M1/times/room/notes remain exact.
4. Upload A with extra leading/trailing spaces and repeated internal spaces
   in title. Expect one updated, same E1, normalized original title. No new event.
5. Upload A with only location changed to `QA2 Cal Key Revised Room DATE`.
   Expect one updated, same E1 with revised room; title/start identity unchanged.
6. Upload A with original title plus ` Revised`, original room. Expect one
   CREATED E2 with different ID, despite duplicates=update. E1 retains original
   title and revised room. Exactly two events, same start/end/M1.
7. Upload original A but start=2028-02-29 12:00, end=2028-02-29 13:00.
   Expect one CREATED E3, different ID, original title at new times. E1/E2
   unchanged. Exactly three events. Start is part of generated identity.
8. Upload original A, duplicates=skip. Expect one skipped; E1 keeps revised
   room, E2/E3 unchanged. No fourth event and no updates.
9. Upload original A, update. Expect one updated, E1 original room restored.
   E2 revised title at 10:00 and E3 original title at 12:00 remain unchanged.
10. Upload original A with whitespace-only title, update. Expect one error
    `Event has no title.`, zero created/updated; failed.csv has the refused row.
    All three events unchanged. Nine jobs: create, repeat, spaces, room, title,
    start, skip, restore, error. Record job IDs and counts.
11. Clean up: close M1, report flash; restore importer source. Retain client,
    closed matter, E1 original title/time/room, E2 revised title, E3 noon start,
    and nine jobs. Verify all three retain M1, leap date and original notes.
    No deletion; all older fixtures untouched.
12. What remains: IDs, generated-identity update/create decisions, exact event
    counts, refusal preservation and per-case table. No credentials or private links.

### S164. Calendar CSV explicit all-day flags override date inference (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6090590217 at 2026-10-09T22:49:50Z

Source checked: importer.py prep_calendar/_calendar_datetime/apply_calendar;
_importmap.py parse_bool and TRUE_WORDS/FALSE_WORDS; calendar.py _event_error;
calendar/form.html; owner-only import permissions. English/ASCII/USD.
Replace DATE with today's YYYYMMDD. Preserve all older fixtures. No mail,
reminders, feeds, money, AI, providers or shared settings. Source generic.
One explicit external_id `QA2 Cal Flags DATE A`, title `QA2 Cal Flags Event DATE`,
M1, starts_at=2028-02-29 (date only), ends_at blank, original location
`QA2 Cal Flags Room DATE`, description `QA2 Cal Flags Notes DATE` throughout.
CSV fields external_id,title,matter_number,starts_at,ends_at,all_day,location,
description. Upload /import/calendar/upload with file/source/fresh CSRF,
explicit mapping, recheck and commit; duplicates=update unless stated.
Each import case is one job. Inspect /calendar/E/edit without saving:
checkbox all_day, date, starts_at and ends_at inputs including hidden inputs.

1. Create client `QA2 Cal Flags Client DATE` and hourly USD matter
   `QA2 Cal Flags Matter DATE`, $100, no office/template. Record IDs/M1/flashes
   and original importer source; no batch event initially.
2. Import all_day=true. Preview one create then commit. Record E/job IDs.
   One all-day leap event, date Feb 29 2028, no end, original matter/text.
3. Update same ID with all_day=false. Expect one updated, checkbox unchecked,
   start Feb 29 00:00 and default end 01:00. Date-only start does not force
   all-day when an explicit false flag is supplied. Same E.
4. Update with all_day=` YES `. Expect one updated, checkbox checked,
   start on leap date and end cleared. Case/space normalization accepted.
5. Update with all_day=0. Expect one updated, timed midnight to 01:00 again.
   Same E, no changed title, matter, location or notes.
6. Update with all_day=x. Expect one updated and all-day with blank end.
   This recognized true alias is not a validation error.
7. Update with all_day=maybe. Expect one updated, timed midnight to 01:00:
   an unrecognized nonempty value defaults to false, not date inference.
   Confirm no error and no second event.
8. Update with all_day empty. Expect one updated, inferred all-day because
   start is date-only; end cleared. Same E and original other fields.
9. Import all_day=false with duplicates=skip. Expect one skipped, no update
   or create. E stays all-day with blank end, despite supplied false flag.
10. Update all_day=true. Expect one updated, original all-day state retained.
    Nine jobs total: create, false, YES, 0, x, maybe, blank, skip, restore.
    Reopen job summaries; exactly one batch event with original fields.
11. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, one all-day leap event with no end and
    nine jobs. Verify closed matter still selected. Older fixtures untouched.
12. What remains: IDs, submitted flags and persisted checkbox/end values,
    counts, skip preservation and per-case PASS/FAIL table. No private links,
    credentials or tokens in the result.

### S165. Calendar CSV notes preserve internal text and clear blank updates (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6090917926 at 2026-10-09T23:19:56Z

Source checked: _importmap.py row_values; importer.py prep_calendar and
apply_calendar; calendar/form.html notes textarea; owner import permissions.
English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve older fixtures.
No mail, reminders, feeds, money, AI, providers or shared settings. Source generic.
One explicit external_id `QA2 Cal Notes DATE A`, title `QA2 Cal Notes Event DATE`,
M1, start=2028-02-29 10:00, end=2028-02-29 11:00, all_day=false, location
`QA2 Cal Notes Room DATE`. CSV fields external_id,title,matter_number,starts_at,
ends_at,all_day,location,description. Each import uses /import/calendar/upload,
file/source/fresh CSRF, explicit mapping, recheck then commit, duplicates=update
unless stated. Quote CSV multiline text correctly. Inspect persisted notes
textarea via /calendar/E/edit without saving, not just rendered page whitespace.

1. Create client `QA2 Cal Notes Client DATE` and hourly USD matter
   `QA2 Cal Notes Matter DATE`, $100, no office/template. Record IDs/flashes,
   original importer source; no batch event initially.
2. Import description `QA2 Cal Notes Original DATE`. Preview one create,
   no errors, then commit. Record E/job IDs; one timed leap event, exact notes.
3. Update same ID with original description padded with spaces at both ends.
   Expect one updated; outer spaces removed, original text persisted.
4. Update notes to two lines: `QA2 Cal Notes First DATE` and
   `Second line, with "quotes" and  two spaces`. Use one LF between lines.
   Expect one updated; internal LF, comma, quotes and doubled spaces retained.
5. Update description to an empty cell. Expect one updated, notes textarea
   empty; same E, unchanged title, matter, room, leap times and timed flag.
6. Restore the two-line notes. Expect one updated, exact internal text back,
   one batch event. No duplicate event from changing notes.
7. Import empty description with duplicates=skip. Expect one skipped,
   zero updates/creates; multiline notes remain intact.
8. Update description containing spaces and tabs only. Expect one updated,
   empty notes again. Whitespace-only notes are allowed, unlike empty title.
9. Update original row but title whitespace-only and description=original.
   Expect one error `Event has no title.`, zero updates; failed.csv has one
   refused row. E still has empty notes and original other fields.
10. Repair with original title and description. Expect one updated,
    original one-line notes restored. Nine jobs: create, padding, multiline,
    empty, multiline restore, skip, whitespace, error, repair. One event only.
11. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, E with original notes/room/title/leap times,
    nine jobs. Closed matter remains selected; older fixtures untouched.
12. What remains: IDs, exact textarea values, blank/skip/refusal outcomes,
    job counts and per-case table. Never disclose credentials or private links.

### S166. Calendar CSV external-ID length boundaries across separate jobs (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6091234346 at 2026-10-09T23:49:55Z

Source checked: importer.py Ctx.ref_get/ref_set (120-character stored key),
prep_calendar/apply_calendar; _importmap.py row_values; calendar/form.html;
owner import permissions. English/ASCII/USD. Replace DATE with today's YYYYMMDD.
Preserve older fixtures. No mail, reminders, feeds, money, AI, providers or
shared settings. Source generic. Construct K119 from `QA2 Cal ID DATE ` plus
X characters to total exactly 119 ASCII characters; K120=K119+A;
K121=K120+B; K121C=K120+C. Report lengths. All imports are SEPARATE single-row
uploads/jobs, not a multi-row file. Stored external IDs truncate at 120.
CSV external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Use M1, leap start 2028-02-29 10:00, end 11:00 same date, all_day=false,
room `QA2 Cal ID Room DATE`, notes `QA2 Cal ID Notes DATE`. Routes
/import/calendar/upload with fresh CSRF/file/source, explicit mapping,
recheck and commit; update unless stated. Inspect edit fields without saving.

1. Create client `QA2 Cal ID Client DATE` and hourly USD matter
   `QA2 Cal ID Matter DATE`, $100, no office/template. Record IDs/flashes,
   original importer source and the four key lengths; no batch event.
2. Import K119, title `QA2 Cal ID Short DATE`. Preview one create, commit.
   Record E1/job. One timed leap event with original room/notes/M1.
3. Import K120, title `QA2 Cal ID Boundary DATE`. Expect one created E2,
   distinct from E1. Exactly two events with respective titles.
4. Import K121, title `QA2 Cal ID Long DATE`. Expect one updated E2 because
   its first 120 characters equal K120. E1 stays Short; no third event.
5. Import K121C, title `QA2 Cal ID Alternate DATE`. Expect one updated E2,
   now Alternate; suffix after character 120 does not create a new identity.
6. Import K120 original Boundary title with duplicates=skip. Expect one
   skipped; E2 stays Alternate, E1 unchanged. No create or update.
7. Import K119 title `QA2 Cal ID Short Revised DATE`, update. Expect one
   updated E1 only; E2 stays Alternate. Short key remains distinct.
8. Import K121 with whitespace-only title. Expect one error
   `Event has no title.`, zero updates; failed.csv one row. Both events intact.
9. Restore K120 with Boundary title, update. Expect one updated E2 only,
   original Boundary title. E1 remains Short Revised.
10. Restore K119 with Short title, update. Expect one updated E1. Nine jobs:
    short, boundary, long, alternate, skip, short edit, error, boundary restore,
    short restore. Exactly two events, original fields except respective titles.
11. Clean up: close M1, report flash; restore importer source. Retain client,
    closed matter, E1 Short and E2 Boundary with original leap times/room/notes,
    nine jobs. Older fixtures untouched; no deletion.
12. What remains: key lengths, E1/E2 IDs, create/update/skip decisions, refused
    update preservation and per-case table. No credentials or private links.

### S167. Calendar CSV date-only formats preserve leap dates (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6091436704 2026-10-10T00:10:28Z

Source checked: _importmap.py _DATE_FORMATS/parse_any_datetime;
importer.py _calendar_datetime/prep_calendar/apply_calendar; calendar/form.html;
owner import permissions. English/ASCII/USD. Replace DATE with today's YYYYMMDD.
Preserve older fixtures. No mail, reminders, feeds, money, AI, providers or
shared settings. Source generic, explicit external_id `QA2 Cal Dates DATE A`,
title `QA2 Cal Dates Event DATE`, M1, all_day=true, ends_at empty, room
`QA2 Cal Dates Room DATE`, description `QA2 Cal Dates Notes DATE`. CSV columns
external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Each import is one upload/job, fresh CSRF/file/source, explicit mapping,
recheck then commit at /import/calendar/upload. Update unless stated.
Inspect persisted date on /calendar/E/edit without saving. No timezone changes.

1. Create client `QA2 Cal Dates Client DATE` and hourly USD matter
   `QA2 Cal Dates Matter DATE`, $100, no office/template. Record IDs/flashes,
   original source; no batch event.
2. Import starts_at=2028-02-29. Preview one create, commit. Record E/job.
   One all-day Feb 29 2028 event, no end, original matter/room/notes/title.
3. Update same ID starts_at=02/29/2028. Expect one updated, same leap date,
   all-day and no end. No additional event.
4. Update starts_at=29-Feb-2028. Expect one updated and same leap date;
   year suffix must not be mistaken for an offset. Same E and other fields.
5. Update starts_at=`February 29, 2028`, properly CSV-quoted. Expect one
   updated, same leap date, original title/room/notes/M1 and blank end.
6. Update starts_at=2028/02/29. Expect one updated, same leap date and E.
7. Update starts_at=20280229. Expect one updated, same leap date and E.
8. Update starts_at=2027-02-29. Expect one error
   `Could not read start '2027-02-29'.`, zero updates, failed.csv one row.
   Fresh E edit remains Feb 29 2028 with original fields.
9. Import starts_at=2028-03-01, duplicates=skip. Expect one skipped,
   no update/create; E remains Feb 29, no end and all-day.
10. Restore starts_at=2028-02-29, update. Expect one updated and original
    state. Nine jobs: ISO, US, abbreviated month, full month, slashes,
    compact, invalid leap, skip, restore. Exactly one event.
11. Clean up: close M1, report flash; restore original source. Retain client,
    closed matter, one all-day leap event with no end, nine jobs. Closed
    matter selected on edit, original text intact, older fixtures untouched.
12. What remains: IDs, input formats and persisted dates, invalid-leap
    preservation, counts and per-case table. No credentials or private links.

### S168. Calendar CSV external-ID case and outer-space handling (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6091633223 2026-10-10T00:30:25Z

Source checked: models.py ExternalRef string key/unique constraint;
importer.py Ctx.ref_get/ref_set and prep_calendar/apply_calendar;
_importmap.py row_values strip; calendar/form.html; owner import permissions.
English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve older fixtures.
No mail, reminders, feeds, money, AI, providers or shared settings. Source generic.
K=`QA2 Cal Case DATE A`, L=`QA2 Cal Case DATE a` differ only in last character.
CSV external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Use M1, starts_at=2028-02-29 10:00, ends_at=2028-02-29 11:00, all_day=false,
room `QA2 Cal Case Room DATE`, notes `QA2 Cal Case Notes DATE`. One row per
upload/job at /import/calendar/upload, fresh CSRF/file/source, explicit mapping,
recheck and commit; update unless stated. Read event edit fields without saving.

1. Create client `QA2 Cal Case Client DATE` and hourly USD matter
   `QA2 Cal Case Matter DATE`, $100, no office/template. Record IDs/flashes,
   original source and absence of batch events.
2. Import K, title `QA2 Cal Case Upper DATE`. Preview one create then commit.
   Record E1/job; one timed leap event with original matter/room/notes.
3. Import L, title `QA2 Cal Case Lower DATE`. Expect one created E2,
   distinct from E1: explicit keys retain case. Two events, respective titles.
4. Import K padded with three outer spaces, title `QA2 Cal Case Upper Revised DATE`.
   Expect one updated E1, not a third event. Mapping strips outer spaces;
   E2 remains Lower with original fields.
5. Import L padded with spaces, title `QA2 Cal Case Lower Revised DATE`.
   Expect one updated E2 only; E1 remains Upper Revised. Two events still.
6. Import original K/Upper title with duplicates=skip. Expect one skipped,
   no updates/creates; E1 stays revised and E2 unchanged.
7. Import original L/Lower title with duplicates=skip. Expect one skipped;
   both revised titles retained, original IDs unchanged.
8. Import K with whitespace-only title. Expect one error
   `Event has no title.`, zero updates, failed.csv one refused row.
   E1/E2 retain revised titles and original other fields.
9. Restore original K/Upper row, update. Expect one updated E1 only;
   E2 remains Lower Revised, same two IDs.
10. Restore original L/Lower row, update. Expect one updated E2, both original
    titles now restored. Nine jobs: upper, lower, padded upper/lower, two skips,
    error, two restores. Exactly two timed leap events.
11. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, E1 Upper and E2 Lower with original
    times/room/notes, nine jobs. All older fixtures untouched.
12. What remains: IDs, key case/whitespace distinctions, counts, refusal
    preservation and per-case table. No credentials, tokens or private links.

### S169. Calendar CSV location length, whitespace and clearing (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6091822175 2026-10-10T00:50:16Z

Source checked: importer.py prep_calendar/apply_calendar and upload/commit;
_importmap.py row_values strips outer whitespace; calendar/form.html location
input; owner import permissions. English/ASCII/USD. Replace DATE with today's
YYYYMMDD. Preserve older fixtures. No mail, reminders, feeds, money, AI,
providers or shared settings. Source generic. One row per upload/job, fresh
CSRF/file/source, explicit mapping, recheck then commit at /import/calendar/upload.
CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Use key `QA2 Cal Location DATE A`, title `QA2 Cal Location Event DATE`, M1,
starts_at=2028-02-29 10:00, ends_at=2028-02-29 11:00, all_day=false,
notes `QA2 Cal Location Notes DATE`. Original room=`QA2 Cal Location Room DATE`.
Build L300 from `QA2 Cal Location DATE ` padded with X to exactly 300 ASCII
characters; L301=L300+Y. Update duplicates unless stated. Read decoded
persisted location input at /calendar/E/edit without saving the event form.

1. Create client `QA2 Cal Location Client DATE` and hourly USD matter
   `QA2 Cal Location Matter DATE`, $100, no office/template. Record IDs/flashes,
   original importer source; no batch event.
2. Import original room. Preview one create, commit one created event E.
   Record job/ID; verify timed leap event with original title/notes/M1.
3. Update same key, room padded with three spaces on each side. Expect one
   updated, outer spaces trimmed, original room and same E; no extra event.
4. Update location=`QA2 Cal Location A  B DATE` with two internal spaces.
   Expect one updated and internal spaces preserved in decoded input.
5. Update location=L300. Expect one updated, exactly 300 stored characters,
   exact L300 and unchanged title/notes/times/M1.
6. Update location=L301. Expect one updated and stored L300 (first 300),
   same E and no additional event. Trailing Y must not persist.
7. Update location empty. Expect one updated and empty location input;
   other fields unchanged and one event still.
8. Import original room with duplicates=skip. Expect one skipped and
   location remains empty. No update/create.
9. Import L300 with whitespace-only title. Expect one error
   `Event has no title.`, zero updates, failed.csv one refused row.
   Fresh event remains original title and empty location, same other fields.
10. Restore original title and room, update. Expect one updated, exact
    original room and same E. Nine jobs: create, padded, internal spaces,
    L300, L301, clear, skip, refused, restore. Exactly one timed leap event.
11. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, E with original fields and all nine jobs.
    Closed matter selected on edit. All older fixtures stay untouched.
12. What remains: IDs, location lengths/decoded values, counts, refused and
    skipped update preservation, per-case results. No secrets or private links.


### S170. Calendar CSV title normalization before length limiting (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6092563159 2026-10-10T02:10:34Z

Source checked: importer.py prep_calendar/apply_calendar/upload/commit;
_importmap.py clean_name and row_values; calendar/form.html title input;
owner import permissions. English/ASCII/USD. Replace DATE with today's YYYYMMDD.
Preserve older fixtures. No mail, reminders, feeds, money, AI, providers or
shared settings. Source generic. Explicit key `QA2 Cal Title Limit DATE A`.
CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Use M1, leap day 2028-02-29 10:00 to 11:00, all_day=false, room
`QA2 Cal Title Limit Room DATE`, notes `QA2 Cal Title Limit Notes DATE`.
Original title=`QA2 Cal Title Limit Event DATE`. Build T300 by padding
`QA2 Cal Title Limit DATE ` with X to exactly 300 ASCII characters.
T301=T300+Y. Use one row/upload/job, fresh CSRF/file/source, explicit mapping,
recheck and commit at /import/calendar/upload. Update unless stated. Read
persisted decoded title at /calendar/E/edit without saving the event form.

1. Create client `QA2 Cal Title Limit Client DATE` and hourly USD matter
   `QA2 Cal Title Limit Matter DATE`, $100, no office/template. Record IDs/flashes,
   original source and absence of batch events.
2. Import original title. Preview one create then commit. Record E/job;
   one timed leap event with original title, room, notes and M1.
3. Update title with three outer spaces around original. Expect one updated,
   original persisted title without padding, same E, no extra event.
4. Update title=`QA2 Cal Title Limit A  B DATE`. Expect one updated with
   single space between A and B; title whitespace collapses, unlike notes.
5. Update title=T300. Expect one updated, exact 300-character T300,
   unchanged other fields and same E.
6. Update title=T301. Expect one updated with stored T300, length 300,
   trailing Y removed. Explicit key keeps this an update.
7. Update title with every single space in T300 replaced by three spaces.
   Expect one updated and exact T300: whitespace collapses before truncation.
   Confirm the full 300-character value, not only its displayed prefix.
8. Import original title with duplicates=skip. Expect one skipped,
   no update/create; persisted title remains T300.
9. Import whitespace-only title, update. Expect one error
   `Event has no title.`, zero updates and failed.csv one refused row.
   E remains T300 with original times/room/notes/M1.
10. Restore original title, update. Expect one updated, same E and original
    fields. Nine jobs: create, outer spaces, internal spaces, T300, T301,
    expanded spaces, skip, refused, restore. Exactly one event.
11. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, E with original fields and nine jobs.
    Closed matter selected on edit; all older fixtures untouched.
12. What remains: IDs, submitted/normalized/stored title lengths and values,
    counts, refusal preservation and per-case results. No secrets/private links.


### S171. Calendar CSV mixed valid and refused rows preserve peers (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6092761993 2026-10-10T02:30:26Z

Source checked: importer.py run_import, prep_calendar/apply_calendar,
upload/commit; _importmap.py row_values; calendar/form.html; owner permissions.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
older fixtures. No mail, reminders, feeds, money, AI, providers or shared settings.
Source generic; explicit keys `QA2 Cal Mixed DATE A`, B and C. Original titles
`QA2 Cal Mixed A DATE`, B and C. All use M1, Feb 29 2028 10:00 to 11:00,
all_day=false, room `QA2 Cal Mixed Room DATE`, notes `QA2 Cal Mixed Notes DATE`.
CSV columns external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Fresh CSRF/file/source, explicit mapping, recheck and commit at
/import/calendar/upload; update unless stated. Read persisted event fields
without saving event forms. One upload makes one job, including refused rows.

1. Create client `QA2 Cal Mixed Client DATE` and hourly USD matter
   `QA2 Cal Mixed Matter DATE`, $100, no office/template. Record IDs/flashes,
   original importer source and no batch events.
2. Upload three rows in order: valid A, B with whitespace-only title, valid C.
   Preview and commit expect two created, zero updated/skipped, one problem
   `Event has no title.` Record E-A/E-C and job. No B event; exactly two events.
3. Read failed.csv: exactly the refused B row with its key and error.
   Inspect A and C: original title/room/notes and leap times, both persisted
   despite the invalid middle row. No older event changed.
4. Repair B in a single-row upload with its original title. Expect one
   created E-B, three total events and original fields. Record job/ID.
5. Upload A Revised title, B invalid starts_at=2027-02-29, C Revised title.
   Expect two updated, one problem `Could not read start '2027-02-29'.`,
   zero created/skipped. A/C revised, B original with leap times unchanged.
6. Upload all three original valid rows with duplicates=skip. Expect three
   skipped, no creates/updates/problems. A/C remain revised, B original.
7. Upload all three original valid rows with update. Expect three updated,
   no creates/problems; all original titles and fields restored, same IDs.
8. Upload B with ends_at=not-a-date alone. Expect one problem
   `Could not read end 'not-a-date'.`, zero updates, failed.csv one row.
   B's original end 11:00 survives; A/C unchanged.
9. Repair B with original valid row. Expect one updated, no errors, same B.
   Three total events with original titles/times/room/notes/M1.
10. Repeat all three original valid rows, update. Expect three updated,
    zero creates/errors and same IDs. Eight jobs total: mixed create, B repair,
    mixed update, skip, restore, invalid end, B repair, repeat.
11. Clean up: close M1, report flash; restore original source. Retain client,
    closed matter, three original timed leap events and all eight jobs.
    Closed matter selected on edit; all older fixtures untouched.
12. What remains: IDs, per-job counts, failed-row identity and peer survival,
    final fields and per-case results. No credentials or private links.


### S172. Calendar CSV repeated explicit keys within one file (qa2)
status: posted https://github.com/Coil-Legal/coil/issues/89#issuecomment-6092991883 2026-10-10T02:50:26Z

Source checked: importer.py Ctx.ref_get/ref_set, prep_calendar/apply_calendar,
run_import and owner upload/commit; calendar/form.html persisted fields.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
all older fixtures. No mail, reminders, feeds, money, AI, providers or settings.
Source generic, key K=`QA2 Cal Repeated DATE A` (under 120 characters).
Titles First=`QA2 Cal Repeated First DATE`, Second=`QA2 Cal Repeated Second DATE`.
CSV external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
All valid rows use K, M1, 2028-02-29 10:00 to 11:00, all_day=false,
room `QA2 Cal Repeated Room DATE`, notes `QA2 Cal Repeated Notes DATE`.
Fresh CSRF/file/source, explicit mapping, recheck then commit at
/import/calendar/upload. Keep listed row order, update unless stated.
Read fresh event edit fields without saving; one upload is one job.

1. Create client `QA2 Cal Repeated Client DATE` and hourly USD matter
   `QA2 Cal Repeated Matter DATE`, $100, no office/template. Record IDs/flashes,
   original source and no batch events.
2. Import two rows K/First then K/Second in one file. Preview and commit:
   one created, one updated, no problems. Exactly one E, final title Second.
   Record E/job and verify leap times/room/notes/M1.
3. Upload those same two rows with duplicates=skip. Expect two skipped,
   zero creates/updates/problems, E still Second and one event only.
4. Upload K/Second then K/First, update. Expect two updated, zero creates,
   final title First, same E. Last valid row wins.
5. Upload K/Second then K with whitespace-only title. Expect one updated,
   one problem `Event has no title.`, final Second. Refused last row does not
   undo valid first row. failed.csv contains only the invalid row.
6. Upload K with invalid start 2027-02-29 then valid K/First. Expect one
   problem `Could not read start '2027-02-29'.` and one updated; final First
   with leap times. A refused first row does not stop the valid second row.
7. Upload three identical K/Second rows, update. Expect three updated,
   zero creates/problems, one E titled Second. Inspect fresh stored fields.
8. Upload K/First once, update. Expect one updated, final First, same E
   and all original times/room/notes/M1.
9. Upload two identical K/First rows, skip. Expect two skipped, no changes,
   one E First. Eight jobs total for cases 2 through 9.
10. Reload event edit twice. Confirm exact ID, First title, leap date 10:00
    to 11:00, original room/notes and M1, no duplicate event from any job.
11. Clean up: close M1, report flash; restore original source. Retain client,
    closed matter, E First and all eight jobs. Closed matter selected on edit;
    older fixtures untouched.
12. What remains: IDs, ordered input rows, per-job counts, final-title
    transitions and failed-row evidence, per-case results. No secrets/private links.


### S173. Calendar CSV skip mode creates new keys and rejects invalid duplicates (qa2)
status: retired by Ian October 9 finite acceptance direction

Source checked: importer.py Ctx refs, prep_calendar validation before skip,
apply_calendar, run_import and owner upload/commit; calendar/form.html.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
older fixtures. No mail, reminders, feeds, money, AI, providers or settings.
Source generic, keys K=`QA2 Cal Skip New DATE A`, L=`QA2 Cal Skip New DATE B`.
Titles First=`QA2 Cal Skip New First DATE`, Second=`QA2 Cal Skip New Second DATE`,
Third=`QA2 Cal Skip New Third DATE`. Valid rows use M1, 2028-02-29 10:00 to
11:00, all_day=false, room `QA2 Cal Skip New Room DATE`, notes
`QA2 Cal Skip New Notes DATE`. CSV columns external_id,title,matter_number,
starts_at,ends_at,all_day,location,description. Fresh CSRF/file/source,
explicit mapping, recheck and commit at /import/calendar/upload.
One upload/job, listed row order. Read persisted edit fields without saving.

1. Create client `QA2 Cal Skip New Client DATE` and hourly USD matter
   `QA2 Cal Skip New Matter DATE`, $100, no office/template. Record IDs/flashes,
   original source and absence of batch events.
2. With duplicates=skip, upload K/First then K/Second. Preview and commit
   one created and one skipped, no problems. Record E1/job; final First,
   exactly one timed leap event with original room/notes/M1.
3. Still skip, upload K/Second then new L/Third. Expect one skipped and
   one created E2. E1 remains First, E2 Third; two distinct events.
4. Still skip, upload K with whitespace-only title then valid L/Second.
   Expect one problem `Event has no title.` and one skipped. Invalid existing
   rows are validated before skip; E1 First/E2 Third remain untouched.
5. Still skip, upload K with invalid start 2027-02-29 then valid L/Third.
   Expect one problem `Could not read start '2027-02-29'.` and one skipped;
   both original leap events unchanged, failed.csv only refused K row.
6. Switch to update; upload K/Second and L/First. Expect two updated,
   no creates/problems; same E1/E2 now Second/First respectively.
7. Switch to skip; upload original K/First and L/Third. Expect two skipped;
   E1/E2 retain Second/First. No duplicate events.
8. Restore with update, original K/First and L/Third. Expect two updated;
   E1 First and E2 Third, original times/room/notes/M1. Seven jobs total.
9. Reload both event edits twice. Confirm original titles and exact IDs,
   two timed leap events, no changes to earlier retained fixtures.
10. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, E1 First/E2 Third and all seven jobs.
    Closed M1 selected on both edits. Report per-case results, counts and
    failed-row identity. No credentials, tokens or private links.


### S174. Calendar CSV blank all-day inference versus explicit false (qa2)
status: retired by Ian October 9 finite acceptance direction

Source checked: importer.py prep_calendar/_calendar_datetime/apply_calendar,
owner upload/commit; _importmap.py parse_bool/row_values; calendar/form.html.
Owner only, English/ASCII/USD. Replace DATE with today's YYYYMMDD. Preserve
older fixtures. No mail, reminders, feeds, money, AI, providers or settings.
Source generic, key `QA2 Cal Infer DATE A`, title `QA2 Cal Infer Event DATE`,
M1, room `QA2 Cal Infer Room DATE`, notes `QA2 Cal Infer Notes DATE`.
CSV external_id,title,matter_number,starts_at,ends_at,all_day,location,description.
Every row leaves ends_at empty. One row/upload/job, fresh CSRF/file/source,
explicit mapping, recheck and commit at /import/calendar/upload; update unless
stated. Inspect all_day checkbox, date and timed input values on fresh edit
without saving that form. No timezone changes or offset-bearing input.

1. Create client `QA2 Cal Infer Client DATE` and hourly USD matter
   `QA2 Cal Infer Matter DATE`, $100, no office/template. Record IDs/flashes,
   original source and no batch event.
2. Import starts_at=2028-02-29, all_day empty. Expect one created E,
   inferred all-day Feb 29, no end. Record E/job and original fields.
3. Update same date-only start with all_day=false. Expect one updated,
   timed midnight 00:00 to 01:00 on Feb 29, same E and other fields.
4. Update same date-only start with all_day=true. Expect one updated,
   all-day Feb 29 with no end; previous timed end is cleared.
5. Update starts_at=2028-02-29 10:00, all_day empty. Expect one updated,
   inferred timed event 10:00 to 11:00, same E and original fields.
6. Update starts_at=2028-02-29, all_day empty. Expect one updated,
   inferred all-day again with no end. One event only.
7. Update date-only start with all_day=0. Expect one updated, timed
   midnight to 01:00 (CSV false), same E, unchanged text/M1.
8. Import date-only start with all_day=true, duplicates=skip. Expect one
   skipped; E remains timed midnight to 01:00. No update/create.
9. Update invalid start=2027-02-29 and all_day=true. Expect one problem
   `Could not read start '2027-02-29'.`, failed.csv one row, zero updates.
   E remains timed leap midnight to 01:00, other fields unchanged.
10. Restore starts_at=2028-02-29 and all_day empty, update. Expect one updated,
    all-day leap with no end. Nine jobs, exactly one E with original fields.
11. Clean up: close M1, report flash; restore original importer source.
    Retain client, closed matter, one all-day leap event and nine jobs.
    Closed matter selected on edit; all older fixtures untouched.
12. What remains: IDs, submitted flags/start shapes, persisted all_day and
    start/end transitions, counts and per-case results. No secrets/private links.


## Backlog

Areas for the coordinator to turn into batches when a bot's queue is empty, in priority
order. Take the first area marked `open`, write one batch for it, and change its marker to
`done <batch id>`. One area may need two batches; then leave it `open` after the first and
say what is left in a sentence under it. Never write a batch for a parked area: the AI
assistant (saved for the very end, Ian 2026-10-04), or anything that sends real email, SMS or money. Since Ian's 2026-10-04 "let's do
Phase 2", invoicing, manual payments, payment plans, multi-currency and trust are in scope on
QA records. Since 2026-10-04 20:45 UTC testfirm runs on Stripe TEST keys (Ian swapped them), so card
payments are in scope on testfirm with Stripe's test cards only (4242 4242 4242 4242 succeeds,
4000 0000 0000 0002 is declined, any future expiry, any CVC). Never a real card number. qa2 has
no Stripe keys, so there the expected answer is the "not configured" message.

### Bot 1 backlog (testfirm)

Current coverage: P2-B1-0 guards passed R116/R118/R119/R120. P2-B1-1 core passed R117; approval-setting checks and P2-B1-2 template settings remain with Bot 2 after signatures. P2-B1-3 core is assigned R121 and roles queued R122; wait for those results before further manual-payment work. R123 is assigned for P2-B1-4 schedule/lifecycle; R124 queues manual-partial effects and R125 credit-to-zero completion/undo. R121 through R125 have now passed, including credit-to-zero and undo. R128 reserves draft-edit concurrency and source-release coverage; shared approval/template settings remain deferred to Bot 2.

Phase 2 first (Ian, 2026-10-04), in this order:

- `open` P2-B1-0. Card payments in Stripe test mode, now unblocked: a QA invoice sent to the
  capture inbox, its public page, Pay now by card with 4242 (the surcharge shown before
  redirect if the firm has one), the payment recorded once from Stripe's webhook, the
  invoice paid; a second invoice declined with 4000 0000 0000 0002 and left unpaid; ACH
  chosen and shown with no surcharge; Request card on file for a QA client with 4242 and a
  charge against it; a plan installment charged to that card. Two batches if needed.
- `open` P2-B1-1. Invoicing core: a new QA matter with time and an expense, an invoice
  drafted from them, approval, send to the capture inbox, resend, reminder, the PDF with
  Greek names, void, and the client statement. Two batches if needed.
- `open` P2-B1-2. Invoice template editor (/settings/invoice-template): logo, colours,
  columns, wording, preview; an invoice PDF picks the change up; put it back as found.
- `open` P2-B1-3. R137 reserves manual method/text normalization; role and further payment coverage remain open. R130 reserves receipt-date/list totals and R131 reserves WIP/A/R/revenue reconciliation; await results. Manual payments: check, cash and wire against a QA invoice, a partial, an
  over-balance refusal, the payment detail page, and A/R and revenue reports agreeing with
  the rows. No card.
- `open` P2-B1-4. Payment plans without cards: a plan on a QA invoice, installments, a
  reminder to the capture inbox, a plan credited to zero (#54), cancel and pause.
- `open` P2-B1-5. Split-payer groups and interest on overdue invoices, with the totals
  agreeing to the cent. R126 passed split-payer core; R129 queues payment isolation and group void protection. Interest remains open and deferred to Bot 2 because its rate is a firm setting.
- `open` P2-B1-6. Multi-currency end to end: EUR, GBP, CAD and MXN QA matters through
  invoice, manual payment, statement, the invoice list footer, dashboard cards, reports and
  the QuickBooks, matters and time CSV exports; nothing adds two currencies into one total.
- `open` P2-B1-7. Bulk invoicing across several QA matters, including one in another
  currency and one with nothing unbilled.
- `open` P2-B1-8. LEDES 1998B export of a QA invoice: the file, the refusal messages for
  missing data, and the date-range filter.

Phase 1 leftovers after that:

- `done R5` B1-1. Calendar feed box keyboard check (fix in `b45327d`): folded into R5 as
  its first case.
- `done R5` B1-2. Document templates and letter generation (/doctemplates): create a
  template with merge fields, generate a letter for a QA matter, check every field filled,
  non-Latin text, a missing field, the PDF, editing the template does not change letters
  already made.
- `done R6` B1-3. Matter templates (/settings/templates): create one with tasks, custom
  fields and milestones without amounts, apply it to a new QA matter, apply twice, deactivate.
- `done R7, R15` B1-4. Time and expenses beyond the basics: the timer start, stop and
  discard, an expense with a receipt upload, editing and deleting entries, rounding. R15
  closed the rest: the suggestions tool end to end, and the role matrix in place of the
  "own-time scoping" this note assumed (no such per-user filter exists on `/time`).
- `done R8` B1-5. Engagement letter templates (/engagements/templates) and a letter sent to
  the capture inbox for a QA contact, signed from the captured link, signed twice, voided.
- `done R9` B1-6. Dashboard and lists under load: create 60 QA contacts by CSV import, then
  check search, sort, paging and the conflict check speed; delete them after. No sort or
  paging controls exist in the contacts list template, so R9 covered search and the
  conflict check only; said so in the result rather than leaving it open on a feature that
  isn't there.
- `done R10` B1-7. Setup guide, feature map, feedback form and the firm's own settings page
  (read and one harmless save each, put back as found). Narrowed in R10: feature map and
  the feedback form were exercised (reads plus real feedback sends, each marked as a
  test); the setup guide's save/skip actions were left alone as provider settings, and
  the firm's own `/settings` page was dropped as firm-wide (Bot 2's territory, already
  done in S7). Nothing left open here.
- `done R12` B1-8. Sign-off: Calendar, deadlines and court rules, per docs/QA-HANDOFF.md's
  "Sign-off batches" outline. PASS. R13-R15 then signed off Conflict check, Client portal
  and Time suggestions the same way, and R16 covered Messages (never a backlog item, never
  previously tested), closing out every Phase 1 tool either bot has found open to date.

### Bot 2 backlog (qa2)

P2-B2-1 core, recipient, template and completed-signature coverage passed S125 through S134. The no-mail-server configuration edge needs a separate operator test, not provider changes by a bot. Money areas remain deferred while Bot 1 holds those tools; non-USD stays parked. Document ZIP boundary/identity checks passed S135/S136, S137 mapping is assigned, and S138/S139 reserve checkpoint and preview-page coverage. S140 reserves the closing owner-permission check. S141 reserves the notes CSV failed-row repair regression while money importers remain deferred. Await these results before further importer coverage.

Phase 2 first (Ian, 2026-10-04), in this order. qa2 has its own capture inbox at
https://qa2.coil.legal/qa-mail/ since 2026-10-04 and no Stripe keys.

- `open` P2-B2-1. Mail now works on qa2: a signature request and an engagement letter sent
  to a QA2 contact land in /qa-mail/ and can be signed from the captured link (#105).
- `open` P2-B2-2. Invoicing on a clean firm: the first invoice number, firm invoice
  settings (interest rate, surcharge, terms), approval by role (owner, attorney, billing;
  paralegal refused), send to /qa-mail/, the client portal showing the invoice, and Pay now
  answering that online payments are not configured.
- `open` P2-B2-3. Manual payments and plans by role: billing records a payment, attorney
  and paralegal cannot, a plan with installments and its reminder in /qa-mail/.
- `open` P2-B2-4. Multi-currency on a clean firm: a EUR and a GBP matter through invoice,
  payment, statement and exports, with the firm default changed midway.
- `open` P2-B2-5. Money tools switched off per firm: Invoices off holds Payments and
  Plans; every money page, card, tab, portal link and API route for them behaves as off.
- `open` P2-B2-6. Accessibility of the money pages: axe on the invoice list, invoice
  detail, payment pages, the statement and the portal invoice view.

Phase 1 leftovers after that:

- `done S5, S14, S15` B2-1. Settings > Tools deeper: Intake, Tasks, Documents, Calendar,
  Messages, Signatures, Conflict check, Engagement letters, Personal injury, Criminal
  defense and Discovery all covered (sidebar, dashboard card, matter tab, the direct URL's
  404, the API). Voice line itself is covered by S13. Still open: the Money section
  (Invoices, Statements, Payments, Plans, Trust, Accounting, Reports), deliberately left
  for Ian given how close a visibility-only toggle sits to the parked exclusions.
- `done S6, S17` B2-2. Spanish: portal login/home/messages/upload/logout, the sign-in email
  in /dev/outbox, the rate-limit duplicate, and the anti-enumeration check on the login
  page's neutral message (S6). The public intake form has no Spanish (confirmed by reading
  the code, not a bug). S17 then covered the engagement-letter half: the sign page's labels
  are fully localized, but two of its three validation errors and all three client-facing
  emails (`send_engagement`, `send_engagement_reminder`, `_email_signed_copies`) are
  hardcoded English with no `t()`/`lang_for()` call. Still open: document e-signature's
  Spanish strings, blocked by #105 (a signature request never leaves draft on qa2 with SMTP
  unset, so its sign page can't be reached live to compare); and invoice Spanish strings
  (invoices are a standing exclusion, so that needs its own call).
- `done S7, S18` B2-3. Firm settings: firm name, address, phone, email, website, timezone,
  client-facing language, currency, daily agenda checkbox, matter numbering. Logo upload
  lives only on the invoice-template page (parked, invoicing exclusion) and no date-format
  setting exists in the code, so both were dropped from the original note. Voice line
  itself is now covered by S13. S18 then covered Settings > Integrations: the cards and
  the CourtListener token field, including its overlong and non-Latin edges and the
  owner-only permission check. Nothing left open here.
- `done S8, S19, S21` B2-4. Importer at scale on a clean firm: 2,000 contact rows with
  mixed scripts, duplicates and bad rows; preview counts, commit, a second run, the
  export round trip (S8, contacts only). S19 then covered Matters, Calendar and Notes
  (small imports plus a 110-row run that crosses the `CSV_BATCH_ROWS=100` background-job
  threshold, continued across a page reload to stand in for an interrupted batch). S21
  closed the activities (time/expense) importer: create/update/skip, the required-date
  guard, the billed-flag behavior, and the owner-only permission check. Document ZIP import boundaries passed S135; S136 is assigned, with S137 mapping and S138 saved-progress coverage queued. Still open: the
  bills/trust importers, deliberately left for Ian since
  they create invoice/trust-ledger rows, the same exclusion as elsewhere.
- `done S10` B2-5. Users at scale: 20 users across 4 roles and 2 offices, rate edits, office
  reassignment, a role change's token revocation, deactivate/reactivate, duplicate-email
  and weak-password edges, the owner self-deactivation guard, the office delete-guard, and
  the audit log (filtered and CSV). S9 blocked on the bot's own login failure (verified not
  a product defect); S10 retried the same ground after Ian refreshed the stored password
  and passed clean, 14 PASS / 0 FAIL / 0 BLOCKED.
- `done S11` B2-6. Documents deep: folders, tags, versions, search with Greek and accents,
  sharing and unsharing many at once, a closed matter's documents.

## U01 implementation verification, held for release

These are finite verification steps for the customization implementation, not reserve
batches. Do not post before C01 and a release/operator handoff identifies the actual
new build and preserved fixture/configuration baselines. Keep C02/C03 sequential.

### U01-A. Profile A appearance and conditional task rule
status: hold, implementation local only; awaits tested release and C01
Gate: C02. Bot 1, testfirm. Start numbering at 3362 only after recording R154.

- As owner, open /settings/customization. Capture existing revision and all non-secret
  appearance/navigation/rule values. Preserve existing published rules if any; if all
  eight slots are used, stop with the prerequisite rather than replacing a rule.
- Preview Forest, compact spacing, workspace name `QA Defense DATE`, navigation label
  Matters = Cases with position 1. Add a single enabled rule in an unused slot: title
  `QA Defense Review DATE`, billing flat, practice area Criminal defense, offset 2.
  Expect the preview banner, proposed appearance, and no persisted change in another
  tab. Publish with the current revision; expect `Firm customization published.`
- Fresh session: verify chosen appearance, Cases navigation and saved rule. Create a
  synthetic client and a new flat-fee Criminal defense matter opened 2028-02-28 with
  the owner responsible. Expect exactly one rule-created ordinary task due 2028-03-01,
  assigned to the owner. Edit the matter name and verify no second rule-created task.
- Create a second matter for that client with hourly billing and the same practice area.
  Expect no task from this rule. Preserve both matters and every older fixture.
- Restore the recorded original revision through history. Expect a new revision and
  original appearance/rules. Existing generated task remains. Restore the profile A
  revision again, retaining the intended profile for upgrade evidence.
- Return browser screenshots, record IDs, revision IDs, matching/nonmatching outcomes
  and retained configuration. Report the exact release. Stop; coordinator releases
  settings ownership to Bot 2. No further field-normalization cases.

### U01-B. Profile B differentiation and persistence
status: hold, awaits U01-A and the same released build
Gate: C03. Bot 2, qa2. Continue after C01's 7271, accounting for any later assignment.

- Snapshot original /settings/customization values/revision, preserving all existing
  rules and fixtures. Select Plum, comfortable spacing, workspace name `QA Hourly DATE`,
  Matters label Client matters. Add one rule in an unused slot: title `QA Billing Review
  DATE`, billing hourly, practice area blank, offset 1. Preview and publish through UI.
- New synthetic client and hourly matter at $150/hour, opened 2028-02-29, owner responsible:
  expect one ordinary workflow task due 2028-03-01 assigned to that owner. A second flat-fee
  matter must not get this hourly-only task. Neither rule runs again on a matter edit.
- Verify fresh-session persistence and the published version history. A stale editor tab
  submitting the older revision must show `Settings changed in another session. Review
  them before saving.` and leave the current configuration unchanged.
- With a disposable non-owner user, prove /settings/customization is forbidden for both
  GET and POST; preserve their role restrictions and record evidence without credentials.
- Restore the original configuration through history and verify generated tasks remain,
  then restore the intended profile B revision for upgrade evidence. Retain only synthetic
  new records and all older fixtures; do not delete existing data.
- Return screenshots, exact pin, revision IDs, generated task IDs and a non-secret manifest.
  Coordinator compares with A's evidence; bots never log in to each other's firms.
  Stop. C06/C07 require real operator upgrade/restore evidence and cannot pass here.
