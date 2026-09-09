# Launch checklist

Every tool in Coil, ordered by what it costs when it breaks rather than by where it sits
in the menu. Work down it. A pass is not "the page loaded", it is "I did the thing and
the result was right".

## How to report

For each item, say what you did, what you expected, and what happened. Three outcomes:

- **PASS** — did it, result was correct.
- **FAIL** — result was wrong. Include the URL, what you clicked, and the actual output.
- **BLOCKED** — could not test, and why.

Two rules that save everyone time:

**Check the value, not just the screen.** "Invoices page loads" is not a pass. "INV-1010
shows a $2,250.00 balance, which matches $4,500.00 total less $2,250.00 paid" is.

**Do not report an unconfigured integration as a bug.** Stripe, Twilio, IMAP and the voice
line are meant to be empty until a firm supplies its own credentials. See *Expected states*
at the end before filing anything.

## The demo data these numbers come from

Reload it any time with `python demo_data.py --clear` then `DEMO_EMAIL=ian@iandolan.com
python demo_data.py`.

| | |
|---|---|
| Matters | M-1008 Marchetti PI (contingency), M-1009 Okonkwo DWI (flat), M-1010 Bluebonnet contract (hourly) |
| Invoices | INV-1008 sent $525.00, INV-1009 paid $700.00, INV-1010 partial $4,500.00 with $2,250.00 outstanding |
| Trust | Okonkwo $2,250.00, Vance $1,600.00, total $3,850.00 |
| Documents | 6 demo files across PDF, DOCX, CSV, EML and plain text |
| Date of loss | 11 Feb 2026. Limitation date must therefore be 11 Feb 2028 |

---

# Tier 1 — Client money

A bug here costs a licence, not a customer. Test these properly even if it is slow.

## Trust accounting `/trust`

- [ ] Ledger totals **$3,850.00** across two clients: Okonkwo $2,250.00, Vance $1,600.00.
- [ ] Open each client ledger. Every entry shows a date, type, amount and running balance.
- [ ] **Try to overdraw.** Disburse more than a client holds. It must **refuse**, not warn
      and proceed. This is the single most important assertion in the app.
- [ ] **Try to cross matters.** Spend one matter's balance on another matter for the same
      client. It must refuse.
- [ ] **Try to cross clients.** A disbursement for client A funded by client B's balance
      must be impossible to express at all.
- [ ] Enter a bank statement at `/trust/reconcile` and run a three-way reconciliation.
      Ledger, client balances and bank must agree, and the one uncleared item must be
      listed as outstanding rather than silently absorbed.
- [ ] Clear that item, reconcile again, confirm it now balances.
- [ ] Trust deposit request `/trust/request-deposit` sends and records.
- [ ] Applying trust to an invoice `/trust/apply` moves money and leaves both sides right.

## Invoices `/invoices`

- [ ] INV-1010 shows **$2,250.00 outstanding**, not $4,500.00.
- [ ] INV-1009 is paid and appears in **no** AR aging bucket and gets **no** reminder.
- [ ] Create an invoice from unbilled time on M-1010. Hours and rate produce the right total.
- [ ] Edit a draft, add a line, adjust, discount. Totals recompute.
- [ ] Approval is opt-in: turn on "require invoice approval" in Settings, then submit,
      approve and reject are available on a draft and recorded in the audit log. With it
      off there is deliberately no approval step.
- [ ] Void an invoice. It stops counting toward AR and cannot be paid.
- [ ] Interest: set an interest rate in Settings first, or the interest action has nothing
      to do. Then `/invoices/<id>/interest` adds one line, not one per run.
- [ ] Monthly bulk billing is opt-in per matter: set a billing day on the matter, otherwise
      `/invoices/bulk/monthly` correctly skips it and says why.
- [ ] Bulk monthly run `/invoices/bulk/monthly` skips matters it should skip and says why.
- [ ] PDF renders with the firm's name and correct figures. A logo only appears once one
      is uploaded in Settings, Invoice template; no logo on a fresh firm is correct.
- [ ] Public view `/p/<token>` shows the invoice without a login and without leaking
      anything about other matters.

## Payments and payment plans

- [ ] `/payments/record` records a manual payment and updates the invoice balance.
- [ ] A payment plan at `/money/plans/new` schedules correctly and the arithmetic sums to
      the invoice total.
- [ ] Pause, resume and cancel a plan.
- [ ] With no Stripe key, pay links show mailing instructions rather than erroring.

## Fee splits and compensation

- [ ] Fee splits live per matter at `/money/splits/<matter_id>`, reached from the matter,
      not from a bare `/money/splits`. Origination and working splits total 100%.
- [ ] The compensation report at `/reports` agrees with the underlying time entries.

