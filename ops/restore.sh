#!/usr/bin/env bash
# Restore one Coil backup into a directory.
#
#   ops/restore.sh [--allow-downgrade] <archive.tar.gz> <target-dir>
#
# Restores practice.db, uploads/, pdf/ and .env when included. It refuses to write into a directory
# that already holds a database, because the one time you run this is the one time you
# cannot afford to overwrite the wrong firm. Move the old data aside first.
#
# It also refuses to restore a backup under older code. Older Coil starts fine on a newer
# database and then shows wrong balances, because it ignores rows it does not understand.
# When the target already holds Coil code, the backup's tables and columns are compared
# with what that code knows, and anything unknown stops the restore before the target is
# touched. --allow-downgrade restores anyway, with a warning.
set -euo pipefail

USAGE="usage: restore.sh [--allow-downgrade] <archive.tar.gz> <target-dir>"
ARCHIVE=''
TARGET=''
POSITIONAL=0
ALLOW_DOWNGRADE=0
for arg in "$@"; do
  case "$arg" in
    --allow-downgrade) ALLOW_DOWNGRADE=1 ;;
    --*) echo "unknown option: $arg"; echo "$USAGE"; exit 2 ;;
    *)
      POSITIONAL=$((POSITIONAL + 1))
      case "$POSITIONAL" in
        1) ARCHIVE="$arg" ;;
        2) TARGET="$arg" ;;
        *) echo "$USAGE"; exit 2 ;;
      esac ;;
  esac
done
[ -f "$ARCHIVE" ] || { echo "$USAGE"; exit 2; }
[ -n "$TARGET" ] || { echo "$USAGE"; exit 2; }

if [ -e "$TARGET/data/practice.db" ] || [ -L "$TARGET/data/practice.db" ]; then
  echo "refusing: $TARGET/data/practice.db already exists. Move it aside first." >&2
  exit 1
fi

# A missing database does not make leftover uploads or PDFs disposable. Restore
# only into a fresh data directory, never through a link to another installation.
if [ -L "$TARGET/data" ] || { [ -e "$TARGET/data" ] && [ ! -d "$TARGET/data" ]; }; then
  echo "refusing: $TARGET/data must be a real directory, not a link or file. Choose a fresh target." >&2
  exit 1
fi
if [ -d "$TARGET/data" ]; then
  shopt -s nullglob dotglob
  EXISTING_DATA=("$TARGET/data/"*)
  shopt -u nullglob dotglob
  if [ "${#EXISTING_DATA[@]}" -gt 0 ]; then
    echo "refusing: $TARGET/data is not empty. Move existing data aside or choose a fresh target." >&2
    exit 1
  fi
fi

# CLI archives include data/; host nightly archives put practice.db at the root.
# Inspect before writing so an ambiguous or unrelated archive cannot look restored.
MEMBERS=$(tar -tzf "$ARCHIVE")
NORMALIZED=$(printf '%s\n' "$MEMBERS" | sed 's|^\./||')
CLI_LAYOUT=0
NIGHTLY_LAYOUT=0
HAS_ENV=0
grep -Fxq 'data/practice.db' <<< "$NORMALIZED" && CLI_LAYOUT=1
grep -Fxq 'practice.db' <<< "$NORMALIZED" && NIGHTLY_LAYOUT=1
grep -Fxq '.env' <<< "$NORMALIZED" && HAS_ENV=1
if [ "$((CLI_LAYOUT + NIGHTLY_LAYOUT))" != 1 ]; then
  echo "FAILED: archive must contain exactly one database layout (data/practice.db or practice.db)." >&2
  exit 1
fi
# coil-backup.json names the code that made the archive. Older archives have none.
MANIFEST_COUNT=$(grep -Fxc 'coil-backup.json' <<< "$NORMALIZED" || true)
if [ "$MANIFEST_COUNT" -gt 1 ]; then
  echo "FAILED: archive must contain at most one coil-backup.json, without duplicates." >&2
  exit 1
