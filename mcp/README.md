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