---

# Tier 2 — Deadlines and conflicts

Missing one of these is malpractice.

## Conflict check `/conflicts`

- [ ] Search "Nordvale". It must find the adverse party on M-1008.
- [ ] Search inside documents: "Bluebonnet" appears in the contract and should surface.
- [ ] The intake notes flag that the firm acts for Bluebonnet, which contracts with
      Nordvale, the adverse party. Does the check surface that relationship?
- [ ] A near-miss spelling still matches.

## Calendar, deadlines and court rules

- [ ] M-1008's limitation date is **11 Feb 2028**, exactly two years from the 11 Feb 2026
      date of loss in the medical records. Verify it against the documents rather than
      trusting the field.
- [ ] Create a deadline chain from a trigger date. Dates land on business days.
- [ ] Recurring events repeat correctly and stop at their end date.
- [ ] The iCal feed subscribes and shows the same events.
- [ ] Court rules `/rules` applies a starter set. Note it is marked *partial* on the
      website: generic sets, not real jurisdiction rules. Confirm it does not present
      itself as more.

## Tasks `/tasks`

- [ ] The overdue task shows as overdue.
- [ ] Standard PI task set `/pi/<id>/tasks/standard` creates once, not twice on re-run.

---

# Tier 3 — Clients see this

## Client portal `/portal`

- [ ] Magic-link login works and expires.
- [ ] A client sees **only** their own matters, invoices, documents and messages. Try to
      reach another client's record by editing the URL. It must refuse.
- [ ] Spanish rendering, if the contact's language is set.

## E-signature `/signatures`

- [ ] Send an engagement letter, sign it, and confirm the certificate records who, when,
      where and what was signed.
- [ ] A signed document cannot be altered afterwards.

## Intake `/intake`

- [ ] Public form submits and creates a lead.
- [ ] Convert a lead to a matter. The conflict check runs as part of it.
- [ ] Pipeline drag and drop moves a lead between stages and persists.
- [ ] Sequences draft rather than send while auto-send is off.

## Messages `/messages`

- [ ] A portal message reaches the client and the reply lands on the matter.
- [ ] Without Twilio, texts are stored and clearly not sent.

---

# Tier 4 — Documents and practice areas

## Documents `/documents`

- [ ] Upload, version, and confirm the older version is still retrievable.
- [ ] Full-text search finds **inside** files: "epidural" (PDF), "indemnify" (DOCX),
      "light duty" (EML), "Lakeshore" (PDF and CSV).
- [ ] Folders and tags filter.
- [ ] Document automation `/doctemplates` fills a Word template from a matter.

## Personal injury `/pi`

- [ ] Providers, records requests and bills requests generate correct letters.
- [ ] Liens: add, edit, and generate a reduction letter.
- [ ] **Settlement worksheet.** Gross, fees at the contingency rate, costs, liens and net
      to client must add up. Costs already billed must not be counted twice.
- [ ] Approve and disburse posts to trust correctly, and the trust ledger reflects it.
- [ ] Demand package assembles the right documents.

## Criminal defense `/criminal`

- [ ] Charges with attorney-entered ranges.
- [ ] Court date chain generates.
- [ ] Speedy-trial calculation is right, and says what it is counting from.
- [ ] Disposition PDF renders.

## Discovery and depositions `/discovery`

- [ ] Propound from a starter set; respond to served discovery with objections flagged.
- [ ] Deposition summary from `deposition-excerpt-demo.txt` produces a summary with page
      and line cites.
- [ ] **Save with an empty summary box keeps the existing summary** and warns. Clearing it
      requires ticking the box. (This was a real bug; confirm the fix.)

## Research `/research`

- [ ] Case law search returns results.
- [ ] Full opinion text loads, now that a CourtListener token is set.
- [ ] **Cite check on `brief-with-citations-demo.txt`.** Six citations. Celotex, Anderson
      and Matsushita are real and must resolve. Marbury and Vasquez-Lindberg are invented
      and must come back not found. **Halloway 812 F.3d 1144 is the interesting one**: that
      page is a real pincite into *Tubbs v. Surface Transportation Board*, so the number
      resolves while the case name does not. It must be reported as **wrong case**, never
      as resolved.
- [ ] Confirm it does not claim to say whether a case is still good law. It is not a
      citator and must not imply it is.

---

# Tier 5 — AI

Currently OpenRouter with `google/gemini-2.5-flash`, on the firm's own key.

- [ ] `/ai` shows available, the model, and today's spend.
- [ ] Ask Coil answers a plain question about a matter.
- [ ] Matter summary, invoice narrative polish, dates from documents.
- [ ] Records to chronology from `medical-records-demo.pdf` produces a dated treatment
      timeline ending at maximum medical improvement on 9 July 2026.