fi
if [ "$HAS_ENV" = 1 ] && { [ -e "$TARGET/.env" ] || [ -L "$TARGET/.env" ]; }; then
  echo "refusing: $TARGET/.env already exists. Move it aside first." >&2
  exit 1
fi

# Prefer Python: some native sqlite3 CLIs cannot open an intact WAL-mode
# snapshot read-only until sidecars exist. Python handles that fresh restore.
# Keep the CLI fallback for hosts without Python. Never skip validation.
if command -v python3 >/dev/null 2>&1; then
  VALIDATOR=python3
elif command -v sqlite3 >/dev/null 2>&1; then
  VALIDATOR=sqlite3
else
  echo "FAILED: install sqlite3 or Python 3 with SQLite support before restoring." >&2
  exit 1
fi

check_database() {
if [ "$VALIDATOR" = sqlite3 ]; then
  if ! CHECK=$(sqlite3 -readonly "$1" "PRAGMA integrity_check;" 2>&1); then
    echo "FAILED: database could not be checked ($CHECK)" >&2
    exit 1
  fi
  [ "$CHECK" = "ok" ] || { echo "FAILED: database is not intact ($CHECK)" >&2; exit 1; }
else
  python3 - "$1" <<'PY'
from pathlib import Path
import sqlite3
import sys

try:
    uri = Path(sys.argv[1]).resolve().as_uri() + '?mode=ro'
    with sqlite3.connect(uri, uri=True) as conn:
        rows = conn.execute('PRAGMA integrity_check').fetchall()
    if rows != [('ok',)]:
        raise ValueError('integrity_check did not return ok')
except (sqlite3.Error, OSError, ValueError) as exc:
    print(f'FAILED: database is not intact ({exc})', file=sys.stderr)
    sys.exit(1)
PY
fi
}

# Validate the single archived database before extracting anything into the target.
DB_MEMBER='practice.db'
[ "$CLI_LAYOUT" = 1 ] && DB_MEMBER='data/practice.db'
if [ "$(grep -Fxc "$DB_MEMBER" <<< "$NORMALIZED")" != 1 ]; then
  echo "FAILED: archive must contain one database member, without duplicates." >&2
  exit 1
fi
grep -Fxq "$DB_MEMBER" <<< "$MEMBERS" || DB_MEMBER="./$DB_MEMBER"
RESTORE_STAGE=$(mktemp -d "${TMPDIR:-/tmp}/coil-restore-check.XXXXXXXX")
PUBLISH_STAGE=''
TARGET_CREATED=0
cleanup_restore() {
  status=$?
  trap - EXIT
  set +e
  # The marker shares the database inode. It also detects a successful rename
  # if a signal arrived before the next shell statement could run.
  if [ -n "$PUBLISH_STAGE" ]; then
    if ! [ "$TARGET/data/practice.db" -ef "$PUBLISH_STAGE/database.marker" ]; then
      # Remove only the environment link made by this invocation.
      if [ "$TARGET/.env" -ef "$PUBLISH_STAGE/payload/.env" ]; then
        rm -f "$TARGET/.env"
      fi
    fi
    rm -rf "$PUBLISH_STAGE"
  fi
  rm -rf "$RESTORE_STAGE"
  if [ "$TARGET_CREATED" = 1 ]; then
    rmdir "$TARGET" 2>/dev/null
  fi
  exit "$status"
}
trap cleanup_restore EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
tar -xOzf "$ARCHIVE" "$DB_MEMBER" > "$RESTORE_STAGE/practice.db"
if [ ! -s "$RESTORE_STAGE/practice.db" ]; then
  echo "FAILED: archived database is empty or is not a readable database file." >&2
  exit 1
fi
check_database "$RESTORE_STAGE/practice.db"

# Version check, still before anything is written into the target. The gate is the
# archived database itself: any table or column the target code does not know means the
# backup came from newer code. Versions are shown but never compared, because names like
# demo-20261006 do not sort.
MANIFEST_FILE=''
if [ "$MANIFEST_COUNT" = 1 ]; then
  MANIFEST_MEMBER='coil-backup.json'
  grep -Fxq "$MANIFEST_MEMBER" <<< "$MEMBERS" || MANIFEST_MEMBER="./$MANIFEST_MEMBER"
  MANIFEST_FILE="$RESTORE_STAGE/coil-backup.json"
  tar -xOzf "$ARCHIVE" "$MANIFEST_MEMBER" > "$MANIFEST_FILE"
