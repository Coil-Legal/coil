#!/usr/bin/env bash
# Pause, close or reactivate a hosted firm.
#
#   ops/firm-state.sh <slug> active
#   ops/firm-state.sh <slug> suspended
#   ops/firm-state.sh <slug> closed [--retain-until YYYY-MM-DD]
#   add --dry-run to any of them to see what would change, changing nothing
#
# Run this ON the VPS. It sets COIL_ACCOUNT_STATE (and, for closed,
# COIL_ACCOUNT_CLOSED_RETAIN_UNTIL, default 90 days from today) in that firm's .env,
# recreates its container so the value takes effect, waits for /health/ready and checks
# the running container sees the new state. What each state does is in
# app/account_state.py; the policy is in docs/OPERATIONS.md.
#
# The .env holds the firm's SECRET_KEY and provider keys, so it is edited in place with
# care: only those two lines change, every other line keeps its order and text, the file
# keeps its mode and owner, and the new file replaces the old one in one rename.
set -euo pipefail

BASE_DOMAIN="${COIL_BASE_DOMAIN:-coil.legal}"
APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
WAIT_SECONDS="${COIL_STATE_WAIT_SECONDS:-90}"
RETAIN_DAYS="${COIL_RETAIN_DAYS:-90}"

USAGE="usage: firm-state.sh [--dry-run] <slug> active|suspended|closed [--retain-until YYYY-MM-DD]"
DRY_RUN=0; SLUG=''; STATE=''; RETAIN=''
while [ "$#" -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --retain-until) [ "$#" -ge 2 ] || { echo "$USAGE" >&2; exit 2; }; RETAIN="$2"; shift ;;
    --retain-until=*) RETAIN="${1#*=}" ;;
    --*) echo "unknown option: $1" >&2; echo "$USAGE" >&2; exit 2 ;;
    *)
      if [ -z "$SLUG" ]; then SLUG="$1"
      elif [ -z "$STATE" ]; then STATE="$1"
      else echo "$USAGE" >&2; exit 2; fi ;;
  esac
  shift
done
case "$SLUG" in
  ""|*[!a-z0-9-]*|-*|*-) echo "slug must be lowercase letters, digits and inner hyphens only" >&2; echo "$USAGE" >&2; exit 2 ;;
esac
case "$STATE" in
  active|suspended|closed) ;;
  *) echo "state must be active, suspended or closed" >&2; echo "$USAGE" >&2; exit 2 ;;
esac
if [ -n "$RETAIN" ] && [ "$STATE" != closed ]; then
  echo "--retain-until only applies to closed" >&2; exit 2
fi
command -v python3 >/dev/null 2>&1 || { echo "python3 is required" >&2; exit 2; }
if [ "$STATE" = closed ]; then
  if [ -z "$RETAIN" ]; then
    RETAIN="$(python3 -c 'import datetime, sys; print(datetime.date.today() + datetime.timedelta(days=int(sys.argv[1])))' "$RETAIN_DAYS")"
  elif ! python3 -c 'import datetime, re, sys; v = sys.argv[1]; assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", v); datetime.date.fromisoformat(v)' "$RETAIN" 2>/dev/null; then
    echo "--retain-until must be a real date written YYYY-MM-DD" >&2; exit 2
  fi
fi

DOMAIN="$SLUG.$BASE_DOMAIN"; DIR="$APPS_DIR/$DOMAIN"; ENV_FILE="$DIR/.env"
[ -d "$DIR" ] || { echo "no app directory at $DIR" >&2; exit 1; }
[ -f "$ENV_FILE" ] && [ ! -L "$ENV_FILE" ] || { echo "no regular .env at $ENV_FILE" >&2; exit 1; }
[ -f "$DIR/docker-compose.yml" ] || { echo "no docker-compose.yml in $DIR" >&2; exit 1; }

env_value() {
  sed -n "s/^$2=//p" "$1" | tail -1 | sed -e 's/[[:space:]]\{1,\}#.*$//' -e 's/[[:space:]]*$//' -e "s/^[\"']//" -e "s/[\"']$//"
}
CURRENT="$(env_value "$ENV_FILE" COIL_ACCOUNT_STATE)"; CURRENT="${CURRENT:-active}"
CURRENT_RETAIN="$(env_value "$ENV_FILE" COIL_ACCOUNT_CLOSED_RETAIN_UNTIL)"

echo "Account state for $DOMAIN"
echo "  now:  $CURRENT${CURRENT_RETAIN:+ (retain until $CURRENT_RETAIN)}"
echo "  new:  $STATE${RETAIN:+ (retain until $RETAIN)}"

