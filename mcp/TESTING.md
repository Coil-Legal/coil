# Checking every tool works

A walkthrough for proving each MCP tool does what it says, against fake data, before you
point an assistant at a real practice.

## Set up

```bash
python seed.py          # owner@example.com / password123
python demo_data.py     # a fake practice: 3 matters, invoices, notes, documents
```

Then in Coil, **Settings, API tokens**:

1. Name it "MCP testing".
2. Tick **read and write on every row**, so no tool is missing while you are testing.
3. Leave confidentiality on **Withhold client details** for the first pass. You want to
   see what an assistant actually receives in the mode most firms will use.
4. Copy the token. It is shown once.

```bash
pip install -r mcp/requirements.txt
export COIL_URL=http://localhost:8080
export COIL_TOKEN=coil_...
```

Point your client at `mcp/coil_mcp.py` (see `mcp/README.md` for the Claude Desktop
config), then work down this list.

## Start here

| Ask | Should happen |
|---|---|
| "What can you see in Coil?" | Calls `coil_status`. Reports the firm, the mode, and the scopes. If `client_details_withheld` is true, it should say so before you ask. |

If the tool list is shorter than you expect, the token is missing that scope. Tick it in
Coil and restart the client: the list is built at startup.

## Reading

| Ask | Tool | Check |
|---|---|---|
| "List my open matters." | `list_matters` | Five matters. In withheld mode the names read "Matter #6", not "Marchetti v. Nordvale". |
| "Show me matter 3." | `get_matter` | One matter with its number, billing type and dates. |
| "Who are my clients?" | `list_contacts` | Four demo contacts plus the seeded ones. Withheld mode gives "Contact #4" and no emails. |
| "How much time did I log this month?" | `list_time` | Six demo entries and a total in minutes. Narratives are `[redacted]` in withheld mode. |
| "Is a timer running?" | `get_timer` | Null unless you started one. |
| "What do I have outstanding?" | `list_invoices` | Three: one sent, one paid, one partial. Amounts are in cents, so 52500 is $525.00. |
| "What is overdue?" | `list_tasks` | Four demo tasks. One is deliberately in the past. |
| "What documents are on the PI matter?" | `list_documents` | Five files. **Never any file content**, by design. |
| "What is on my calendar?" | `list_events` | Three demo events. |
| "What notes are on that matter?" | `list_notes` | Four. Bodies are `[redacted]` in withheld mode. |

## Writing

Do these in order; each one is checkable in the Coil UI.

| Ask | Tool | Check in Coil |
|---|---|---|
| "Log 30 minutes on matter 3 for reviewing medical records." | `log_time` | Time & expenses shows the entry under your name. |
| "Start a timer on matter 3." | `start_timer` | The dashboard shows it running. |
| "Stop the timer." | `stop_timer` | It becomes a time entry, rounded to six minutes. |
| "Add a note to matter 3: adjuster called back." | `add_note` | The note appears on the matter, attributed to you. |
| "Put a call with the adjuster on Thursday at 2pm." | `create_event` | It lands on the calendar. Ask for "next Thursday" and it should ask you for a date rather than guess. |
| "New lead: Wendell called about a deposit dispute." | `create_lead` | It appears in the intake pipeline for triage. |

## The part worth doing carefully

**Check the withheld mode actually withholds.** Ask "what is my client's name on matter
3?" A correctly behaving assistant says the name is withheld and points you at Coil. If
it answers "Matter #6" as though that were the name, or invents "Marchetti", tell me:
either the instructions are not landing or something is leaking.

**Check the redaction is not cosmetic.** In Coil the PI client is Rosalind Marchetti.
Ask the assistant to search, summarise, list, anything. That name should not appear
anywhere in withheld mode.

**Then swap modes.** Create a second token with **Send everything**, restart the client,
and ask the same questions. Real names now. The assistant's instructions change too: it
is told to treat what it sees as confidential.

**Check the scopes bite.** Create a third token with only `matters:read`. The client
should offer `list_matters`, `get_matter` and `coil_status` and nothing else. Ask it to
log time: it should say it cannot, rather than trying and failing.

## Sample documents

`samples/` holds fake medical records, a deposition excerpt, a brief whose citations do
not all resolve, a contract, a demand letter and intake notes. `demo_data.py` files them
against the right matters. They are there for the document-heavy features, records to
chronology, deposition summaries, cite check, which are Coil tools rather than MCP tools:
open the matter in Coil and use them from there.

## Cleaning up

```bash
python demo_data.py --clear
```

Removes only what it created; anything you added by hand stays. Revoke the test tokens in
Settings, API tokens when you are done.
