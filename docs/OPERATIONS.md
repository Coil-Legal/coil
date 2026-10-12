# Running hosted Coil

This is the operator's guide for the hosted firms at `<slug>.coil.legal`: one container per
firm on the VPS, app directories under `/home/deploy/apps/<slug>.coil.legal/`, each with its
own `.env` and a bind-mounted `data/`. Self-hosters want [SELF-HOSTING.md](SELF-HOSTING.md)
instead.

Everything below runs on the VPS as root. The scripts live in `ops/` in the repo. Copy the
ones cron runs into `/home/deploy/scripts/` (the existing nightly backup is already there as
`coil-backup.sh`), keeping `restore.sh` next to `restore-drill.sh`. `export-firm.sh` checks
each export with the host's own Python, so copy `app/firm_export.py` and
`app/backup_manifest.py` into the same directory as it (it imports the second).

## Account lifecycle policy

Hosted firms are free while Coil is young. There are five hosted spots, no trial period and
no billing, so nothing here depends on a payment. An account is in one of three states, set
by the operator in that firm's `.env` as `COIL_ACCOUNT_STATE`:

| State | What the firm can do | What its clients see |
|---|---|---|
| `active` | Everything. | Everything. |
| `suspended` | Sign in, read every page, export everything, change their own password. Every other change is refused with HTTP 423 and the message "This account is paused. You can view and export your data. Contact hello@coil.legal to reactivate." | Pay links, signing links, the portal and the public intake form show a "temporarily unavailable" page (HTTP 503). Nothing is charged, signed or sent. |
| `closed` | Sign in, sign out, and the owner's export page at `/settings/export`. Every other page shows "This account is closed. The owner can still sign in and download all firm data until <date>." | The same pages show "no longer available, contact the firm" (HTTP 410). |

In both paused states:

- A banner with the message sits at the top of every staff page.
- `/health`, `/health/ready` and static files keep working, so monitoring keeps working.
- Inbound provider webhooks (`/webhooks/stripe`, `/webhooks/twilio`) get HTTP 503. Stripe
  retries a failed delivery for up to three days, so a firm reactivated inside three days
  loses nothing. After that, replay the events from the Stripe dashboard. Twilio does not
  retry inbound texts; they stay in the Twilio console, so check it after a long pause.
- Email open pixels answer 204 and record nothing.
- The API and MCP answer JSON with HTTP 423 for anything they refuse. While suspended,
  reads still work and so do OAuth token refresh and revocation.
- The cron jobs that send, charge, call or change records (agenda, reminders, interest,
  emailin, sequences, webhooks, monthly_invoicing, case_audit, payment_plans,
  voice_reminders) print a "skipped" notice and do nothing. Unread mail stays on the IMAP
  server, so `emailin` files it after reactivation. Backups keep running.

Why 423 and not 403 for a refused write: in Coil 403 means "your role cannot do this". A
paused account is not a role problem, so it gets its own code, and the logs, the QA bots
and API clients can tell the two apart.

An unrecognised value in `COIL_ACCOUNT_STATE` is treated as `suspended` and logged. A typo
should not leave an account fully writable when the operator meant to pause it.

### Cancellation

1. The owner asks to leave, or Ian decides an account has to close.
2. Offer the export first. The owner downloads it from `/settings/export`, which works in
   every state.
3. Close the account with a retention date. The default is 90 days from today:
   `ops/firm-state.sh <slug> closed` (or `--retain-until YYYY-MM-DD`).
4. The container keeps running until the retention date so the owner can still sign in and
   export. Nightly backups continue for that time.
5. Purge happens only through a separately approved process. `ops/remove-firm.sh --purge`
   refuses today on purpose, until a verified export, restore integrity and retention
   approval are in place. `remove-firm.sh` without `--purge` stops the container and keeps
   the directory.

### Pause, reactivate, close

```
ops/firm-state.sh <slug> suspended
ops/firm-state.sh <slug> active
ops/firm-state.sh <slug> closed --retain-until 2027-01-31
ops/firm-state.sh --dry-run <slug> suspended      # shows the change, makes none
```

The script changes only the `COIL_ACCOUNT_STATE` and `COIL_ACCOUNT_CLOSED_RETAIN_UNTIL`
lines of that firm's `.env` (every other line, its mode and its owner are kept, and the new
file replaces the old one in one rename), recreates the container with
`docker compose up -d --force-recreate`, waits for `/health/ready`, and checks the running
container sees the new state. It exits non-zero if either check fails. Reactivating removes
the retention line.

## Reading /health/ready

`/health` only says a worker is up. The self-updater polls it right after a restart, so it
never touches the database, and a 200 from it proves nothing about the database, the cron
jobs, the disk or backups.

