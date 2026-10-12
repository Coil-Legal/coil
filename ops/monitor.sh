#!/usr/bin/env bash
# Fleet monitor for every Coil instance on this host. Alerts only when something changes.
#
#   ops/monitor.sh              check everything once, alert on changes (same as --once)
#   ops/monitor.sh --once       the same; there is no loop, cron is the loop
#   ops/monitor.sh --dry-run    check and print, send nothing, remember nothing
#
# Cron (as root), every 10 minutes:
#   */10 * * * * /home/deploy/scripts/coil-monitor.sh >> /var/log/coil-monitor.log 2>&1
#
# An instance is found the same way ops/backup.sh finds one: an app directory whose
# data/ holds practice.db. For each instance:
#   container  the compose `web` service is running
#   ready      GET <BASE_URL>/health/ready answers 200 (BASE_URL from that firm's .env)
#   backup     the newest nightly archive in <backup root>/<firm>/ is under 26 hours old
#   offsite    the last nightly run copied it off-site (<backup root>/<firm>/.coil-backup-status,
#              written by ops/backup.sh), and that record is under 26 hours old
#   drill      the last restore drill passed (<backup root>/<firm>/.coil-drill-status, written
#              by ops/restore-drill.sh) within 35 days
# and once for the host:
#   disk       free space on / is above 10% and above 2 GB
#
# Alerts go out only when a check changes state, ok to fail or fail to ok. The last state
# of every check is kept in $COIL_MONITOR_STATE_DIR/state. A check seen for the first time
# alerts only if it is failing. If no alert could be delivered the state file is left
# alone, so the next run tries again rather than forgetting the change.
#
# Alert channels, either or both, usually set in /etc/coil-monitor.env:
#   COIL_ALERT_WEBHOOK=https://...   POSTed JSON: {"text", "host", "changes": [...]}
#   COIL_ALERT_EMAIL=ops@example.com sent with the host's `mail`, or `sendmail` if that is
#                                    what is installed
# With neither set it still checks and logs, says loudly that nothing can be alerted,
# and exits 3.
#
# Exit status: 0 all ok, 1 something is failing, 3 no alert channel configured,
# 4 an alert was due and every channel failed to deliver it.
set -uo pipefail

CONFIG="${COIL_MONITOR_CONFIG:-/etc/coil-monitor.env}"
# shellcheck disable=SC1090
[ -f "$CONFIG" ] && . "$CONFIG"

APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
# Hosted firms live at <slug>.coil.legal. Old lab and recovery copies (coil-phase1-lab and
# the like) also hold a practice.db but are stopped on purpose; watching them would alert on
# every run. Widen with COIL_INSTANCE_GLOB if instances are ever named differently.
INSTANCE_GLOB="${COIL_INSTANCE_GLOB:-*.coil.legal}"
BACKUP_ROOT="${COIL_BACKUP_ROOT:-/home/deploy/backups/coil}"
STATE_DIR="${COIL_MONITOR_STATE_DIR:-/var/lib/coil-monitor}"
BACKUP_MAX_HOURS="${COIL_MONITOR_BACKUP_MAX_HOURS:-26}"
DRILL_MAX_DAYS="${COIL_MONITOR_DRILL_MAX_DAYS:-35}"
DISK_PATH="${COIL_MONITOR_DISK_PATH:-/}"
DISK_MIN_PERCENT="${COIL_MONITOR_DISK_MIN_PERCENT:-10}"
DISK_MIN_MB="${COIL_MONITOR_DISK_MIN_MB:-2048}"
WEBHOOK="${COIL_ALERT_WEBHOOK:-}"
EMAIL="${COIL_ALERT_EMAIL:-}"
HOST_LABEL="${COIL_MONITOR_HOST:-$(hostname 2>/dev/null || echo host)}"

DRY_RUN=0
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --once) ;;
    *) echo "usage: monitor.sh [--once] [--dry-run]" >&2; exit 2 ;;
  esac
done

