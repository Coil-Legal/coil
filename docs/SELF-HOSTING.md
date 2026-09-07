# Running Coil yourself

Coil is one container and one database file. It runs on a Mac mini in the office, a laptop, a
Windows PC with Docker Desktop, or a small cloud server. Your data never leaves the machine you
run it on.

## What you need

- A computer that stays on when you want to use Coil (a Mac mini or an old laptop is plenty).
- Docker Desktop (Mac, Windows) or Docker Engine (Linux). Free for a firm of your size.
- Ten minutes.

## Install on a Mac or Linux

Open Terminal and paste:

```bash
curl -fsSL https://raw.githubusercontent.com/Coil-Legal/coil/main/install.sh | sh
```

Then open http://localhost:8080 and create the owner account. That is the whole install.

## Install on Windows

1. Install Docker Desktop and start it.
2. Make a folder, for example `C:\coil`, and inside it save the two files below.
3. In PowerShell, run `cd C:\coil` then `docker compose up -d`.
4. Open http://localhost:8080.

`.env`:

```
SECRET_KEY=change-this-to-a-long-random-string
BASE_URL=http://localhost:8080
DATABASE_URL=sqlite:////app/data/practice.db
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
MAIL_FROM=
```

`docker-compose.yml`:

```yaml
services:
  coil:
    image: ghcr.io/coil-legal/coil:latest
    restart: unless-stopped
    env_file: .env
    ports:
      - "8080:8000"
    volumes:
      - ./data:/app/data
```

If `docker compose pull` comes back with `denied` or `unauthorized`, the prebuilt image is not
public yet. Build it from source instead, which takes a few minutes and produces the same thing:

```
git clone --depth 1 https://github.com/Coil-Legal/coil.git src
```

Then replace the `image:` line above with `build: ./src` and run `docker compose up -d --build`.
To update a source build later, run `git -C src pull && docker compose up -d --build`.

## Let a coding agent do it for you

If a terminal is not your idea of a good afternoon, a coding agent will run the install and answer
questions in plain English while it works. Install one of Claude Code, OpenAI Codex or Grok, open it
in a folder on your machine, and give it something like this:

```
Install Coil, the open-source law practice management app, on this computer.
The installer is at https://coil.legal/install.sh and the setup guide is at
https://coil.legal/docs. Install Docker Desktop first if it is not already
there. When Coil is running, open it and help me create the owner account.
My install key is COIL-XXXX-XXXX-XXXX and the email it is tied to is
me@myfirm.com.
```

Put your own key and email in the last two lines. An agent asks permission before it runs anything,
so read what it proposes rather than approving on autopilot, and do not paste client information
into it during setup.

The install is the easy part. An agent earns its keep on what comes after: email, a nightly backup,
reaching Coil from your phone, and putting the scheduled jobs on a timer. Point it at the sections
below and ask for one at a time.

## Sending email

Invoices, engagement letters and portal links go out by email. Until you fill in the SMTP
settings, Coil stores them under Settings > Dev outbox so you can see what would have been sent.
Any mailbox works: Google Workspace (smtp.gmail.com, port 587, an app password), Microsoft 365
(smtp.office365.com, port 587), or a transactional provider. Set `MAIL_FROM` to the address
clients should reply to.

## Reaching it from outside the office

The install listens on your local network only. To use Coil from home or a phone:

- **Tailscale** (simplest): install it on the Coil machine and your devices, then use the
  Tailscale address. Nothing is exposed to the internet.
- **Cloudflare Tunnel**: gives you a real HTTPS address like coil.yourfirm.com without opening
  ports. Set `BASE_URL` to that address so links in emails work.
- **A reverse proxy** (Caddy, nginx) with HTTPS if you run it on a cloud server.

Do not forward port 8080 on your router to the internet. Coil expects HTTPS in front of it.

## Backups

Everything is in the `data` folder next to your `.env`: the database, uploaded documents,
generated PDFs, and logs.