`/health/ready` is the real check. It is public and shows only check names and one-word
states:

```
curl -s https://<slug>.coil.legal/health/ready
{"status": "ready", "checks": {"database": "ok", "data_dir": "ok", "disk": "ok",
 "jobs.emailin": "ok", "jobs.agenda": "unknown", ...}, "version": "...", "commit": "..."}
```

| Check | Fails when |
|---|---|
| `database` | a trivial read of the real database file fails or takes over 2 seconds |
| `data_dir` | the data directory will not take a test write |
| `disk` | free space on the data directory's filesystem is under 5% or under 1 GB, whichever is larger |
| `jobs.<command>` | `stale`: the last success is older than its limit. `fail`: the last run failed more recently than it succeeded |
| `heartbeats` | the heartbeat file exists but cannot be read |

`unknown` means a job has never run here (a new firm, or a job this firm does not
schedule). It does not fail readiness. Any `fail` or `stale` makes the answer HTTP 503 with
`"status": "degraded"`.

Job limits: `emailin` and `webhooks` 45 minutes; `agenda`, `reminders`, `sequences`,
`case_audit`, `payment_plans`, `voice_reminders` and `backup` 26 hours; `interest` and
`monthly_invoicing` 32 days. Change them in the firm's `.env`, for example
`COIL_JOB_STALE_MINUTES=emailin=60,voice_reminders=0`, where 0 drops a job from the check.
Disk limits are `COIL_READY_DISK_MIN_PERCENT` and `COIL_READY_DISK_MIN_MB`.

Each cron run records its result in `data/job-heartbeats.json` inside the firm's data
directory: command names, times and, for a failure, the error type only. To see why a job
failed, read `data/cron.log`.

## The fleet monitor

`ops/monitor.sh` checks every hosted firm on the host: app directories named `<slug>.coil.legal`
whose `data/` holds `practice.db`. Stopped lab and recovery copies (`coil-phase1-lab` and the
like) are skipped so they never alert; set `COIL_INSTANCE_GLOB` to widen it. The monthly
restore drill's `--all` uses the same rule.

| Check | Passes when |
|---|---|
| `<firm>:container` | the compose `web` service is running |
| `<firm>:ready` | `<BASE_URL>/health/ready` answers 200, with BASE_URL from the firm's `.env` |
| `<firm>:backup` | the newest nightly archive in `/home/deploy/backups/coil/<firm>/` is under 26 hours old |
| `<firm>:offsite` | the last nightly run copied it off-site, per `.coil-backup-status` in that folder, written by `backup.sh`, and that record is under 26 hours old |
| `<firm>:drill` | the last restore drill passed within 35 days |
| `host:disk` | `/` has more than 10% and more than 2 GB free |

It alerts only when a check changes, ok to fail or fail to ok, and remembers the last state
in `/var/lib/coil-monitor/state`. If an alert cannot be delivered it keeps the old state, so
the next run tries again.

Set the alert channel in `/etc/coil-monitor.env` (root only, `chmod 600`):

```
COIL_ALERT_WEBHOOK=https://...        # receives a JSON POST: {"text", "source", "host", "changes"}
COIL_ALERT_EMAIL=ops@example.com      # sent through the SMTP account below, else mail or sendmail
COIL_ALERT_SMTP_HOST=smtp.gmail.com   # this VPS has no mail program, so alerts go out by SMTP
COIL_ALERT_SMTP_PORT=587
COIL_ALERT_SMTP_USER=...
COIL_ALERT_SMTP_PASS=...              # an app password; root-only file
COIL_ALERT_SMTP_FROM=...
COIL_ALERT_SUBJECT_PREFIX="Coil monitor"
```

On idcprojects the alerts go to ian@iandolan.com through the same Gmail account the coil.legal
site sends from, with subjects starting "Coil Alerts Test" while the monitor is being proven.

Either or both. Point the webhook at whatever already receives this host's alerts. With
neither set the monitor still checks and logs, prints `NO ALERT CHANNEL CONFIGURED` on every
run and exits 3, so a missing channel is never silent.

Other settings in the same file: `COIL_MONITOR_BACKUP_MAX_HOURS` (26),
`COIL_MONITOR_DRILL_MAX_DAYS` (35), `COIL_MONITOR_DISK_MIN_PERCENT` (10),
`COIL_MONITOR_DISK_MIN_MB` (2048).

Exit codes: 0 all ok, 1 something failing, 3 no alert channel, 4 an alert was due and no
channel delivered it. `--dry-run` checks and prints what it would send, sends nothing and
remembers nothing.

## The restore drill

`ops/restore-drill.sh --all` (or `<slug>`) takes each firm's newest nightly archive and:

1. restores it with `restore.sh` into a private temp directory under
   `/home/deploy/backups/coil/.drill-work/`, with a copy of the firm's `docker-compose.yml`
   so `restore.sh` checks the archive against the image that firm actually runs
   (`COIL_DRILL_SCHEMA_CHECK=0` skips that);
2. runs `PRAGMA integrity_check` on the restored database;
3. checks every table in the archive's `coil-backup.json` manifest is present with the same
   columns, and that every table's row count matches the database read straight out of the
   archive;
4. deletes the temp directory, which holds a full copy of the firm's data and `.env`;
5. writes `.coil-drill-status` next to the archives, which the monitor reads.

`--dry-run` names the archive it would drill and touches nothing.

## Cron lines (root)

```
# nightly backup, already installed
20 2 * * * /home/deploy/scripts/coil-backup.sh >> /var/log/coil-backup.log 2>&1
# fleet monitor, every 10 minutes
*/10 * * * * /home/deploy/scripts/coil-monitor.sh >> /var/log/coil-monitor.log 2>&1
# restore drill, monthly, after that night's backup
30 4 3 * * /home/deploy/scripts/coil-restore-drill.sh --all >> /var/log/coil-restore-drill.log 2>&1
```

`coil-restore-drill.sh` finds `restore.sh` (or `coil-restore.sh`) in its own directory, or
set `COIL_RESTORE_SCRIPT`.

## Provisioning a firm

`ops/new-firm.sh <slug> "<Firm Name>" <owner-email>` builds the new firm from the source app
(`demo.coil.legal` by default, `COIL_SOURCE_APP` to change it). The release is pinned:

- The commit is the source checkout's `git rev-parse HEAD`, and the version is
  `git describe --tags --always`. `COIL_COMMIT` and `COIL_VERSION` in the environment
  override them, and `COIL_COMMIT` must match the checkout when the source is one. A source
  that is not a git checkout needs both set.
- A source with uncommitted changes to anything that goes into the image is refused.
  `--allow-dirty` builds anyway and the report says so. The source's own
  `docker-compose.yml`, `data/` and `.env` do not count, since they never reach the new firm.
- The image is built with `docker compose build --build-arg COIL_COMMIT=... --build-arg
  COIL_VERSION=...`, then started.

After start it checks, and prints a provisioning report:

- `/health` reports exactly the pinned commit;
- `/health/ready` answers 200 and `/setup` is open for the owner to create the account;
- the nightly backup's discovery (`backup.sh --dry-run`) lists the new firm, and root's
  crontab has the nightly backup line;
- isolation: the data directory, the compose project, the Traefik router names and the
  `SECRET_KEY` are not shared with any other instance. Keys are compared by sha256 and never
  printed.

Any failed check makes the script exit 1 with "Do not hand this firm over until they pass."
`--dry-run` shows the pin and every step without changing anything.

### Rehearsal

Before onboarding a real firm on a new release, rehearse on a throwaway slug:

```
ops/new-firm.sh --dry-run rehearsal-20261012 "Rehearsal" owner@example.com
ops/new-firm.sh rehearsal-20261012 "Rehearsal" owner@example.com
curl -s https://rehearsal-20261012.coil.legal/health        # the pinned commit
curl -s https://rehearsal-20261012.coil.legal/health/ready  # 200
ops/firm-state.sh rehearsal-20261012 suspended               # then active again
ops/remove-firm.sh rehearsal-20261012                         # stops it, keeps the directory
```

Create the owner on `/setup` with test details only, and remove the kept directory by hand
once the rehearsal is recorded.

## Support

**Who answers:** Ian. There is no second support person yet.

**Where requests arrive:**

- In-app feedback (the Feedback link, `app/blueprints/feedback.py`) posts to
  `https://coil.legal/api/coil-feedback`, with the page, the Coil version and commit, and
  the sender's role. The coil.legal API writes every message to `data/coil-feedback.jsonl` on
  that site first, then forwards it through the forms relay to Ian's inbox, so a relay
  outage never loses one. A firm that cannot reach coil.legal is told to email instead.
- Email to `hello@coil.legal`. The app names this address in error messages and on the
  paused and closed pages. It needs Cloudflare Email Routing on the coil.legal zone,
  forwarding `hello@coil.legal` to `ian@iandolan.com`. Without it, mail to that address
  bounces, because coil.legal has no MX record. Check with `dig +short MX coil.legal`.

**Response targets (proposed default, Ian to confirm):** a reply within one business day;
the same day for anything that loses data, stops a firm signing in, or takes money wrongly.

**Checking delivery without sending live feedback:** `dig +short MX coil.legal` returns
Cloudflare's route servers; the newest line in coil.legal's `data/coil-feedback.jsonl` on the
VPS matches the newest feedback email in Ian's inbox. Send a real test message only when Ian
asks, marked as a test.