log() { echo "$(date -u '+%F %T') $*"; }
NOW="$(date -u +%s)"
case "$NOW" in ''|*[!0-9]*) log "ERROR: date did not return epoch seconds"; exit 2 ;; esac

WORK="$(mktemp -d "${TMPDIR:-/tmp}/coil-monitor.XXXXXX")" || { log "ERROR: cannot create a temp dir"; exit 2; }
trap 'rm -rf "$WORK"' EXIT
RESULTS="$WORK/results"     # one line per check: key<TAB>ok|fail<TAB>detail
: > "$RESULTS"

check() { printf '%s\t%s\t%s\n' "$1" "$2" "$3" >> "$RESULTS"; }
mtime() { stat -c %Y "$1" 2>/dev/null || stat -f %m "$1" 2>/dev/null; }
# KEY=value from an env-style file, last one wins, quotes and a trailing comment stripped.
env_value() {
  sed -n "s/^[[:space:]]*\(export[[:space:]]\{1,\}\)\{0,1\}$2=//p" "$1" 2>/dev/null | tail -1 \
    | sed -e 's/[[:space:]]\{1,\}#.*$//' -e 's/[[:space:]]*$//' -e "s/^[\"']//" -e "s/[\"']$//"
}
age_text() {  # seconds -> "3h 20m"
  local s="$1"
  if [ "$s" -ge 86400 ]; then echo "$((s / 86400))d $((s % 86400 / 3600))h"
  else echo "$((s / 3600))h $((s % 3600 / 60))m"; fi
}

found=0
for dir in "$APPS_DIR"/$INSTANCE_GLOB/; do
  [ -f "$dir/data/practice.db" ] || continue
  dir="${dir%/}"
  firm="$(basename "$dir")"
  found=$((found + 1))

  # container
  running="$(cd "$dir" && docker compose ps -q --status running web 2>/dev/null | head -1)"
  if [ -n "$running" ]; then check "$firm:container" ok "running"
  else check "$firm:container" fail "the web container is not running"; fi

  # readiness through the firm's own public URL, so DNS, proxy and app are all covered
  base=""
  [ -f "$dir/.env" ] && base="$(env_value "$dir/.env" BASE_URL)"
  if [ -z "$base" ]; then
    check "$firm:ready" fail "no BASE_URL in $dir/.env"
  else
    body="$WORK/ready-body"
    code="$(curl -s -o "$body" -w '%{http_code}' --max-time 15 "${base%/}/health/ready" 2>/dev/null)" || true
    [ -n "$code" ] || code=000
    if [ "$code" = 200 ]; then
      check "$firm:ready" ok "200"
    else
      failing="$(python3 -c '
import json, sys
try:
    checks = json.load(open(sys.argv[1])).get("checks") or {}
except Exception:
    sys.exit(0)
print(", ".join(f"{k} {v}" for k, v in sorted(checks.items()) if v in ("fail", "stale")))
' "$body" 2>/dev/null || true)"
      check "$firm:ready" fail "/health/ready answered $code${failing:+ ($failing)}"
    fi
  fi

  # newest nightly archive
  newest="$(ls -1t "$BACKUP_ROOT/$firm/$firm"-*.tar.gz 2>/dev/null | head -1)"
  if [ -z "$newest" ]; then
    check "$firm:backup" fail "no nightly archive in $BACKUP_ROOT/$firm"
  else
    age=$((NOW - $(mtime "$newest" || echo 0)))
    if [ "$age" -le $((BACKUP_MAX_HOURS * 3600)) ]; then check "$firm:backup" ok "$(basename "$newest")"
    else check "$firm:backup" fail "newest archive is $(age_text "$age") old ($(basename "$newest"))"; fi
  fi

  # off-site copy of the last nightly run
  status="$BACKUP_ROOT/$firm/.coil-backup-status"
  if [ ! -f "$status" ]; then
    check "$firm:offsite" fail "no off-site record yet ($status); backup.sh has not run since it started writing one"
  else
    offsite="$(env_value "$status" offsite)"; epoch="$(env_value "$status" epoch)"
    case "$epoch" in ''|*[!0-9]*) epoch=0 ;; esac
    age=$((NOW - epoch))
    if [ "$offsite" != ok ]; then
      check "$firm:offsite" fail "last nightly run: off-site copy ${offsite:-unknown}, local $(env_value "$status" local)"
    elif [ "$age" -gt $((BACKUP_MAX_HOURS * 3600)) ]; then
      check "$firm:offsite" fail "last successful off-site copy was $(age_text "$age") ago"
    else
      check "$firm:offsite" ok "$(env_value "$status" archive)"
    fi
  fi

  # restore drill
  drill="$BACKUP_ROOT/$firm/.coil-drill-status"
  if [ ! -f "$drill" ]; then
    check "$firm:drill" fail "no restore drill recorded; run ops/restore-drill.sh"
  else
    result="$(env_value "$drill" result)"; epoch="$(env_value "$drill" epoch)"
    case "$epoch" in ''|*[!0-9]*) epoch=0 ;; esac
    age=$((NOW - epoch))
    if [ "$result" != pass ]; then
      check "$firm:drill" fail "last restore drill ${result:-unknown}: $(env_value "$drill" detail)"
    elif [ "$age" -gt $((DRILL_MAX_DAYS * 86400)) ]; then
      check "$firm:drill" fail "last passing restore drill was $(age_text "$age") ago"
    else
      check "$firm:drill" ok "$(env_value "$drill" archive)"
    fi
  fi
