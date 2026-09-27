# Nightly backup workspace ownership

`ops/backup.sh` is the Linux host fleet backup script. It needs Python 3.8 or newer on the host, POSIX advisory file locks on local storage, GNU tar/date, Docker and the configured rclone remote. This requirement is separate from the application's container runtime and `python -m app.cli backup`.

Each firm gets a permanent `data/.coil-nightly-registry.lock`. Do not delete this file while any backup can run: recreating it permits unrelated locks on different inodes. A short exclusive registry lock protects workspace creation and reclamation.

A job creates a private `data/.coil-nightly-job-*` directory and a shared `lease` lock. The Python supervisor and its host children inherit that lease. The Docker snapshot process acquires its own shared lease under the registry lock because it may outlive its host launcher. A delayed Docker child opens only the existing lease; if cleanup already removed the workspace, it fails without recreating files.

The SQLite snapshot and its sidecars stay inside the workspace. The temporary archive sits on the backup destination filesystem, named after that workspace with a `.partial` suffix. A completed archive is published by hardlink before the partial name is removed. Final archives keep mode 0600.

On the next run, cleanup takes the registry lock and attempts a nonblocking exclusive lease for each workspace. Active jobs are skipped. Unlocked workspaces and their corresponding partial archives are removed. An incomplete workspace with no lease can be reclaimed while holding the registry lock. Symlink workspaces are ignored. Cleanup also runs after a handled completion, but retains a workspace if a detached container child still holds its lease or the supervised shell died by signal.

Legacy flat `.backup-snapshot.*` and old partial files are deliberately not claimed by this protocol. Their ownership cannot be inferred from age or a missing launcher PID. Removing them requires a separate quiescence review. Changing `COIL_BACKUP_ROOT` while old jobs remain also needs operator review: reclamation uses the current destination and cannot locate partial files under a previous destination.

These checks establish process-lifetime safety on the tested local Linux filesystem. They do not establish power-loss durability, network filesystem lock semantics, offsite availability, or a restore across application versions. Published archives and fixture-level passes are not full recovery signoff.
