# Production Hardening Changes (2026-09-06)

This file tracks all production-related improvements made to Coil.

## Changes Made

### 1. Secure Configuration (`app/config.py` + `app/__init__.py`)
- Added `ProductionConfig` class with strong defaults.
- Automatic strong `SECRET_KEY` generation using `secrets.token_hex(32)` if none is provided (replaces weak default).
- Secure session cookies: `SESSION_COOKIE_SECURE=True`, `SESSION_COOKIE_HTTPONLY=True`, `SESSION_COOKIE_SAMESITE='Lax'`.
- Added comprehensive security headers via `after_request` handler:
  - `X-Frame-Options: DENY`
  - `X-Content-Type-Options: nosniff`
  - `X-XSS-Protection: 1; mode=block`
  - `Referrer-Policy: strict-origin-when-cross-origin`
  - Basic `Content-Security-Policy`
- Set `DEBUG=False` for production.

### 2. App Initialization (`app/__init__.py`)
- Now uses `ProductionConfig` by default instead of base `Config`.
- Added security headers middleware.

### Next Planned Changes
- Update `install.sh` and create `.env.example` with clear production guidance.
- Add `app.cli backup` command for automated dated backups.
- Add rate limiting on authentication endpoints.
- Review error handling and logging across CLI commands.

These changes significantly raise the security and operational maturity of self-hosted Coil deployments.

Last updated: 2026-09-07

## Final Cleanup Completed

**Removed all watchparty debugging artifacts**
- Cleaned hardcoded test streams, temporary comments, and forced URLs from `browser/run.sh` and `docker-compose.yml`.
- Restored original Hudl stream as default.
- Updated tracking file.

**Version bumped to 0.3.1**

**Coil is now ready for launch.**

All major production hardening, security, backup, and cleanup tasks are complete. The project is in excellent shape for self-hosting release.

## Most Recent Changes

**Final Cleanup & Pre-Launch Polish**
- Removed all remaining debug artifacts from the watchparty session (hardcoded URLs, temporary comments, forced test stream logic).
- Updated installer, documentation, and tracking file.
- Added `/health` endpoint, rate limiting, secure config, backup CLI, and automated backup recommendations.
- Coil is now in strong production-ready state.

**Current Version**: 0.3.1 (updated from 0.3.0)

**Launch Recommendation**: Coil is ready for public self-hosting release. The main risks (secrets management, backups, brute-force protection, security headers) have been addressed.

## Most Recent Changes

**Added recommended cron example for automated backups** (`docs/SELF-HOSTING.md`)
- Clear nightly backup command using the new `app.cli backup`.
- Improved backup section with restore instructions.

**Added /health endpoint** and rate limiting on login (previous steps).

All major production hardening items are now complete.

## Most Recent Changes

**Added /health endpoint** (`app/__init__.py`)
- Simple health check for monitoring and uptime systems (`GET /health`).

**Added rate limiting on login** (previous step).

**Added backup CLI command** and improved installer (previous steps).

**Added ProductionConfig** with secure defaults (previous step).

## Most Recent Changes

**Added rate limiting on login endpoint** (`app/blueprints/auth.py`)
- Simple in-memory rate limit (10 attempts per IP in 5 minutes).
- Prevents basic brute-force attacks on the login form.

**Added backup CLI command** and updated installer (previous step).

**Added ProductionConfig** with secure defaults, automatic strong SECRET_KEY, security headers, and secure cookies (previous step).

## Most Recent Changes

**Added backup CLI command (`python -m app.cli backup`)**  
- Creates dated `.tar.gz` archives of the entire `data/` directory (database + uploads + PDFs).
- Safe to run while the app is live.
- Updated installer messages to recommend using this command.

**Improved installer (`install.sh`)**  
- Stronger SECRET_KEY generation using `openssl rand -hex 32`.
- Better `.env` template with production guidance.
- Updated post-install messaging to highlight config, backups, and new CLI command.

**Created `.env.example`** with clear production recommendations.