done

[ "$found" -gt 0 ] || check "host:instances" fail "no Coil instances found under $APPS_DIR"

# host disk
df_line="$(df -Pk "$DISK_PATH" 2>/dev/null | tail -1)"
total_kb="$(echo "$df_line" | awk '{print $2}')"; avail_kb="$(echo "$df_line" | awk '{print $4}')"
case "$total_kb$avail_kb" in
  ''|*[!0-9]*) check "host:disk" fail "could not read free space on $DISK_PATH" ;;
  *)
    floor_kb=$((total_kb * DISK_MIN_PERCENT / 100))
    [ "$floor_kb" -ge $((DISK_MIN_MB * 1024)) ] || floor_kb=$((DISK_MIN_MB * 1024))
    pct=$((avail_kb * 100 / (total_kb > 0 ? total_kb : 1)))
    if [ "$avail_kb" -ge "$floor_kb" ]; then check "host:disk" ok "${pct}% free"
    else check "host:disk" fail "only $((avail_kb / 1024)) MB (${pct}%) free on $DISK_PATH"; fi ;;
esac

# Compare with the last run.
STATE_FILE="$STATE_DIR/state"
CHANGES="$WORK/changes"; : > "$CHANGES"
NEWSTATE="$WORK/state"; : > "$NEWSTATE"
failing=0
while IFS="$(printf '\t')" read -r key state detail; do
  [ -n "$key" ] || continue
  printf '%s %s\n' "$key" "$state" >> "$NEWSTATE"
  [ "$state" = fail ] && failing=$((failing + 1))
  prev="$(awk -v k="$key" '$1 == k { print $2 }' "$STATE_FILE" 2>/dev/null | tail -1)"
  if [ "$state" = fail ] && [ "$prev" != fail ]; then
    printf 'FAIL\t%s\t%s\n' "$key" "$detail" >> "$CHANGES"
  elif [ "$state" = ok ] && [ "$prev" = fail ]; then
    printf 'RECOVERED\t%s\t%s\n' "$key" "$detail" >> "$CHANGES"
  fi
  if [ "$state" = fail ]; then log "FAIL $key: $detail"; else log "ok   $key: $detail"; fi
done < "$RESULTS"

nchanges="$(wc -l < "$CHANGES" | tr -d ' ')"
log "summary: $found instance(s), $failing failing check(s), $nchanges change(s) since the last run"

channels=0
[ -n "$WEBHOOK" ] && channels=$((channels + 1))
[ -n "$EMAIL" ] && channels=$((channels + 1))
if [ "$channels" = 0 ]; then
  log "!!! NO ALERT CHANNEL CONFIGURED. Nobody is told when a check fails."
  log "!!! Set COIL_ALERT_WEBHOOK and/or COIL_ALERT_EMAIL in $CONFIG."
