#!/usr/bin/env bash
# Turn a waitlist signup into a running Coil instance.
#
#   ops/new-firm.sh <slug> "<Firm Name>" <owner-email>
#   ops/new-firm.sh --dry-run <slug> "<Firm Name>" <owner-email>
#   ops/new-firm.sh --allow-dirty <slug> "<Firm Name>" <owner-email>
#
# Run this ON the VPS. It creates the app directory, a firm-only .env, DNS, the
# container and that firm's cron jobs, then waits until the site answers.
#
# Release pin. The image is built with explicit --build-arg COIL_COMMIT and COIL_VERSION
# taken from the source checkout's git (or from COIL_COMMIT / COIL_VERSION in the
# environment, which must match the checkout when it is one). A source with uncommitted
# changes is refused, because the commit would then not describe the code that runs;
# --allow-dirty builds anyway and says so in the report. After start it checks:
#   - /health reports exactly that commit
#   - /health/ready answers 200 and /setup is open for the owner
#   - ops/backup.sh's discovery (--dry-run) lists the new firm
#   - isolation: the data directory, compose project, Traefik names and SECRET_KEY are
#     not shared with any other instance (keys compared by hash, never printed)
# and ends with a short provisioning report.
#
# Two traps this script exists to avoid, both learned the hard way on this host:
#   1. Traefik keys routers, services and middlewares by NAME across every container
#      on the machine. Two firms sharing a name makes Traefik resolve the wrong
#      backend and answer 503. Every name here is namespaced with the firm slug.
#   2. The container runs as a non-root user. A root-owned data directory fails with
#      EACCES at the first write, so ownership is set explicitly.
set -euo pipefail

BASE_DOMAIN="${COIL_BASE_DOMAIN:-coil.legal}"
ZONE_ID="${COIL_ZONE_ID:-6ba7ed6eec107adbde335ed1c299d8e6}"   # coil.legal
VPS_IP="${COIL_VPS_IP:-204.168.134.211}"
APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
SOURCE_APP="${COIL_SOURCE_APP:-$APPS_DIR/demo.coil.legal}"   # code and SMTP settings come from here
CF_TOKEN_FILE="${COIL_CF_TOKEN_FILE:-/root/.cloudflare-token}"

# The script ops/backup.sh's cron runs is the real enrollment, so check that one first.
BACKUP_SCRIPT="${COIL_BACKUP_SCRIPT:-}"
if [ -z "$BACKUP_SCRIPT" ]; then
  for candidate in /home/deploy/scripts/coil-backup.sh "$(cd "$(dirname "$0")" && pwd)/backup.sh"; do
    [ -f "$candidate" ] && { BACKUP_SCRIPT="$candidate"; break; }
  done
fi

DRY_RUN=0; ALLOW_DIRTY=0; POS=()
for arg in "$@"; do
  case "$arg" in
    --dry-run) DRY_RUN=1 ;;
    --allow-dirty) ALLOW_DIRTY=1 ;;
    --*) echo "unknown option: $arg" >&2; exit 2 ;;
    *) POS+=("$arg") ;;
  esac
done
SLUG="${POS[0]:-}"; FIRM="${POS[1]:-}"; EMAIL="${POS[2]:-}"
if [ -z "$SLUG" ] || [ -z "$FIRM" ] || [ -z "$EMAIL" ] || [ "${#POS[@]}" -gt 3 ]; then
  echo "usage: new-firm.sh [--dry-run] [--allow-dirty] <slug> \"<Firm Name>\" <owner-email>" >&2; exit 2
fi
case "$SLUG" in
  *[!a-z0-9-]*|-*|*-) echo "slug must be lowercase letters, digits and inner hyphens only" >&2; exit 2 ;;
esac

DOMAIN="$SLUG.$BASE_DOMAIN"
DIR="$APPS_DIR/$DOMAIN"
NS="coil-$SLUG"          # Traefik namespace, unique per firm

say() { echo "  $*"; }
run() { if [ "$DRY_RUN" = 1 ]; then echo "  would: $*"; else eval "$@"; fi; }

echo "Provisioning $FIRM"
say "domain:  https://$DOMAIN"
say "owner:   $EMAIL"
say "dir:     $DIR"
[ "$DRY_RUN" = 1 ] && say "(dry run, nothing will change)"

[ -d "$DIR" ] && { echo "refusing: $DIR already exists" >&2; exit 1; }
[ -d "$SOURCE_APP" ] || { echo "refusing: source app $SOURCE_APP not found" >&2; exit 1; }

