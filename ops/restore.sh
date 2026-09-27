#!/usr/bin/env bash
# Restore one Coil backup into a directory.
#
#   ops/restore.sh <archive.tar.gz> <target-dir>
#
# Restores practice.db, uploads/, pdf/ and .env when included. It refuses to write into a directory
# that already holds a database, because the one time you run this is the one time you
# cannot afford to overwrite the wrong firm. Move the old data aside first.
set -euo pipefail

ARCHIVE="${1:-}"
TARGET="${2:-}"
[ -f "$ARCHIVE" ] || { echo "usage: restore.sh <archive.tar.gz> <target-dir>"; exit 2; }
[ -n "$TARGET" ] || { echo "usage: restore.sh <archive.tar.gz> <target-dir>"; exit 2; }

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
