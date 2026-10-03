# Draft: next Bot 2 batch, Intake sign-off (written by Claude Code, 2026-10-03)

For whoever holds #89. Fill the placeholders from Bot 2's Users/Roles 5077-5091 result: case numbers continue after 5091, PIN/VER from qa2 /health, PRESERVE from that result's final state. Not posted yet.

## Next: Cases {N0} to {N13}, Intake and leads sign-off

QA Bot 2 only, https://qa2.coil.legal. Pin: `/health` commit `{PIN}`, version `{VER}`. Check before starting and before each mutation; stop if it moves. ACK first. Start every ACK, result and finding with `[QA Bot 2]`. One `| Case | PASS/FAIL/BLOCKED | Evidence |` row per case. BLOCKED means a request that was never sent or a missing prerequisite, never a pass. Never post passwords, tokens or private links.

Preserve everything the last result listed as retained{PRESERVE}. Create only records named `QA2 ... 20261003`. qa2 sends no email: notices land in the owner-only `/dev/outbox`. Do not start a follow-up sequence, do not send a draft, no invoices, payments, AI, SMS or provider settings.

The public intake form allows 5 submissions per address in 10 minutes. This batch uses 3. Use a signed-out browser session for the public form and a separate owner session for everything else.

| Case | Action and expected result |
|---|---|
| {N0} | Owner baseline. Open `/intake` and `/intake/pipeline`. Record the lead count and the count in each stage. Change nothing. |
| {N1} | Signed out, open `/intake/form` and submit with the name blank and every other field filled. Expect HTTP 400, the flash `Please tell us your name.`, the other fields still filled in, and no new lead for the owner. |
| {N2} | Signed out, submit: name `QA2 Intake Lead A 20261003`, email `qa2-intake-a-20261003@example.test`, phone `555-0100`, matter type Other with `QA2 custom type`, other party `QA2 Adverse 20261003 Καλημέρα`, and a two-line description with Greek on the second line. Expect the thank-you page. As owner: one new lead, status new, stage New, matter type `QA2 custom type`, other party and description exact. `/dev/outbox` has `New intake lead: QA2 Intake Lead A 20261003 (QA2 custom type)`. |
| {N3} | Signed out, submit a second lead with no email: name `QA2 Intake Lead B 20261003 ` followed by 220 letters `x`. Expect the thank-you page. As owner, the stored name is the first 200 characters, nothing else changed, no error page. |
| {N4} | Owner moves Lead A to Contacted, then to Consult scheduled. Expect `Moved QA2 Intake Lead A 20261003 to Contacted.` then `... to Consult scheduled.`, and the pipeline shows it in that column only. |
| {N5} | Owner edits Lead A's phone to `555-0101` and saves. Expect `Lead updated.` and the new phone after reload. |
| {N6} | Owner opens Lead A in a SECOND tab and leaves its Decline form loaded and unsent. In the FIRST tab, convert Lead A: new contact, billing Flat, matter name `QA2 Intake Matter 20261003`. If the flash says the conflict search found hits, record the names it lists, tick the conflict box, give the reason `QA2 waiver 20261003`, and convert again. Expect a success flash naming a new matter number; the lead is converted and links to that matter; the new contact is a client. Record the lead, contact and matter IDs. |
| {N7} | Stale decline, the fix in `7acb3a4`. In the SECOND tab, submit the Decline form loaded before conversion, reason `QA2 stale 20261003`. Expect `Converted leads keep their status.`; Lead A stays converted with the same matter; the matter is still open. |
| {N8} | Stale status. From that same stale page, use the status control to mark Lead A declined. Expect `Converted leads keep their status.` and nothing changed. |
| {N9} | Replay the conversion: in the FIRST tab, go back to Lead A's convert form and submit it again unchanged. Expect `This lead was already converted.` and no second matter or contact (matter and contact counts unchanged). |
| {N10} | Owner declines Lead B with reason `QA2 not a fit 20261003`. Expect `Declined QA2 Intake Lead B 20261003 xxx...` (name as stored), status declined, stage Lost, the reason shown on the lead. Then mark Lead B new with the status control. Expect `Marked ... as new.` and stage New. |
| {N11} | Roles. Owner reactivates the NEW billing and readonly users created in 5077. Billing signs in: `/intake` and Lead B open; a Decline POST for Lead B with current CSRF returns 403 and Lead B stays new. Readonly signs in: `/intake` opens; a stage POST for Lead B returns 403 and nothing changes. If a browser cannot send the POST, mark BLOCKED with that reason. |
| {N12} | Owner deactivates both users again. Expect `User saved` and inactive status for each, everything else about them unchanged. |
| {N13} | Owner audit and final state. Audit has a create for each public lead, the stage moves, the Lead A update, the conversion and its matter, and Lead B's decline. The stale decline, stale status, replay and the role-refused POSTs have no success entry. Final: Lead A converted with its matter open, Lead B new, the two reactivated users inactive again, the earlier protected fixtures unchanged, all 27 tools on, `/health` still pinned. |

This is the Intake sign-off. All PASS lets the tool be marked QA complete; any FAIL is filed as `QA2:` and only the failing cases are rerun after the fix. Next after this: a short retest of the quoted multi-line CSV import fix (`b1ccb23`).
