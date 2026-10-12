#!/usr/bin/env bash
# Remove a Coil instance: container, cron, DNS, and optionally the data.
#
#   ops/remove-firm.sh <slug> [--purge]
#
# The app directory is always retained. Purge is refused until a separately
# reviewed process verifies a complete export, restore integrity and retention.
set -euo pipefail

BASE_DOMAIN="${COIL_BASE_DOMAIN:-coil.legal}"
ZONE_ID="${COIL_ZONE_ID:-6ba7ed6eec107adbde335ed1c299d8e6}"
APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
CF_TOKEN_FILE="${COIL_CF_TOKEN_FILE:-/root/.cloudflare-token}"

SLUG="${1:-}"
if [ "$#" -lt 1 ] || [ "$#" -gt 2 ]; then
  echo "usage: remove-firm.sh <slug> [--purge]" >&2; exit 2
fi
case "$SLUG" in
  ""|*[!a-z0-9-]*|-*|*-) echo "slug must be lowercase letters, digits and inner hyphens only" >&2; exit 2 ;;
esac
if [ "$#" -eq 2 ]; then
  if [ "$2" != "--purge" ]; then
    echo "unknown option: $2" >&2; exit 2
  fi
  echo "REFUSING purge: verified export, restore integrity and retention approval are required. No changes made." >&2
  echo "ops/export-firm.sh $SLUG builds and verifies the firm's complete export; it does not remove anything." >&2
  exit 1
fi
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

[ -d "$DIR" ] && echo "  directory KEPT at $DIR"
echo "Done."