# ---- release pin: which commit is being built, and is the source exactly that commit?
SRC_COMMIT=''; DIRTY=no
if git -C "$SOURCE_APP" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  SRC_COMMIT="$(git -C "$SOURCE_APP" rev-parse HEAD)"
  # Only what gets copied into the image counts. The source's own compose file, data and
  # .env never reach the new firm (new-firm writes its own compose; rsync skips the rest).
  if [ -n "$(git -C "$SOURCE_APP" status --porcelain -- . ':(exclude)data' ':(exclude).env' \
        ':(exclude)docker-compose.yml' ':(exclude)docker-compose.override.yml' ':(exclude).venv' \
        ':(exclude)node_modules' ':(exclude).claude' ':(exclude)tests' ':(exclude)audit' 2>/dev/null)" ]; then
    DIRTY=yes
  fi
fi
if [ -n "${COIL_COMMIT:-}" ]; then
  if [ -n "$SRC_COMMIT" ] && [ "$COIL_COMMIT" != "$SRC_COMMIT" ]; then
    echo "refusing: COIL_COMMIT=$COIL_COMMIT but $SOURCE_APP is at $SRC_COMMIT (give the full commit)" >&2; exit 1
  fi
  PIN_COMMIT="$COIL_COMMIT"
elif [ -n "$SRC_COMMIT" ]; then
  PIN_COMMIT="$SRC_COMMIT"
else
  echo "refusing: $SOURCE_APP is not a git checkout, so its commit is unknown. Set COIL_COMMIT and COIL_VERSION." >&2
  exit 1
fi
if [ "$DIRTY" = yes ] && [ "$ALLOW_DIRTY" = 0 ]; then
  echo "refusing: $SOURCE_APP has uncommitted changes, so commit $PIN_COMMIT would not describe the code that runs." >&2
  echo "Commit or discard them, or pass --allow-dirty to build anyway." >&2
  exit 1
fi
if [ -n "${COIL_VERSION:-}" ]; then
  PIN_VERSION="$COIL_VERSION"
elif [ -n "$SRC_COMMIT" ]; then
  PIN_VERSION="$(git -C "$SOURCE_APP" describe --tags --always 2>/dev/null || echo "${PIN_COMMIT:0:12}")"
else
  PIN_VERSION="${PIN_COMMIT:0:12}"
fi
case "$PIN_COMMIT$PIN_VERSION" in
  *[!A-Za-z0-9._+-]*) echo "refusing: commit and version may hold only letters, digits and . _ + -" >&2; exit 1 ;;
esac
if [ "$DIRTY" = yes ]; then
  say "release: $PIN_VERSION (commit $PIN_COMMIT), source has UNCOMMITTED changes (--allow-dirty)"
elif [ -n "$SRC_COMMIT" ]; then
  say "release: $PIN_VERSION (commit $PIN_COMMIT), source clean"
else
  say "release: $PIN_VERSION (commit $PIN_COMMIT from COIL_COMMIT; the source is not a git checkout, so it was not checked)"
fi

# ---- code
run "mkdir -p '$DIR/data/uploads' '$DIR/data/pdf'"
run "rsync -a --exclude .git --exclude .venv --exclude __pycache__ --exclude data \
  --exclude .env --exclude node_modules --exclude .claude --exclude tests --exclude audit \
  '$SOURCE_APP/' '$DIR/'"

# ---- env. Never copy the source firm's SECRET_KEY: a shared key means one firm's
# session cookie is valid on another firm's instance.
if [ "$DRY_RUN" = 1 ]; then
  say "would: write $DIR/.env with a fresh SECRET_KEY and the SMTP block from $SOURCE_APP"
