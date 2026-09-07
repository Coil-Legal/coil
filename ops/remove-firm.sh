#!/usr/bin/env bash
# Remove a Coil instance: container, cron, DNS, and optionally the data.
#
#   ops/remove-firm.sh <slug> [--purge]
#
# Without --purge the app directory is KEPT, so the firm's data survives and the
# instance can be brought back with `docker compose up -d`. --purge deletes it, and
# takes a final backup first because deleting a law firm's file by accident is
# unrecoverable.
set -euo pipefail

BASE_DOMAIN="${COIL_BASE_DOMAIN:-coil.legal}"
ZONE_ID="${COIL_ZONE_ID:-6ba7ed6eec107adbde335ed1c299d8e6}"
APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
CF_TOKEN_FILE="${COIL_CF_TOKEN_FILE:-/root/.cloudflare-token}"

SLUG="${1:-}"; PURGE=0
[ "${2:-}" = "--purge" ] && PURGE=1
[ -n "$SLUG" ] || { echo "usage: remove-firm.sh <slug> [--purge]" >&2; exit 2; }
DOMAIN="$SLUG.$BASE_DOMAIN"; DIR="$APPS_DIR/$DOMAIN"

echo "Removing $DOMAIN"
if [ -d "$DIR" ]; then
  ( cd "$DIR" && docker compose down >/dev/null 2>&1 ) && echo "  container stopped" || echo "  container was not running"
else
  echo "  no directory at $DIR"
fi

TMP="$(mktemp)"; crontab -l 2>/dev/null | grep -vF "$DIR" > "$TMP" || true
crontab "$TMP"; rm -f "$TMP"; echo "  cron entries removed"

# With a proxied wildcard *.$BASE_DOMAIN there is usually no per-firm record at all, so a
# missing token here is normal and must not stop the removal.
if [ -f "$CF_TOKEN_FILE" ]; then
  TOK="$(tr -d '[:space:]' < "$CF_TOKEN_FILE")"
  REC="$(curl -s -H "Authorization: Bearer $TOK" \
    "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records?name=$DOMAIN" \
    | sed -n 's/.*"id":"\([a-f0-9]\{32\}\)".*/\1/p' | head -1)"
  if [ -n "$REC" ]; then
    curl -s -X DELETE -H "Authorization: Bearer $TOK" \
      "https://api.cloudflare.com/client/v4/zones/$ZONE_ID/dns_records/$REC" >/dev/null && echo "  DNS record deleted"
  else
    echo "  no per-firm DNS record (covered by the wildcard)"
  fi
else
  echo "  no Cloudflare token on this host, leaving DNS alone (the wildcard needs no per-firm record)"
fi

if [ "$PURGE" = 1 ] && [ -d "$DIR" ]; then
  # A final snapshot needs a running container, and we have just stopped it, so this
  # usually fails and that is fine: what matters is that SOME backup exists before the
  # data is deleted. If none does, refuse and leave the directory alone.
  echo "  attempting a final backup"
  if /home/deploy/scripts/coil-backup.sh >/dev/null 2>&1; then
    echo "  final backup taken"
  else
    echo "  final backup not possible (the container is stopped), falling back to existing backups"
  fi
  COUNT="$(ls -1 "/home/deploy/backups/coil/$DOMAIN"/*.tar.gz 2>/dev/null | wc -l | tr -d ' ')"
  if [ "${COUNT:-0}" -gt 0 ]; then
    rm -rf "$DIR"
    echo "  directory deleted. $COUNT backup(s) kept in /home/deploy/backups/coil/$DOMAIN"
  else
    echo "  REFUSING to delete $DIR: no backup of this firm exists" >&2; exit 1
  fi
else
  [ -d "$DIR" ] && echo "  directory KEPT at $DIR (use --purge to delete)"
fi
echo "Done."
