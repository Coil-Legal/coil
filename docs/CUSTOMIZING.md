# How one firm's Coil becomes its own

Every firm runs the same Coil. What makes a firm's Coil its own is a set of switches stored
on the firm, never a separate copy of the code. That is what lets a firm have software that
fits the way it works and still take every update the day it ships.

## What a firm can change today

**Tools.** Settings > Tools, owner only. Each tool in `app/tools.py` can be switched off.
A switched-off tool leaves the sidebar, the dashboard cards and the matter tabs, and its
staff pages answer 404 with a note pointing the owner back to Settings > Tools. Nothing is
deleted. Switching it back on brings back everything recorded in it.

Never switched off, on purpose:

- **Core:** dashboard, contacts, matters, settings, audit log, exports, import, setup guide.
  Exports in particular: a firm must always be able to take its data and leave.
- **Links already sent to clients:** signing, pay, public invoice and tracking links. The
  client was promised them.
- **Webhooks, the API and MCP:** Twilio and Stripe keep posting and are recorded, so
  switching off Messages or Payments never loses a text or a payment. API and MCP access is
  governed by each token's scopes. (A tool switch does not yet narrow the API; if a firm
  wants that, make it a follow-up rather than assume it.)

Tools can depend on each other. Payments and Plans need Invoices, Time suggestions needs
Time, Court rules needs Tasks. Switching the parent off takes the dependent with it, and the
firm's own tick is kept, so switching the parent back on restores both.

**Dashboard cards.** Each user already picks and orders their own cards under Dashboard >
Customize. Cards for switched-off tools disappear for everyone.

## When a firm asks for something

The promise on coil.legal is that most requests are built, tested and live within 7 days,
and that a feature built for one firm becomes available to all of them, for each firm to
switch on if it wants it. Here is how to keep
both halves of that true.

1. **Decide the shape.** A change to how an existing screen behaves for everyone is an
   ordinary change. A new tool, or a behaviour only some firms want, is a switch.
2. **For a new tool:** add a `Tool(...)` to `TOOLS` in `app/tools.py` with its URL prefixes
   and `default_on=False`. Wrap its sidebar link in `{% if tool_on('key') %}`. It ships to
   every firm in the next update, switched off; the firm that asked turns it on under
   Settings > Tools, where it is marked *optional*.
3. **For a behaviour inside an existing tool:** prefer a firm setting with the current
   behaviour as its default, so no firm sees a change it did not ask for.
4. **Leave it off by default, even if it proves popular.** The promise is that every firm
   can have a requested feature, not that every firm gets it. A firm opts in; nobody wakes
   up to a tool they did not choose. `default_on=True` is only for changes to how an
   existing tool works that every firm has effectively asked for, and even then prefer a
   setting whose default keeps today's behaviour.
5. **Tests.** Add a case to `tests/test_firm_tools.py` for any new tool: off by default if
   optional, its pages close when off, its link leaves the menu.

Never fork the code for one firm. A private version stops receiving updates and breaks the
"one update away" promise every self-hosted firm relies on.