else
  SECRET="$(openssl rand -hex 32)"
  {
    echo "# $FIRM. Provisioned $(date -u +%F) by ops/new-firm.sh"
    echo "SECRET_KEY=$SECRET"
    echo "DOMAIN=$DOMAIN"
    echo "BASE_URL=https://$DOMAIN"
    echo "DATABASE_URL=sqlite:////app/data/practice.db"
    echo "COIL_SKIP_INSTALL_KEY=1   # hosted: the key gate is for self-installs"
    echo "COIL_HOSTING=hosted       # we run this box, so Coil ignores any AI key in this"
    echo "                          # environment: it would be ours, and the firm's usage"
    echo "                          # must never be billed to us. See app/llm.py _setting."
    echo ""
    echo "# Email, shared relay account."
    grep -E "^(SMTP_HOST|SMTP_PORT|SMTP_USER|SMTP_PASS|MAIL_FROM)=" "$SOURCE_APP/.env" || true
    echo ""
    echo "# The firm's own accounts. Blank until they supply them; every feature that"
    echo "# needs one degrades with an explanation rather than breaking."
    echo "STRIPE_SECRET_KEY="
    echo "STRIPE_PUBLISHABLE_KEY="
    echo "STRIPE_WEBHOOK_SECRET="
    echo "TWILIO_ACCOUNT_SID="
    echo "TWILIO_AUTH_TOKEN="
    echo "TWILIO_FROM_NUMBER="
    echo "# AI is bring-your-own-key. These stay EMPTY on a hosted instance: the firm adds"
    echo "# its own under Settings, AI, and pays the model maker directly. A key here would"
    echo "# be ignored anyway because COIL_HOSTING=hosted, and that is deliberate."
    echo "OPENROUTER_API_KEY="
    echo "ANTHROPIC_API_KEY="
    echo "COURTLISTENER_TOKEN="
  } > "$DIR/.env"
  chmod 600 "$DIR/.env"
  chown -R 1000:1000 "$DIR/data"      # the container runs as a non-root user
  say "wrote .env (600) and set data ownership"
fi

# ---- compose, with per-firm Traefik names
if [ "$DRY_RUN" = 1 ]; then
  say "would: write $DIR/docker-compose.yml with Traefik names namespaced '$NS'"
else
  cat > "$DIR/docker-compose.yml" <<YML
