#!/usr/bin/env bash
# Prove the newest nightly backup of a firm actually restores.
#
#   ops/restore-drill.sh <slug>             drill one firm (<slug>.coil.legal)
#   ops/restore-drill.sh --all              drill every firm that has a nightly archive
#   ops/restore-drill.sh --dry-run <slug>   say which archive would be drilled, touch nothing
#
# Cron (as root), monthly, after the nightly backup has run:
#   30 4 3 * * /home/deploy/scripts/coil-restore-drill.sh --all >> /var/log/coil-restore-drill.log 2>&1
# restore.sh must sit next to this script (as restore.sh or coil-restore.sh), or set
# COIL_RESTORE_SCRIPT.
#
# For each firm it takes the newest archive in <backup root>/<firm>/ and:
#   1. restores it with ops/restore.sh into a fresh private temp directory named like the
#      firm's app directory. A copy of the firm's docker-compose.yml goes in first, so
#      restore.sh runs its version check against the image that firm runs (one
#      `docker run --network none ... known_schema`, a few seconds). Set
#      COIL_DRILL_SCHEMA_CHECK=0 to skip that and restore into an empty directory.
#   2. runs PRAGMA integrity_check on the restored database.
#   3. checks every table the archive's coil-backup.json manifest lists is present in the
#      restored database with the same columns, and that every table has the same row
#      count as the database read straight out of the archive (and as the manifest's
#      row_counts, when a manifest carries them).
#   4. deletes the temp directory completely. It holds a full copy of the firm's data and
#      its .env, so it is created mode 700 and removed on every exit path.
#   5. writes <backup root>/<firm>/.coil-drill-status (time, archive name, pass or fail and
#      a short reason with no firm data), which ops/monitor.sh reads.
#
# Exit status: 0 every drill passed, 1 any failed, 2 usage.
set -uo pipefail

BASE_DOMAIN="${COIL_BASE_DOMAIN:-coil.legal}"
APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
# --all drills hosted firms only (<slug>.coil.legal), the same set ops/monitor.sh watches.
INSTANCE_GLOB="${COIL_INSTANCE_GLOB:-*.coil.legal}"
BACKUP_ROOT="${COIL_BACKUP_ROOT:-/home/deploy/backups/coil}"
WORK_ROOT="${COIL_DRILL_TMP:-$BACKUP_ROOT/.drill-work}"
SCHEMA_CHECK="${COIL_DRILL_SCHEMA_CHECK:-1}"
HERE="$(cd "$(dirname "$0")" && pwd)"
RESTORE="${COIL_RESTORE_SCRIPT:-}"
if [ -z "$RESTORE" ]; then
  for candidate in "$HERE/restore.sh" "$HERE/coil-restore.sh"; do
    [ -f "$candidate" ] && { RESTORE="$candidate"; break; }
  done
fi

USAGE="usage: restore-drill.sh [--dry-run] <slug>|--all"
DRY_RUN=0; ALL=0; SLUG=''
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --all) ALL=1 ;;
    --*) echo "unknown option: $arg" >&2; echo "$USAGE" >&2; exit 2 ;;
    *) [ -z "$SLUG" ] || { echo "$USAGE" >&2; exit 2; }; SLUG="$arg" ;;
  esac
done
if [ "$ALL" = 1 ] && [ -n "$SLUG" ]; then echo "$USAGE" >&2; exit 2; fi
if [ "$ALL" = 0 ]; then
  case "$SLUG" in
    ""|*[!a-z0-9-]*|-*|*-) echo "slug must be lowercase letters, digits and inner hyphens only" >&2; echo "$USAGE" >&2; exit 2 ;;
  esac
fi
[ -n "$RESTORE" ] && [ -f "$RESTORE" ] || { echo "restore.sh not found next to this script; set COIL_RESTORE_SCRIPT" >&2; exit 2; }
command -v python3 >/dev/null 2>&1 || { echo "python3 is required for the drill checks" >&2; exit 2; }

log() { echo "$(date -u '+%F %T') $*"; }