- [ ] Case audit sweep runs and flags something real.
- [ ] PI case scoring produces a score with reasons.

### Does it make things up

The demo documents contain deliberate traps. These matter more than the happy paths.

- [ ] **The deposition contradicts itself**: a twenty-minute fuel stop, then the logbook
      says forty-five, then "I don't remember exactly". A summary that reports one figure
      as fact is wrong. Run it twice: contradiction detection has been inconsistent.
- [ ] **The email corrects the intake notes**: light duty for three weeks, not four. Does
      anything notice the newer document supersedes the older?
- [ ] **The demand letter concedes** the C6-C7 changes are chronic and not from the
      collision. A summary that omits that is telling you what you want to hear.
- [ ] **The CSV totals $22,607.00**, matching the demand exactly. A tool reporting a
      different figure has an arithmetic problem.
- [ ] Ask the AI something the documents do not answer. It should decline rather than
      invent.

---

# Tier 6 — Platform

## API and MCP

- [ ] Token scopes: a `matters:read` token exposes 3 MCP tools; a full token exposes 17.
- [ ] Ask a read-only token to log time. It should say it cannot, not fail trying.
- [ ] **Withheld mode.** With a redacted token, "Marchetti" must not appear in any API or
      MCP response. Then repeat with a full token and confirm it does. Absence alone
      proves nothing.
- [ ] `/api/v1/documents` returns metadata only, never file bytes or the filesystem path.
- [ ] Rate limit returns 429 with Retry-After. Note the counter is per worker: with
      WEB_CONCURRENCY=2 the advertised 120 a minute is enforced as 60 per worker, so
      sequential calls over a slow link may never trip it. Hammer it from one connection.
- [ ] Full walkthrough in `mcp/TESTING.md`.

## Exports, import, webhooks

- [ ] `/exports` produces CSV for contacts, matters, time, invoices, payments and the full
      trust ledger. Open one and confirm the figures match the screens.
- [ ] Importer `/importer`: run a Clio-shaped CSV through preview, confirm the mapping,
      commit, and check nothing unrelated was overwritten.
- [ ] Failed-rows CSV downloads and explains each failure.
- [ ] Webhooks fire on task.completed and matter.closed, retry on failure, and the secret
      is never shown to a readonly user.

## Backup and restore

- [ ] `python -m app.cli backup` writes to `data/backups`, keeps the newest 14.
- [ ] Extract one and run `PRAGMA integrity_check` on the database inside it.
- [ ] Confirm the archive survives a container rebuild.

---

# Tier 7 — Setup and administration

## Setup guide `/setup-guide`

- [ ] All five steps render, each saying what it does, whether you need it, and the cost.
- [ ] Skip a step. It records as skipped and moves on without changing anything.
- [ ] Come back and complete a skipped step.
- [ ] Save a value, then save again with the box blank. The stored value survives.
- [ ] Type `none` to clear one.

## Settings `/settings`

- [ ] Firm details, offices, users and roles.
- [ ] **Permissions.** Log in as readonly and confirm trust and settings are unreachable.
      A paralegal must not reach trust.
- [ ] Invoice template: logo, colours, columns, wording, preview.
- [ ] AI settings: model, cap, provider choice, and both privacy toggles.
- [ ] Choosing "Anthropic directly" shows the warning that Coil cannot enforce retention
      for you.
- [ ] API tokens: the scope grid, the confidentiality choice, revoke.
- [ ] Audit log records every destructive action with who and when.

## Feedback

- [ ] The sidebar link submits and reaches us, carrying the page, build and firm.

---

# Expected states, not bugs

Do not file these.

| What you will see | Why it is correct |
|---|---|
| Stripe, Twilio, IMAP unset | The firm supplies its own. Every feature degrades with an explanation. |
| Voice line disabled | Needs Twilio and a deliberate switch-on in Settings. |
| Trust reconciliation "out of balance" with an uncleared item | That is what a reconciliation is for. Enter a bank statement to test it properly. |
| No AI key on a hosted instance until the firm adds one | Coil never covers inference. The environment is deliberately ignored on hosted instances. |
| Court rules described as generic starter sets | Marked *partial* on the website. Honest, not incomplete. |
| Cite check does not say whether a case is still good law | CourtListener has no citator. Stated on the page. |
| Interior screens cramped on a phone | One breakpoint at 1000px; the site says the screens are laid out for a desktop. |

# When you are done

Report by tier, worst first. For anything that failed, give the URL, the steps, expected
versus actual, and whether you could repeat it. If something failed once and passed on
retry, say so: intermittent is a different problem from broken, and it is usually the
model rather than the code.
