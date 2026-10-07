"""What a backup says about the code that made it, and what code can safely open it (#115).

A restore into older code can start healthy and still be wrong. A current backup restored
under commit e007fa9 reported $100.00 owed instead of $90.00, because that code does not
understand the newer credit rows. So every archive carries `coil-backup.json` at its root,
naming the Coil version and commit that made it and the tables and columns its database
holds. ops/restore.sh compares that schema with what the target code knows and refuses a
restore that would hand older code data it cannot read. Version strings like
`demo-20261006` do not sort reliably, so the schema is the gate and versions are only shown.

ops/backup.sh and ops/restore.sh compute the same schema and fingerprint inline, because
they must work without importing this package (the host has no Flask, and a container may
run older code than the host script). Keep all three definitions identical.
"""
import hashlib
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MANIFEST_NAME = "coil-backup.json"
MANIFEST_FORMAT = 1

# Tables the app creates outside the models (raw SQL, FTS shadow tables and the like).
# There are none today. Anything added by raw SQL must be listed here, or every restore
# into this code will be refused and every startup will warn about it.
EXTRA_KNOWN_TABLES = {}

log = logging.getLogger("schema")


def known_schema():
    """{table: sorted column names} for the tables this code's models define."""
    from .extensions import db
    from . import models  # noqa: F401  (registers every table on db.metadata)
    schema = {table.name: sorted(col.name for col in table.columns) for table in db.metadata.tables.values()}
    for name, columns in EXTRA_KNOWN_TABLES.items():
        schema[name] = sorted(set(schema.get(name, ())) | set(columns))
    return schema


def database_schema(conn):
    """{table: sorted column names} for a SQLite connection, without SQLite's own tables.

    Accepts a sqlite3 connection or a SQLAlchemy connection; both take a plain SQL string
    through exec_driver_sql / execute.
    """
    run = getattr(conn, "exec_driver_sql", None) or conn.execute
    rows = run("SELECT m.name, p.name FROM sqlite_master AS m, pragma_table_info(m.name) AS p "
               "WHERE m.type = 'table'").fetchall()
    schema = {}
    for table, column in rows:
        if not table.startswith("sqlite_"):
            schema.setdefault(table, []).append(column)
    return {table: sorted(columns) for table, columns in schema.items()}


def schema_fingerprint(schema):
    """sha256 of the canonical JSON of a schema, so two schemas compare with one string."""
    canonical = json.dumps(schema, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_manifest(snapshot, producer, version, commit):
    """The manifest for an archive whose database snapshot is at `snapshot` (or None)."""
    schema = {}
    if snapshot is not None:
        # Read-only: the snapshot is what gets archived, and reading it must not change it.
        conn = sqlite3.connect(Path(snapshot).resolve().as_uri() + "?mode=ro", uri=True)
        try:
            schema = database_schema(conn)
        finally:
            conn.close()
    return {
        "format": MANIFEST_FORMAT,
        "coil_version": version or "dev",
        "coil_commit": commit or "unknown",
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "producer": producer,
        "schema": schema,
        "schema_fingerprint": schema_fingerprint(schema),
    }


def unknown_to(schema, known):
    """(tables, columns) in `schema` that `known` does not have. Columns are 'table.column'.

    A column of an unknown table is not listed again: the table already says it.
    """
    tables = sorted(t for t in schema if t not in known)
    columns = sorted(f"{t}.{c}" for t, cols in schema.items() if t in known
                     for c in cols if c not in set(known[t]))
    return tables, columns


def short_list(items, limit=8):
    """'a, b, c and 4 more', so a long list cannot bury the message around it."""
    items = list(items)
    if len(items) <= limit:
        return ", ".join(items)
    return ", ".join(items[:limit]) + f" and {len(items) - limit} more"


def warn_if_newer_database(engine):
    """Log a warning when the live database holds tables or columns this code does not know.

    That is what a database restored from a newer Coil looks like: the app starts, and
    then shows totals computed without the rows it does not understand. Called once at
    startup after migrations. One query, and it never raises: a failed check must not
    stop Coil from starting.
    """
    try:
        if engine.dialect.name != "sqlite":
            return None
        with engine.connect() as conn:
            live = database_schema(conn)
        tables, columns = unknown_to(live, known_schema())
        if not tables and not columns:
            return None
        parts = []
        if tables:
            parts.append(f"tables {short_list(tables)}")
        if columns:
            parts.append(f"columns {short_list(columns)}")
        message = ("This database looks like it came from a newer Coil version: it has "
                   + " and ".join(parts) + " that this code does not know. Totals and balances "
                   "may be wrong until you run that Coil version or newer.")
        log.warning(message)
        return message
    except Exception:  # noqa: BLE001
        log.debug("schema check skipped", exc_info=True)
        return None