fi

final() {
  if [ "$channels" = 0 ] && [ "$DRY_RUN" = 0 ]; then exit 3; fi
  [ "$failing" = 0 ] && exit 0
  exit 1
}

if [ "$nchanges" = 0 ]; then
  if [ "$DRY_RUN" = 0 ] && [ "$channels" != 0 ]; then
    mkdir -p "$STATE_DIR" && cp "$NEWSTATE" "$STATE_FILE.tmp" && mv -f "$STATE_FILE.tmp" "$STATE_FILE"
  fi
  final
fi

subject="Coil monitor on $HOST_LABEL: $(grep -c '^FAIL' "$CHANGES" || true) new failure(s), $(grep -c '^RECOVERED' "$CHANGES" || true) recovered"
MESSAGE="$WORK/message"
{
  echo "$subject"
  echo
  while IFS="$(printf '\t')" read -r kind key detail; do echo "$kind $key: $detail"; done < "$CHANGES"
  if [ "$failing" -gt 0 ]; then
    echo
    echo "Still failing now:"
    awk -F '\t' '$2 == "fail" { print "  " $1 ": " $3 }' "$RESULTS"
  fi
} > "$MESSAGE"

if [ "$DRY_RUN" = 1 ]; then
  log "dry run, would alert:"
  sed 's/^/  /' "$MESSAGE"
  final
fi
if [ "$channels" = 0 ]; then
  log "!!! these changes were NOT sent anywhere:"
  sed 's/^/  /' "$MESSAGE"
  final
fi

delivered=0
if [ -n "$WEBHOOK" ]; then
  payload="$WORK/payload.json"
  if python3 - "$MESSAGE" "$CHANGES" "$HOST_LABEL" > "$payload" <<'PYJSON'
import json, sys
message, changes, host = sys.argv[1:4]
rows = []
for line in open(changes, encoding="utf-8"):
    kind, key, detail = (line.rstrip("\n").split("\t") + ["", "", ""])[:3]
    rows.append({"change": kind, "check": key, "detail": detail})
print(json.dumps({"text": open(message, encoding="utf-8").read(), "source": "coil-monitor",
                  "host": host, "changes": rows}))
PYJSON
  then
    if curl -fsS -o /dev/null --max-time 15 -X POST -H 'Content-Type: application/json' \
         --data-binary "@$payload" "$WEBHOOK"; then
      delivered=$((delivered + 1)); log "alert sent to the webhook"
    else
      log "ERROR: alert webhook did not accept the alert"
    fi
  else
    log "ERROR: could not build the webhook payload (python3 missing?)"
  fi
fi
if [ -n "$EMAIL" ]; then
  if command -v mail >/dev/null 2>&1; then
    if mail -s "$subject" "$EMAIL" < "$MESSAGE"; then delivered=$((delivered + 1)); log "alert mailed to $EMAIL"
    else log "ERROR: mail could not send the alert to $EMAIL"; fi
  elif SENDMAIL="$(command -v sendmail 2>/dev/null || ls /usr/sbin/sendmail 2>/dev/null)" && [ -n "$SENDMAIL" ]; then
    if { printf 'To: %s\nSubject: %s\n\n' "$EMAIL" "$subject"; cat "$MESSAGE"; } | "$SENDMAIL" -t; then
      delivered=$((delivered + 1)); log "alert mailed to $EMAIL"
    else log "ERROR: sendmail could not send the alert to $EMAIL"; fi
  else
    log "ERROR: COIL_ALERT_EMAIL is set but neither mail nor sendmail is installed on this host"
  fi
fi

if [ "$delivered" = 0 ]; then
  log "!!! the alert was not delivered by any channel; keeping the old state so the next run retries"
  sed 's/^/  /' "$MESSAGE"
  exit 4
fi
mkdir -p "$STATE_DIR" && cp "$NEWSTATE" "$STATE_FILE.tmp" && mv -f "$STATE_FILE.tmp" "$STATE_FILE"
final
