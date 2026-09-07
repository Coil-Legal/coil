#!/usr/bin/env bash
# Restore one Coil backup into a directory.
#
#   ops/restore.sh <archive.tar.gz> <target-dir>
#
# Restores practice.db, uploads/, pdf/ and .env. It refuses to write into a directory
# that already holds a database, because the one time you run this is the one time you
# cannot afford to overwrite the wrong firm. Move the old data aside first.
set -euo pipefail

ARCHIVE="${1:-}"
TARGET="${2:-}"
[ -f "$ARCHIVE" ] || { echo "usage: restore.sh <archive.tar.gz> <target-dir>"; exit 2; }
[ -n "$TARGET" ] || { echo "usage: restore.sh <archive.tar.gz> <target-dir>"; exit 2; }

if [ -f "$TARGET/data/practice.db" ]; then
  echo "refusing: $TARGET/data/practice.db already exists. Move it aside first." >&2
  exit 1
fi

mkdir -p "$TARGET/data"
tar -xzf "$ARCHIVE" -C "$TARGET/data" --exclude .env
# .env was archived at the app-dir level, not under data/.
tar -xzf "$ARCHIVE" -C "$TARGET" .env 2>/dev/null || echo "note: no .env in this archive"

echo "restored into $TARGET"
[ -f "$TARGET/data/practice.db" ] && echo "  database: $(du -h "$TARGET/data/practice.db" | cut -f1)"
[ -d "$TARGET/data/uploads" ] && echo "  uploads:  $(find "$TARGET/data/uploads" -type f | wc -l | tr -d ' ') file(s)"
echo "Next: put the app code in $TARGET, check .env, then docker compose up -d"