fi
COMPOSE_FILE=''
for name in compose.yaml compose.yml docker-compose.yaml docker-compose.yml; do
  if [ -f "$TARGET/$name" ]; then COMPOSE_FILE="$name"; break; fi
done
TARGET_CODE=none
KNOWN_FILE="$RESTORE_STAGE/known-schema.json"
KNOWN_ERRORS="$RESTORE_STAGE/known-schema.err"
KNOWN_ERROR=''
if [ -f "$TARGET/app/models.py" ] || [ -n "$COMPOSE_FILE" ]; then
  TARGET_CODE=unavailable
  # A source checkout first. No bytecode: nothing may be written into the target yet.
  if [ -f "$TARGET/app/models.py" ]; then
    if ! command -v python3 >/dev/null 2>&1; then
      KNOWN_ERROR="python3 is not installed"
    elif (cd "$TARGET" && PYTHONDONTWRITEBYTECODE=1 python3 -m app.cli known_schema) \
        < /dev/null > "$KNOWN_FILE" 2> "$KNOWN_ERRORS"; then
      TARGET_CODE=ok
    elif grep -Fq 'unknown command: known_schema' "$KNOWN_FILE"; then
      KNOWN_ERROR="the code in $TARGET has no known_schema command, so it predates this check and is older than any backup that has a manifest"
    else
      KNOWN_ERROR="python3 -m app.cli known_schema failed: $(tail -n 1 "$KNOWN_ERRORS")"
    fi
  fi
  # Otherwise ask the image the compose file runs, which is the code that will start.
  # Compose reads a private copy of the compose file next to an empty .env: the target's
  # own .env usually cannot exist yet (a nightly archive carries it, and this script refuses
  # to overwrite one), and compose will not load a file whose env_file is missing. The copy
  # sits in a directory with the target's name, so compose derives the same project and
  # image names. The image then runs on its own with no network and no mounts, rather than
  # through `compose run`, which would join the proxy network carrying the live site's
  # routing labels and could be sent real traffic for as long as it runs.
  if [ "$TARGET_CODE" != ok ] && [ -n "$COMPOSE_FILE" ]; then
    if ! command -v docker >/dev/null 2>&1; then
      KNOWN_ERROR="${KNOWN_ERROR:+$KNOWN_ERROR; }docker is not installed"
    elif ! command -v python3 >/dev/null 2>&1; then
      KNOWN_ERROR="${KNOWN_ERROR:+$KNOWN_ERROR; }python3 is not installed, so the compose file could not be read"
    else
      PROJECT_COPY="$RESTORE_STAGE/project/$(basename "$(cd "$TARGET" && pwd)")"
      mkdir -p "$PROJECT_COPY"
      cp "$TARGET/$COMPOSE_FILE" "$PROJECT_COPY/$COMPOSE_FILE"
      : > "$PROJECT_COPY/.env"
      # Prints the service, then its image: an explicit image, or compose's own
      # <project>-<service> name for one it builds.
      if ! SERVICE_IMAGE=$( (cd "$PROJECT_COPY" && docker compose -f "$COMPOSE_FILE" config --format json) \
          2> "$KNOWN_ERRORS" | python3 -c '
import json, sys
config = json.load(sys.stdin)
services = config.get("services") or {}
name = next((s for s in ("web", "coil") if s in services), None)
if name is None and len(services) == 1:
    name = next(iter(services))
if name is None:
    sys.exit("no web or coil service in the compose file")
print(name)
print(services[name].get("image") or "%s-%s" % (config.get("name"), name))
' 2>> "$KNOWN_ERRORS"); then
        KNOWN_ERROR="${KNOWN_ERROR:+$KNOWN_ERROR; }docker compose could not read $COMPOSE_FILE: $(tail -n 1 "$KNOWN_ERRORS")"
      else
        SERVICE=$(sed -n 1p <<< "$SERVICE_IMAGE")
        IMAGE=$(sed -n 2p <<< "$SERVICE_IMAGE")
        if ! docker image inspect "$IMAGE" > /dev/null 2> "$KNOWN_ERRORS"; then
          KNOWN_ERROR="${KNOWN_ERROR:+$KNOWN_ERROR; }the image $SERVICE runs ($IMAGE) is not on this host. Build or pull it first"
        elif docker run --rm --network none --entrypoint python "$IMAGE" -m app.cli known_schema \
            < /dev/null > "$KNOWN_FILE" 2> "$KNOWN_ERRORS"; then
          TARGET_CODE=ok
        elif grep -Fq 'unknown command: known_schema' "$KNOWN_FILE"; then
          KNOWN_ERROR="${KNOWN_ERROR:+$KNOWN_ERROR; }the image $SERVICE runs ($IMAGE) has no known_schema command, so it predates this check and is older than any backup that has a manifest"
        else
          KNOWN_ERROR="${KNOWN_ERROR:+$KNOWN_ERROR; }docker run $IMAGE python -m app.cli known_schema failed: $(tail -n 1 "$KNOWN_ERRORS")"
        fi
      fi
    fi
  fi
fi
if [ "$VALIDATOR" != python3 ]; then
  # Reading the manifest and comparing schemas needs Python. Fail closed when there is
  # code to compare against; otherwise say what was skipped.
  if [ "$TARGET_CODE" = none ]; then
    echo "Version check skipped: python3 is not installed, so the backup manifest was not read."
  elif [ "$ALLOW_DOWNGRADE" = 1 ]; then
    echo "WARNING: --allow-downgrade given. python3 is not installed, so this backup was NOT checked against the code in $TARGET." >&2
  else
    echo "refusing: python3 is not installed, so this backup cannot be checked against the code in $TARGET." >&2
    echo "Install Python 3, or pass --allow-downgrade once you are sure that code is the version that made the backup or newer." >&2
    exit 1
  fi
elif ! python3 - "$RESTORE_STAGE/practice.db" "$MANIFEST_FILE" "$TARGET_CODE" "$KNOWN_FILE" "$KNOWN_ERROR" "$TARGET" "$ALLOW_DOWNGRADE" <<'PY'
import hashlib
import json
import sqlite3
import sys
from pathlib import Path

db, manifest_path, code, known_path, known_error, target, allow = sys.argv[1:8]
allow = allow == '1'


def say(*lines):
    print('\n'.join(lines), file=sys.stderr)


def short(items, limit=8):
    items = list(items)
    if len(items) <= limit:
        return ', '.join(items)
    return ', '.join(items[:limit]) + f' and {len(items) - limit} more'


# Same definition as app/backup_manifest.py and ops/backup.sh; keep all three in step.
def schema_of(path):
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    conn = sqlite3.connect(uri, uri=True)
    try:
        rows = conn.execute('SELECT m.name, p.name FROM sqlite_master AS m, '
                            'pragma_table_info(m.name) AS p WHERE m.type = ?', ('table',)).fetchall()
    finally:
        conn.close()
    schema = {}
    for table, column in rows:
        if not table.startswith('sqlite_'):
            schema.setdefault(table, []).append(column)
    return {table: sorted(columns) for table, columns in schema.items()}


def fingerprint(schema):
    canonical = json.dumps(schema, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(canonical.encode('utf-8')).hexdigest()


archive_schema = schema_of(db)
manifest = None
if manifest_path:
    try:
        manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
        if not isinstance(manifest, dict):
            raise ValueError('not a JSON object')
    except (OSError, ValueError) as exc:
        manifest = None
        say(f'WARNING: the backup manifest could not be read ({exc}), so the Coil version that made this backup is unknown.')
else:
    say('WARNING: this backup has no coil-backup.json manifest, so the Coil version that made it cannot be checked.',
        'Backups made before Coil started writing one look like this.')
if manifest:
    version = str(manifest.get('coil_version') or 'unknown')
    commit = str(manifest.get('coil_commit') or 'unknown')
    producer = {'cli': 'the Coil backup command', 'nightly': 'the nightly host backup'}.get(
        manifest.get('producer'), str(manifest.get('producer') or 'unknown'))
    print('Backup manifest:')
    print(f'  Coil version: {version}')
    print(f'  commit:       {commit}')
    print(f'  created:      {manifest.get("created_at") or "unknown"} (UTC)')
    print(f'  made by:      {producer}')
    if manifest.get('schema_fingerprint') != fingerprint(archive_schema):
        say('WARNING: the manifest does not describe the database in this archive. Checking the database itself.')
    backup_label = f'Coil {version} (commit {commit})'
    newer = f'Coil {version} or newer'
else:
    backup_label = 'an unknown Coil version (no manifest)'
    newer = 'the Coil version that made this backup, or newer'

if code == 'none':
    print(f'Version check skipped: {target} holds no Coil code yet, so there is nothing to compare this backup against.')
    print(f'When you add the code, use {newer}.')
    sys.exit(0)

known = None
if code == 'ok':
    # docker compose can print its own lines around the command's, so take the JSON line.
    try:
        for line in reversed(Path(known_path).read_text(encoding='utf-8').splitlines()):
            try:
                candidate = json.loads(line)
            except ValueError:
                continue
            if isinstance(candidate, dict) and isinstance(candidate.get('schema'), dict) and candidate['schema']:
                known = candidate
                break
        else:
            known_error = 'the known_schema output held no schema'
    except (OSError, UnicodeDecodeError) as exc:
        known_error = f'the known_schema output could not be read ({exc})'

if known is None:
    details = [f'  backup: {backup_label}', f'  error:  {known_error or "unknown"}']
    if allow:
        say(f'WARNING: --allow-downgrade given. The tables and columns the code in {target} knows could not be read,',
            'so this backup was NOT checked against it.', *details)
        sys.exit(0)
    say(f'refusing: {target} holds Coil code, but the tables and columns that code knows could not be read,',
        'so this restore cannot check that the code is as new as the backup.', *details,
        f'Fix that, or put {newer} there, and run the restore again.',
        f'Pass --allow-downgrade only once you are sure the code is {newer}.')
    sys.exit(3)

target_label = f'Coil {known.get("coil_version") or "unknown"} (commit {known.get("coil_commit") or "unknown"})'
known_schema = known['schema']
tables = sorted(t for t in archive_schema if t not in known_schema)
columns = sorted(f'{t}.{c}' for t, cols in archive_schema.items() if t in known_schema
                 for c in cols if c not in set(known_schema[t]))
if not tables and not columns:
    print(f'Version check passed: the code in {target} knows every table and column in this backup.')
    print(f'  target: {target_label}')
    sys.exit(0)

details = [f'  backup: {backup_label}', f'  target: {target_label}']
if tables:
    details.append(f'  tables the target code does not know: {short(tables)}')
if columns:
    details.append(f'  columns the target code does not know: {short(columns)}')
if allow:
    say('WARNING: --allow-downgrade given. Restoring a backup from newer Coil code into older code.', *details,
        'Older code ignores data it does not understand, so balances and totals can be wrong without any error.',
        f'Check them before anyone relies on this install, and move to {newer} as soon as you can.')
    sys.exit(0)
say(f'refusing: this backup came from newer Coil code than the code in {target}.', *details,
    'Older code ignores data it does not understand, so balances and totals can be wrong without any error.',
    f'Restore with {newer}, or pass --allow-downgrade to restore anyway.')
sys.exit(3)
PY
then
  exit 1
fi

# Extract privately on the destination filesystem. A recursive final copy can
# fail halfway through; a same-filesystem directory rename publishes all data.
if [ ! -d "$TARGET" ]; then
  mkdir -p "$TARGET"
  TARGET_CREATED=1
fi
PUBLISH_STAGE=$(mktemp -d "$TARGET/.coil-restore.XXXXXXXX")
RESTORE_PAYLOAD="$PUBLISH_STAGE/payload"
mkdir -p "$RESTORE_PAYLOAD"
if [ "$CLI_LAYOUT" = 1 ]; then
  tar -xzf "$ARCHIVE" -C "$RESTORE_PAYLOAD"
else
  mkdir -p "$RESTORE_PAYLOAD/data"
  tar -xzf "$ARCHIVE" -C "$RESTORE_PAYLOAD/data" --exclude='.env' --exclude='./.env'
  if [ "$HAS_ENV" = 1 ]; then
    ENV_MEMBER='.env'
    grep -Fxq './.env' <<< "$MEMBERS" && ENV_MEMBER='./.env'
    tar -xzf "$ARCHIVE" -C "$RESTORE_PAYLOAD" "$ENV_MEMBER"
  fi
fi

check_database "$RESTORE_PAYLOAD/data/practice.db"

# The manifest describes the archive and is not part of the install. Drop it before the
# install-root check below, which refuses anything unexpected.
if [ "$MANIFEST_COUNT" = 1 ]; then
  EXTRACTED_MANIFEST="$RESTORE_PAYLOAD/coil-backup.json"
  [ "$CLI_LAYOUT" = 1 ] || EXTRACTED_MANIFEST="$RESTORE_PAYLOAD/data/coil-backup.json"
  if [ -L "$EXTRACTED_MANIFEST" ] || [ ! -f "$EXTRACTED_MANIFEST" ]; then
    echo "FAILED: archived coil-backup.json must be a regular file." >&2
    exit 1
  fi
  rm -f "$EXTRACTED_MANIFEST"
fi

# Only data and the optional environment belong in a restore. Do not publish
# unexpected top-level archive entries over existing application files.
shopt -s nullglob dotglob
RESTORE_ENTRIES=("$RESTORE_PAYLOAD/"*)
shopt -u nullglob dotglob
for entry in "${RESTORE_ENTRIES[@]}"; do
  case "$entry" in
    "$RESTORE_PAYLOAD/data"|"$RESTORE_PAYLOAD/.env") ;;
    *) echo "FAILED: unexpected install-root archive entry: $entry" >&2; exit 1 ;;
  esac
