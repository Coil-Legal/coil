#!/usr/bin/env sh
# Coil self-update for a self-hosted firm. Installed as a nightly cron by install.sh.
#
#   ops/self-update.sh              update if there is something newer
#   ops/self-update.sh --dry-run    say what would happen, change nothing
#   ops/self-update.sh --rollback   go back to the previous image
#
# The order matters and is the whole point of this script:
#
#   1. Back up the database FIRST, through SQLite's online backup API, so a snapshot
#      exists before anything moves. A backup taken after an upgrade goes wrong is
#      not a backup.
#   2. Pull, and stop if the digest did not move. No restart, no downtime, no noise.
#   3. Restart, then poll /health until it answers or the deadline passes.
#   4. If it does not come back, pin the previous digest and restart again. A firm
#      should wake up to yesterday's Coil, not to no Coil.
#
# Schema changes are additive (app/migrate.py only ever adds columns), so rolling the
# image back leaves an unused column rather than a broken database. That is what makes
# an automatic rollback safe here. It would not be safe if migrations dropped anything.
#
# Note this never prunes images. The previous image IS the rollback path, and a prune
# after a successful update would throw it away.
set -eu

DIR="${COIL_DIR:-$(cd "$(dirname "$0")/.." && pwd)}"
PORT="${COIL_PORT:-8080}"
HEALTH_URL="${COIL_HEALTH_URL:-http://localhost:$PORT/health}"
DEADLINE="${COIL_HEALTH_DEADLINE:-90}"
SERVICE="${COIL_SERVICE:-coil}"
LOG="$DIR/data/update.log"
STATE="$DIR/data/.update-previous"
BADSTATE="$DIR/data/.update-bad"
OVERRIDE="$DIR/docker-compose.override.yml"

DRY_RUN=0
ROLLBACK=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --rollback) ROLLBACK=1 ;;
    *) echo "unknown option: $arg" >&2; exit 2 ;;
  esac
done

cd "$DIR"
mkdir -p "$DIR/data"
log() { printf '%s %s\n' "$(date -u '+%Y-%m-%dT%H:%M:%SZ')" "$*" | tee -a "$LOG"; }

docker compose version >/dev/null 2>&1 || { log "ERROR docker compose is not available"; exit 1; }

# A source build has no image to pull. Say so plainly rather than failing obscurely.
if ! grep -qE '^[[:space:]]*image:' docker-compose.yml 2>/dev/null; then
  log "SKIP this install builds from source. Update with: git -C src pull && docker compose up -d --build"
  exit 0
fi

# The channel tag as written in docker-compose.yml. Deliberately NOT `docker compose
# config --images`: that merges docker-compose.override.yml, so once a failed update has
# pinned a digest it would return the digest and every later run would try to `pull` a
# bare sha256, fail, and report the registry as unreachable forever.
image_ref() {
  sed -n 's/^[[:space:]]*image:[[:space:]]*//p' docker-compose.yml | head -1 | tr -d "\"'"
}
image_id() { docker image inspect --format '{{.Id}}' "$1" 2>/dev/null || true; }
running_id() { docker compose images -q "$SERVICE" 2>/dev/null | head -1; }

healthy() {
  code=$(curl -fsS -o /dev/null -w '%{http_code}' --max-time 5 "$HEALTH_URL" 2>/dev/null || echo 000)
  [ "$code" = "200" ]
}

wait_for_health() {
  waited=0
  while [ "$waited" -lt "$DEADLINE" ]; do
    healthy && return 0
    sleep 3
    waited=$((waited + 3))
  done
  return 1
}

# Pin the service to one image id. Compose resolves `image:` from the tag, and the tag
# still points at the bad build, so pinning is the only way to get the old one back.
pin_to() {
  cat > "$OVERRIDE" <<OVR
# Written by ops/self-update.sh after an update failed its health check.
# Coil is pinned to the build that was running before. Delete this file to follow the
# channel tag again, once a release has fixed whatever went wrong.
services:
  $SERVICE:
    image: "$1"
OVR
}

roll_back_to() {
  previous="$1"
  [ -n "$previous" ] || { log "ERROR no previous image recorded; cannot roll back"; return 1; }
  log "ROLLBACK pinning $SERVICE to $previous"
  pin_to "$previous"
  docker compose up -d >>"$LOG" 2>&1 || true
  if wait_for_health; then
    log "ROLLBACK ok, yesterday's build is running. Pinned in $OVERRIDE; delete it once a release fixes this."
    return 0
  fi
  log "ROLLBACK FAILED Coil is not answering $HEALTH_URL. Restore from $DIR/data/backups and read: docker compose logs"
  return 1
}

if [ "$ROLLBACK" -eq 1 ]; then
  [ -f "$STATE" ] || { log "ERROR nothing recorded in $STATE to roll back to"; exit 1; }
  roll_back_to "$(cat "$STATE")"
  exit $?
fi

ref=$(image_ref)
[ -n "$ref" ] || { log "ERROR could not work out the image from docker-compose.yml"; exit 1; }
before=$(running_id)
log "START channel $ref, running ${before:-nothing}"

# A pin means the last update failed its health check and we put the old build back.
# Keep following the channel anyway: the moment a release lands that is not the build
# that broke, unpin and try it. Otherwise a firm sits on a pinned build forever and the
# fix we shipped for them never arrives.
PINNED=0
if [ -f "$OVERRIDE" ]; then
  PINNED=1
  bad=$(cat "$BADSTATE" 2>/dev/null || true)
  log "PINNED a previous update failed; holding ${before:-the previous build}"
fi

if [ "$DRY_RUN" -eq 1 ]; then
  docker compose pull >>"$LOG" 2>&1 || { log "DRY-RUN pull failed"; exit 1; }
  after=$(image_id "$ref")
  if [ "$before" = "$after" ]; then log "DRY-RUN already current, nothing to do"
  else log "DRY-RUN a newer build is available ($after); would back up, restart and health-check"; fi
  exit 0
fi

log "PULL checking for a newer build"
# Pull the channel tag itself, not the merged config, so a pin does not block this.
docker pull -q "$ref" >>"$LOG" 2>&1 || { log "ERROR pull failed (registry unreachable, or the image is private)"; exit 1; }
after=$(image_id "$ref")

if [ "$PINNED" -eq 1 ]; then
  if [ -n "$bad" ] && [ "$after" = "$bad" ]; then
    log "HOLDING the channel still points at the build that failed. Staying on the pinned one."
    exit 0
  fi
  log "RECOVER a new build is out; unpinning and trying it"
  rm -f "$OVERRIDE"
elif [ -n "$before" ] && [ "$before" = "$after" ]; then
  log "UP-TO-DATE nothing to do"
  exit 0
fi

# Snapshot before anything restarts.
if docker compose exec -T "$SERVICE" python -m app.cli backup >>"$LOG" 2>&1; then
  log "BACKUP ok"
else
  log "ERROR backup failed; refusing to update. Fix the backup first."
  exit 1
fi
[ -n "$before" ] && printf '%s\n' "$before" > "$STATE"

rm -f "$OVERRIDE"

log "RESTART bringing Coil up on $after"
docker compose up -d >>"$LOG" 2>&1

if wait_for_health; then
  rm -f "$BADSTATE"
  log "OK updated and healthy. $(curl -fsS --max-time 5 "$HEALTH_URL" 2>/dev/null || echo '')"
  exit 0
fi

log "UNHEALTHY the new build did not answer $HEALTH_URL within ${DEADLINE}s"
printf '%s\n' "$after" > "$BADSTATE"
roll_back_to "$before"
exit 1
