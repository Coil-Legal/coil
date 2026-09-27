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
# Requires Python 3 on the host for cross-process workspace ownership.
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
# The supervisor and every host child retain a shared lease. Docker exec is
# daemon-owned, so its Python process takes the same lease separately below.
# Registry locks serialize initialization, acquisition and reclamation. Never
# unlink the registry file, or two processes could lock different inodes.
owned_backup() {
  python3 - "$0" "$dir" "$dest" <<'PYOWN'
import fcntl, os, pathlib, shutil, subprocess, sys, tempfile
script, firm, destination = sys.argv[1:]
data = pathlib.Path(firm, 'data').resolve()
dest = pathlib.Path(destination).resolve()
registry = open(data / '.coil-nightly-registry.lock', 'a+b')
os.chmod(registry.name, 0o600)

def remove(workspace):
    (dest / (workspace.name + '.partial')).unlink(missing_ok=True)
    shutil.rmtree(workspace)

fcntl.flock(registry, fcntl.LOCK_EX)
for old in data.glob('.coil-nightly-job-*'):
    if old.is_symlink() or not old.is_dir():
        continue
    try:
        lease = open(old / 'lease', 'r+b')
    except FileNotFoundError:
        # Initialization died under the registry lock before creating its lease.
        remove(old)
        continue
    with lease:
        try:
            fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            continue
        remove(old)
workspace = pathlib.Path(tempfile.mkdtemp(prefix='.coil-nightly-job-', dir=data))
lease = open(workspace / 'lease', 'w+b')
os.chmod(lease.name, 0o600)
fcntl.flock(lease, fcntl.LOCK_SH)
fcntl.flock(registry, fcntl.LOCK_UN)
result = None
try:
    result = subprocess.run(['bash', script], env=dict(os.environ,
        COIL_NIGHTLY_FIRM=firm, COIL_NIGHTLY_WORKSPACE=str(workspace)),
        pass_fds=(lease.fileno(),))
finally:
    fcntl.flock(registry, fcntl.LOCK_EX)
    try:
        # A detached container child may still be running after exec fails.
        fcntl.flock(lease, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except BlockingIOError:
        pass
    else:
        if result is not None and result.returncode >= 0:
            remove(workspace)
    lease.close()
    registry.close()
sys.exit(result.returncode)
PYOWN
}

# A Coil instance is an app directory whose data dir holds the app's database.
for dir in "$APPS_DIR"/*/; do
  [ -z "${COIL_NIGHTLY_FIRM:-}" ] || [ "$dir" = "$COIL_NIGHTLY_FIRM" ] || continue
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
  if [ -z "${COIL_NIGHTLY_WORKSPACE:-}" ]; then
    if ! owned_backup; then failures=$((failures + 1)); fi
    continue
  fi

  # Consistent snapshot of the live database. sqlite3 is not installed on this host, so
  # use the container's python, which is the same SQLite the app writes with.
  container="$(cd "$dir" && docker compose ps -q web 2>/dev/null | head -1)"
  if [ -n "$container" ]; then
    # Every invocation owns its snapshot, including cleanup after a failed run.
    # A concurrent backup must never replace or delete this run's database.
    if ! snap=$(mktemp "$COIL_NIGHTLY_WORKSPACE/.backup-snapshot.XXXXXX"); then
      log "  ERROR: cannot create snapshot file for $firm"
      failures=$((failures + 1)); continue
    fi
    if ! docker exec "$container" python -c "
import fcntl, pathlib, sqlite3, sys
workspace = pathlib.Path(sys.argv[1]).parent
# A child delayed until after its launcher died must not recreate a reclaimed
# workspace. Open the existing lease under the same registry lock as cleanup.
with open('/app/data/.coil-nightly-registry.lock', 'r+b') as registry:
    fcntl.flock(registry, fcntl.LOCK_EX)
    lease = open(workspace / 'lease', 'r+b')
    fcntl.flock(lease, fcntl.LOCK_SH)
src = sqlite3.connect('/app/data/practice.db')
dst = sqlite3.connect(sys.argv[1])
with dst:
    src.backup(dst)          # SQLite online backup: safe against concurrent writers
dst.close(); src.close()
" "/app/data/${COIL_NIGHTLY_WORKSPACE##*/}/${snap##*/}" 2>/dev/null; then
      log "  ERROR: snapshot failed for $firm, skipping (database NOT backed up)"
      failures=$((failures + 1)); continue
    fi
  else
    log "  ERROR: no running container for $firm, skipping (a file copy could be torn)"
    failures=$((failures + 1)); continue
  fi

  # Build privately, then publish a complete archive without replacing an older one.
  # A failed retry in the same second must not truncate or delete a good backup.
  temp_archive="$dest/${COIL_NIGHTLY_WORKSPACE##*/}.partial"
  if ! (umask 077; set -o noclobber; : > "$temp_archive"); then
    log "  ERROR: cannot create temporary archive for $firm"
    failures=$((failures + 1)); continue
  fi
  archive="$dest/$firm-$STAMP-${COIL_NIGHTLY_WORKSPACE##*job-}.tar.gz"
  archive_args=(-C "$COIL_NIGHTLY_WORKSPACE" --transform 's|^[.]backup-snapshot[.][[:alnum:]]*$|practice.db|' "${snap##*/}")
  [ ! -d "$dir/data/uploads" ] || archive_args+=(-C "$dir/data" uploads)
  [ ! -d "$dir/data/pdf" ] || archive_args+=(-C "$dir/data" pdf)
  [ ! -f "$dir/.env" ] || archive_args+=(-C "$dir" .env)
  if tar -czf "$temp_archive" "${archive_args[@]}" 2>/dev/null \
        && ln "$temp_archive" "$archive"; then
    rm -f "$temp_archive"
    size="$(du -h "$archive" | cut -f1)"
    log "  ok $archive ($size)"
  else
    log "  ERROR: archive creation or publication failed for $firm"
    failures=$((failures + 1)); rm -f "$temp_archive"; continue
  fi

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
