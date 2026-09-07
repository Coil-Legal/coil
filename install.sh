#!/usr/bin/env sh
# Coil installer for Mac and Linux. Needs Docker (Docker Desktop on a Mac).
#   curl -fsSL https://raw.githubusercontent.com/Law-Firm-Automate/coil/main/install.sh | sh
set -e
DIR="${COIL_DIR:-$HOME/coil}"
PORT="${COIL_PORT:-8080}"
# `stable` is promoted from `edge` once a build has soaked for a few days. Set
# COIL_CHANNEL=edge to follow every push instead, which is useful for testing and a
# bad idea on a machine holding real matters.
CHANNEL="${COIL_CHANNEL:-stable}"
IMAGE="${COIL_IMAGE:-ghcr.io/law-firm-automate/coil:$CHANNEL}"
AUTO_UPDATE="${COIL_AUTO_UPDATE:-1}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed. On a Mac, install Docker Desktop from https://www.docker.com/products/docker-desktop/ and run this again."
  exit 1
fi
if ! docker info >/dev/null 2>&1; then
  echo "Docker is installed but not running. Start Docker Desktop and run this again."
  exit 1
fi

mkdir -p "$DIR/data"
cd "$DIR"

if [ ! -f .env ]; then
  SECRET=$(openssl rand -hex 32 2>/dev/null || head -c 32 /dev/urandom | od -An -tx1 | tr -d ' \n')
  cat > .env <<ENV
# Coil Production Configuration
# Generated on $(date)

SECRET_KEY=$SECRET
BASE_URL=http://localhost:$PORT
DATABASE_URL=sqlite:////app/data/practice.db

# === REQUIRED FOR PRODUCTION ===
# Change BASE_URL to your real domain (https://coil.yourfirm.com)
# Fill in SMTP settings below to enable emails

SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
MAIL_FROM=

# Optional: Stripe for online payments
STRIPE_SECRET_KEY=
STRIPE_PUBLISHABLE_KEY=
STRIPE_WEBHOOK_SECRET=

# Optional: AI (Anthropic recommended)
# ANTHROPIC_API_KEY=sk-ant-...

# See .env.example for full documentation and production recommendations.
ENV
  chmod 600 .env
  echo "Created secure $DIR/.env with strong SECRET_KEY."
  echo "Edit it to add your email/SMTP settings and change BASE_URL to your real domain."
fi

cat > docker-compose.yml <<YML
services:
  coil:
    image: $IMAGE
    container_name: coil
    restart: unless-stopped
    env_file: .env
    environment:
      COIL_CHANNEL: "$CHANNEL"
    ports:
      - "$PORT:8000"
    volumes:
      - ./data:/app/data
YML

if ! docker compose pull 2>/dev/null; then
  echo "Could not pull the prebuilt image; building from source instead (takes a few minutes)."
  if ! command -v git >/dev/null 2>&1; then echo "git is needed to build from source."; exit 1; fi
  [ -d src ] || git clone --depth 1 https://github.com/Law-Firm-Automate/coil.git src
  (cd src && git pull -q || true)
  sed -i.bak "s#image: .*#build: ./src#" docker-compose.yml && rm -f docker-compose.yml.bak
  docker compose build
fi
docker compose up -d

# Fetch the updater next to the install so a source-built or image-based install both
# have it, then run it nightly. Without this, daily releases never reach anyone: the
# firm would have to remember to run a command, and nobody does.
if [ "$AUTO_UPDATE" = "1" ]; then
  mkdir -p ops
  if [ -f src/ops/self-update.sh ]; then
    cp src/ops/self-update.sh ops/self-update.sh
  else
    curl -fsSL https://raw.githubusercontent.com/Law-Firm-Automate/coil/main/ops/self-update.sh \
      -o ops/self-update.sh 2>/dev/null || true
  fi
  if [ -s ops/self-update.sh ]; then
    chmod +x ops/self-update.sh
    LINE="17 3 * * * cd $DIR && COIL_PORT=$PORT ./ops/self-update.sh >> $DIR/data/update.log 2>&1"
    if command -v crontab >/dev/null 2>&1; then
      # Replace our own line only, so the firm's other cron jobs are untouched.
      (crontab -l 2>/dev/null | grep -v 'coil.*self-update.sh' ; echo "$LINE") | crontab - 2>/dev/null \
        && echo "Nightly updates are on (3:17am). Turn them off with: crontab -e" \
        || echo "Could not install the update cron. Run ./ops/self-update.sh yourself, or add: $LINE"
    else
      echo "No crontab on this machine. Run ./ops/self-update.sh on a schedule to stay current."
    fi
  fi
fi

echo
echo "Coil is running."
echo "  Open:    http://localhost:$PORT"
echo "  Config:  $DIR/.env          (edit BASE_URL, email settings, and secrets)"
echo "  Data:    $DIR/data          (back this folder up regularly - contains everything)"
if [ -d src ]; then
  echo "  Update:  cd $DIR && git -C src pull && docker compose up -d --build"
else
  echo "  Update:  runs nightly on its own. Force one now: cd $DIR && ./ops/self-update.sh"
  echo "  Undo:    cd $DIR && ./ops/self-update.sh --rollback"
fi
echo "  Channel: $CHANNEL   (stable is promoted weekly; COIL_CHANNEL=edge follows every build)"
echo "  Backup:  cd $DIR && docker compose exec coil python -m app.cli backup"
echo
echo "First visit will create the owner account and ask for your install key from https://coil.legal/download."
echo
echo "See PRODUCTION_CHANGES.md for recent security and operational improvements."
