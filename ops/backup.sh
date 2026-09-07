#!/usr/bin/env bash
# Nightly backup of every Coil instance on this host.
#
# Why this exists when weekly-fleet-backup.sh already tars /home/deploy/apps:
#   1. That runs weekly. A firm losing six days of time entries and trust ledger
#      movements is not an acceptable recovery point for client money.
#   2. It copies practice.db with plain tar while the app is writing to it, which can
#      capture a torn file: a backup that restores into a corrupt database is worse
#      than no backup, because you find out during the emergency.
#
# This uses SQLite's own online backup API through the container's python, which takes
# a consistent snapshot of a live database, then archives that snapshot alongside the
# firm's uploads, generated PDFs and .env.
#
#   ops/backup.sh              back up every instance found
#   ops/backup.sh --dry-run    list what would happen, touch nothing
#
# Cron (as root):
#   20 2 * * * /home/deploy/scripts/coil-backup.sh >> /var/log/coil-backup.log 2>&1
set -euo pipefail

APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
BACKUP_ROOT="${COIL_BACKUP_ROOT:-/home/deploy/backups/coil}"
REMOTE="${COIL_BACKUP_REMOTE:-gdrive:VPS-Coil-Backups}"   # rclone remote, already configured on this host
KEEP_DAILY="${COIL_KEEP_DAILY:-14}"
KEEP_WEEKLY="${COIL_KEEP_WEEKLY:-8}"                      # Sunday archives kept this many weeks
DRY_RUN=0
[ "${1:-}" = "--dry-run" ] && DRY_RUN=1

STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
DOW="$(date -u +%u)"          # 7 = Sunday, kept longer
failures=0
found=0

log() { echo "$(date -u '+%F %T') $*"; }
run() { if [ "$DRY_RUN" = 1 ]; then echo "  would: $*"; else "$@"; fi; }

# A Coil instance is an app directory whose data dir holds the app's database.
for dir in "$APPS_DIR"/*/; do
  db="$dir/data/practice.db"
  [ -f "$db" ] || continue
  firm="$(basename "$dir")"
  found=$((found + 1))
  dest="$BACKUP_ROOT/$firm"
  archive="$dest/$firm-$STAMP.tar.gz"
  log "backing up $firm"

  if [ "$DRY_RUN" = 1 ]; then
    echo "  would: snapshot $db, archive with uploads/ pdf/ .env into $archive"
    continue
  fi
  mkdir -p "$dest"

  # Consistent snapshot of the live database. sqlite3 is not installed on this host, so
  # use the container's python, which is the same SQLite the app writes with.
  container="$(cd "$dir" && docker compose ps -q web 2>/dev/null | head -1)"
  snap="$dir/data/.backup-snapshot.db"
  rm -f "$snap"
  if [ -n "$container" ]; then
    if ! docker exec "$container" python -c "
import sqlite3
src = sqlite3.connect('/app/data/practice.db')
dst = sqlite3.connect('/app/data/.backup-snapshot.db')
with dst:
    src.backup(dst)          # SQLite online backup: safe against concurrent writers
dst.close(); src.close()
" 2>/dev/null; then
      log "  ERROR: snapshot failed for $firm, skipping (database NOT backed up)"
      failures=$((failures + 1)); rm -f "$snap"; continue
    fi
  else
    log "  ERROR: no running container for $firm, skipping (a file copy could be torn)"
    failures=$((failures + 1)); continue
  fi

  # Archive the snapshot as practice.db so a restore drops straight into place.
  if tar -czf "$archive" \
        -C "$dir/data" --transform 's|^\.backup-snapshot\.db$|practice.db|' .backup-snapshot.db \
        $( [ -d "$dir/data/uploads" ] && echo uploads ) \
        $( [ -d "$dir/data/pdf" ] && echo pdf ) \
        -C "$dir" $( [ -f "$dir/.env" ] && echo .env ) 2>/dev/null; then
    size="$(du -h "$archive" | cut -f1)"
    log "  ok $archive ($size)"
  else
    log "  ERROR: tar failed for $firm"
    failures=$((failures + 1)); rm -f "$archive" "$snap"; continue
  fi
  rm -f "$snap"

  # Retention: keep the last N dailies, and Sunday archives for N weeks.
  ls -1t "$dest"/$firm-*.tar.gz 2>/dev/null | tail -n +$((KEEP_DAILY + 1)) | while read -r old; do
    od="$(basename "$old" | sed -E 's/.*-([0-9]{8})T.*/\1/')"
    keep_until=$(date -u -d "$od +$((KEEP_WEEKLY * 7)) days" +%Y%m%d 2>/dev/null || echo 0)
    if [ "$(date -u -d "$od" +%u 2>/dev/null || echo 0)" = "7" ] && [ "$keep_until" -ge "$(date -u +%Y%m%d)" ]; then
      continue                     # a Sunday archive still inside the weekly window
    fi
    rm -f "$old"
  done

  # Off-site. The local copy is on the same disk as the thing it protects, so this is
  # the copy that actually matters.
  if command -v rclone >/dev/null 2>&1; then
    if rclone copy "$archive" "$REMOTE/$firm/" 2>>"$BACKUP_ROOT/rclone.log"; then
      log "  off-site: $REMOTE/$firm/"
      rclone delete --min-age $((KEEP_WEEKLY * 7))d "$REMOTE/$firm/" 2>>"$BACKUP_ROOT/rclone.log" || true
    else
      log "  ERROR: off-site copy FAILED for $firm, see $BACKUP_ROOT/rclone.log"
      failures=$((failures + 1))
    fi
  else
    log "  WARNING: rclone is not installed, this backup exists ONLY on the same disk as the data"
    failures=$((failures + 1))
  fi
done

[ "$found" = 0 ] && { log "no Coil instances found under $APPS_DIR"; exit 1; }
log "done: $found instance(s), $failures failure(s)"
exit $([ "$failures" -eq 0 ] && echo 0 || echo 1)
