# Mike: an optional AI workbench beside Coil

> On coil.legal this is offered as **Harfree** (https://coil.legal/harfree): the same
> software, requested separately, standalone or connected to Coil. This document is the
> technical side of that page.

[Mike](https://mikeoss.com) (MikeOSS) is an open-source legal AI platform for document
review, drafting and research. AGPL-3.0, the same license as Coil. Coil does not depend
on it and does not bundle it. A firm that wants it runs it as its own stack and points
it at Coil; a firm that does not never sees it.

What the pairing gives you: Mike's chat, document review and drafting, with live access
to the matters, tasks, notes, time and document text in Coil, under a token whose scopes
and confidentiality mode you chose. Coil stays the system of record for money, deadlines
and trust, which Mike does not do. Mike becomes the place an assistant works.

## Why it is an add-on rather than a feature

Mike is a Next.js frontend, an Express backend, Supabase Postgres and auth, and
R2-compatible object storage: roughly eight containers to Coil's one, and its own login.
That is a reasonable thing to run on a server you already manage and an unreasonable
thing to make every solo self-hoster carry. So the integration is a door, not a merge:
Coil exposes its tools over MCP at `/mcp`, and Mike, which speaks MCP as a client, walks
through it.

## Setting it up

1. **Run Mike.** Follow its own quick start: `git clone https://github.com/open-legal-products/mike`,
   copy the env templates, set the two secrets, add your model key (or run Ollama for a
   model that never leaves the building), `docker compose up --build`. Put it behind your
   proxy at something like `ai.yourfirm.com`. Its docs cover production deployment.

2. **Create a token in Coil.** *Settings, API tokens.* Give it only the scopes the assistant
   needs; `matters:read`, `documents:read`, `notes:read`, `tasks:read`, `time:read` and
   `time:write` is a sensible start. Leave confidentiality on **Withhold client details**
   unless the model Mike uses is one you would trust with a client's name. The token is
   shown once.

3. **Add Coil as a connector in Mike.** *Settings, Connectors, Add.* URL
   `https://coil.yourfirm.com/mcp`, authentication *bearer token*, paste the token. Mike
   stores it encrypted. The tools appear in the assistant immediately.

4. **Tell Coil where Mike is, optionally.** Set `MIKE_URL=https://ai.yourfirm.com` in
   Coil's `.env` (or under *Settings, Integrations* on a hosted firm) and Coil shows an
   *AI workbench* link in its navigation. Leave it unset and nothing appears.

## What the assistant can and cannot do through the door

Exactly what the token allows, nothing more. Coil registers only the tools the token's
scopes cover, so a read-only token is never even shown "log time". A redacted token gets
`Client #4` and `[redacted]` in place of names and matter substance, and Coil tells the
model in its instructions that those are placeholders, so it does not report them as
facts. Trust is deliberately not exposed over the API at all; no token can move client
money.

Document **bytes** are not served through MCP today, only metadata and extracted text.
Mike's review-and-edit features want the file. Until a `documents:files` scope exists, a
document that needs editing in Mike is uploaded to Mike's own library.

## What to watch

- **Rate limit.** Each MCP tool call is two API calls (identify the token, then the tool),
  so it draws on the token's limit twice as fast as the desktop bridge does.
- **Two logins.** Coil and Mike have separate accounts. There is no single sign-on between
  them yet.
- **Updates.** Both projects move quickly. Pull Mike from upstream rather than forking it
  to change it; Coil's side of the door is the REST API's contract, which is stable.

## For firms Coil hosts

Ask. Running Mike beside a hosted firm is a per-firm decision, and it is not part of the
free hosting; it is another stack with its own footprint.