**Recommended automated backup** (add to cron or Task Scheduler):

```bash
# Nightly backup at 2:00 AM
0 2 * * * cd /path/to/coil && docker compose exec -T coil python -m app.cli backup >> /var/log/coil-backup.log 2>&1
```

The `backup` command creates a dated `.tar.gz` file in `backups/`. Keep at least 7–30 days of backups.
To restore: stop the container, replace the `data/` folder with the extracted backup, and restart.

Manual backup: `docker compose exec coil python -m app.cli backup`

## Updating

```bash
cd ~/coil && docker compose pull && docker compose up -d
```

Your data folder is untouched by updates.

## Online payments

Create a Stripe account, paste the secret and publishable keys into `.env`, and point a Stripe
webhook at `BASE_URL/webhooks/stripe` for `checkout.session.completed` and
`checkout.session.async_payment_succeeded`. Restart the container after editing `.env`.

## Scheduled jobs

Coil sends the morning agenda, invoice and engagement reminders, and follow-up sequence steps
from a small command. Run these from cron or Task Scheduler on the Coil machine:

```
15 7 * * * cd ~/coil && docker compose exec -T coil python -m app.cli agenda
30 7 * * * cd ~/coil && docker compose exec -T coil python -m app.cli reminders
0  8 * * * cd ~/coil && docker compose exec -T coil python -m app.cli sequences
0  6 1 * * cd ~/coil && docker compose exec -T coil python -m app.cli interest
```

## Getting help

Open an issue at https://github.com/Coil-Legal/coil/issues, or email the address on the Coil page
at coil.legal.

## Updates

Coil ships most days. Firms follow the `stable` tag, which is promoted from `edge` once a
build has soaked for a few days on our own instances, so a release lands on your matters
after it has been running somewhere real, not the morning it is pushed.

The installer sets up a nightly job that does this, at 3:17am:

1. Backs up the database first, through SQLite's online backup API. A backup taken after
   an upgrade goes wrong is not a backup.
2. Pulls. If nothing moved, it stops there. No restart, no downtime.
3. Restarts and polls `/health` until it answers.
4. If the new build does not come back, it pins the previous one and restarts again. You
   wake up to yesterday's Coil, not to no Coil.

This is safe to do unattended because schema changes are additive only: `app/migrate.py`
adds missing columns and never drops or renames one, so going back an image leaves an
unused column rather than a broken database.

When a rollback happens, Coil writes `docker-compose.override.yml` pinning the build that
worked and records the one that failed. The nightly job keeps checking: while the channel
still points at the build that broke, it holds and does nothing. As soon as a different
build appears, it removes the pin and takes the new one. You do not have to do anything.

```bash
./ops/self-update.sh --dry-run   # what would happen
./ops/self-update.sh             # update now
./ops/self-update.sh --rollback  # go back to the previous build
```

`data/update.log` has the history. Turn the schedule off with `crontab -e`, or install
with `COIL_AUTO_UPDATE=0` to never add it.

To follow every build instead of weekly stable, install with `COIL_CHANNEL=edge`. That is
useful for testing and a bad idea on a machine holding real matters.

`/health` reports the build a firm is on, which is the first thing to check in a bug
report:

```bash
curl -s http://localhost:8080/health
```

Old images are kept rather than pruned, because the previous image is the rollback path.
If disk gets tight, `docker image prune -a` clears them, at the cost of that path.

## Sending feedback

There is a "Send feedback" link in the sidebar of every page. It carries the page you
were on, your name and email, the firm name and the exact build you are running, so a bug
report does not start with three rounds of "which version are you on?".

Your instance makes that request, not your browser, and the form lists every field before
you send it. Nothing from your matters, contacts, documents or ledgers is included.

Set `FEEDBACK_ENABLED=0` in `.env` to remove the link and the route. Point
`COIL_FEEDBACK_URL` somewhere else to send it to your own endpoint instead.