done
ln "$RESTORE_PAYLOAD/data/practice.db" "$PUBLISH_STAGE/database.marker"
if [ "$HAS_ENV" = 1 ]; then
  if [ ! -f "$RESTORE_PAYLOAD/.env" ] || [ -L "$RESTORE_PAYLOAD/.env" ]; then
    echo "FAILED: archived .env must be a regular file." >&2
    exit 1
  fi
  # ln refuses an existing destination and never exposes a partial file.
  ln "$RESTORE_PAYLOAD/.env" "$TARGET/.env"
fi
# Existing data must still be empty. mv replaces that empty directory, while
# nonempty data refuses the rename. The app and other writers must be stopped.
mv "$RESTORE_PAYLOAD/data" "$TARGET/"

# Never report success without looking. A restore that quietly half-worked is worse than
# one that failed, because nobody goes back to check.
if [ ! -f "$TARGET/data/practice.db" ]; then
  echo "FAILED: no database at $TARGET/data/practice.db after extracting $ARCHIVE" >&2
  echo "The archive may be from a different version. Its contents:" >&2
  tar -tzf "$ARCHIVE" | head -10 >&2
  exit 1
fi
check_database "$TARGET/data/practice.db"

echo "restored into $TARGET"
echo "  database: $(du -h "$TARGET/data/practice.db" | cut -f1)"
[ -d "$TARGET/data/uploads" ] && echo "  uploads:  $(find "$TARGET/data/uploads" -type f | wc -l | tr -d ' ') file(s)"
echo
if [ "$HAS_ENV" = 1 ]; then
  echo "The archive's .env was restored at the install root. Keep it private."
else
  echo "The backup does NOT contain .env. Copy the original .env into $TARGET yourself."
fi
echo "Without the original SECRET_KEY every session, magic link and signed token is void."
echo
echo "Next: put the app code in $TARGET, restore .env, then docker compose up -d"