FIRMS=()
if [ "$ALL" = 1 ]; then
  for d in "$BACKUP_ROOT"/$INSTANCE_GLOB/; do
    f="$(basename "$d")"
    case "$f" in .*) continue ;; esac
    ls "$d$f"-*.tar.gz >/dev/null 2>&1 && FIRMS+=("$f")
  done
  [ "${#FIRMS[@]}" -gt 0 ] || { log "no nightly archives under $BACKUP_ROOT"; exit 1; }
else
  FIRMS=("$SLUG.$BASE_DOMAIN")
fi

WORK=''
cleanup() {
  if [ -n "$WORK" ] && [ -d "$WORK" ]; then
    chmod -R u+rwx "$WORK" 2>/dev/null
    rm -rf "$WORK"
  fi
  WORK=''
}
trap 'cleanup' EXIT
trap 'exit 130' INT
trap 'exit 143' TERM

record() {  # <firm> <archive name> <pass|fail> <detail>
  local dest="$BACKUP_ROOT/$1" tmp
  mkdir -p "$dest" || return 1
  tmp="$dest/.coil-drill-status.$$"
  { printf 'epoch=%s\n' "$(date -u +%s)"; printf 'archive=%s\n' "$2"; printf 'result=%s\n' "$3"
    printf 'detail=%s\n' "$(printf '%s' "$4" | tr '\n\t' '  ' | cut -c1-300)"; } > "$tmp" && mv -f "$tmp" "$dest/.coil-drill-status"
}