if [ "$DRY_RUN" = 1 ]; then
  echo "  would: set COIL_ACCOUNT_STATE=$STATE in $ENV_FILE"
  if [ "$STATE" = closed ]; then echo "  would: set COIL_ACCOUNT_CLOSED_RETAIN_UNTIL=$RETAIN"
  else echo "  would: remove COIL_ACCOUNT_CLOSED_RETAIN_UNTIL"; fi
  echo "  would: docker compose up -d --force-recreate in $DIR, then wait for /health/ready"
  echo "(dry run, nothing changed)"
  exit 0
fi

# Atomic, minimal .env edit. Same directory for the temp file, so the rename is atomic.
python3 - "$ENV_FILE" "$STATE" "$RETAIN" "$(date -u +%F)" <<'PYENV'
import os, re, sys, tempfile
path, state, retain, today = sys.argv[1:5]
st = os.stat(path)
with open(path, encoding="utf-8") as f:
    lines = f.read().splitlines(keepends=True)
key = re.compile(r"^\s*(?:export\s+)?(COIL_ACCOUNT_STATE|COIL_ACCOUNT_CLOSED_RETAIN_UNTIL)\s*=")
want = [f"COIL_ACCOUNT_STATE={state}\n"]
if state == "closed":
    want.append(f"COIL_ACCOUNT_CLOSED_RETAIN_UNTIL={retain}\n")
out, placed = [], False
for line in lines:
    if key.match(line):
        if not placed:
            out.extend(want)
            placed = True
        continue
    out.append(line)
if not placed:
    if out and not out[-1].endswith("\n"):
        out[-1] += "\n"
    out.append(f"\n# Account state, managed by ops/firm-state.sh (first set {today}). See docs/OPERATIONS.md.\n")
    out.extend(want)
fd, tmp = tempfile.mkstemp(prefix=".env.firm-state.", dir=os.path.dirname(os.path.abspath(path)))
try:
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        f.writelines(out)
        f.flush()
        os.fsync(f.fileno())
    os.chmod(tmp, st.st_mode & 0o7777)
    try:
        os.chown(tmp, st.st_uid, st.st_gid)
    except PermissionError:
        pass
    os.replace(tmp, path)
except BaseException:
    if os.path.exists(tmp):
        os.unlink(tmp)
    raise
PYENV
echo "  .env updated (only the account state lines changed)"

if ! ( cd "$DIR" && docker compose up -d --force-recreate >/dev/null 2>&1 ); then
  echo "  ERROR: docker compose up -d --force-recreate failed in $DIR. The .env already says $STATE." >&2
  echo "         Check: cd $DIR && docker compose logs web" >&2
  exit 1
fi
echo "  container recreated, waiting for /health/ready"

BASE="$(env_value "$ENV_FILE" BASE_URL)"
ready_code() {
  if [ -n "$BASE" ]; then
    curl -s -o /dev/null -w '%{http_code}' --max-time 10 "${BASE%/}/health/ready" 2>/dev/null || true
  else
    # No BASE_URL: ask from inside the container instead.
    ( cd "$DIR" && docker compose exec -T web python -c '
import urllib.request, urllib.error
try:
    print(urllib.request.urlopen("http://127.0.0.1:8000/health/ready", timeout=8).status)
except urllib.error.HTTPError as e:
    print(e.code)
except Exception:
    print("000")
' 2>/dev/null ) || true
  fi
}
code=000; waited=0
while [ "$waited" -lt "$WAIT_SECONDS" ]; do
  code="$(ready_code)"; code="${code:-000}"
  [ "$code" = 200 ] && break
  sleep 3; waited=$((waited + 3))
done

seen="$( (cd "$DIR" && docker compose exec -T web printenv COIL_ACCOUNT_STATE) 2>/dev/null | tr -d '\r[:space:]' || true)"
seen="${seen:-active}"
echo
echo "Result for $DOMAIN"
echo "  account state in the running container: $seen"
echo "  /health/ready: $code"
if [ "$seen" != "$STATE" ]; then
  echo "  ERROR: the container does not see COIL_ACCOUNT_STATE=$STATE" >&2; exit 1
fi
if [ "$code" != 200 ]; then
  echo "  ERROR: /health/ready did not answer 200 within ${WAIT_SECONDS}s. The state is set; check the instance." >&2
  exit 1
fi
case "$STATE" in
  active) echo "  Reactivated. Everything works again." ;;
  suspended) echo "  Paused. The firm can sign in, read and export; nothing can be changed or sent." ;;
  closed) echo "  Closed. The owner can sign in and export until $RETAIN. Purge is a separate, approved process." ;;
esac
