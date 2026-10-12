#!/usr/bin/env bash
# Build, copy out and verify a complete export of one Coil firm (gate C08, offboarding).
#
#   ops/export-firm.sh <slug>             export <slug>.$COIL_BASE_DOMAIN
#   ops/export-firm.sh <slug> --dry-run   say what would happen, touch nothing
#
# Runs `python -m app.cli export_firm` inside the firm's running container (the export is
# built from a SQLite online-backup snapshot, so the firm can keep working), copies the zip
# to $COIL_EXPORT_ROOT/<slug>/ with 0600 permissions without replacing any earlier export,
# then checks the copy with the host's python3 and app/firm_export.py, which needs nothing
# but the standard library. Only a copy that passes is reported as the export; the copy
# left inside the firm's data folder is then removed so client data is not kept twice.
#
# This does not remove the firm. ops/remove-firm.sh still refuses --purge.
set -euo pipefail

BASE_DOMAIN="${COIL_BASE_DOMAIN:-coil.legal}"
APPS_DIR="${COIL_APPS_DIR:-/home/deploy/apps}"
EXPORT_ROOT="${COIL_EXPORT_ROOT:-/home/deploy/exports}"
SERVICE="${COIL_SERVICE:-web}"
PYTHON="${COIL_PYTHON:-python3}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VERIFIER="$SCRIPT_DIR/../app/firm_export.py"

usage() { echo "usage: export-firm.sh <slug> [--dry-run]" >&2; exit 2; }
[ "$#" -ge 1 ] && [ "$#" -le 2 ] || usage
SLUG="$1"
case "$SLUG" in
  ""|*[!a-z0-9-]*|-*|*-) echo "slug must be lowercase letters, digits and inner hyphens only" >&2; exit 2 ;;
esac
DRY_RUN=0
if [ "$#" -eq 2 ]; then
  [ "$2" = "--dry-run" ] || { echo "unknown option: $2" >&2; exit 2; }
  DRY_RUN=1
fi

DOMAIN="$SLUG.$BASE_DOMAIN"; DIR="$APPS_DIR/$DOMAIN"; DEST="$EXPORT_ROOT/$SLUG"
[ -d "$DIR" ] || { echo "no Coil instance at $DIR" >&2; exit 1; }
[ -f "$DIR/data/practice.db" ] || { echo "no database at $DIR/data/practice.db" >&2; exit 1; }
[ -f "$VERIFIER" ] || { echo "verifier not found at $VERIFIER" >&2; exit 1; }

if [ "$DRY_RUN" = 1 ]; then
  echo "Exporting $DOMAIN (dry run, nothing changed)"
  echo "  would: (cd $DIR && docker compose exec -T $SERVICE python -m app.cli export_firm --slug $SLUG)"
  echo "  would: copy the zip from $DIR/data/exports/ to $DEST/ with mode 0600, never replacing a file"
  echo "  would: $PYTHON -I $VERIFIER verify <copied zip>"
  echo "  would: remove the zip from $DIR/data/exports/ once the copy passes"
  exit 0
fi

echo "Exporting $DOMAIN"
out="$(cd "$DIR" && docker compose exec -T "$SERVICE" python -m app.cli export_firm --slug "$SLUG")" || {
  printf '%s\n' "$out" >&2
  echo "FAILED: export inside the container did not finish. Nothing copied." >&2; exit 1; }
printf '%s\n' "$out" | sed '/^EXPORT_FILE=/d; s/^/  /'

inside="$(printf '%s\n' "$out" | sed -n 's/^EXPORT_FILE=//p' | tail -1)"
name="${inside##*/}"
case "$inside" in
  /app/data/exports/coil-export-*.zip) ;;
  *) echo "FAILED: the container did not report an export file under /app/data/exports." >&2; exit 1 ;;
esac
case "$name" in
  *[!A-Za-z0-9._-]*) echo "FAILED: unexpected export file name $name" >&2; exit 1 ;;
esac
src="$DIR/data/exports/$name"
if [ -L "$src" ] || [ ! -f "$src" ]; then
  echo "FAILED: $src is not a regular file." >&2; exit 1
fi

(umask 077; mkdir -p "$DEST")
chmod 700 "$DEST"
partial="$DEST/.$name.partial"
cleanup() { rm -f "$partial"; }
trap cleanup EXIT
# Copy privately, then publish with a hard link, which refuses to replace an existing file.
(umask 077; set -o noclobber; : > "$partial") || { echo "FAILED: cannot create $partial" >&2; exit 1; }
cp "$src" "$partial"
chmod 600 "$partial"
if ! ln "$partial" "$DEST/$name"; then
  echo "FAILED: $DEST/$name already exists; it was left alone." >&2; exit 1
fi
rm -f "$partial"
final="$DEST/$name"

if ! "$PYTHON" -I "$VERIFIER" verify "$final"; then
  echo "FAILED: the copy at $final did not pass verification. Do not rely on it." >&2
  echo "The container's copy is kept at $src for inspection." >&2
  exit 1
fi
rm -f "$src"
size="$(du -h "$final" | cut -f1)"
echo "Verified export: $final ($size)"
echo "It holds client data and hashed sign-in credentials. Hand it over securely."
