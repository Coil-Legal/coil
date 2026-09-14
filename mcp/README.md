# Coil MCP server

Lets an AI assistant work with a Coil instance: read the practice, log time, run the
timer, take notes, book calendar entries and file intake leads. It works against any
Coil, hosted or self-hosted, over the same REST API a script would use.

It holds no credentials of its own and grants nothing. **A token decides everything**,
and the firm creates that token in Coil at Settings, API tokens:

- **Which resources** it may touch, read and write, one checkbox each.
- **Whether client details leave the building at all.**

## The confidentiality choice

Tokens default to withholding client details. In that mode Coil replaces identity and
substance before anything leaves the server: client and contact names, matter names,
time narratives, note bodies, document names. Numbers, dates, amounts and statuses come
through, so an assistant can still answer "how much did I bill last week" or "what is
due on M-1001" without learning who the client is or what the case is about.

Choose "send everything" only for a model running on your own hardware, or a provider
you have checked retains nothing. That is a Rule 1.6 decision and it is yours.

The server reads the mode at startup and tells the model which one it is in, so an
assistant seeing "Client #4" knows that is a redaction rather than a client called
Client #4.

## Checking it works

`TESTING.md` walks every tool with fake data, including how to prove that withheld
mode really withholds. Load the fake practice first with `python demo_data.py`.

## Running it

```bash
pip install -r requirements.txt
export COIL_URL=https://coil.yourfirm.com
export COIL_TOKEN=coil_...
python coil_mcp.py
```

In Claude Desktop, add to `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "coil": {
      "command": "python",
      "args": ["/full/path/to/coil/mcp/coil_mcp.py"],
      "env": {
        "COIL_URL": "https://coil.yourfirm.com",
        "COIL_TOKEN": "coil_..."
      }
    }
  }
}
```

Only the tools your token allows are registered, so a read-only token shows no tools
that write. If a tool is missing, the token does not have the scope: tick it in Coil
and restart.

## What no token can reach

Trust accounting, payments, user permissions, firm settings and deleting anything are
not in the API at all. They are absent rather than gated, so no token, however it is
configured, can move client funds or remove a record.

## Over HTTP, for web clients such as Mike

`coil_mcp.py` runs beside a desktop assistant. A web tool cannot reach it, so Coil also
serves the same tools itself at **`/mcp`** over MCP's Streamable HTTP transport. No extra
process, no extra credential: the client sends the API token as a bearer header, exactly
as it would to `/api/v1`.

    URL:     https://coil.yourfirm.com/mcp
    Header:  Authorization: Bearer coil_...

Everything a token can see or do over HTTP is decided by the same scopes and the same
confidentiality mode as the REST API, because every tool call is dispatched through the
REST API in-process. A read-only token is not shown a tool that writes; a redacted token
never receives a client's name, whatever the client on the other end asks for.

Responses are plain JSON. The endpoint never opens a server-to-client event stream (GET
returns 405 with an explanation), and no session id is issued: the token is the session.

**Mike** ([mikeoss.com](https://mikeoss.com), AGPL, an open-source legal AI workbench)
connects this way from *Settings, Connectors, Add*: paste the URL, paste the token. See
`docs/MIKE.md` for running Mike beside Coil as an optional add-on.

One cost worth knowing: each tool call over HTTP is two API calls (one to identify the
token, one for the tool), so it draws on the token's rate limit twice as fast as the bridge.