# $FIRM. Generated by ops/new-firm.sh. Traefik names are namespaced per firm because
# Traefik keys them across every container on this host; sharing one answers 503.
services:
  web:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - ./data:/app/data
    networks:
      - coolify
    labels:
      - traefik.enable=true
      - traefik.http.routers.$NS.rule=Host(\`$DOMAIN\`)
      - traefik.http.routers.$NS.entrypoints=https
      - traefik.http.routers.$NS.tls.certresolver=letsencrypt
      - traefik.http.services.$NS.loadbalancer.server.port=8000
      - traefik.http.routers.$NS-http.rule=Host(\`$DOMAIN\`)
      - traefik.http.routers.$NS-http.entrypoints=http
      - traefik.http.routers.$NS-http.middlewares=$NS-redirect
      - traefik.http.middlewares.$NS-redirect.redirectscheme.scheme=https
networks:
  coolify:
    external: true
YML
  say "wrote docker-compose.yml (Traefik namespace: $NS)"
fi

# ---- DNS. A proxied wildcard *.$BASE_DOMAIN covers every firm, so there is normally
# nothing to do here. Cloudflare's free certificate covers one level of subdomain, which
# is why firms live on $BASE_DOMAIN rather than two levels down under another domain.
if [ "$DRY_RUN" = 1 ]; then
  say "would: check DNS resolves (a wildcard *.$BASE_DOMAIN should already cover it)"
else
  if getent hosts "$DOMAIN" >/dev/null 2>&1 || host "$DOMAIN" >/dev/null 2>&1; then
    say "DNS resolves (wildcard)"
  elif [ -f "$CF_TOKEN_FILE" ]; then
    TOK="$(tr -d '[:space:]' < "$CF_TOKEN_FILE")"
    curl -s -X POST -H "Authorization: Bearer $TOK" -H "Content-Type: application/json" \
      "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records" \
      --data "{\"type\":\"A\",\"name\":\"$SLUG\",\"content\":\"$VPS_IP\",\"proxied\":true,\"ttl\":1,\"comment\":\"Coil: $FIRM\"}" >/dev/null \
      && say "DNS record created for $DOMAIN"
  else
    say "WARNING: $DOMAIN does not resolve yet and no Cloudflare token is on this host."
    say "         Add a proxied wildcard A record *.$BASE_DOMAIN -> $VPS_IP once, and every"
    say "         future firm needs no DNS step at all."
  fi
fi

# ---- start
if [ "$DRY_RUN" = 1 ]; then
  say "would: docker compose build --build-arg COIL_COMMIT=$PIN_COMMIT --build-arg COIL_VERSION=$PIN_VERSION"
  say "would: docker compose up -d, then wait for the site to answer"
else
  ( cd "$DIR" && docker compose build --build-arg "COIL_COMMIT=$PIN_COMMIT" --build-arg "COIL_VERSION=$PIN_VERSION" >/dev/null 2>&1 ) \
    || { echo "  ERROR: image failed to build" >&2; exit 1; }
  ( cd "$DIR" && docker compose up -d >/dev/null 2>&1 ) || { echo "  ERROR: container failed to start" >&2; exit 1; }
  say "container started, waiting for it to answer"
  ok=0
  for i in $(seq 1 20); do
    code="$(curl -sk --resolve "$DOMAIN:443:127.0.0.1" "https://$DOMAIN/login" -o /dev/null -w '%{http_code}' --max-time 10 || true)"
    # A brand new instance has no users, so /login redirects to /setup. Both mean it is up.
    [ "$code" = "200" ] || [ "$code" = "302" ] && { ok=1; break; }
    sleep 5
  done
  [ "$ok" = 1 ] && say "site answers on the origin" || { echo "  ERROR: site did not answer, check: cd $DIR && docker compose logs web" >&2; exit 1; }
fi

# ---- cron, appended without disturbing what is already there
CRON_JOBS="15 7|agenda
30 7|reminders
0 8|sequences
*/10 *|emailin
*/15 *|webhooks
0 6 1 * *|interest
45 6|monthly_invoicing
0 5|case_audit
0 9|payment_plans
0 10|voice_reminders"
if [ "$DRY_RUN" = 1 ]; then
  say "would: add 10 cron jobs for $DOMAIN"
else
  TMP="$(mktemp)"; crontab -l 2>/dev/null > "$TMP" || true
  added=0
  while IFS='|' read -r when cmd; do
    [ -z "$cmd" ] && continue
    case "$when" in
      "0 6 1 * *") sched="0 6 1 * *" ;;
      "*/10 *")    sched="*/10 * * * *" ;;
      "*/15 *")    sched="*/15 * * * *" ;;
      *)           sched="$when * * *" ;;
    esac
    line="$sched cd $DIR && docker compose exec -T web python -m app.cli $cmd >> data/cron.log 2>&1"
    grep -qF "$DIR && docker compose exec -T web python -m app.cli $cmd " "$TMP" || { echo "$line" >> "$TMP"; added=$((added+1)); }
  done <<< "$CRON_JOBS"
  crontab "$TMP"; rm -f "$TMP"
  say "cron: $added job(s) added"
fi

# ---- verification: the release pin, readiness, owner setup, backup enrollment, isolation
REPORT=()
problems=0
note() { REPORT+=("$1"); }
bad() { REPORT+=("$1"); problems=$((problems + 1)); }
if [ "$DRY_RUN" = 1 ]; then
  say "would: check /health reports commit $PIN_COMMIT, /health/ready answers 200 and /setup is open"
  say "would: check ${BACKUP_SCRIPT:-ops/backup.sh} --dry-run lists $DOMAIN"
  say "would: check the data dir, compose project, Traefik names and SECRET_KEY are not shared with another instance"
else
  origin() { curl -sk --resolve "$DOMAIN:443:127.0.0.1" --max-time 10 "$@"; }
  health="$(origin "https://$DOMAIN/health" || true)"
  running_commit="$(printf '%s' "$health" | python3 -c 'import json,sys; print(json.load(sys.stdin).get("commit",""))' 2>/dev/null || true)"
  if [ "$running_commit" = "$PIN_COMMIT" ]; then note "release pin:   /health reports $running_commit"
  else bad "release pin:   FAILED, /health reports '${running_commit:-nothing}', expected $PIN_COMMIT"; fi
  ready="$(origin -o /dev/null -w '%{http_code}' "https://$DOMAIN/health/ready" || true)"
  if [ "$ready" = 200 ]; then note "readiness:     /health/ready 200"
  else bad "readiness:     FAILED, /health/ready answered ${ready:-nothing}"; fi
  setup="$(origin -o /dev/null -w '%{http_code}' "https://$DOMAIN/setup" || true)"
  if [ "$setup" = 200 ]; then note "owner setup:   /setup is open for $EMAIL to create the owner account"
  else bad "owner setup:   FAILED, /setup answered ${setup:-nothing}"; fi

  if [ -z "$BACKUP_SCRIPT" ]; then
    bad "backups:       FAILED, no backup script found (set COIL_BACKUP_SCRIPT)"
  # Captured first: with pipefail, grep -q closing the pipe early would read as a failure.
  elif discovered="$(COIL_APPS_DIR="$APPS_DIR" bash "$BACKUP_SCRIPT" --dry-run 2>/dev/null || true)" \
      && grep -Fq "backing up $DOMAIN" <<< "$discovered"; then
    if grep -Eq 'coil-backup|ops/backup\.sh' <<< "$(crontab -l 2>/dev/null || true)"; then
      note "backups:       enrolled, the nightly backup discovers $DOMAIN"
    else
      bad "backups:       FAILED, $DOMAIN is discoverable but no nightly backup line is in root's crontab"
    fi
  else
    bad "backups:       FAILED, $BACKUP_SCRIPT --dry-run does not list $DOMAIN"
  fi

  # Isolation. Nothing secret is printed: keys are compared by their sha256 only.
  my_data="$(cd "$DIR/data" && pwd -P)"
  my_key_hash="$(sed -n 's/^SECRET_KEY=//p' "$DIR/.env" | tail -1 | tr -d '[:space:]' | python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.read().encode()).hexdigest())')"
  shared=()
  for other in "$APPS_DIR"/*/; do
    other="${other%/}"
    [ "$other" = "$DIR" ] && continue
    [ -d "$other/data" ] || [ -f "$other/.env" ] || continue
    if [ -d "$other/data" ] && [ "$(cd "$other/data" && pwd -P)" = "$my_data" ]; then
      shared+=("data directory with $(basename "$other")")
    fi
    if [ -f "$other/.env" ]; then
      other_hash="$(sed -n 's/^SECRET_KEY=//p' "$other/.env" | tail -1 | tr -d '[:space:]' | python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.read().encode()).hexdigest())')"
      if [ "$other_hash" = "$my_key_hash" ]; then shared+=("SECRET_KEY with $(basename "$other")"); fi
    fi
    if [ -f "$other/docker-compose.yml" ] && grep -Fq "traefik.http.routers.$NS." "$other/docker-compose.yml"; then
      shared+=("Traefik name $NS with $(basename "$other")")
    fi
  done
  container="$(cd "$DIR" && docker compose ps -q web 2>/dev/null | head -1)"
  project=''; mount=''
  if [ -n "$container" ]; then
    project="$(docker inspect -f '{{index .Config.Labels "com.docker.compose.project"}}' "$container" 2>/dev/null || true)"
    mount="$(docker inspect -f '{{range .Mounts}}{{if eq .Destination "/app/data"}}{{.Source}}{{end}}{{end}}' "$container" 2>/dev/null || true)"
  fi
  if [ -z "$project" ]; then
    shared+=("compose project unknown (no running container)")
  else
    while read -r wd; do
      [ -z "$wd" ] || [ "$wd" = "$DIR" ] || shared+=("compose project $project with $wd")
    done < <(docker ps -a --filter "label=com.docker.compose.project=$project" \
               --format '{{.Label "com.docker.compose.project.working_dir"}}' 2>/dev/null | sort -u)
  fi
  if [ -n "$container" ] && [ "$mount" != "$my_data" ] && [ "$mount" != "$DIR/data" ]; then
    shared+=("container mounts /app/data from '${mount:-nothing}', not $my_data")
  fi
  if [ "${#shared[@]}" = 0 ]; then
    note "isolation:     own data dir, compose project ${project}, Traefik namespace $NS and SECRET_KEY"
  else
    bad "isolation:     FAILED, shares ${shared[*]}"
  fi
fi

echo
echo "Provisioning report for $DOMAIN"
echo "  release:       $PIN_VERSION (commit $PIN_COMMIT)$( [ "$DIRTY" = yes ] && echo ', built from a DIRTY source with --allow-dirty')"
for line in ${REPORT[@]+"${REPORT[@]}"}; do echo "  $line"; done
if [ "$problems" -gt 0 ]; then
  echo "  $problems check(s) FAILED. Do not hand this firm over until they pass." >&2
  exit 1
fi

echo
echo "Done. Send the firm:"
echo "  Your Coil is at https://$DOMAIN"
echo "  Open it and create the owner account with $EMAIL. You choose the password."
echo "  Payments and texting need your own Stripe and Twilio keys, added under Settings."
echo
echo "  AI is bring-your-own-key. The firm adds its own under Settings, AI, and pays the"
echo "  model maker directly. Do NOT put an operator key in $DIR/.env: every AI call that"
echo "  firm makes would be billed to whoever owns it. We cover the server, not inference."
# An if, not `[ ] && echo`: as the last line, that made every real run exit 1.
if [ "$DRY_RUN" = 1 ]; then echo "(dry run: nothing was actually created)"; fi
exit 0