drill() {
  local firm="$1" archive name target out detail rc
  archive="$(ls -1t "$BACKUP_ROOT/$firm/$firm"-*.tar.gz 2>/dev/null | head -1)"
  if [ -z "$archive" ]; then
    log "FAIL $firm: no nightly archive in $BACKUP_ROOT/$firm"
    [ "$DRY_RUN" = 1 ] || record "$firm" "" fail "no nightly archive found"
    return 1
  fi
  name="$(basename "$archive")"
  if [ "$DRY_RUN" = 1 ]; then
    log "would drill $firm: restore $name into a private temp dir under $WORK_ROOT, check integrity, tables and row counts, delete it, record the result"
    return 0
  fi
  log "drilling $firm with $name"
  mkdir -p "$WORK_ROOT" && chmod 700 "$WORK_ROOT" 2>/dev/null
  WORK="$(umask 077; mktemp -d "$WORK_ROOT/drill.XXXXXXXX")" || { log "FAIL $firm: cannot create a temp dir"; record "$firm" "$name" fail "cannot create temp dir"; return 1; }
  chmod 700 "$WORK"
  target="$WORK/$firm"            # named like the app dir, so compose derives the same image name
  mkdir -p "$target"
  local schema=skipped
  if [ "$SCHEMA_CHECK" = 1 ] && [ -f "$APPS_DIR/$firm/docker-compose.yml" ]; then
    cp "$APPS_DIR/$firm/docker-compose.yml" "$target/docker-compose.yml"
    schema=checked
  fi
  out="$WORK/restore.out"
  # restore.sh keeps its own staging under TMPDIR; keep that inside the drill dir too.
  (umask 077; TMPDIR="$WORK" bash "$RESTORE" "$archive" "$target") > "$out" 2>&1
  rc=$?
  if [ "$rc" != 0 ]; then
    detail="restore.sh exited $rc: $(grep -E 'FAILED|refusing' "$out" | head -1 | cut -c1-200)"
    log "FAIL $firm: $detail"
    sed 's/^/    /' "$out" | grep -vi 'secret' | tail -20
    cleanup; record "$firm" "$name" fail "$detail"; return 1
  fi
  if [ "$schema" = checked ] && ! grep -q 'Version check passed' "$out"; then
    detail="restore.sh did not report a passed version check against the firm's image"
    log "FAIL $firm: $detail"
    cleanup; record "$firm" "$name" fail "$detail"; return 1
  fi
  # The database straight out of the archive, to compare row counts against.
  local member=practice.db
  tar -tzf "$archive" | sed 's|^\./||' | grep -Fxq 'data/practice.db' && member=data/practice.db
  tar -tzf "$archive" | grep -Fxq "./$member" && member="./$member"
  local manifest_member=coil-backup.json
  tar -tzf "$archive" | grep -Fxq './coil-backup.json' && manifest_member=./coil-backup.json
  tar -xOzf "$archive" "$member" > "$WORK/archived.db" 2>/dev/null
  tar -xOzf "$archive" "$manifest_member" > "$WORK/manifest.json" 2>/dev/null || : > "$WORK/manifest.json"
  detail="$(python3 - "$target/data/practice.db" "$WORK/archived.db" "$WORK/manifest.json" <<'PYDRILL'
import json, sqlite3, sys
from pathlib import Path
restored, archived, manifest_path = sys.argv[1:4]

def connect(path):
    return sqlite3.connect(Path(path).resolve().as_uri() + "?mode=ro", uri=True)

def schema_and_counts(path):
    conn = connect(path)
    try:
        tables = [r[0] for r in conn.execute(
            "SELECT name FROM sqlite_master WHERE type = 'table' AND name NOT LIKE 'sqlite_%' ORDER BY name")]
        schema = {t: sorted(r[1] for r in conn.execute(f'PRAGMA table_info("{t}")')) for t in tables}
        counts = {t: conn.execute(f'SELECT count(*) FROM "{t}"').fetchone()[0] for t in tables}
        integrity = conn.execute("PRAGMA integrity_check").fetchall()
    finally:
        conn.close()
    return schema, counts, integrity

problems = []
try:
    schema, counts, integrity = schema_and_counts(restored)
except sqlite3.Error as exc:
    print(f"FAIL restored database unreadable ({type(exc).__name__})"); sys.exit(1)
if integrity != [("ok",)]:
    problems.append("integrity_check did not return ok")
try:
    _, archived_counts, _ = schema_and_counts(archived)
except sqlite3.Error as exc:
    archived_counts = None
    problems.append(f"archived database unreadable ({type(exc).__name__})")
manifest = None
try:
    text = Path(manifest_path).read_text(encoding="utf-8")
    manifest = json.loads(text) if text.strip() else None
except (OSError, ValueError):
    problems.append("manifest unreadable")
if manifest is None:
    note = "no manifest in archive"
else:
    listed = manifest.get("schema") or {}
    missing = sorted(t for t in listed if t not in schema)
    if missing:
        problems.append(f"{len(missing)} manifest table(s) missing after restore: {', '.join(missing[:5])}")
    changed = sorted(t for t in listed if t in schema and sorted(listed[t]) != schema[t])
    if changed:
        problems.append(f"columns differ from manifest in {len(changed)} table(s): {', '.join(changed[:5])}")
    extra = sorted(t for t in schema if t not in listed)
    if extra:
        problems.append(f"{len(extra)} restored table(s) not in manifest: {', '.join(extra[:5])}")
    expected = manifest.get("row_counts")
    if isinstance(expected, dict):
        off = sorted(t for t, n in expected.items() if counts.get(t) != n)
        if off:
            problems.append(f"row counts differ from manifest in {len(off)} table(s): {', '.join(off[:5])}")
    note = f"{len(listed)} manifest tables present"
if archived_counts is not None and archived_counts != counts:
    off = sorted(t for t in set(counts) | set(archived_counts) if counts.get(t) != archived_counts.get(t))
    problems.append(f"row counts differ from the archived database in {len(off)} table(s): {', '.join(off[:5])}")
if problems:
    print("FAIL " + "; ".join(problems)); sys.exit(1)
print(f"PASS integrity ok, {note}, {len(counts)} tables, {sum(counts.values())} rows, counts match the archive")
PYDRILL
)"
  rc=$?
  cleanup
  if [ -d "$target" ]; then
    log "FAIL $firm: could not remove the temp restore at $target. It holds firm data; remove it by hand."
    record "$firm" "$name" fail "temp restore not removed"; return 1
  fi
  if [ "$rc" != 0 ]; then
    detail="${detail#FAIL }"
    log "FAIL $firm: $detail"
    record "$firm" "$name" fail "$detail"; return 1
  fi
  detail="${detail#PASS }; schema check against the firm's image: $schema"
  log "PASS $firm: $detail"
  record "$firm" "$name" pass "$detail"
  return 0
}

failures=0
for firm in "${FIRMS[@]}"; do
  drill "$firm" || failures=$((failures + 1))
done
log "done: ${#FIRMS[@]} drill(s), $failures failure(s)"
[ "$failures" = 0 ]
