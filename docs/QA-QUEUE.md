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
status: queued

A systematic map rather than spot checks. Use the inactive users 10 (paralegal) and 11 (readonly) from S1, reactivated for this batch, and create `QA2 Sec Attorney 20261003` (attorney) and `QA2 Sec Billing 20261003` (billing). Deactivate all four at the end.

1. For each of the four roles, GET each of these and record the HTTP status: `/`, `/contacts`, `/matters`, `/intake`, `/conflicts`, `/tasks`, `/calendar`, `/documents`, `/messages`, `/time`, `/reports`, `/exports`, `/trust`, `/invoices`, `/payments`, `/settings`, `/settings/users`, `/settings/tools`, `/settings/api`, `/audit`, `/dev/outbox`, `/import`. Present it as one table, role by route. Compare it with the role descriptions on `/settings/users`; any route a role can open that its description says it cannot is a finding.
2. For readonly, send a POST with a valid CSRF token to `/contacts/new`, `/matters/new`, `/tasks/new` and `/calendar/new`. Each must be refused with nothing saved.
3. For billing, send a POST with a valid CSRF token to `/contacts/new` and to a closed matter's edit URL. Each must be refused (billing reads matters and contacts but does not change them).
4. Owner signs in, copies the session cookie value into a second client, then logs out in the first. The second client's next request must go to the login page.
5. The session cookie has `Secure`, `HttpOnly` and `SameSite=Lax` (or stricter). Report the flags.
6. Five wrong passwords for user 10 in a row, then the right one. Report what happens at each step (lockout, delay or nothing). Then sign in normally after any lockout clears, or record that it did not.
7. Password reset (if offered on the login page) for `qa2-sec-x-20261003@example.test`, a client contact, not a user: expect the same neutral message as for a real user and no email in `/dev/outbox`.
8. Deactivate the four users. Report the final state.

## Backlog

Areas for the coordinator to turn into batches when a bot's queue is empty, in priority
order. Take the first area marked `open`, write one batch for it, and change its marker to
`done <batch id>`. One area may need two batches; then leave it `open` after the first and
say what is left in a sentence under it. Never write a batch for a parked area: invoicing,
payments and plans, multi-currency, trust, the AI assistant, or anything that sends real
email, SMS or money.

### Bot 1 backlog (testfirm)

- `open` B1-1. Calendar feed box keyboard check (fix in `b45327d`): the feed URL boxes on
  /calendar take keyboard focus; axe `scrollable-region-focusable` is gone. Fold into the
  next batch as its first case rather than a batch of its own.
- `open` B1-2. Document templates and letter generation (/doctemplates): create a template
  with merge fields, generate a letter for a QA matter, check every field filled, non-Latin
  text, a missing field, the PDF, editing the template does not change letters already made.
- `open` B1-3. Matter templates (/settings/templates): create one with tasks, custom fields
  and milestones without amounts, apply it to a new QA matter, apply twice, deactivate.
- `open` B1-4. Time and expenses beyond the basics: the timer start, stop and discard, an
  expense with a receipt upload, editing and deleting entries, time suggestions if switched
  on, rounding, a staff user's own time only. No invoicing.
- `open` B1-5. Engagement letter templates (/engagements/templates) and a letter sent to the
  capture inbox for a QA contact, signed from the captured link, signed twice, voided.
- `open` B1-6. Dashboard and lists under load: create 60 QA contacts by CSV import, then
  check search, sort, paging and the conflict check speed; delete them after.
- `open` B1-7. Setup guide, feature map, feedback form and the firm's own settings page
  (read and one harmless save each, put back as found).

### Bot 2 backlog (qa2)

- `open` B2-1. Settings > Tools deeper: switch off each of five tools one at a time and check
  the sidebar, the dashboard card, the matter tab, the direct URL (404 with the owner
  message) and the API for that tool; switch each back on.
- `open` B2-2. Spanish: set a client contact's language to Spanish and walk the portal,
  the sign-in email in /dev/outbox, the public intake form in Spanish if offered, and any
  page that still shows English.
- `open` B2-3. Firm settings: firm name, address, logo upload (PNG, a large image, an SVG),
  time zone, date formats; check they appear where expected; put everything back.
- `open` B2-4. Importer at scale on a clean firm: 2,000 contact rows with mixed scripts,
  duplicates and bad rows; preview counts, commit, a second run, the export round trip.
- `open` B2-5. Users at scale: 20 users across roles and offices, deactivate and reactivate,
  rates, office reassignment, the audit trail of it all.
- `open` B2-6. Documents deep: folders, tags, versions, search with Greek and accents,
  sharing and unsharing many at once, a closed matter's documents.
