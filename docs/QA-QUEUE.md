# QA queue

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

## Backlog

Areas for the coordinator to turn into batches when a bot's queue is empty, in priority
order. Take the first area marked `open`, write one batch for it, and change its marker to
`done <batch id>`. One area may need two batches; then leave it `open` after the first and
say what is left in a sentence under it. Never write a batch for a parked area: the AI
assistant (saved for the very end, Ian 2026-10-04), or anything that sends real email, SMS or money. Since Ian's 2026-10-04 "let's do
Phase 2", invoicing, manual payments, payment plans, multi-currency and trust are in scope on
QA records. Card payments are not: testfirm holds LIVE Stripe keys, so on testfirm never
click Pay now, Request card on file, Charge card, or start a Stripe checkout. qa2 has no
Stripe keys, so there the expected answer is the "not configured" message.

### Bot 1 backlog (testfirm)

Phase 2 first (Ian, 2026-10-04), in this order:

- `open` P2-B1-1. Invoicing core: a new QA matter with time and an expense, an invoice
  drafted from them, approval, send to the capture inbox, resend, reminder, the PDF with
  Greek names, void, and the client statement. Two batches if needed.
- `open` P2-B1-2. Invoice template editor (/settings/invoice-template): logo, colours,
  columns, wording, preview; an invoice PDF picks the change up; put it back as found.
- `open` P2-B1-3. Manual payments: check, cash and wire against a QA invoice, a partial, an
  over-balance refusal, the payment detail page, and A/R and revenue reports agreeing with
  the rows. No card.
- `open` P2-B1-4. Payment plans without cards: a plan on a QA invoice, installments, a
  reminder to the capture inbox, a plan credited to zero (#54), cancel and pause.
- `open` P2-B1-5. Split-payer groups and interest on overdue invoices, with the totals
  agreeing to the cent.
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
  guard, the billed-flag behavior, and the owner-only permission check. Still open: the
  documents ZIP importer and the bills/trust importers, deliberately left for Ian since
  they create invoice/trust-ledger rows, the same exclusion as elsewhere.
- `done S10` B2-5. Users at scale: 20 users across 4 roles and 2 offices, rate edits, office
  reassignment, a role change's token revocation, deactivate/reactivate, duplicate-email
  and weak-password edges, the owner self-deactivation guard, the office delete-guard, and
  the audit log (filtered and CSV). S9 blocked on the bot's own login failure (verified not
  a product defect); S10 retried the same ground after Ian refreshed the stored password
  and passed clean, 14 PASS / 0 FAIL / 0 BLOCKED.
- `done S11` B2-6. Documents deep: folders, tags, versions, search with Greek and accents,
  sharing and unsharing many at once, a closed matter's documents.
