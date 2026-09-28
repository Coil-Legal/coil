# Tool readiness register

## Calendar form date-boundary fix, 2026-09-28 00:54 UTC

Reviewed from 59393f6 in isolated /private/tmp/coil-calendar-boundary-review. Files: app/blueprints/calendar.py and tests/test_calendar_form_boundaries.py. No schema change. Synthetic disposable event 1 and API/import fixture IDs only; no live boundary records created by Codex.

Ten baseline cases failed and three controls passed in 5.57 seconds. Actual create/edit submissions crashed when the default one-hour end overflowed, or when an explicit local start/end could not convert to UTC. All-day 9999-12-31 and timed recurring UNTIL 9999-12-31 in Chicago were accepted, then crashed feed generation. A rejected edit must keep the prior event intact.

The form now returns a clear validation error for default-end overflow. Shared calendar validation checks the all-day exclusive end, timed start/end UTC conversion and timed inclusive recurrence cutoff before saving. Invalid timezone configuration retains the existing UTC fallback. Invalid edit rendering uses the existing no-autoflush and rollback path. Existing historical data is not rewritten and subscriptions are not silently truncated. Focused form/API/CSV/DST checks: 66 passed, 23 warnings in 23.10 seconds, including API naive lower-bound JSON refusal and CSV all-day upper-bound row refusal.

Grok independently passed CAL-CSV-OFFSETS 5861171420, CAL-CSV-REFUSALS 5861171568 and CAL-CSV-REIMPORT 5861171723 on 37ba7e9, ACK 5861026697. Events 47/48, job 34 preserve UTC/+09:00 local and firm/owner feed times. Job 35 rejects five bad rows with 0 created/0 updated/5 errors. Controls events 49/50, jobs 36/37 preserve all-day DATE and legacy timed date/default end. Event 51, jobs 38/39 keeps ID/UID/title/times after invalid re-import. Source clio, firm-wide/no matter, tag QA-CAL-CSV-20260927. Exhibits /workspace/coil-qa/phase5/exhibits/codex-37ba7e9-cal-csv/. These are bounded case passes, not full calendar/import signoff.

Phase 1 remains incomplete. Timed recurring DST/month-year alignment, external calendar clients, second-fold selection and broader importer cases remain open. Historical discarded offsets require original source/request evidence. Portal capture, operational recovery, Stripe test keys, handset SMS and remaining AI/browser/operator/offsite gates remain blocked or pending as previously recorded. Productivity 54 remains autonomous/Cursor-owned. Main unpushed; 30-minute schedule unchanged.

A separate synthetic timed-recurrence probe confirms the existing open defect. Chicago weekly 09:00 on October 25, November 1 and November 8, 2026 stays at 09:00 in the UI, but UTC RRULE expansion becomes 08:00 after the clock change. Monthly January 31 at 09:00 through April 2027 yields four clamped UI dates, while the feed yields only January 31 at 09:00 and March 31 at 10:00. Evidence calendar-timed-recurrence-repro.json. This boundary fix does not change recurrence encoding. A timezone-aware recurrence design and independent acceptance are still required.

Full suite: 1155 passed, 1 skipped, 149 warnings in 239.34 seconds. Tested isolated commit 66bcabc6fb24719e1489d0cd1d8dc682db20329f. Evidence: calendar-boundary-baseline.log, calendar-boundary-focused.log and calendar-boundary-full.log. Reviewed calendar.py SHA 646d1cd7a6f4ecd2226e3bd3a1a4e8b9079be3fac4867384e38300fb73dd2f10; predecessor 144111d3b1192c354eb9d59135015d54de58bf92fa4ac03006b1aa2393208c40.

Both sites deployed and publicly verified healthy on 66bcabc (stable, demo-20260927). Linux candidate: 120 passed, 53 warnings in 162.74 seconds. Guarded fast-forward preserved shared coordination edits. Host/runtime calendar.py hashes match the reviewed commit; environment and Compose hashes unchanged. Backups /home/deploy/backups/coil/{domain}/calendar-boundary-66bcabc-r1, rollback images testfirmcoillegal:before-66bcabc and democoillegal:before-66bcabc. Data archives: testfirm coil-backup-20260928-004743-li7srdc0.tar.gz; demo coil-backup-20260928-005042-zdl6hf6o.tar.gz. A normal startup connection refusal recovered on health retry; no rollback needed.

SQLite quick_check passed before/after. Testfirm events 28-51 (24 rows) retain SHA 0f3b63e508d71e76cdb105b9ae5c5712b198343c93901143d534eccbaba154f5; tasks 78-81 retain SHA 58ab150b3b11b59bf64799ba31392d7faa9b061b912ccbe5f40c19a5d33ab241; 18 portal tokens retain SHA 6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec. Unchanged importer source and empty demo fingerprints also verified. The deployer now enforces protected fingerprints within activation, with rollback on mismatch; separate before/after comparisons also passed. Evidence: calendar-boundary-prepare.log, calendar-boundary-activate.log and before/after/health JSON.

Independent batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5861431619. Priority1 CAL-FORM-BOUNDARIES/CAL-FORM-EDIT-PRESERVE, priority2 independent CAL-TIMED-RECURRENCE-REPRO for the existing unfixed defect. Fresh tag QA-CAL-BOUNDS-20260928, firm-wide/no matter, actual live IDs pending. Existing events 28-51/tasks 78-81 remain protected. No acknowledgment at assignment. Existing portal/recovery prerequisites and autonomous/Cursor productivity ownership remain visible.

Verified 16 cells across five ranges; statuses, portal formula F12, Cursor fields, task/portal rows and Overview B2 preserved. S89 row104 synced. No acknowledgment/result observed for assignment5861431619 at final check.

## Calendar CSV timestamp fix, 2026-09-28 00:07 UTC

Reviewed from ab4ac4b in isolated /private/tmp/coil-calendar-import-review. Files: app/blueprints/importer.py and tests/test_calendar_import_time.py. The shared _importmap datetime parser, schema, provider settings and historical event rows stay unchanged. All local fixtures are synthetic, disposable event 1 and external ID qa-import-clock.

Baseline: 12 failed, 3 passed, 16 warnings in 6.28 seconds. Calendar CSV ingestion stripped explicit UTC/offset suffixes before storing, producing the same wrong local/feed times as the earlier API defect. It accepted nonexistent spring-forward start/end values and second-fold instants, silently replaced malformed end text with a default, and overwrote a valid imported event with an invalid clock time on re-import.

Calendar-only parsing now preserves the source instant and converts it to the firm's local timezone, retaining the existing UTC fallback for invalid configuration. Naive input and date-only all-day input keep their existing meaning. Both explicit start/end and generated one-hour end pass the calendar form's clock validation. Unrepresentable second-fold values, malformed nonempty end text and datetime overflow become row errors before ExternalRef or CalendarEvent mutation. Invalid re-import keeps the existing ID, UID, title and timestamps. Valid imports still use the existing end-before-start fallback. Other entities keep the original shared parser.

Focused import/API/form checks: 58 passed, 44 warnings in 17.66 seconds. Six further controls were added before the full/Linux runs: three legacy date-only formats must not be mistaken for offsets, non-ISO AM/PM plus offset conversion, and two datetime boundary errors. The first full run exposed two failures in those added legacy-date cases (1138 passed, 1 skipped). Calendar parsing now tries supported date formats before the general parser can discard the year. The corrected focused run passed 64 tests in 19.51 seconds. Review caught and corrected the date-suffix ambiguity before integration: the year in 05-Oct-2026 must not be interpreted as offset -20:26. Tests compare persisted local values and both firm/owner feed start/end instants after real CSV upload/preview/commit paths, plus re-import preservation. No live imports were run by Codex.

Grok independently passed CAL-API-OFFSETS 5860810379 and CAL-API-CLOCK-REFUSAL 5860810464 on 356ec08, ACK 5860792033. New live events 44/45 preserve UTC/+09:00 intended instants and default ends; event 46 is the positive first-fold control. Three bad-clock requests return JSON 400 and create no event. Owner 1/matter 3071, tag QA-CAL-API-20260927. Exhibits /workspace/coil-qa/phase5/exhibits/codex-356ec08-cal-api/. These are bounded API case passes; second-fold selection remains not built.

Phase 1 remains incomplete. Timed recurring DST/month-year alignment, external calendar-client acceptance, second-fold selection, broader importer cases and court-specific completeness remain open. Historical discarded offsets require original source/request evidence before any repair. Portal capture, operational recovery, provider test keys/handset SMS and remaining AI/browser/operator/offsite gates remain blocked or pending as recorded. Productivity 54 remains autonomous/Cursor-owned. Main remains unpushed, with the 30-minute schedule unchanged.

Final full suite: 1140 passed, 1 skipped, 148 warnings in 221.65 seconds. Tested commit 37ba7e980e6a6afc6188c9457e7209aa0346e1fc integrated by guarded fast-forward, preserving coordination edits. The initial full result (2 failed, 1138 passed, 1 skipped in 224.99 seconds) is retained in calendar-import-full-initial.log; the corrected full result is calendar-import-full.log. Other evidence: calendar-import-baseline.log, calendar-import-focused.log and calendar-import-focused-final.log.

Both sites deployed and verified healthy on 37ba7e9 (stable, demo-20260927). Linux candidate: 105 passed, 52 warnings in 135.38 seconds. Host/runtime importer SHA 4630e84fd818578353e38ee62f92d057cdbff2888db829ef4ca568e33284d515 matches reviewed code; old source SHA 7f80b6a32484df4428f0bd2cdde712b95d27441d55f261f274222a2fcfdf09ce. Expected predecessor health 356ec08 was checked before preparation; environment and Compose hashes unchanged. Backups: /home/deploy/backups/coil/{domain}/calendar-import-37ba7e9-r1; rollback images testfirmcoillegal:before-37ba7e9 and democoillegal:before-37ba7e9. Data archives: testfirm coil-backup-20260927-235502-hzmi4myq.tar.gz; demo coil-backup-20260927-235733-3qhd41ts.tar.gz.

SQLite quick_check passed before/after. Testfirm events 28-46 (19 rows) retain SHA 7bbd0e8f6da74ffd04fa30ebfb1b683b844166be630bbb70c0653e4592ac6459; tasks 78-81 retain SHA 58ab150b3b11b59bf64799ba31392d7faa9b061b912ccbe5f40c19a5d33ab241; 18 portal tokens retain SHA 6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec. Empty demo fingerprints and unchanged feed source verified. Evidence: calendar-import-prepare.log, calendar-import-activate.log, calendar-import-live-check.py and before/after/health JSON.

Independent CSV batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5861020328. CAL-CSV-OFFSETS tests two UTC/+09:00 start/end rows; CAL-CSV-REFUSALS tests five invalid rows plus all-day and legacy-date controls; CAL-CSV-REIMPORT tests preservation after a rejected update. Fresh QA-CAL-CSV-20260927/source IDs, firm-wide/no matter fixtures, actual event/job IDs pending. Existing events 28-46/tasks 78-81 remain protected, feed keys private. No acknowledgment claimed at assignment.

Final issue 12 check found Grok ACK 5861026697 at 2026-09-27 23:59:42 UTC for all three CSV cases on 37ba7e9; results pending. Sheet S88 synced and exactly verified: 16-cell update plus three acknowledgment revisions; existing statuses, formula F12, Cursor fields, task/portal rows and Overview B2 preserved. No full calendar or phase signoff.

## Calendar API timestamp fix, 2026-09-27 23:09 UTC

Reviewed from b69aef8 in isolated /private/tmp/coil-calendar-api-review. Files: app/blueprints/api.py and tests/test_calendar_api_time.py. No schema change. Local event 1 and scoped API tokens exist only in disposable test databases. No production token was created or disclosed.

Baseline: 9 failures, 4 passing controls in 4.26 seconds. API calendar creation accepted offset-bearing ISO timestamps, then SQLite discarded the offset. With a Chicago firm, 2026-10-05T14:00:00Z was saved as local 14:00 and exported five hours late. A +09:00 timestamp also lost the intended local date. The API accepted nonexistent spring-forward times and explicit second-occurrence fall-back instants that its local naive storage cannot preserve.

Explicit instants now convert to the firm's local time before saving, with the feed's existing UTC fallback for invalid timezone configuration. Naive input remains firm-local. The API records the existing default one-hour end explicitly and uses the calendar form's clock validation for both start and end. Explicit second-fold instants return JSON 400 without creating an event because fold selection is not built into the persisted model. Out-of-range conversion/default-end values also return JSON 400. This prevents silent time shifts without claiming second-fold support or fixing the separate recurring-DST feed problem.

Focused API, scope and calendar-form checks: 47 passed, 3 warnings in 10.79 seconds. Two date-boundary cases were added before the full suite and Linux candidate run. Tests compare persisted local values, API responses, staff edit page and firm/owner feed instants across Chicago/Tokyo/UTC/invalid-zone cases, including date crossover and first-fold controls. Invalid start/default end/second-fold requests leave no events. Read-only scope remains unable to create.

Grok long-series cases independently PASS on 0726538: ACK 5860448678, ICAL-LONG-DAILY 5860479245 (event 42, 2496 expanded occurrences, October 31 dates/November none), ICAL-LONG-MONTHLY 5860479338 (event 43, 1528 occurrences, Jan31/Feb28/Mar31/Apr30 2027, May none). Owner 1/matter 3071; tag QA-ICAL-LONG-20260927. Both UI and firm/owner feeds checked. Exhibits /workspace/coil-qa/phase5/exhibits/codex-0726538-ical-long/. Grok labels filter URLs user_id in the comment, while the application parameter is user; this does not undermine the date result, but no new filter-specific signoff is inferred. Existing user-filter evidence remains separate.

Phase 1 remains incomplete. Timed recurring DST/month-year alignment, importer timezone handling, external calendar clients, second-fold selection and court-specific completeness remain open. Portal capture access, operational recovery, provider test keys/handset SMS and remaining AI/browser/operator/offsite gates remain blocked or pending as previously recorded. Productivity 54 remains autonomous/Cursor-owned. No live charges, provider changes, GitHub push or schedule change.

Full suite: 1119 passed, 1 skipped, 126 warnings in 217.97 seconds. Tested commit 356ec080d4310df3f4bfbd3c22ea7946100454f3 integrated by guarded fast-forward, preserving shared coordination edits. Evidence: calendar-api-baseline.log, calendar-api-focused.log and calendar-api-full.log. The change applies to new API requests. Historical records cannot recover discarded offsets from the naive row alone; any correction requires original request/source evidence. No historical dates were rewritten.

Both sites deployed and verified healthy on 356ec08 (stable, demo-20260927). Linux candidate: 90 passed, 5 warnings in 96.52 seconds. Host/runtime API source SHA 3d85c52322a1f7545de7554682c1a7f38942f7ef3193661f38d65b3ec42257d7 matches reviewed code; old source SHA 4982ea4cff00c10d06421459b6cd416c6f5f06975d8657900280ac242957761c. Environment and Compose hashes unchanged. Backups: /home/deploy/backups/coil/{domain}/calendar-api-356ec08-r1; rollback images testfirmcoillegal:before-356ec08 and democoillegal:before-356ec08. Data archives: testfirm coil-backup-20260927-230316-8i6a5xm6.tar.gz; demo coil-backup-20260927-230508-ns7dvhg9.tar.gz. Initial connection refusal during startup recovered through the normal health retry; no rollback.

SQLite quick_check passed before/after. Testfirm events 28-43 (16 rows) retain SHA aaf2b3a8c4cbe5aac65c50e235fe624c96bf135d97a421e38ff0a920694548fc; tasks 78-81 retain SHA 58ab150b3b11b59bf64799ba31392d7faa9b061b912ccbe5f40c19a5d33ab241; 18 portal tokens retain SHA 6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec. Empty demo fingerprints and unchanged calendar source also verified. Evidence: calendar-api-prepare.log, calendar-api-activate.log, calendar-api-live-check.py and before/after/health JSON.

Independent API two-case batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5860683000. CAL-API-OFFSETS checks UTC/+09:00 saved local values and exact firm/owner feed instants; CAL-API-CLOCK-REFUSAL checks invalid spring start/default end and explicit second-fold refusals, plus first-fold positive control. Fresh QA-CAL-API-20260927 fixtures on matter 3071/owner 1. Existing authorized calendar-write API access is required; if unavailable, Grok must report BLOCKED. No acknowledgment claimed at assignment.

Sheet S87 synced and exactly verified: 16 cells across five ranges, preserving statuses, formula F12, Cursor fields, task/portal rows and Overview B2. Final issue 12 check found no acknowledgment or result for 5860683000. Calendar and Phase 1 remain pending.

## Long-running calendar series fix, 2026-09-27 22:24 UTC

Reviewed from b01e27b in isolated /private/tmp/coil-calendar-long-review. Files: app/models.py (CalendarEvent.occurrences only) and tests/test_calendar_long_series.py. No columns, schema, stored records, provider settings or feed format change.

The 1000-occurrence cap silently hid established recurring events from calendar windows while subscriptions continued. Baseline: 10 failures and 2 controls passed in 1.47 seconds after removing an unavailable optional HTML parser from the probe. All five recurrence types fail beyond their 1000th occurrence; authenticated timed/all-day daily series saved at 2020-01-01 show no events in October 2026. Monthly January 31 clamping and inclusive cutoff also disappear for older series.

The method now seeks to the requested date window and computes each occurrence from the original anchor, retaining month-end and leap-year behavior without scanning the entire history. Expansion stops at the exclusive window end or inclusive recurrence cutoff, and handles datetime's upper bound. Twelve initial cases plus existing calendar/DST/feed/Phase 1 regressions passed, 95 checks in 20.28 seconds. Three upper-bound controls were then added and are included in the full suite and Linux candidate checks. Local fixture event 1 exists only in disposable databases.

Grok independently accepted prior all-day ICAL-MONTH-END (5860148785) and ICAL-LEAP-YEAR (5860148909), ACK 5860112268, on add92b4. Monthly events 38/39/40 match five exact dates January through May 2027; yearly event 41 matches February 29, 2024, February 28 in 2025-2027, and February 29, 2028. Both firm/owner feeds and UI cells agree. Owner 1, matter 3071, tag QA-ICS-DATE-20260927. Exhibits /workspace/coil-qa/phase5/exhibits/codex-add92b4-ical-date/. These are individual case passes; external calendar clients remain untested.

Next independent queue: fresh long-running daily all-day series and monthly month-end series, with exact current-month cells, feed date expansion, inclusive cutoff and empty following month. Preserve events 28-41/tasks 78-81 and private feed keys. Record actual event IDs and redacted UIDs. Assignment does not imply acknowledgment.

Phase 1 remains incomplete. Timed recurrence DST/month-year alignment, API/import, second-fold selection, external calendars and court-specific completeness remain open. Portal replacement/limit/race acceptance retains issue 49 authorized Mailpit capture access; recovery retains exact-source/disposable access prerequisites. Stripe test keys, authentic handset SMS, remaining AI/browser/operator/offsite checks remain open. Productivity 54 stays autonomous/Cursor-owned. Main remains unpushed and the 30-minute schedule unchanged.

Full suite: 1104 passed, 1 skipped, 126 warnings in 212.69 seconds. Tested commit 0726538d10a7a95762de453575d5d4959c905a93 integrated by guarded fast-forward. Shared coordination edits preserved. Evidence: calendar-long-baseline.log, calendar-long-focused.log and calendar-long-full.log.

Both sites deployed and verified healthy on 0726538 (stable, demo-20260927). Linux candidate: 98 passed, 2 warnings in 87.91 seconds. Host/runtime models.py SHA 26bab662889638e6e4e6bbe570d905edc11c56d3cc2188cf654d08de859bddcc matches reviewed code; old source SHA b975cd5656e941ac83764197b40e62980b13c133c7d0791a306c59bd2a860d4a. Environment and Compose hashes unchanged. Backups: /home/deploy/backups/coil/{domain}/calendar-long-0726538-r1. Rollback images: testfirmcoillegal:before-0726538 and democoillegal:before-0726538. Data archives: testfirm coil-backup-20260927-221850-kk8m2e7b.tar.gz; demo coil-backup-20260927-222033-pc2bosjc.tar.gz.

SQLite quick_check passed before and after. Testfirm events 28-41 (14 rows) retain SHA a6c1404482b81b14afd686837f8f3a887931c37d48d36402ced29d1b2df81cad; tasks 78-81 retain SHA 58ab150b3b11b59bf64799ba31392d7faa9b061b912ccbe5f40c19a5d33ab241; 18 portal tokens retain SHA 6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec. Empty demo fingerprints and unchanged calendar feed source also verified. Evidence: calendar-long-prepare.log, calendar-long-activate.log, calendar-long-live-check.py and before/after/health JSON.

Independent long-series batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5860378559. No acknowledgment claimed at assignment. Daily all-day 2020-01-01 through October 31, 2026 must show all 31 October dates and no November dates. Monthly all-day 1900-01-31 through April 30, 2027 must show Jan31/Feb28/Mar31/Apr30 and no May date. Fresh QA-ICAL-LONG-20260927 fixtures, owner 1/matter 3071; actual live IDs pending.

Sheet S86 synced and exactly verified: 16 cells across five ranges; statuses, formula F12, Cursor fields, task/portal rows and Overview B2 preserved. Final issue 12 check found no acknowledgment or result for 5860378559. No full calendar or phase signoff.

## All-day month-end and leap-day fix, 2026-09-27 21:36 UTC

Reviewed from 2c0ae52 in isolated /private/tmp/coil-calendar-allday-review. Files: app/blueprints/calendar.py and tests/test_calendar_allday_recurrence.py. No schema change. Local event 1 is synthetic and exists only in disposable databases; production fixtures are not edited by this review.

Baseline: eight failures, five passing controls in 1.47 seconds. The UI's existing monthly recurrence clamps January 29/30/31 to the last valid day in shorter months, but the plain monthly feed rule skips a month when that original day does not exist. The UI's yearly February 29 event similarly appears on February 28 in non-leap years while its feed skipped those years. Authenticated form creation reproduced both mismatches in firm and owner feeds.

The fix changes only all-day rules. For monthly days 29-31, BYMONTHDAY lists days 28 through the original day and BYSETPOS=-1 selects the last valid one each month. For yearly February 29, BYMONTH=2 plus BYMONTHDAY=28,29 and BYSETPOS=-1 selects February's last day. The UI's recurrence dates and stored series stay unchanged. Dateutil feed expansion matches the screen occurrence generator through leap/non-leap months and the next leap year. The January 28 control and daily/weekly/biweekly rule shapes still pass.

Thirteen new checks and 50 existing calendar/DST/cutoff/feed regressions passed: 63 passed in 9.32 seconds. Evidence: calendar-allday-baseline.log and calendar-allday-focused.log. The new tests compare actual expanded dates, including both authenticated form-to-feed paths; they do not certify external calendar-client behavior.

Grok independently passed the prior cutoff cases on 5a89963, ACK 5859796305: ICAL-UNTIL-TIMED 5859830529 and ICAL-UNTIL-ALLDAY 5859830607. Current event 36 is the new daily 23:00 Chicago series and event 37 is the all-day daily series, owner 1/matter 3071. Both UI and dateutil expansion yield exactly October 5/6/7, with October 8 absent. Event 36 has a new UID and reuses the ID of the earlier deleted lifecycle fixture; do not confuse those two records. Exhibits: /workspace/coil-qa/phase5/exhibits/codex-5a89963-ical-until/. Events 28-35, tasks 78-81, timezone and provider settings were left unchanged. Feed keys remain private.

Next independent queue: monthly all-day January 29/30/31 through May 2027 and yearly all-day February 29, 2024 through March 2028, using fresh QA-ICS-DATE-20260927 fixtures. Record actual event IDs and redacted UIDs, leave existing events 28-37/tasks 78-81 unchanged, and keep assignment separate from acknowledgment and results.

Phase 1 remains incomplete. Timed recurrence DST and month/year alignment, API/import, second-fold selection and external calendar subscriptions remain open. Portal replacement/limit/race acceptance retains issue 49 authorized Mailpit capture access; recovery retains exact-source/disposable access prerequisites. Stripe test keys, authentic handset SMS, remaining AI/browser/operator/offsite checks and other prior gates stay open. Productivity 54 remains autonomous/Cursor-owned. No live charges, provider changes, GitHub push or schedule change.

Full suite: 1089 passed, 1 skipped, 126 warnings in 212.30 seconds. Tested commit add92b4569ed98990eae26eb06f4cb378f9244fc integrated by guarded fast-forward, preserving shared coordination edits. Evidence: calendar-allday-full.log.

Both sites deployed and verified healthy on add92b4. Linux candidate: 83 passed, 2 warnings in 84.28 seconds. Host/runtime calendar source SHA 144111d3b1192c354eb9d59135015d54de58bf92fa4ac03006b1aa2393208c40 matches reviewed code. Environment and Compose hashes unchanged. Backups: /home/deploy/backups/coil/{domain}/calendar-allday-add92b4-r1. Rollback images: testfirmcoillegal:before-add92b4 and democoillegal:before-add92b4. Data archives: testfirm coil-backup-20260927-213211-v26yhnsn.tar.gz; demo coil-backup-20260927-213350-l3gz50kx.tar.gz. An initial testfirm startup health timeout recovered on retry; no rollback was needed.

Before/after SQLite quick_check is OK. Testfirm 18 portal tokens retain SHA 6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec; events 28-37 retain SHA 14870ed6189eeff8b53ef9b66134210648e3727f319e7d082787c3364b1a6000; tasks 78-81 retain SHA 58ab150b3b11b59bf64799ba31392d7faa9b061b912ccbe5f40c19a5d33ab241. Demo empty fingerprints unchanged. Evidence: calendar-allday-live-check.py, before/after/health JSON and prepare/activate logs.

Independent monthly/yearly all-day batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5860032332. No acknowledgment claimed at assignment.

Sheet S85 synced and exactly verified: 16 cells across five ranges. Existing statuses, formula F12, Cursor fields, task/portal rows and Overview B2 preserved. Individual cases remain separate from full calendar or phase signoff.

Final issue 12 check found no acknowledgment or result for batch 5860032332. New all-day acceptance remains pending; prior cutoff cases are accepted individually.

## September 27 calendar recurrence cutoff fix, 20:54 UTC

Reviewed from 9f41d6b in isolated /private/tmp/coil-calendar-until-review. Changes are limited to app/blueprints/calendar.py, new tests/test_calendar_recurrence_until.py and the cutoff assertion in tests/test_small_features.py. No schema or provider changes.

Baseline: nine failures and five passing controls in 2.81 seconds. Daily late-evening Chicago events lost their final local day in the feed, while early Tokyo/Kiritimati events gained a day after the selected cutoff. All-day series used DATE-TIME UNTIL with DATE DTSTART. The form-saved Chicago timed and all-day cases reproduced the same output in firm/owner feeds. Synthetic event 1 and staff user 1 belong only to disposable databases.

The fix keeps all-day UNTIL date-only and converts the timed series' inclusive local end-of-day to UTC. October 7 in Chicago becomes October 8 at 04:59:59Z; its 23:00 final occurrence remains included. All-day October 7 becomes UNTIL=20261007. UTC and invalid-zone fallback, missing cutoff and nonrecurring controls are unchanged. New tests use dateutil recurrence expansion to compare the resulting local dates with the application's screen occurrences. Calendar recurrence across DST transitions and month/year clamping are separate unresolved review gates.

The cutoff typing and inclusive interpretation follow RFC 5545 section 3.3.10: https://www.rfc-editor.org/rfc/rfc5545#section-3.3.10. This source supports the format requirement, not external calendar-client acceptance.

Final focused checks: 50 passed in 8.36 seconds, including 14 new cutoff cases and existing DST, calendar and deadline/feed regressions. Evidence: calendar-until-baseline.log and calendar-until-focused.log. The initial focused run found the old test's hardcoded UTC-midnight cutoff expectation; that assertion was corrected to the Chicago boundary and the focused set rerun.

Grok's prior lifecycle batch independently passed on 9b70380, ACK 5859460789: ICAL-EDIT-DELETE 5859677536, ICAL-TASK-STATE 5859677654 and ICAL-KEY-BOUNDARY 5859677802. Event 36 was intentionally deleted after same-UID edit/feed validation. Task 81 remains open and undated after complete/reopen/clear-date checks. Proper anonymous firm/user feeds returned 200; invalid and wrong-route/user keys returned 404 without event content. Existing events 28-35 and tasks 78-80 were left unchanged. Exhibits: /workspace/coil-qa/phase5/exhibits/codex-9b70380-ical-lifecycle/. Feed secrets are private. These close the three assigned server-response cases, not external calendar refresh acceptance.

Next independent queue will use fresh synthetic daily all-day and late-evening Chicago events with a finite cutoff, preserving events 28-35 and tasks 78-81. Record assignment separately from acknowledgment and acceptance.

Phase 1 remains incomplete. Portal replacement/limit/race acceptance retains issue 49 authorized Mailpit capture access; recovery retains exact-source/disposable access prerequisites. Stripe test keys, authentic handset SMS, remaining AI/browser/operator/offsite checks, external calendar subscriptions and other prior gates remain open. Productivity case 54 stays with autonomous/Cursor. No live Stripe charges, provider credential changes, GitHub push or automation schedule changes.

Full suite: 1076 passed, 1 skipped, 126 warnings in 209.99 seconds. Tested commit 5a89963d9b944d7814230ad4dd2021d5a07b1be4 was integrated by guarded fast-forward, preserving shared coordination edits. Evidence: calendar-until-full.log.

Both sites deployed and verified healthy on 5a89963. Linux candidate: 70 passed, 2 warnings in 76.52 seconds. Runtime/host calendar source SHA f51569e69b8a3001180d18fbcb706f947106a07ba613b97e5d91eb1cd0346552 matches reviewed code. Environment and Compose hashes unchanged. Source/image backups are /home/deploy/backups/coil/{domain}/calendar-until-5a89963-r1; rollback images testfirmcoillegal:before-5a89963 and democoillegal:before-5a89963. Data archives: testfirm coil-backup-20260927-204934-x09qf73y.tar.gz; demo coil-backup-20260927-205106-43j9i6g8.tar.gz. No rollback needed.

Before/after SQLite quick_check is OK. Testfirm 18 portal tokens retain SHA 6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec; events 28-35 retain SHA 1c14f952c2e3af72cd91e3595d4a4b2693a97b6539576c9dadaf4e563dde4e2d; tasks 78-80 retain SHA 0c68690fefcd88ea78ae49374e9ee176e00c25614d6287a5b820f2a0ca1bd4ec. Demo empty fixtures remain unchanged. Evidence: calendar-until-live-check.py, before/after/health JSON, prepare/activate logs.

Independent timed/all-day cutoff batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5859728817. No acknowledgment claimed at assignment.

Sheet S84 synced and exactly verified: 21 cells across five ranges. Existing statuses, formula F12, Cursor fields, portal row and Overview B2 preserved. Case acceptance remains separate from whole-tool signoff.

Final issue 12 check found no acknowledgment or result for cutoff batch 5859728817. Prior lifecycle/key cases are accepted; new cutoff acceptance remains pending.

## September 27 calendar feed lifecycle and access review, 20:12 UTC

Reviewed 2026-09-27 from aeda87d in isolated checkout /private/tmp/coil-calendar-feed-lifecycle. Application commit 9b70380 remains deployed on both sites. No application source, schema, provider settings or live fixtures changed. The local probe is tests/probe_calendar_feed_lifecycle.py, preserved as outputs/calendar-feed-lifecycle-probe.py. It uses disposable SQLite databases, synthetic contact/matter 1, users 1-3, event 1 or task 1 per fresh case, and blocks external HTTP.

Nine new cases plus 31 existing calendar regressions passed: 40 passed in 9.89 seconds. Evidence: outputs/calendar-feed-lifecycle-probe.log. Five key-boundary cases return 404 without event content: invalid key, firm key on user route, user key on firm route, user 1 key on user 2 route, and valid locally derived key for nonexistent user 999. Proper firm/owner feeds remain anonymously downloadable with text/calendar and no-cache headers. The anonymous staff edit route redirects to login. Keys are bearer access; no claim of account-deactivation revocation or per-feed rotation is made.

The event lifecycle case creates October 6, 2026, 09:00 Chicago, edits it to October 7, 11:00, and then deletes it through authenticated routes. Both fresh feeds preserve one UID across the edit, update the title and UTC time from 14:00Z to 16:00Z, then omit the deleted UID. The deleted detail page returns 404. Three task-kind cases cover task, deadline and court_date: date-only October 8 start/October 9 exclusive end; completion removes each item from both feeds; reopening restores the same UID once; clearing the due date leaves an open task outside both feeds. These are server response checks, not proof that external calendar clients refresh or remove entries correctly.

Grok independently passed ICAL-UNICODE in issue 12 comment 5859128313 and ICAL-USER-SCOPE in 5859128423, following ACK 5859094593, on 9b70380. Event 32 has the 144-character emoji/accent/Japanese title and multiline escaped notes; saved/edit forms and unfolded ICS match, with maximum physical line length 75 UTF-8 bytes. Its October 5, 09:00/10:00 Chicago times export as 14:00Z/15:00Z. Events 33, 34 and 35 belong to owner 1, other active user 20 and the firm respectively. Firm feed includes all three; owner feed excludes 34; UI all/mine/1/20 filters match. Existing events 28-31 and provider/timezone settings were left unchanged. Exhibits: /workspace/coil-qa/phase5/exhibits/codex-9b70380-ical-unicode-scope/. Feed secrets remain private.

Next independent batch: ICAL-EDIT-DELETE, ICAL-TASK-STATE and ICAL-KEY-BOUNDARY, using fresh QA-ICS-LIFECYCLE-20260927 fixtures. Existing events 28-35 and task fixtures 78-80 are protected. Assignment and acknowledgment will be recorded separately. No full calendar/tasks or phase signoff.

Phase 1 remains incomplete. Portal replacement/limit acceptance is explicitly blocked by issue 49 authorized Mailpit capture access; portal consumption race shares that prerequisite. Recovery exact-source/disposable access, Stripe test keys, authentic handset SMS, remaining AI/browser/operator/offsite checks and external calendar subscriptions stay open. Calendar API/import, recurrence DST and second-fold selection remain separate review gates. Productivity case 54 remains autonomous/Cursor-owned. No duplicate unchanged access ping, GitHub push or schedule change.

No application changes required new deployment or full-suite rerun. The prior application full suite was 1062 passed, 1 skipped on 9b70380; this run's evidence is the 40 focused checks above, not a fresh full-suite result.

Independent batch assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5859408473. Final issue 12 check found no Grok acknowledgment or result for this batch. The earlier Unicode/scope passes remain accepted.

Both public health endpoints checked this run report healthy, stable 9b70380, version demo-20260927. Evidence: calendar-feed-testfirm-health.json and calendar-feed-demo-health.json.

Sheet S83 updated and exactly verified: 21 cells across five ranges. Existing tool statuses, formula F12, Cursor fields, portal row and Overview B2 preserved. New case results are separate from full tool acceptance.

## September 27 portal single-use consumption and calendar feed review, 19:33 UTC

Reviewed from b0407d2 in isolated /private/tmp/coil-portal-consume-review. Source changes: app/blueprints/portal.py and tests/test_portal_token_concurrency.py. No schema changes. Tested and integrated9b70380c7bf9e8a50121b4d4cb73ab437dde925c by guarded fast-forward, preserving shared coordination edits. Both deployments healthy on9b70380. Synthetic local contact1 and generated token rows only, in disposable SQLite databases with mail captured in memory; no live authentication or provider requests.

Four baseline failures in2.41 seconds. A barrier after both/all four token reads lets two/four independent test clients authenticate using one token. A paused authentication read resumes after a replacement request expires that token and still signs in from its stale model. A simulated commit failure returns500 but leaves portal_contact_id in the session cookie, while token usage and audit changes roll back.

The fix releases the initial read transaction, then conditionally updates the token only if it is still unused, unexpired and portal-purpose. Exactly one updated row permits login. A zero-row competitor/replacement loser rolls back and receives410. The audit and token update commit before a portal session is created. Releasing the initial read transaction avoids upgrading an obsolete SQLite snapshot: an initial conditional-update implementation produced database-locked errors in three race cases; retained in portal-consume-first-fix-lock.log, corrected before integration.

Final focused34 checks passed with4 warnings in7.59 seconds, including deterministic2/4-consumer races, replacement versus paused read, failed commit, prior lifecycle and portal/signature regressions. Winner alone gets302/session and one audit; competitors get410/no session. Replacement loser leaves used_at unset and no login audit. Failed commit creates no session and preserves unused token/no audit. This covers these controlled interleavings; broader storage outages and concurrent replacement-request ordering are not newly certified.

Independent calendar probe:1 scenario passed in0.85 seconds, three local events1-3. Authenticated form creation and firm/owner feeds preserve a long emoji/accent/Japanese title and CRLF notes with semicolon/comma/backslash. Unfolded UTF-8 text matches exactly, all physical lines are at most75 bytes. Firm feed contains owner, other-user and firm-wide events; owner feed excludes other user while retaining firm-wide. Evidence outputs/ics-unicode-probe.py and ics-unicode-probe.log. No calendar source change or real external subscription test.

Grok public portal2 cases independently PASS5858714839 at18:49:13 UTC on stable2a159f1, ACK5858707421. Unknown synthetic email request returns200 neutral; synthetic invalid auth token returns410 and no portal session. Unauthenticated document119/matter3067 request redirects302 to /portal/login with only213-byte redirect HTML, no document content. Document/matter unchanged. Exhibits /workspace/coil-qa/phase5/exhibits/codex-2a159f1-portal-public/. Grok explicitly reports PORTAL-REPLACE and PORTAL-LIMIT BLOCKED on existing issue49 authorized Mailpit capture access; no contact1781 inbox retries, provider changes or minted tokens. Public passes do not close those cases.

New independent single-use race case shares the capture-mail prerequisite and remains deferred. No repeat access ping is needed. ICAL-UNICODE and ICAL-USER-SCOPE provide independent executable QA with fresh synthetic events and private feed URLs. No full calendar/portal or Phase1 signoff. Remaining provider, operational recovery, AI/browser, external calendar subscriptions and other prior gates stay open; productivity54 stays Cursor/autonomous. GitHub main unpushed,30-minute automation unchanged.

Full suite:1062 passed,1 skipped,126 warnings in210.13 seconds. Evidence portal-consume-baseline.log, portal-consume-first-fix-lock.log, portal-consume-focused.log and portal-consume-full.log. The calendar probe is preserved separately in workspace outputs, not a source change.

Linux candidate:55 passed,2 warnings in69.49 seconds. Both public/container health endpoints report9b70380. Host/runtime portal source SHAc01bb908f2f9178bdd003ff82eef53e7a1dca21f94786e7f34448486c1497bda matches reviewed source; environment/Compose hashes unchanged. Backups /home/deploy/backups/coil/{domain}/portal-consume-9b70380-r1 retain source, build/tests and state. Rollback images testfirmcoillegal:before-9b70380 and democoillegal:before-9b70380. Data archives: testfirm data/backups/coil-backup-20260927-192603-6jfjw2mc.tar.gz; demo data/backups/coil-backup-20260927-192725-5887_m8k.tar.gz. No rollback required.

Before/after SQLite quick_check passed. Testfirm18 token rows retain SHA6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec; calendar28-31 retain SHA9ae19ae90dc5b7dfecc94d61a8ab54eec9931e4a9243a0cc9d9ed93d92474a31. Demo empty fingerprints unchanged. No live token consumption, fixture mutation, provider changes or GitHub push. Evidence portal-consume-live-check.py, before/health JSON files and prepare/activate logs.

Independent retest batch assigned in issue 12 comment 5859083560: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5859083560. ICAL-UNICODE and ICAL-USER-SCOPE are executable with fresh synthetic events. PORTAL-CONSUME-RACE remains deferred under the existing capture access prerequisite. Assignment is not acknowledgment.

Final issue check: Grok acknowledged both new calendar cases in 5859094593 on testfirm 9b70380, retaining the deferred portal race. No calendar result observed yet. This is acknowledgment, not acceptance.

Sheet S82 synced and exactly verified: 21 cells across 7 ranges. Existing status/formula cells, Cursor fields and Overview B2 preserved. Calendar acknowledgment 5859094593 recorded separately from a result. No full tool or phase signoff.

## September27 portal login-link lifecycle and calendar acceptance,18:44 UTC

Reviewed from b3c4df2 in /private/tmp/coil-portal-link-review. Files: app/blueprints/portal.py and tests/test_portal_link_lifecycle.py. No schema changes. Tested and integrated2a159f1ca85ed00c5e163f3fd95a3c6636574277 by fast-forward, preserving shared coordination edits. Both deployments healthy on2a159f1. Local synthetic contact1/2, matter1, document1 and generated token rows belong only to disposable databases; no live token values appear in evidence.

Six baseline failures, four controls passed. Requesting a replacement sign-in link left the previous link usable, including after a logged-only or failed mail attempt. Earlier links also remained valid after three requests and a rate-limited fourth. Three card-purpose tokens incorrectly exhausted the portal's three-per-15-minute login limit. A frozen-clock control accepted a link at exactly expires_at.

The fix expires older unused portal-purpose links for the selected contact when an eligible new request is created. It leaves used_at unchanged, keeps other contacts/card links intact, and changes the expiry check to reject equality. Only portal-purpose rows count toward the login limit. A fourth rate-limited request creates nothing and leaves the newest valid link intact. Replacement and new-token changes commit together. Existing neutral confirmation and logged/failing mail behavior are preserved; this is not proof of real message delivery, concurrent single-use consumption or cross-worker race handling.

Ten new synthetic cases plus existing portal/signature/money regressions passed,36 total in8.02 seconds. Mail is captured in memory and external HTTP disabled. Controls also document shared-email behavior: client records rank before nonclients; among clients the lowest contact ID wins. No chooser, combined identity or shared-inbox redesign is claimed. Unsharing a document blocks its next download even in an already authenticated session. A closed matter's still-shared document remains on the client's portal and downloads correctly.

Grok CAL-GAP-CREATE, CAL-GAP-EDIT and CAL-DST-CONTROLS independently PASS5858401749 at18:06:30 UTC on stablecbf3617, ACK5858377161. Fresh events28-31 on matter3071, tagQA-DST-GAP-20260927. Event28 saved only after rejecting Chicago March8,2026 start02:30, explicit end02:30 and generated end02:30; corrected01:30/03:30 exports07:30Z/08:30Z. Event29 invalid edits retain draft and original09:00/10:00, including a server-submitted empty Starts without500; valid09:30/10:30 correction persists. Event30 fall-back01:30/02:30 exports06:30Z/08:30Z; event31 all-day March8 exports date-only March8/March9. Firm timezone, billing/provider settings and old queues unchanged. Exhibits /workspace/coil-qa/phase5/exhibits/codex-cbf3617-dst-gap/. These close the three assigned cases, not full calendar acceptance.

Issue49 remains an access block. Its existing operator finding confirms Mailpit captured contact1781's messages on September24; the real inbox did not receive them because capture is the configured default. No send-code defect or credential change is needed for that finding. New replacement/limit independent acceptance requires authorized capture-mail read access and stays blocked. Do not repeatedly request links or relay email without the required access/authorization. Public invalid-token/neutral-confirmation and anonymous-download checks can run independently.

Phase1 incomplete. Portal mobile/keyboard/screen-reader, payment prerequisites, actual captured-link replacement acceptance, calendar API/import/recurring DST and external subscriptions, recovery exact-source/disposable access, Stripe test keys, authentic handset SMS and remaining AI/operator/offsite gates stay open. Productivity54 stays with Cursor/autonomous. No Phase2/3 signoff, GitHub main unpushed,30-minute schedule unchanged.

Full suite:1058 passed,1 skipped,126 warnings in208.70 seconds. Logs portal-links-baseline.log, portal-links-focused.log and portal-links-full.log. No GitHub push.

Linux candidate:51 passed,2 warnings in61.37 seconds. Both public/container health endpoints report2a159f1. Host/runtime portal source SHA33715bbbb56b6b4a84dc66857ada56c949c73fe84679285bb25fdc7e554326ff matches reviewed source. Environment/Compose hashes unchanged. Backups under /home/deploy/backups/coil/{domain}/portal-links-2a159f1-r1; rollback images testfirmcoillegal:before-2a159f1 and democoillegal:before-2a159f1. Data archives: testfirm data/backups/coil-backup-20260927-184113-bn3hd8r_.tar.gz; demo data/backups/coil-backup-20260927-184227-t0vdrv7z.tar.gz. No rollback required.

Before/after SQLite quick_check passed. Testfirm18 portal token rows retain SHA6f6af2b70d1f0c940c8fb5961e6905fca5e5617c16ac36e2fdaf97e0d9af50ec; calendar events28-31 retain SHA9ae19ae90dc5b7dfecc94d61a8ab54eec9931e4a9243a0cc9d9ed93d92474a31. Demo empty fingerprints unchanged. Existing token rows, fixtures and provider credentials were not changed during deployment; future eligible login requests apply replacement behavior. Evidence portal-links-live-check.py, prepare/activate logs and both before/health JSON files.

Independent queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5858679282. PORTAL-PUBLIC-ERRORS and PORTAL-ANON-DOWNLOAD assigned, no acknowledgment observed at assignment. New PORTAL-REPLACE/LIMIT cases explicitly blocked on existing issue49 capture-mail access; no retry of contact1781 or request to alter shared SMTP. Public route passes cannot close those gates.

Sheet S81 synced and exactly verified at2026-09-27 18:46 UTC:21 cells across7 ranges. Fresh reads and RAW writes preserve prior case evidence, Overview B2, Cursor fields, statuses, Tools F12 formula and formatting. Evidence portal-links-sheet-latest.json, portal-links-sheet-changes.json and portal-links-sheet-readback.json. Final issue12 check found no new Grok acknowledgment/result for5858679282. Public2 remain assigned; replacement/limit acceptance remains explicitly blocked.


## September27 calendar form fix and deadline acceptance,18:00 UTC

Reviewed from b761ce5, isolated /private/tmp/coil-calendar-gap-review. Application changes: app/blueprints/calendar.py and tests/test_calendar_dst_gap.py. No schema changes. Tested and integrated cbf3617a56d989b5247797ad7357cf40f6f570ea on local main, preserving the existing coordination edits. GitHub remains unpushed. Both deployments are healthy on cbf3617.

Nine baseline failures, six controls passed. Eight failures reproduce nonexistent start/end times accepted by the create/edit routes: Chicago March8,2026 02:30, explicit end02:30, generated end02:30 from start01:30, and Lord Howe October4,2026 02:15. A ninth failure reproduces clearing Starts on edit: a query flushes the invalid model before the form can render and raises a NOT NULL database error. Before the fix, Chicago02:30/03:30 exports both endpoints as08:30Z, so an accepted one-hour wall-clock entry has zero exported duration.

The forms validate each timed endpoint by converting from the firm's timezone to UTC and back. A changed wall time receives a field-specific error, with the draft retained and no saved mutation. Invalid edits render without autoflush and roll back. The existing timezone-configuration fallback and fall-back first-occurrence policy are preserved. All-day events bypass timed validation. Corrected submissions save normally without a rejected-attempt duplicate.

Focused validation:29 passed in8.85 seconds. This includes15 new tests and existing module-A/small-feature tests. The new controls cover a valid spring transition crossing01:30/03:30 (07:30Z/08:30Z),03:00boundary, fall-back01:30/02:30 (06:30Z/08:30Z), Phoenix/UTC no-gap controls, all-day transition date and missing-start edit handling. Synthetic databases only, external HTTP disabled. Full suite:1048 passed,1 skipped,126 warnings in204.54 seconds. Linux candidate:56 passed,2 warnings in75.95 seconds. Logs calendar-gap-baseline.log, calendar-gap-focused.log, calendar-gap-full.log and calendar-gap-prepare.log.

Scope limits: these are calendar create/edit form fixes. Old saved events are not rewritten. API/import validation, generated recurring occurrences across DST, explicit second-occurrence selection at fall-back, and external Outlook/Google/Apple subscriptions are not established by these cases. No calendar tool-wide acceptance is claimed.

Grok DEADLINE-MONTH-END and DEADLINE-LEAP-YEAR independently PASS5858024701 at17:16:59 UTC on stable74ffffc, ACK5858001279. Fresh ruleset5 with rules25/26 on QA event, rolling off: matter3101/contact1840, Jan31 trigger previews Feb28/Mar31; task78 retains month-end explanation and alternativeMar3, task79 has Mar31; both open/overdue, replay Added0/Skipped2. Rule27 on QA leap event, matter3102/contact1841: Feb29,2024 trigger gives task80 dueFeb28,2025 with alternativeMar1; open/overdue, replay Added0/Skipped1. Source notes retained; no shared holiday or earlier-fixture changes. Exhibits /workspace/coil-qa/phase5/exhibits/codex-74ffffc-deadline-arith/. These two cases are accepted separately from full calendar signoff.

Remaining priorities: independent calendar form/ICS batch after deployment; productivity Case54 stays with the existing Cursor/autonomous queue; operational recovery cases require exact-source/disposable access. Stripe test access, authentic handset SMS, remaining AI/browser evidence, operator/offsite recovery, producer-version metadata/refusal and other prior gates remain open. Phase1 incomplete, no Phase2/3 signoff, GitHub main unpushed and30-minute schedule unchanged.

Deployment verified September27,18:00 UTC. Both container and public health report cbf3617. Host/runtime calendar source SHA3181bf592bb050b3bc89cda2ed33c4a75777039181435981f95b3686c69ec054 matches reviewed source. Environment and Compose hashes are guarded and unchanged. Backups under /home/deploy/backups/coil/{domain}/calendar-gap-cbf3617-r1 with source, build/test logs and state; rollback images testfirmcoillegal:before-cbf3617 and democoillegal:before-cbf3617. Data archives: testfirm data/backups/coil-backup-20260927-175630-f2uliaym.tar.gz; demo data/backups/coil-backup-20260927-175758-mmr_5sxm.tar.gz. No rollback required.

Read-only SQLite checks passed before/after. Testfirm27 calendar rows retain SHA6f8b05a04e762ae43d510893ffda21861d384f071feca921f982c93972ec109f; tasks78-80 retain SHA0c68690fefcd88ea78ae49374e9ee176e00c25614d6287a5b820f2a0ca1bd4ec. Demo has no corresponding rows and empty fingerprints remain identical. No live fixture or provider mutation. Evidence calendar-gap-live-check.py, both before/health JSON files and calendar-gap-activate.log.

Independent batch CAL-GAP-CREATE, CAL-GAP-EDIT and CAL-DST-CONTROLS requires fresh QA-DST-GAP-20260927 events, unchanged America/Chicago configuration, exact validation and persisted-state checks, UTC feed endpoints and all-day/fall-back controls. Draft in calendar-gap-retest-queue.md. Assignment is5858352373; no acknowledgment observed at assignment.

Assigned https://github.com/Coil-Legal/coil/issues/12#issuecomment-5858352373. No acknowledgment observed at assignment. A scheduled check is not evidence that Grok has started.

Sheet S80 synced and exactly verified at2026-09-27 18:01 UTC:16 cells across5 ranges. Fresh reads and RAW writes preserved earlier evidence, Overview B2, Cursor J10/K10, formulas and formatting. Evidence calendar-gap-sheet-latest.json, calendar-gap-sheet-changes.json and calendar-gap-sheet-readback.json. Final issue12 check found no new Grok acknowledgment/result for5858352373 or related new issue. Assignment remains unacknowledged.


## September27 deadline boundaries and conflict acceptance,17:10 UTC

Reviewed committed971d411/application74ffffc in /private/tmp/coil-deadline-review-971d411 at2026-09-27 17:10 UTC. No application source change, deployment, provider action, live rule/holiday/fixture mutation or GitHub push. Synthetic local rule set/rule96001 and matter1 belong only to disposable test databases.

Six new route/configuration cases plus20 existing month-arithmetic checks passed,26 total in2.94 seconds. Authenticated preview and POST application agree for January31 2026 plus one month without rolling (February28); February29 2024 plus one year (February28 2025); January31 2027 plus one month with weekend rolling (March1); May15 2026 minus three months (February15); and an already-past January10 2000 plus one calendar day (January11). Persisted tasks retain original trigger, source rule, synthetic rule note and applicable construction warning. The January case retains alternate March3, the leap case alternate March1, and the rolled case the pre-roll February28 explanation. Repeated identical application creates only one task per rule/trigger. Past unfinished tasks show overdue on task detail and the rule application history.

Holiday controls: with no configured holidays, the preview warns that only weekends are skipped; one court day after November25 2026 lands on November26. Explicit synthetic closures on November26/27 move that case to November30; one court day before November30 then lands on November25. These are configured date-arithmetic checks, not certification of federal or local court holidays. The old review-register statement that holidays are not modeled was stale: Holiday rows, owner-managed entries and a US-federal load action exist. Corrected the register to distinguish configured holiday support from court-specific completeness. The no-holidays warning checks whether the table is empty, not coverage of each jurisdiction/year.

Evidence: outputs/deadline-acceptance-probe.py and deadline-acceptance.log. Local HTTP integrations disabled by the inherited synthetic fixture. These cases do not establish actual court-rule applicability, calendar-client subscription behavior, DST-gap handling or full calendar signoff. Existing full1033 passed/1 skipped and44 deployment-container checks remain the deployed source validation; no code change required another full suite.

Grok CONFLICT-TWO-ROLES, CONFLICT-ROLE-ORDER and ALIAS-SAVED-HISTORY independently PASS5857910912, ACK5857774417, on stable74ffffc. Fresh contacts1836/1837, matter3099 M-1075, party12 adverse then13 witness, saved87 retains both and stays unresolved. Independent contacts1838/1839, matter3100 M-1076, party14 witness then15 adverse, saved88 retains both; duplicate adverse16 still yields exactly two distinct role hits in saved89. Read-only checks82/85 continue to exclude1834/1835 respectively, while83/86 retain post-alias hits. Existing1833-1835 and77-86 preserved. Exhibits /workspace/coil-qa/phase5/exhibits/codex-74ffffc-conflict-roles/. These close the assigned role/history cases, not the whole tool.

New independent deadline batch https://github.com/Coil-Legal/coil/issues/12#issuecomment-5857978175: DEADLINE-MONTH-END and DEADLINE-LEAP-YEAR. Requires fresh synthetic rules/matters only, rolling disabled, exact preview/persisted dates and warnings, duplicate-skip feedback, overdue indicators and actual live IDs. No shared holiday edits. Assigned, no acknowledgment observed at assignment. Existing independent passes remain recorded; expanded deadline acceptance awaits results.

Phase1 remains incomplete. Automatic Greek/Cyrillic transliteration is not built. Operational recovery exact-source/disposable access, Stripe test access, authentic handset SMS, remaining AI/browser evidence, operator/offsite recovery and external calendar subscriptions remain blocked/pending. Productivity Case54 stays with the existing autonomous/Cursor queue. No Phase2/3 signoff. The30-minute automation is unchanged.


Sheet S79 synced and exactly verified at 2026-09-27 17:14 UTC:24 cells across7 ranges. Fresh reads and RAW writes preserve earlier evidence, Overview B2, Cursor J/K cells, formulas and formatting. Expanded deadline scope remains QA pending. Evidence deadline-sheet-fresh.json, deadline-sheet-changes.json and deadline-sheet-readback.json. Final issue12 check found no new acknowledgment/result for5857978175.

## September27 same-matter conflict roles,16:34 UTC

Tested and integrated74ffffc04e5ba4567f103b973d00cb56f8be98e9 from isolated /private/tmp/coil-conflict-role-review, preserving shared26ae436 and the existing coordination changes. Application changes are limited to app/blueprints/conflicts.py and tests/test_conflict_multiple_roles.py. No schema changes or GitHub push.

Reproduction through authenticated routes: adding the same name twice on one matter, adverse then witness, saved only adverse in the conflict result. Reversing insertion order saved only witness. The database retained both party rows; search deduplication dropped the second distinct role because its key contained only query/source/URL/label. Two corrected baseline cases failed on the missing-role assertion; a same-role duplicate control passed. An initial harness error used ConflictCheck.query as a query object despite it being a model column; fixed to db.session.query, retained in conflict-role-harness-first.log, and not counted as a product failure.

Fix includes role in the deduplication key. Both different roles survive regardless of insertion order; identical same-role duplicates still collapse. New saved checks render both roles and remain unresolved. Existing saved checks are historical snapshots and are not rewritten; rerun a search to use the updated matcher. No provider, financial or live-fixture mutation is required by this change.

Validation:12 focused passed,32 deselected, in4.20 seconds; full1033 passed,1 skipped,126 warnings in199.77 seconds;44 candidate Linux checks passed with2 warnings in58.26 seconds. Files conflict-role-baseline.log, conflict-role-focused.log, conflict-role-full.log and conflict-roles-prepare.log. Scope reviewed before fast-forward integration, shared source remained unchanged by other agents during this fix.

Backups prepared for both apps under /home/deploy/backups/coil/{domain}/conflict-roles-74ffffc-r1, including old source, build/test logs and deployment state. Rollback images testfirmcoillegal:before-74ffffc and democoillegal:before-74ffffc. Testfirm data archive data/backups/coil-backup-20260927-163017-tlkaz8xx.tar.gz; demo data/backups/coil-backup-20260927-163131-e8bcr4ux.tar.gz. Environment and Compose files are guarded and preserved. Deployment status and final checks will be appended after activation.

Grok corrected ALIAS-EMAIL-EVIDENCE, ALIAS-CYR-CONTROL and ALIAS-GREEK-CONTROL independently PASS5857571253, ACK5857488448 on stable01bfaec. Email hit in saved78 and extra alias hit79 confirmed; prior1833 FAIL remains an explained fixture expectation, not a transliteration defect. Fresh1834 Cyrillic exact81, pre-alias ASCII82 absent own contact, post-alias83 present; fresh1835 Greek84, ASCII85 absent own contact, post-alias86 present. Existing77-80 preserved. Source evidence /workspace/coil-qa/phase5/exhibits/codex-01bfaec-alias-controls/. Names/roles across different matters remain passed5857130378.

One requested detail remains independently unproven: Grok checked old77-80 after aliases, not explicitly the actual pre-alias82/85 snapshots. Read-only follow-up ALIAS-SAVED-HISTORY requires82 still excludes1834 and85 excludes1835, while83/86 retain post-alias hits. New independent fix cases CONFLICT-TWO-ROLES and CONFLICT-ROLE-ORDER require fresh synthetic matter/party IDs, both insertion orders, reopened results and same-role duplicate control. Draft queue is outputs/conflict-role-retest-queue.md, to be posted after verified deployment.

Automatic Greek/Cyrillic transliteration remains not built. Whole conflict-tool acceptance and Phase1 remain incomplete. Recovery exact-source/disposable access, Stripe test access, authentic handset SMS, remaining AI/browser, operator/offsite and recovery gates stay open. Productivity Case54 remains with the autonomous/Cursor queue. No Phase2/3 signoff. The existing30-minute automation is unchanged.

Deployment verified16:34 UTC: both public health endpoints and containers healthy74ffffc, host/runtime source SHA6c01d010251e76ee3f2041a615c7a09446f66af6fd3914310f4176d91cc91d83 matches the candidate. Environment/Compose hashes unchanged. SQLite quick_check ok. Testfirm14 saved checks73-86 retain SHA55d44676dc10389e67945e7270b595c583584ee7f29f76a3d3f6dc8ed7daa178; demo has none, its empty fingerprint unchanged. No rollback required. Transient startup connection refusals resolved during polling. Python urllib public probe received403; curl verified both public endpoints successfully. Evidence conflict-roles-activate.log, conflict-roles-testfirm-health.json, conflict-roles-demo-health.json and both before fingerprints.

Independent batch posted https://github.com/Coil-Legal/coil/issues/12#issuecomment-5857712390. Assigned, no acknowledgment observed at assignment.


Sheet S78 synced and exactly verified at16:36 UTC:16 cells across5 ranges, fresh reads and RAW writes. Prior case history, Overview B2, Cursor J9/K9, formulas and formatting preserved. Evidence conflict-roles-sheet-beforewrite.json, conflict-roles-sheet-changes.json and conflict-roles-sheet-readback.json. Final issue12 check found no new Grok acknowledgment or result for5857712390; independent acceptance remains pending.

## September27 conflict email discrepancy,15:53 UTC

Reviewed shared2a640a7, application01bfaec, at2026-09-27 15:53 UTC. No application source changes, deployment, provider calls, live mutations or GitHub push. Read-only inspection was restricted to synthetic contact1833 and saved conflict checks77-80. The deployed and isolated conflicts.py match SHA256 8d200e4169e2624439a604632eb5551192db727529ba5c701b77ee379ac7c93a.

Grok report5857130378 independently passes CONFLICT-NAMES and CONFLICT-ROLES on stable01bfaec, acknowledgment5857094036. Contacts1828 Mira Vale-Wren,1829 Owen J Caspian III and1830 Nguyễn Minh match their assigned variants after reopening checks73/74/75. Nguyen also matches contacts1423/1583; that is recorded as additional fuzzy output, not silently ignored. Contact1831 Tessa Quenby is client on matter3097 and adverse on matter3098 for other client1832. Check76 retains both links/roles and remains unresolved. These are case passes, not whole-tool signoff.

Grok marked CONFLICT-ALIASES FAIL because ASCII Irina Volkova already found contact1833 before an alias. The saved evidence explains it: check78 contains only the email-labeled hit Ирина Волкова <irina.volkova.qa-conflict-20260927@example.com>, score100. The search normalizes punctuation to spaces, so Irina Volkova is a substring of that email. Check79 after adding the alias contains both a name-only hit and the email hit. Exact Cyrillic checks77/80 also hit. This is email matching, not automatic transliteration. The original failed test expectation remains recorded; its precondition was confounded by an independently indexed field.

Three isolated disposable cases passed in2.28 seconds using synthetic contact95001: the exact live email produces the pre-alias hit with match=email and score100; a neutral email and blank email do not. Explicit ASCII aliases then produce a name-only score100 hit in all three cases. Reloading each earlier saved check after the alias update preserves its original result JSON exactly. Source unchanged from the prior15 new and9 existing conflict checks. No new full suite required for this probe/documentation review; prior deployed1030 passed/1skipped and31 container checks remain the source validation.

Evidence: outputs/conflict-alias-live-inspect.py, conflict-alias-live-inspection.json, conflict-email-boundary-probe.py, conflict-email-boundary.log and conflict-email-boundary-results.jsonl. Source/probe directory /private/tmp/coil-conflict-review-d077ce3, same application source as current2a640a7. External HTTP disabled for local probes. Local95001 is not a live fixture ID.

Corrected independent batch assigned https://github.com/Coil-Legal/coil/issues/12#issuecomment-5857398674: ALIAS-EMAIL-EVIDENCE (read-only checks78/79), ALIAS-CYR-CONTROL and ALIAS-GREEK-CONTROL (fresh tagged synthetic contacts, neutral/blank emails, own-contact matches before/after aliases and immutable saved history). Each has separate acceptance criteria and requires actual IDs. Assigned, no acknowledgment observed at assignment. Do not infer a start from this scheduled run. Preserve existing1833 and historical checks.

Working in observed cases: exact-script, diacritic, name variants, cross-matter roles, indexed-email and explicit-alias matching; persisted snapshots. Not built: automatic Greek/Cyrillic transliteration. Pending: independent clarification and controlled script cases; full conflict false-positive/scale coverage. Productivity Case54 remains defective with existing Cursor/autonomous ownership. Recovery exact-source/disposable access, Stripe test credentials, authentic handset SMS, remaining AI/browser and operator/offsite gates remain open. Phase1 incomplete; no Phase2/3 or new tool-wide signoff. The30-minute schedule remains unchanged.


Sheet S77 synced and exactly verified:16 cells across5 ranges, fresh read before RAW writes. Overview B2, prior case history, Cursor J9/K9, formulas and formatting preserved. Evidence alias-sheet-fresh.json, alias-sheet-changes.json and alias-sheet-readback.json. Final issue12 check found no new Grok acknowledgment or result for5857398674.

## September27 conflict boundaries and independent rounding acceptance,15:14 UTC

Reviewed committed d077ce3 in isolated /private/tmp/coil-conflict-review-d077ce3. Application release remains 01bfaec. No application source change, deployment, live mutation, provider action or GitHub push.

Fifteen disposable synthetic checks passed in 4.74 seconds. Contacts94001 to94014, matters94001/94002 and adverse party94001 exist only in the probe database. Cases cover hyphen versus spaces; absent middle initial and suffix; Jr versus III as a possible fuzzy match; a company and person sharing Nordvale; company-only and employer fields; Vietnamese diacritics; Greek/Cyrillic exact script; uppercase/whitespace; separate duplicate-name contacts with different email addresses; and Lee, Brown, Long and Young against this small control set. Exact expected contact sets passed. This small corpus does not establish false-positive rates or large-data performance.

Tessa Quenby, contact94005, remains a client hit and an adverse-party hit on matter94002. The saved check stays unresolved and its authenticated HTML contains both links. This verifies different roles across matters, not every combination of multiple roles on one matter.

Automatic transliteration is NOT BUILT. Cyrillic contact94007 (Ирина Волкова) did not match ASCII Irina Volkova; Greek94008 (Νίκος Παπαδόπουλος) did not match Nikos Papadopoulos. Both stored checks returned clear before an explicit alias. After adding each ASCII spelling to aliases, both returned unresolved with score100. These are observed product boundaries, not successful automatic transliteration acceptance. Exact-script search and explicit alternate names work for these fixtures. A clear result is only a result for the supplied spelling.

Evidence: outputs/conflict-acceptance-probe.py, conflict-acceptance.log and conflict-acceptance-boundaries.json. External HTTP disabled by the inherited independent-review fixture. The disposable database and provider settings are separate from live data. No new full suite was needed for a probe/documentation-only change; prior deployed source validation remains1030 passed/1 skipped and31 deployment-container checks.

Grok REAL-ROUND-A/B/CSV independently PASS5856816233 on stable01bfaec, following ACK5856799194. EUR fixtures3095/invoice3067/payment14 and3096/invoice3068/payment15 report collected1/2 cents, invoice balances1 cent each, collection50%/66.7%. September CSV EUR200.05/0.05/0.03 with collection60%, USD313587.27/114723.89/1550.66 with collection1.4%, CAD417.08/417.08/0 with collection0%. Matter sums reconcile, protected unbilled3093/3094 remain unchanged. Exhibits /workspace/coil-qa/phase5/exhibits/codex-01bfaec-real-round/. Those cases are accepted, not the full realization or multi-currency tool.

New independent batch CONFLICT-NAMES, CONFLICT-ROLES and CONFLICT-ALIASES is in outputs/conflict-retest-queue.md. Requires fresh tagged synthetic records and separate results with actual live IDs, saved-check evidence and tested health commit. Local94001+ IDs must not be mistaken for live fixtures. Assignment is not acknowledgment.

Remaining priorities: independent conflict UI results; operational recovery cases after exact-source/disposable access; productivity Case54 with its existing Cursor/autonomous queue. Stripe test access, authentic handset SMS, remaining AI/browser acceptance, operator/offsite recovery, producer-version metadata/refusal and other recovery gates remain open. Phase1 incomplete. Phase2/3 and tool-wide statuses are not newly signed off. The existing30-minute automation remains unchanged.

Nine existing conflict/intake-gate regressions also passed,32 deselected, in3.19 seconds (conflict-existing-regressions.log). Independent assignment https://github.com/Coil-Legal/coil/issues/12#issuecomment-5857087371 posted15:13 UTC. No acknowledgment observed at assignment.



Sheet S76 synced and exactly verified at15:17 UTC: seven ranges/24 cells. Fresh reads preceded RAW updates. Historical case evidence, Overview B2 and Cursor J/K cells retained; formulas and formatting untouched. Expanded conflict status is QA pending until new independent evidence arrives, with earlier signoff retained in history. Evidence conflict-sheet-fresh.json, conflict-sheet-changes.json and conflict-sheet-readback.json.
Final check: Grok acknowledged all three conflict cases in5857094036 at15:15 UTC on01bfaec. Results remain pending. Sheet acknowledgment update fresh-read and exactly verified in3 cells; evidence conflict-ack-fresh.json and conflict-ack-readback.json. Review documentation commit3a3ca13 is local and unpushed.


## September27 realization receipt rounding,14:34 UTC

Tested, integrated and deployed01bfaecb534837f8b58ff5437c04e590cb30d3aa. Reviewed shared7ea8343 and the autonomous loop's completed realization70 deploymentc2f1ef6 before editing. Isolated checkout /private/tmp/coil-realization-review. Changed only app/blueprints/reports.py and new tests/test_realization_rounding.py. No schema changes. GitHub main remains unpushed.

Independent review reproduced a separate rounding defect: a one-cent receipt over two equal time entries reported zero collected; two cents over three entries reported three. Five baseline regression failures cover conservation, date-window consistency, expense separation and CSV output. New helper allocates each invoice's combined time share with exact fractions, rounds that share once, and distributes remaining whole cents by fractional remainder with stable entry-ID ordering. Allocation includes all dates before applying the report date filter. Split-payer invoices are allocated separately, legacy entries without source lines remain supported, and expense shares are not counted as collected time.

Validation:31 focused passed; full1030 passed,1 skipped,126 warnings in201.51 seconds;31 candidate deployment-container checks passed in29.88 seconds. Additional controls cover split payers, imported legacy entries, full payments and void invoices. Source SHA ba506f5916a006a415489ee8d651eb1c37530536e98f85056fccf226c32c87a8. Fast-forward integration preserved the autonomous c2f1ef6 commit and shared coordination changes. Evidence realization-rounding-baseline.log, realization-rounding-focused-final.log, realization-rounding-full.log and realization-rounding-prepare.log.

Two new synthetic testfirm cases independently reproduced the baseline before deployment. Contact1827; matter3095 QA-RND-20260927-A, invoice3067 QA-RND-INV-A-20260927, time41564/41565, check payment14: total2 cents, paid1, balance1, reported collected0 before and1 after. Matter3096 QA-RND-20260927-B, invoice3068 QA-RND-INV-B-20260927, time41566/41567/41568, check payment15: total3 cents, paid2, balance1, reported collected3 before and2 after. CurrencyEUR, datesSeptember27. These are synthetic check records; no funds transferred, provider request or client message. Existing protected invoice fingerprints3044/3048/3064/3065/3066 unchanged at fixture creation. Auto invoicing disabled on the two new matters. Existing3093/3094 time41562/41563 remain unbilled and unchanged. Evidence create-realization-rounding-fixtures.py and realization-rounding-fixtures.json.

Both public sites and container health report healthy01bfaec. Host/runtime report hashes match candidate; environment and Compose hashes unchanged. No rollback needed. Source/state/build/test backups under /home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/realization-rounding-01bfaec-r1. Rollback images testfirmcoillegal:before-01bfaec and democoillegal:before-01bfaec. Data backups created for both sites; the latest testfirm backup includes the new fixtures: data/backups/coil-backup-20260927-143115-isvvui9k.tar.gz. Logs realization-rounding-prepare.log, realization-rounding-fixture-backup.log, realization-rounding-activate.log. Temporary startup connection refusals resolved within health polling.

Read-only deployed verification: A/B collected1/2 cents, invoice balances1 cent each. September totals CAD worked41708/billed41708/collected0; EUR worked20005/billed5/collected3; USD worked31358727/billed11472389/collected155066, all integer cents. Matter totals equal report totals. EUR collection60.0%; no invented zero-denominator percentage. Demo has no time rows for this range. This is local/live engineering evidence, not independent acceptance.

Grok REAL70-HTML/CSV/PCT independently PASS5856714125 on stablec2f1ef6, ACK5856701004, assignment5856682966. Currency totals, separate hour sums, fixture3093 USD100/3094 EUR200 and percentage ratios passed. These passes stand for those cases; they did not exercise the new partial-cent defect. Grok exhibits /workspace/coil-qa/phase5/exhibits/codex-c2f1ef6-real70/.

Independent new batch https://github.com/Coil-Legal/coil/issues/12#issuecomment-5856754854: REAL-ROUND-A, REAL-ROUND-B and REAL-ROUND-CSV, all read-only and executable independently. Exact IDs, expected receipt/report values and rounding percentages provided. Assigned, no acknowledgment or result observed at assignment. Preserve all fixtures; no additional payments/credits/billing/send/void actions. Productivity Case54 remains unresolved with the existing autonomous/Cursor queue. No full multi-currency or realization-tool signoff.

Phase1 remains incomplete: Stripe test access, authentic handset SMS, remaining AI/browser evidence, independent operational exact-source/disposable access, operator/offsite recovery and remaining recovery gates stay open. Producer-version metadata/refusal and automatic SIGKILL cleanup remain not built. No Phase2/3 signoff.30-minute schedule unchanged.


Sheet S75 synced and exactly verified at14:36 UTC: five ranges/16 cells. Fresh reads preceded updates; historical evidence, Overview B2, Cursor Tools J29/K29, formulas and formatting preserved. Evidence realization-rounding-sheet-fresh.json, realization-rounding-sheet-changes.json and realization-rounding-sheet-readback.json. Final issue12 check found no new rounding acknowledgment/result; assignment remains pending.

## September27 financial restore compatibility,13:50 UTC

Reviewed shared 7c7a01d and restore eec47ab, SHA df1adac4d87ff82cc7bc7bf70f44bf7e42964e662523aeb920415cae98a27675. Used isolated git archives of committed sources, never the autonomous realization working copy. No application source edits, deployment, live restore, app restart, provider request or financial mutation. External HTTP disabled and synthetic configuration only.

Two local application-level cases passed: CLI backup produced by40b4c35 restored into7c7a01d, and CLI backup produced by7c7a01d restored into the same commit. Fixture QA-RESTORE-FINANCIAL-20260927, IDs93001/93002/93003 in disposable databases, one separate client/matter/invoice per USD/EUR/GBP. Each invoice retains total10001, payment2501, issued credit1000, balance6500, statuspartial and its currency. A void99-cent credit stays void and excluded. Separate trust deposit10000/disbursement2501 retain7499 cents per matter. These are stored synthetic ledger rows, not live payment or trust workflow execution.

Restored statements independently reconcile10001 to7500 to6500 in their own currencies, with payments2501 and credits1000. Invoice pages and authenticated document downloads return200; all three upload byte strings and a generated control PDF match the original hashes. PDF byte preservation is verified, not rendered PDF layout. Restored database bytes match the archived snapshot before app startup; integrity isok. A second fresh Python app startup preserves all six financial/document table snapshots and the observed balances/files exactly. The login audit may add audit entries; those are outside the six preserved tables.

Evidence: outputs/restore-financial-worker.py, restore-financial-probe.py, restore-financial.log and restore-financial-results.json. The first harness attempt treated trust_balance_cents as a property; corrected to call the method before running both complete cases. The failed harness log is retained as restore-financial-harness-first.log. No product defect was inferred from that harness error. Disposable databases, archives and isolated sources were removed after recording hashes/results.

The actual CLI archive member lists contain database/uploads/PDF only, despite an explicit producer commit in app health. No producer-version manifest or archived environment is present. Source review of ops/backup.sh likewise finds database/uploads/PDF/optional environment but no release manifest. Restore validates database integrity and layout, not producer/consumer compatibility. Automatic version metadata and refusal remain NOT BUILT. Prior unsupported downgrade evidence remains applicable; these two successful paths do not establish arbitrary upgrade/downgrade compatibility. Keep the producer commit/image with the archive and restore matching application code first.

Issue12 and related findings checked this run: no new Grok reply since the prior handoff5856149070. PROFIT69-PCT remains independently passed5855896593, acknowledged5855891012. Operational recovery cases remain BLOCKED/deferred for exact-source/disposable access, with no start or acknowledgment inferred. No duplicate unchanged ping or assignment posted. Prioritized queue remains PUB-ENOSPC/PUB-BOUNDARY and other operational cases after access, then report retests after completed autonomous deployment handoffs. Case54 productivity and realization70 remain defective/loop-owned.

Phase1 remains incomplete. Working: these two local financial restore cases. Not built: producer metadata/refusal and automatic SIGKILL cleanup. Blocked/pending: independent operational acceptance, operator/offsite recovery, Stripe test access, authentic handset SMS, remaining AI/browser acceptance. Power-loss durability, untrusted archive and concurrent-writer acceptance remain open. No Phase2/3 or full-tool signoff. The prior full1017 passed/1skipped result is retained; no source change requires a new suite. GitHub main unpushed;30-minute schedule unchanged.


Sheet S74 synced and exactly verified at 2026-09-27 13:50 UTC: four ranges/18 cells, preserving prior history, Overview B2, the currency tool row, formulas and formatting. Evidence restore-financial-sheet-fresh.json, restore-financial-sheet-changes.json and restore-financial-sheet-readback.json.

## September 27 bounded SIGKILL recovery review, 13:10 UTC

Reviewed shared da42515 and unchanged installed restore eec47ab. Both installed copies match SHA df1adac4d87ff82cc7bc7bf70f44bf7e42964e662523aeb920415cae98a27675. App endpoints remain healthy aec23fc. No application source change, deployment, live restore, app restart, provider action or financial mutation.

Fixture QA-RESTORE-SIGKILL-20260927 uses a synthetic 12345-cent SQLite row, 12582912-byte upload and optional synthetic environment. Each installed copy passed 12 bounded observation/recovery cases, 24 total: root/data archive layouts, with/without environment, process-group SIGKILL during real GNU tar extraction at checkpoint4, immediately before data rename and immediately after rename. Exit -9, no success message, existing application file and permissions preserved, original archive unchanged. Evidence outputs/restore-sigkill-probe.py and outputs/restore-sigkill-linux.jsonl.

All killed restores retained their private destination staging and validation directory. During extraction no data or environment was published; same-target retry succeeded but retained prior staging. Before rename, the archived environment link blocked same-target retry in four cases; without an archive environment, retry succeeded with old residue in four cases. After rename, complete data and any archived environment survived; all eight repeated restores refused the existing database. Twelve same-target retries therefore refused, while twelve succeeded with old residue. This confirms a known limitation, not automatic cleanup acceptance.

Every case also restored into a separate fresh target, recovered exact cents/upload/environment bytes and SQLite integrity, retained the interrupted target unchanged, and left no new staging from the successful fresh restore. All disposable fixtures were removed by the harness after collecting results. No application startup acceptance was performed on this minimal database fixture. SIGKILL observations do not establish power-loss durability. Automatic interrupted-job cleanup and producer-version metadata/refusal remain not built; operator/offsite, untrusted archive, concurrent writer and provider/AI gates remain open. Previous source full suite 1017 passed/1 skipped is retained, not rerun for this probe/documentation-only review.

SELF-HOSTING guidance now explains these observed states and recommends preserving an interrupted target and restoring the retained archive into a fresh directory before application-level checks. Do not remove an environment or staging directory based only on its filename, and do not restart from an interrupted installation based only on a readable SQLite file.

Grok PROFIT69-PCT acknowledgment 5855891012 and PASS 5855896593 are recorded on aec23fc: CAD revenue0/margin-151.67 gives blank undefined percentage; EUR0.50/-99.50 gives -19900.0%; USD4373.51/-55625.63 gives -1271.9%; M-1058 EUR0.50/0.50 gives100.0%. Existing independent CSV reused, no mutation. HTML/CSV/percentage cases passed; whole currency tool is not signed off. Case54 productivity remains defective and realization70 remains under autonomous working edits. No report source edits or duplicate unchanged retests by Codex.

Issue12 handoff https://github.com/Coil-Legal/coil/issues/12#issuecomment-5856149070 records new recovery observations, the completed percentage result and a prioritized queue. Operational PUB-ENOSPC/PUB-BOUNDARY and prior nightly/CLI/WAL/preflight/target cases remain deferred for exact-source/disposable access. SIGKILL observations/fresh-target recovery criteria join that deferred scope, with no acknowledgment or start claimed. No new access ping. Report retests wait for completed deployment handoffs.

Phase1 remains incomplete; Phase2/3 are not signed off. Next executable work: producer-version metadata/refusal review, followed by other Phase1 cases before later phase inventories. GitHub main remains unpushed;30-minute schedule unchanged.


Sheet S73 synced and exactly verified at 13:12 UTC: six ranges/23 cells. Fresh reads preceded updates; existing history, Overview B2, Cursor Tools J29/K29, formulas and formatting preserved. Evidence restore-sigkill-sheet-fresh.json, restore-sigkill-sheet-changes.json and restore-sigkill-sheet-readback.json.

## September 27 restore publication, 2026-09-27 12:30 UTC

Reviewed source d3bd22e and installed restore4dc6249. Eight controlled destination-write regressions leave target files behind on the baseline. Actual Linux reproduction used a private8 MiB destination tmpfs and a12 MiB synthetic upload: cp returned No space left on device with zero free bytes and left .env, data/practice.db and an incomplete data/uploads/fixture.bin. The existing-data guard blocks clean retry. Evidence restore-publication-baseline.log and restore-publication-linux-baseline.log. The baseline log also contains six publication-boundary expectations added for the new implementation, not six additional baseline reproductions.

Isolated /private/tmp/coil-restore-publication. Fix eec47abce0b1fdee5b44b614fd5ff78af19c2e80 extracts into a private destination directory, checks SQLite and publishes the complete data directory by same-filesystem rename. The optional environment is linked without clobbering an existing path. A database inode marker distinguishes completed publication even if SIGTERM arrives immediately after rename. Cleanup removes only this invocation's unpublished environment link and staging directories; a complete published data/environment pair is retained. Unexpected install-root entries and nonregular archived environments are refused. Existing application files remain preserved.

Changed ops/restore.sh, tests/test_restore_publication.py, tests/test_restore_integrity.py and docs/SELF-HOSTING.md. No schema/provider/application changes. Destination filesystem needs hard links and rename support, with space for the full extracted payload; temporary storage needs one database validation copy. SIGKILL/power-loss recovery across environment and data paths is not implemented. Concurrent writers, untrusted archive-member security, version metadata/refusal, operator/offsite and provider prerequisites remain open. The application and other writers must be stopped during actual restores. No whole-tool or Phase1 signoff.

Focused58 passed; full1017 passed,1 skipped,126 warnings in196.05 seconds. Candidate Linux six actual destination-ENOSPC/extraction-SIGTERM cases passed, plus14 controlled destination-write/rename-refusal/before-and-after-rename interruption cases. Each successful retry restores12345 cents, exact12582912-byte upload/environment bytes and integrity; original archive and application files preserved. After successful rename followed by SIGTERM, complete data/environment remain and repeat restore correctly refuses. Probe initially held a verification SQLite connection open and could not unmount its private filesystem; explicit connection close fixed the harness, and the complete rerun passed. No application-code adjustment was needed for that harness correction.

Candidate SHA df1adac4d87ff82cc7bc7bf70f44bf7e42964e662523aeb920415cae98a27675. Evidence restore-publication-focused.log, restore-publication-full.log, restore-publication-linux-candidate.log, restore-publication-linux-boundaries.log; executable restore-publication-linux-probe.py and restore-publication-boundaries-probe.py. Integration fast-forwarded eec47ab after checking five autonomous realization working-file hashes before and after; all unchanged. Installed on both hosts;54 synthetic checks per installed script,108 total, all passed. Settings hashes unchanged; rollback available, not used. Backups /home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/restore-before-eec47ab.sh. Install evidence restore-publication-install.log. Both public endpoints remain healthyaec23fc. No live restore, backup, app restart, financial mutation or GitHub push by Codex.

Grok ACK5855527583 covers the aec23fc profitability/productivity batch. PROFIT69-HTML PASS5855690721: EUR3078/M-1058 revenue0.50, USD3091/M-1071 revenue25.01; totals CAD0/EUR0.50/USD4373.51, cost CAD151.67/EUR100/USD59999.14, margin CAD-151.67/EUR-99.50/USD-55625.63. Missing-cost card reports250 flagged; unknown cost is not confirmed zero. PROFIT69-CSV PASS5855692777 independently downloaded397 rows, separate CAD/EUR/USD totals and hours1.52/1.00/1167.67, row sums reconcile. Percentage ratios need a focused independent check; they must be recomputed, not summed.

Case54 productivity FAIL5855692865 on aec23fc: Billable value USD288091.81, billable hours922.58, nonbillable247.60, no euro sign despite protected unbilled EUR3094. No mutations. Cursor/autonomous queue owns report implementation; realization70 remains under active working edits. No duplicate unchanged retest or report edit by Codex. Prior case passes remain separate from currency tool signoff. Fixture3078/3091/3093/3094 protected.

Phase1 remains incomplete; Phase2/3 open. Main unpushed;30-minute schedule unchanged. Next independent recovery work is SIGKILL/power-loss residue and producer-version metadata/refusal.

New issue12 handoff https://github.com/Coil-Legal/coil/issues/12#issuecomment-5855818595 assigns PROFIT69-PCT using the existing CSV: check actual exported ratios against margin/revenue, with zero-revenue CAD undefined. No ACK observed at assignment. RESTORE-PUB-ENOSPC and RESTORE-PUB-BOUNDARY criteria updated for eec47ab, explicitly deferred for existing exact-source/disposable access. No duplicate unchanged report retest or repeated access ping. Known disposable probe residue removed after verifying no mount remained.



Sheet S72 synced and exactly verified at 2026-09-27 12:31 UTC: six ranges/23 cells. Existing history, Cursor Tools J29/K29, Overview B2, formulas and formatting preserved. Evidence restore-publication-sheet-fresh.json, restore-publication-sheet-changes.json and restore-publication-sheet-readback.json.


## September 27 restore staging acceptance, 2026-09-27 11:43 UTC

Reviewed shared59d32d1 and unchanged installed restore4dc6249. Both installed copies have SHA9e17affda2ca183a062ed74d0faedefcf3ff832de06f1a6e3df79250f25e469f. No application source change or new deployment by Codex. The prior exact-commit full suite remains999 passed/1 skipped; it was not repeated for this probe-only review.

Fixture QA-RESTORE-STAGING-20260927 uses a synthetic12345-cent SQLite row, a12582912-byte upload and a synthetic environment. Both root and data/ archive layouts tested. Each installed copy passed four actual ENOSPC cases across absent/existing targets and two process-group SIGTERM cases with existing targets,12 total. Every failed restore returned nonzero, printed no success message, preserved the target snapshot, cleaned scratch space and left the archive unchanged. All12 retries restored exact cents, SQLite integrity, upload/environment bytes, application file and existing install permissions.

Disk exhaustion used a private mount namespace with an8 MiB tmpfs, not a live application filesystem. A wrapper ran actual GNU tar and recorded zero free bytes immediately after its real write failure, before restore cleanup. The initial harness expected the words No space left on device, but this GNU tar instead reports Wrote only6144 of10240 bytes. The assertion was corrected to require measured zero capacity and tar's failure; no restore code changed. Termination used actual GNU tar checkpoint4 after the staged database existed, then SIGTERM to the entire disposable process group. Exit143 and cleanup observed. Archives, temporary mounts and targets were disposable; the namespace and all mounts were removed.

Evidence: outputs/restore-staging-linux-probe.py and outputs/restore-staging-linux-results.jsonl in the current Codex workspace. The probe is reproducible with unshare and Python3 on a disposable Linux host. This establishes bounded staging/extraction ENOSPC and handled process-group SIGTERM only. Final-copy disk errors/interruption, SIGKILL residue, concurrent writers, unsafe archive members, root-filesystem exhaustion, power loss, automatic producer-version manifest/refusal, operator/offsite and provider/AI prerequisites remain open. Phase1 remains incomplete; no recovery tool signoff or independent Grok acceptance claimed.

Autonomous profitability69 completed/deployed aec23fc. Its handoff reports1003 passed/1 skipped. Both public health endpoints independently verified healthyaec23fc. Realization70 remains defective; reports.py working edits belong to the autonomous loop. Codex did not change report code or protected live fixtures.

New independent batch https://github.com/Coil-Legal/coil/issues/12#issuecomment-5855494785 assigns PROFIT69-HTML and PROFIT69-CSV separately on aec23fc. Protected fixture3078/displayM-1058 EUR0.50;3091/displayM-1071 USD25.01; revenue totals EUR0.50/USD4373.51. CSV requires per-currency hours/cost/margin/percentage reconciliation. Cursor's outstanding Case54 productivity gate refreshed to aec23fc after the committed diff confirmed productivity unchanged. Original read-only/no-CSV scope retained; unbilled3093/3094 remain protected. Asked for separate results or concrete blockers. No acknowledgment observed in the subsequent issue12 read. Existing operational cases remain explicitly deferred for exact-source/disposable access; no repeated access ping.

Next independent Phase1 work: final-copy failure preservation and version metadata/refusal. Phase2/3 remain open. Main unpushed;30-minute schedule unchanged.



Sheet S71 synced and exactly verified at 2026-09-27 11:45 UTC: six ranges/23 cells; prior history, Cursor Tools J29/K29, Overview B2, formulas and formatting preserved. Evidence restore-staging-sheet-current.json, restore-staging-sheet-fresh.json, restore-staging-sheet-changes.json and restore-staging-sheet-readback.json.


## September 27 restore extraction failure, 2026-09-27 11:04 UTC

Reviewed source9bc0bcc and installed restore77c2df7. A valid SQLite database followed by a file/directory collision in an upload or PDF causes tar to fail after it has already written the database and other files into the restore target. The existing-data guard then prevents a clean retry. Eight baseline regressions failed across root/data and leading-dot archive layouts, with absent and existing targets.

Synthetic fixture QA-RESTORE-EXTRACTION-20260927 contains12345 cents, exact upload bytes, a synthetic environment and an existing application file. Regression cases require an unchanged target after extraction failure, no temporary residue, successful retry, correct database/upload/environment bytes and preserved existing target permissions. No live data involved.

The isolated fix in /private/tmp/coil-restore-extraction extracts the entire payload in private scratch space, validates the extracted database, and only then copies payload entries into the target. Copying entries individually preserves the existing install directory permissions. Changed ops/restore.sh, tests/test_restore_extraction.py, tests/test_restore_integrity.py and docs/SELF-HOSTING.md. Temporary capacity must accommodate the extracted archive plus the separate database validation copy. Final publication remains nontransactional. Disk errors or interruption during final copy, SIGKILL cleanup, concurrent writers, unsafe archive members, version metadata/refusal and operator/offsite prerequisites remain open.

Focused44 passed. Both the initial and final Linux candidates passed8 cases; the final candidate includes target-permission preservation in acceptance. Initial full999 passed,1 skipped,126 warnings in190.38 seconds. Final committed candidate4dc624943685981fc3160854c85c16fd019d00dc passed999 tests,1 skipped,126 warnings in184.50 seconds. Final source SHA9e17affda2ca183a062ed74d0faedefcf3ff832de06f1a6e3df79250f25e469f. Evidence restore-extraction-baseline.log, restore-extraction-focused.log, restore-extraction-linux-candidate-final.log and standalone restore-extraction-linux-probe.py. Full-suite evidence is restore-extraction-final-full.log.

Independent report evidence on appa1793c5: ACK5854997046, results5855011714 give ORIG66-HTML PASS, ORIG66-CSV PASS and COMP68-CSV PASS. Correct identity is matter3091/displayM-1071, USD25.01, versus3078/displayM-1058 EUR0.50; Share100.0% EUR +100.0% USD. Compensation ALL fees EUR0.50 +USD4328.51. WIP67 hours and compensation HTML already passed in5854953863. These are individual fixture passes, not whole-tool signoff.

Cursor assigned realization Case53 in5855066460, ACK5855136273, FAIL5855148717. Main Worked USD314204.35; protected unbilled matter3094/time41563 EUR200 appears asUSD200, matter3093/time41562 USD100 appears correctly. No euro shown. Cursor owns this report queue; issue69 profitability and current report working changes remain with the autonomous loop. No duplicate unchanged retest requested. No Codex report or fixture mutations.

Phase1 remains incomplete. Exact-source/disposable independent operational acceptance remains deferred; provider/AI, operator/offsite and remaining recovery gates stay open. Phase2/3 are not signed off. GitHub main remains unpushed;30-minute schedule unchanged.

Final committed full suite:999 passed,1 skipped,126 warnings in184.50 seconds. Integrated4dc6249 by fast-forward after comparing all five autonomous report working files before and after; hashes unchanged. Installed on both hosts; each installed script passed34 synthetic Linux cases,68 total, comprising8 extraction/retry,12 preflight,10 target preservation and4 WAL/corrupt checks. Environment and Compose hashes unchanged; rollback available, not used. Backups /home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/restore-before-4dc6249.sh. Install log restore-extraction-install.log. Both public health endpoints remain healthya1793c5. No live backup/restore, financial write, application restart or GitHub push by Codex.

Cursor recorded realization as issue70 and assigned read-only/no-CSV Case54 productivity in5855255617. No Case54 acknowledgment observed at handoff. New recovery handoff https://github.com/Coil-Legal/coil/issues/12#issuecomment-5855269947 records separate RESTORE-EXTRACTION-ROOT/CLI acceptance criteria behind the existing exact-source/disposable-access prerequisite. No start or acknowledgment claimed. Existing operational acceptance cases remain deferred. Next independent recovery work: final-copy disk-error/interruption preservation and version metadata/refusal.



Sheet S70: all six affected ranges and23 cells were freshly read, updated and exactly verified at11:05 UTC. Cursor's new productivity assignment in Tools J29/K29 and Overview B2 were preserved, along with existing history, formulas and formatting. Evidence restore-extraction-sheet-current.json, restore-extraction-sheet-changes.json and restore-extraction-sheet-readback.json.


## September 27 restore database preflight, 10:18 UTC

Source a924968, installed restoreabd32b3. Restore checked SQLite only after extracting all files, so a corrupt database left a populated data directory and an archived environment in the target. A valid retry was then refused by the existing-data guard. Empty and duplicate database members were also accepted.

Eight baseline regressions failed: corrupt database with root/data and leading-dot layouts, plus empty/duplicate members in both main layouts. New tests require the original target to remain unchanged, no private scratch residue, and a valid retry with exact12345 cents and upload bytes. Fixture QA-RESTORE-PREFLIGHT-20260927. No live data involved.

Changed ops/restore.sh, tests/test_restore_preflight.py, tests/test_restore_integrity.py (hermetic PATH includes mktemp/rm), docs/SELF-HOSTING.md. Validation now copies the single archived database to a private temporary directory, rejects empty/duplicate members, checks SQLite before target extraction, and rechecks the restored database afterward. EXIT/INT/TERM cleanup is present; this review verifies normal failure/success cleanup, not interruption acceptance. This is not transactional extraction: I/O failure, SIGKILL, concurrent writes and unsafe archive members remain separate review gates. Producer-version manifest/refusal remains not built. Operator/offsite and exact-source/disposable independent acceptance prerequisites remain open.

Focused36 passed; candidate12 synthetic Linux cases passed across root/data and leading-dot layouts, including four successful retries with exact database/upload bytes and no scratch residue. Candidate SHA0d92d8e01eec33caf34b646c3faa9d8d9c1c25a57b1c74f37381f39afc69152d. Evidence restore-preflight-baseline.log, restore-preflight-focused.log and restore-preflight-linux-candidate.log; executable restore-preflight-linux-probe.py.

Autonomous loop completed report66/67/68 asfbfffe9/9d77ed8/a1793c5, with final full983 passed/1 skipped reported. Both public sites independently verified healthya1793c5. Grok prior cases were BLOCKED5854797973 by release changes, not product failures. Cursor refreshed9d77ed8 in5854876896. Codex verified unchanged profitability/origination functions and refresheda1793c5 in5854923887, adding COMP68-HTML to existing Case52,ORIG66-HTML,ORIG66-CSV,WIP67-HOURS. ACK5854940695 confirms all five; results pending. Existing operational cases remain deferred without duplicate access pings. No report edits or fixture writes by Codex.

Tested/integrated/deployed77c2df7. Full991 passed,1 skipped,126 warnings in185.76 seconds. Both installed script copies passed26 synthetic Linux cases each:12 preflight/retry,10 target-preservation and4 WAL/corrupt checks. Settings hashes unchanged; automatic rollback available, not used. Backups /home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/restore-before-77c2df7.sh. Install log restore-preflight-install.log. No live backup/restore, app restart, financial/provider action or GitHub push by Codex.

Grok result5854953863 on a1793c5: WIP67-HOURS PASS, EUR1.00/USD14247.50 hours and EUR200/USD4679050.68 money; COMP68-HTML PASS, EUR0.50/USD4328.51. Case52 profitability FAIL: M-1058 incorrectlyUSD0.50 and combinedUSD4374.01. ORIG66 HTML/CSV reported FAIL for ID3091 versus displayedM-1071, despite correct currency amounts/totals. Read-only source proof confirms they are the same fixture, linked to INV-1065; source amounts USD25.01 and share100.0% EUR +100.0% USD. Evidence origination-fixture-confirmation.json, confirm-origination-fixture.py. These reported failures are pending clarified independent verdicts, not unilaterally relabeled PASS.

Actionable follow-up https://github.com/Coil-Legal/coil/issues/12#issuecomment-5854968851: confirm HTML href/share cell, resolve CSV fixture mapping using existing artifact, and independently test compensation CSV. No acknowledgment observed at assignment. Recovery preflight criteria explicitly deferred with prior operational cases for exact-source/disposable access. Provider/AI, operator/offsite, compatibility/refusal and transactional extraction gates remain open. Phase1 incomplete; Phase2/3 not signed off. Main unpushed;30-minute schedule unchanged.

Sheet S69: six ranges/23 cells freshly read, updated and verified exactly at10:18 UTC. Prior history, Cursor J29/K29, OverviewB2, formulas and formatting preserved. Evidence restore-preflight-sheet-current.json, restore-preflight-sheet-changes.json and restore-preflight-sheet-readback.json. Public endpoints both healthy a1793c5 after script-only deployment.


## September 27 restore target preservation, 09:36 UTC

Reviewed shared df8fd3e and installed restore0423182. The restore command only refused an existing database, so a target with uploads/PDFs but no database could have those files overwritten by extraction. A nightly-layout restore through an existing data symlink wrote to the linked directory. A CLI-layout symlink case failed extraction but still changed the install target. Hidden leftovers were merged with a new database rather than refused.

Synthetic fixture QA-RESTORE-TARGET-20260927, integer12345 cents, two archive layouts and five target states. Corrected baseline eight failures/two fresh-target controls passed. Target snapshots compare all file hashes before and after; linked destinations checked separately. Evidence restore-target-baseline.log and restore-target-baseline-evidence.json.

Isolated /private/tmp/coil-restore-target-review. Changed ops/restore.sh, tests/test_restore_target_preservation.py, docs/SELF-HOSTING.md. New guard refuses nonempty data directories, data symlinks and data files before extraction. Existing app code outside data and an empty real data directory remain allowed. Existing database/environment refusal retained. Focused28 passed; candidate ten synthetic Linux cases passed with exact12345 cents and preserved files. No schema/provider changes.

Source SHA16486fdfc8319158639716f9ee7a52266e8284f992610260f2305fef26055ab2. This is an offline preflight guard. Concurrent writers, power loss, transactional extraction, untrusted-archive member validation and automatic version refusal are not established by these tests. Operator/offsite and exact-source/disposable independent acceptance prerequisites remain open.

Grok results on51a3da8: AR65-CREDIT PASS5854417657, WIP64-MONEY PASS5854417756, WIP64-HOURS FAIL5854417845 (issue67). Case51 compensation FAIL5854545628: EUR matter3078 shows USD0.50 and no euro sign; main fees4329.01 dollars. Cursor owns the browser queue. Origination66 remains defective with uncommitted loop work. No duplicate case assignments. Existing fixture protections retained, including unbilled3093/3094 and paused webhooks9/10.

Initial full suite975 passed,1 skipped,126 warnings in184.43 seconds; bash syntax check passed. Isolated tested commit2ed6271. Both host scripts installed from that exact commit/hash with automatic rollback available, not used. Each installed copy passed all ten Linux cases. Existing environment/Compose hashes unchanged. Backups /home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/restore-before-2ed6271.sh. No live backup/restore, financial write or application restart by Codex. Installation log restore-target-install.log.

The shared branch advanced to autonomous origination commitfbfffe9 before fast-forward integration, which correctly refused. The tested restore delta was then cherry-picked asabd32b3. A comparison against older uncommitted report hashes detected the loop's intervening edits; final diff againstfbfffe9 confirmed every committed report file was unchanged by the cherry-pick. New test_wip_currency.py working changes were left untouched. Isolated checkout rebased toabd32b3 for a combined full-suite run. The installed restore bytes remain identical to the original tested candidate.

Final combined suite onabd32b3 (including autonomous originationfbfffe9):979 passed,1 skipped,126 warnings in182.99 seconds. No repeat deployment needed because restore bytes were unchanged. Autonomous loop reports origination full969 passed/1 skipped and completed deployment; both public health endpoints independently verified healthyfbfffe9. New reports/WIP working changes remain excluded.

Grok new batch https://github.com/Coil-Legal/coil/issues/12#issuecomment-5854685200: ORIG66-HTML and ORIG66-CSV assigned independently, ACK5854687654 with healthyfbfffe9 gate; results pending. RESTORE-TARGET-A/B explicitly deferred with existing operational prerequisites; no repeated access ping. Case52 old release-gate blocker resolved in5854695793 after verifying profitability_data and profitability function bytes match51a3da8 exactly. Original read-only/no-CSV scope retained. Compensation68 and WIP67 remain defective, origination66 independent acceptance pending.

SheetS68: six ranges/23 cells freshly read, updated and exactly verified. Existing history, Cursor J29/K29 and OverviewB2 preserved. Evidence restore-target-sheet-current.json, restore-target-sheet-changes.json and restore-target-sheet-readback.json. Phase1 incomplete; Phase2/3 outcomes remain open; main unpushed;30-minute schedule unchanged.


## September 27 dashboard credit fix and WIP currency review, 08:53 UTC

Grok acknowledgment5854387684 confirms health51a3da8 and acceptance of all three read-only cases; separate results pending. Sheet Overview and QA queue acknowledgment status updated after fresh reads. New reports.py, origination.html and test_phase2_c.py working changes observed at close were left untouched for the autonomous loop. Shared review commitbe543d1, main unpushed.

Issue65: the dashboard summed invoice totals minus payments, omitting issued credits. Grok independently traced GBP invoice3048/INV-1049 and CN-1009 to card1.00 versus invoicebalance0.50 in comment5854142678. Earlier isolated fixture92001 reproduced9000-cent invoicebalance versus10000-cent card.

The fix aggregates issued credits once per invoice, subtracts payments and credits, clamps each remaining balance at zero, and retains currency grouping. Voided credits and draft/void/paid invoices do not contribute. No schema or provider changes.

Changed app/blueprints/dashboard.py and new tests/test_dashboard_credit_balance.py. Four corrected baseline failures and one control pass. Final focused13 passed. Initial isolated full962 passed,1 skipped,126 warnings in179.08 seconds. Rebased onto completed WIP release0edc7be and coordinationffc1f03, preserving the autonomous loop's changes. Final tested isolated51a3da8.

Grok Case49 FAIL5854142774 confirms origination66 still labels EUR0.50 as USD. Cursor Case50 PASS5854243353 is a report observation with no foreign-currency fixture, so it does not establish foreign-currency realization acceptance. Existing60/61/62/63 display case passes remain separate from credit arithmetic and tool readiness.

Independent restore/nightly/CLI acceptance remains deferred for exact-source/disposable access. Provider/AI, offsite/operator, version metadata/refusal and remaining recovery gates remain open. Phase1 incomplete; Phase2/3 inventory not signed off. Main unpushed;30-minute schedule unchanged.

Final combined full965 passed,1 skipped,126 warnings in180.24 seconds. Integrated/deployed51a3da8. Linux16 passed in14.64 seconds. First image test attempt ran no tests because two source regression files were absent from the previous image; added them to the disposable image and reran successfully before activation. Both public HTTPS endpoints healthy51a3da8; host/runtime dashboard hash33808bf1c8e819495a85f69d2ee50139bcf8f2f335de1761eb018a0d9030cb47; environment/Compose unchanged. Startup connection refusals resolved within health polling. No rollback needed.

Backups: /home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/dashboard-51a3da8-r2; rollback images testfirmcoillegal:before-51a3da8 and democoillegal:before-51a3da8. Data archives under each app data/backups: testfirm coil-backup-20260927-084902-dhpbhqt4.tar.gz; demo coil-backup-20260927-084927-j1sq9vfb.tar.gz. Earlier preparation backup retained. Logs: dashboard-credit-combined-full.log, dashboard-credit-prepare.log, dashboard-credit-prepare-r2.log, dashboard-credit-activate.log.

Read-only deployed comparison: GBP50 cents and USD101387525 cents exactly equal the sum of all open invoice.balance_cents values. GBP3048/INV-1049 total100-paid0-credit50=balance50; USD3064/INV-1065 total10001-paid2501-credit1000=balance6500. Demo has no open invoices.

Created only two new synthetic unbilled WIP fixtures on testfirm:3093 QA-WIP-USD-20260927-CX, time41562,60min at10000 cents;3094 QA-WIP-EUR-20260927-CX,time41563,60min at20000 cents. Auto invoicing disabled. Existing invoices3044/3048/3064/3065/3066 monetary fingerprints unchanged. No invoice, payment, credit, provider charge or message created. HTML/CSV fixture amounts correct; footer EUR200.00 plus USD4679050.68.

New defect: WIP CSV currency TOTAL rows both repeat14248.50 hours; EUR should1.00 and USD14247.50 from current fixture rows. Monetary splitting works for the sampled rows, but WIP remains defective overall. Left reports.py to autonomous loop; finding included in the independent batch. Evidence dashboard-credit-wip-fixtures.log and executable create-wip-review-fixtures.py.

Grok queue https://github.com/Coil-Legal/coil/issues/12#issuecomment-5854362540: AR65-CREDIT, WIP64-MONEY and WIP64-HOURS separately assigned. No acknowledgment observed at assignment. Existing operational cases remain deferred. Origination66 remains defective, realization foreign-currency acceptance untested. No full tool signoff.

Sheet S67: freshly read affected cells, updated five disjoint ranges/16 cells and verified exact readback. Preserved OverviewB2, Cursor J29/K29, formulas and formatting. Evidence dashboard-credit-sheet-current.json, dashboard-credit-sheet-changes.json and dashboard-credit-sheet-readback.json.


## September 27 WAL snapshot restore fix and version compatibility review, 08:04 UTC

The native macOS SQLite CLI rejected an intact WAL-mode snapshot when its sidecars did not exist. Both nightly-root and CLI-data layouts reproduced the failure. Python read-only integrity validation accepted the same bytes and exact12345-cent row. Restore now prefers Python3 when available and retains the native CLI fallback for hosts without Python. CLI-only WAL behavior is not expanded by this fix. No database bytes are changed by validation. Two baseline regressions failed; focused18 passed. Candidate Linux checks passed both valid layouts, both corrupt rejections, exact bytes/rows and repeat refusal.

Isolated source `/private/tmp/coil-restore-compat`, based on40b4c35/applicationf280d87. Changed files: ops/restore.sh, tests/test_restore_wal_snapshot.py and docs/SELF-HOSTING.md. Restore SHA25665be623cf60251a6f591b594504a0c2088f9eb2f9aa567328c7c80aef85a2675. No application/schema/provider change. Full-suite and deployment results are recorded below when complete.

Actual historical CLI archives were restored and opened with current code: **e007fa9 to40b4c35**, **dc5d025 to40b4c35**, and **40b4c35 to40b4c35** passed. Synthetic fixture QA-RESTORE-COMPAT-20260927, local client/matter/invoice92001. Invoice12345 cents, paid2345; balance10000 for old-source fixtures and9000 with current1000-cent credit. Exact upload/PDF bytes, SQLite integrity, archive hashes, invoice HTTP200 and a second application start passed. First attempts stopped at the native-validator defect and are retained separately; final evidence correctly identifies the new validator candidate. Three successful samples do not establish support for every past version.

**Automatic version compatibility checks are not built.** Archives have no producer-version manifest; the restore command does not know the target code or refuse an unsupported downgrade. Negative control40b4c35 to pre-credit-note e007fa9 retained the1000-cent credit row but ignored it in its balance calculation:10000 instead of9000, despite health and invoice HTTP200. This is an unsupported downgrade, not a current-code data loss claim. SELF-HOSTING now tells operators to retain the producer commit/image, restore matching code first, reconcile financial records/files and then upgrade. Manifest and automatic compatibility refusal remain executable follow-up work; broad recovery acceptance stays open.

Autonomous loop committed/deployed **f280d87** for issues60/61/62/63, full955 passed/1 skipped reported. Both public sites independently verified healthy; demo briefly503 during rollout then recovered. Grok acknowledged independent batch5853976327 as5853982614. **CUR60 PASS5854007025** confirms grouped invoice badges/footer and protected INV-1065 total100.01, paid25.01, credit10.00, balance65.00. **CUR61 display PASS5854007131** confirms dashboard GBP1.00 + USD1013913.00; exact source reconciliation remains partial because the result only says directional. **CUR62 PASS5854007220** confirms separate GBP/USD aging rows/totals and CSV Currency column. **CUR63 PASS5854007298** confirms EUR0.50 + USD4373.51, matter3078 EUR0.50 and3091 USD25.01 in page and CSV. These are case results, not currency-tool signoff. WIP64 remains queued/unfixed. Case48 ACK5853882727/PASS5853888652 confirms time CSV Currency header but zero M-1058 rows, so foreign-currency values remain untested by that case.

Evidence in the Codex workspace outputs: restore-wal-baseline.log, restore-wal-focused.log, restore-wal-full.log, restore-wal-linux.log, restore-compat-first-attempt.log, restore-compat-final.log, restore-compat-results.json and historical/current invoice HTML. Executable probes restore-compat-probe.py, restore-compat-worker.py and restore-wal-linux-probe.py. Synthetic scratch directories removed; no live financial fixtures modified. Independent/operator/offsite access, version metadata/refusal, legacy cleanup, backup-destination changes, root exhaustion and provider/AI gates remain open. Phase1 incomplete; Phase2/3 inventory remains open. Main unpushed;30-minute schedule unchanged.

Tested isolated **0239240**, integrated/deployed **0423182**. Final full suite **957 passed,1 skipped**,126 warnings in180.37 seconds. Both installed restore copies match65be623cf60251a6f591b594504a0c2088f9eb2f9aa567328c7c80aef85a2675 and each passed four synthetic Linux valid/corrupt layout cases plus exact-data and repeat-refusal checks. Backups: `/home/deploy/backups/coil/{testfirm.coil.legal,demo.coil.legal}/restore-before-0423182.sh`. Guarded installer retains automatic rollback; none needed. Both public sites remain healthyf280d87, no application restart. Deployment log: outputs/restore-wal-deploy.log. Independent RESTORE-WAL criteria5854034226 are deferred for the existing exact-source/disposable-environment prerequisite; no acknowledgment assumed.

**Additional dashboard arithmetic defect confirmed**, independent from currency display. Currentf280d87 on synthetic invoice92001 shows correct invoice9000 cents (12345 total minus2345 paid minus1000 issued credit), but dashboard A/R shows10000. Its SQL sums total minus payments without credits. Evidence: outputs/dashboard-credit-reproduce.py, dashboard-credit-evidence.json and dashboard-credit.html. No dashboard edits; handed to the autonomous fix queue at5854043915 alongside WIP64. CUR61 display pass retained, arithmetic acceptance marked defective. One live read-only GBP source follow-up5854034226 is assigned to Grok; no acknowledgment yet. USD aggregate reconciliation remains open. Next prioritized work: dashboard credit fix/retest, WIP64, backup producer-version metadata and incompatible-version refusal.

SheetS66: four ranges/25 cells freshly read, updated and exactly verified. Existing history, Cursor edits, formulas, formatting and OverviewB2 preserved.


## September 27 snapshot restart acceptance and WIP defect, 07:20 UTC

Unchanged installed nightly **6fe4009** passed two actual disposable application-container cases: graceful restart and forced SIGKILL/start during SQLite online backup. Instrumentation paused the API after one page, with1142 of1143 pages remaining. In both cases the script exited1 with snapshot failure, published no incomplete archive, preserved the prior archive hash, removed its workspace, and succeeded on retry. Four total final archives restored exact100/300-cent states, all64 padding rows, exact upload bytes and SQLite integrity; archive permissions0600. Application health recovered on33ac88c. Image sha256:9b9782737bec51c496067d1dedd5959f69ace705d874d97ad51ebe4061984f27. Both network-disabled synthetic containers and temporary directories removed. No live restart, backup or financial mutation. Offsite transport simulated; no power-loss guarantee. First forced-stop attempt failed in Docker's command invocation before the acceptance result; the corrected SIGKILL spelling passed separately. The first log retains that unsuccessful attempt.

Fixture **QA-NIGHTLY-RESTART-20260927**. Installed script hash c7d8bcac48ff0e9f8d3aac642bc9cfe2781dc0caaff801661d20641a87a4deae. Logs/probe: `outputs/nightly-container-restart.log`, `nightly-container-forced-restart.log`, `nightly-container-restart-probe.py` in the Codex review workspace. No application or operational edits/deployment, so prior full947 passed/1 skipped remains the implementation regression evidence; no new full-suite claim.

**WIP currency defect reproduced** independently by Codex using isolated c6f2e9f, whose application code matches33ac88c. Synthetic fixture QA-WIP-CURRENCY-20260927 has local matters/time entries91001 USD100.00 and91002 EUR200.00, each60 minutes. GET /reports/wip renders EUR as$200.00 and combines both currencies as$300.00. CSV has no Currency column and combines bare100.00/200.00 into TOTAL300.00. Expected explicit currencies and separate totals. The actual HTML/CSV and executable reproduction are saved as `outputs/wip-currency.*`, `wip-currency-evidence.json` and `wip-currency-reproduce.py`. Shared reports.py remains owned by the autonomous loop for issue62; new finding handed off for that queue, not edited concurrently.

Grok Case46 ACK5853482887, FAIL5853487829 had no demonstrated foreign-currency WIP row; Cursor5853612978 correctly left it unfiled. That case remains inconclusive. The new synthetic reproduction establishes the code defect separately. Case47 ACK5853655806, **PASS5853664437** on33ac88c: matter3078 shows rate EUR275.00/hr, currencyEUR and outstanding EUR0.00. Assigned display case only, no whole-tool signoff. Issue12 handoff5853717314 records WIP HTML/CSV retest prerequisites; no acknowledgment observed. Cursor owns browser assignment; NIGHTLY-CLEAN-A/B and CLI-CLEAN-A/B remain deferred, exact-source access blocked. No duplicate unchanged ping.

Remaining: autonomous currency fixes60/61/62, revenue63 and newly reproduced WIP; independent recovery/operator/offsite acceptance, legacy files, backup-destination changes, root exhaustion, version compatibility and provider/AI gates. Synthetic container restart is now locally accepted; broader Phase1 remains incomplete. Phase2/3 register remains open. Next independent recovery review: restore across supported application versions with explicit refusal for unsupported versions. Main unpushed;30-minute schedule retained.

Sheet S65: all four affected ranges (25 cells) freshly read, updated and exactly verified. Cursor text preserved with appended result updates; formulas, formatting and OverviewB2 retained.


## September 27 nightly workspace cleanup deployed, 06:36 UTC

Tested isolated `c6f2e9f`, integrated/deployed **6fe4009** to the central nightly script and both app script copies. The supervisor and host children retain a shared workspace lease; the Docker snapshot child separately acquires it under a permanent registry lock. Later runs reclaim only unlocked new workspaces and matching destination partials. Active children retain their files, delayed children fail without recreating a reclaimed workspace, and legacy flat files and symlink targets remain untouched. Final archives stay mode0600. Host Python3.8+ and local POSIX locks are required; see `docs/NIGHTLY-BACKUP-OWNERSHIP.md`.

Baseline **six failures, three live controls passed**. Final local full suite **947 passed,1 skipped**,126 warnings,177.03 seconds. Focused14 passed/1 GNU-only skip; nine strengthened process-lifetime checks also passed. Linux15 regression checks and five actual disposable Docker exec/GNU tar cases passed, then repeated successfully on **each of all three installed scripts**. Each five-case batch restored16 final archives with exact100/200/300/400-cent states, upload bytes and SQLite integrity. Prior archive hashes preserved. Offsite transport was simulated. First Linux run found an unused trailing GNU tar -C option with no optional files; it was corrected before final full/Linux testing and deployment.

All three script hashes are `c7d8bcac48ff0e9f8d3aac642bc9cfe2781dc0caaff801661d20641a87a4deae`. Backups: `/home/deploy/backups/coil/{host,testfirm.coil.legal,demo.coil.legal}/backup-before-6fe4009.sh`. Guarded installer retained automatic rollback, not needed. Disposable containers removed. No live backup/restore, application restart, financial/provider mutation or GitHub push. Both public health endpoints remain healthy **33ac88c** because this release changes host scripts. All nine pre-existing working files were verified byte-identical across integration; unfinished currency work remains owned by the autonomous loop.

Grok **QB59-INVOICES PASS5853123989** and **QB59-PAYMENTS PASS5853124147** on33ac88c independently confirm EUR INV-1045 omission, USD INV-1065 invoice100.01/payment13 check25.01 retention, and explicit omission warnings. Cursor marked issue59 qa:verified. Case44 **FAIL5853123815**, A/R grand total1013875.75 dollars with no euro, is issue62. Case45 **FAIL5853248145**, revenue4374.01 dollars/13 payments and EUR matter3078 mislabeled$0.50, is issue63. Issues60/61/62/63 remain open. Assigned-case passes are not whole-tool signoff.

Cursor **Case46 WIP assigned5853410571** at33ac88c, no ACK observed at this check; read-only, no CSV or Invoice action. New NIGHTLY-CLEAN-A/B independent acceptance criteria are **explicitly deferred** for exact source/disposable Linux-Docker access. CLI-CLEAN-ACCESS remains blocked, CLI A/B and older operational batch deferred. New queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5853438442. No duplicate browser assignment or unchanged access ping.

Sheet **S64**, five ranges/32 cells freshly read, updated and exactly verified. Existing evidence, Cursor edits, formulas, formatting and OverviewB2 preserved. Handoff, executable probes and deployment log: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-nightly-cleanup-handoff.md`. Independent/operator/offsite access, legacy cleanup, backup-root changes with old jobs, power-loss durability, root exhaustion, actual app restart during snapshot, compatibility and provider/AI gates remain open. Next independent executable recovery review: actual disposable application-container restart during snapshot. Phase1 incomplete; Phase2/3 inventory remains open. Main unpushed;30-minute schedule unchanged.


## September 27 nightly interruption review, 05:51 UTC

Reviewed source `1cea9fe`, unchanged nightly `6762c9b`. Four synthetic Linux probes used actual Docker exec, SQLite and GNU tar. SIGKILL before tar, after tar and after publication preserved prior archives and allowed retries; a fourth case proved the container snapshot child can outlive its killed host process group. All nine final archives restored exact 100/200/300-cent states, upload bytes and SQLite integrity. The tested script hash matched all three installed copies. Disposable containers and temporary data were removed. Offsite transport was simulated; this is not power-loss or live-app restart acceptance.

**Nightly cleanup remains defective:** one snapshot or a snapshot plus partial archive survived each interrupted job and its subsequent retry. Safe reclamation must cover both launcher and container-child ownership, including delayed child startup. Legacy flat files remain separate because they carry no ownership proof. No operational or application change was made in this review, no deployment or full-suite rerun. The separate CLI workspace fix `ebceeaf` remains deployed. First probe attempt had invalid generated-wrapper quoting and exercised no case; the corrected four-case run is the recorded evidence.

Both public sites independently verified healthy `33ac88c`. The autonomous loop's completed QuickBooks issue59 fix excludes non-USD rows and shows omission warnings, reported full suite 938 passed/1 skipped. Independent acceptance remains pending. Its new mixed-currency dashboard/invoice/helper/template work and test file are unfinished and were left untouched.

Grok Case43 **FAIL5852879277** on `ebceeaf`: Outstanding A/R `$1,013,914.00`, `1453 overdue`, filed as issue61. CLI-CLEAN-ACCESS **BLOCKED** in the same result: exact CLI source/image missing, operational A/B and previous batch remain deferred. Case44 acknowledged then blocked on the changed release gate, comments5853075229/5853075306. New gate and independent batch5853086565 now **ACK5853103522** on `33ac88c`: resumed Case44, QB59-INVOICES and QB59-PAYMENTS. Separate results pending. Existing statement HTML/content/visual fixture acceptance remains valid; no whole-tool signoff. Cursor owns the broader browser queue. https://github.com/Coil-Legal/coil/issues/12#issuecomment-5853086565

Sheet **S63**, five ranges/32 cells read before writing and verified exactly; acknowledgment follow-up recorded separately. Handoff and executable probe: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-nightly-interruption-handoff.md` and `review-nightly-sigkill.py`, results `nightly-sigkill-results.json`. Next Codex work: isolated nightly workspace ownership implementation with delayed-child/live-job controls, full checks before deployment. Operator/offsite, exact-source access, provider/AI and remaining Phase1 recovery gates remain open. Phase2/3 outcomes remain incomplete. Main unpushed, 30-minute schedule unchanged.


## September 26 local retention acceptance and credit-race defect, 23:10 UTC

Local retention case **QA-BACKUP-RETENTION-20260926** passed on unchanged backup **6762c9b** and restore **68809b3**. Two overlapping jobs at14-daily/8-week capacity began with22 old synthetic archives and kept exactly17 expected archives: two new, twelve recent old and three older Sunday controls. The55-day Sunday stayed; the62-day Sunday expired. All17 restored with SQLite integrity OK and exact12345 cents. Retained hashes/source unchanged; no temporary leftovers. Actual GNU tar/date/SQLite, with local Docker/offsite doubles. This covers one controlled interleaving and local retention, not remote retention or arbitrary concurrency. No source change, deployment or new full-suite run.

Grok case31 is defective despite its PASS label: result5850552410 recorded HTTP500 on the second simultaneous credit request. Cursor filed issue58. CN-1015 was created and the balance held at25 cents, but response handling failed. Invoicing is now **Known defect** in the Sheet; earlier individual passes remain. Case32 single oversized-credit refusal independently PASS5850729530, ACK5850722552. Invoice3051 / INV-1052 remains sent at25 cents due, Paid0/Credited75 cents; CN-1013/CN-1015 issued, CN-1014 void.

The shared invoice blueprint and new concurrency test are uncommitted work for the autonomous fix queue. Codex left them untouched; no completed handoff or deployment claimed. Cursor owns the browser queue. Priority: completed issue58 fix, then independent concurrency retest on an authorized fixture. Do not repeat the race on protected fixtures.

Both apps remain healthy **9ae51a0**. Recovery stays QA pending. Next executable operational review: backup/update overlap. Offsite/remote retention, operator acceptance, version compatibility, whole-host root exhaustion, power loss and forced-termination cleanup remain open. Phase1 provider and broader AI gates remain. No GitHub push or phase signoff.

Handoff: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-backup-retention-handoff.md`. Evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5850764600 and https://github.com/Coil-Legal/coil/issues/58. Sheet source **S53**, seven ranges/31 cells verified; existing evidence, formulas and OverviewB2 preserved. Schedule remains30 minutes.

## September 26 source-volume exhaustion fix, 22:33 UTC

Deployed backup **6762c9b** with rollback copies to the active nightly script and both installed app copies. Actual SQLite disk-full failure previously left a1024-byte rollback journal after deleting its partial snapshot. Cleanup now removes only that invocation's exact snapshot and sidecar paths. A regression protects another job's journal. Baseline failed; focused21 passed/1 GNU-only skip; full **911 passed,1 skipped**.

All three installed copies passed actual SQLite failures with65536 and0 free bytes and mktemp refusal with0 free inodes in a bounded8 MiB/128-inode source filesystem. Source and prior archives survived, failed outputs were not published/transferred, handled temporary files were removed and retries passed. Fixture **QA-BACKUP-SOURCE-ENOSPC-20260926** restored four archives per copy with integrity OK, exact12345 cents, exact2 MiB database BLOB and control upload. Prior overlap/publication/restore checks also passed. Docker/offsite transport were local doubles. Both apps remain healthy **9ae51a0**; restore **68809b3** unchanged. No restart or GitHub push; Cursor's work preserved.

Recovery remains QA pending. SIGKILL can still leave temporary files. Next executable review: retention at capacity during overlapping jobs. Whole-host root exhaustion, power loss, forced-termination cleanup, backup/update overlap, offsite retrieval, version compatibility and independent operator acceptance remain open. Phase1 provider and broader AI gates remain.

Grok case30 PASS5850301159, acknowledged5850289465: CN-1014 void, CN-1013 issued, invoice3051 / INV-1052 sent at75 cents outstanding, Paid0/Credited25 cents. No extra payment-plan sentence, email or payment. Cursor owns the next browser case; no duplicate assignment or acknowledgment inferred.

Handoff: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-backup-source-exhaustion-handoff.md`. Finding and operator retest criteria: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5850484860. Sheet source **S52**, seven ranges/24 cells verified; recovery formula and OverviewB2 preserved. No whole-tool/phase signoff. Schedule remains30 minutes.

## September 26 bounded disk-full and interruption acceptance, 21:49 UTC

On unchanged backup **552a8b9** and restore **68809b3**, actual GNU tar/gzip ENOSPC in an isolated 8 MiB filesystem preserved the earlier archive, rejected the failed output and cleaned handled temporary files. Retry after freeing space passed. SIGKILL after snapshot creation and before archive publication preserved the prior archive, published nothing from the interrupted job and allowed retries. Killed jobs left temporary snapshots; the publication-stage kill also left a partial archive. Automatic cleanup is not established.

Fixture **QA-BACKUP-ENOSPC-20260926**: four successful archives restored with SQLite integrity OK, exact12345 cents and exact2097152-byte uploads. Source unchanged. Private filesystem unmounted and synthetic fixtures removed. Both apps remain healthy **9ae51a0**. No source change, deployment, restart or GitHub push; no full-suite rerun needed for acceptance-only work. Prior code-change full910 passed/1 skip remains historical evidence.

Recovery stays QA pending. This proves bounded archive-destination ENOSPC and two interruption cases, not full-root/source-disk exhaustion, power-loss durability or independent signoff. Docker/offsite transport were local doubles. Next executable checks: source-volume exhaustion and retention during overlapping jobs at capacity. Temporary cleanup policy, backup/update overlap, offsite retrieval, version compatibility and independent operator acceptance remain open. Phase1 provider and broader AI gates remain.

Grok case29 independently PASS5850075365, acknowledged5850070711: CN-1014 credits remaining75 cents on invoice3051 / INV-1052. Current status paid, outstanding0, Paid0, Credited100 cents; CN-1013 retained. No payment or further email. Cursor owns the next browser queue; no duplicate assignment.

Handoff: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-backup-exhaustion-handoff.md`. Issue evidence: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5850183645. Sheet source **S51**, seven ranges/24 cells verified; original formula and OverviewB2 preserved. No tool/phase signoff. The30-minute schedule remains.

## September 26 overlapping backup snapshots, 21:12 UTC

Deployed backup utility **552a8b9** to the active nightly script and both installed copies, with prior-hash guards and rollback copies. Two jobs previously shared one SQLite snapshot: the second job deleted the first job's snapshot, whether the second succeeded or failed. Every invocation now owns a separate snapshot; archive layout stays compatible. Two baseline regressions failed. Final **910 passed, 1 GNU-only skip**; focused20 passed/1 skip. Actual Linux archive checks passed at all three installed scripts, and the candidate passed using disposable network-disabled Docker containers with synthetic data.

Fixture **QA-BACKUP-OVERLAP-20260926** retained distinct100/200-cent snapshots; a failing second snapshot left the first100-cent archive intact. Earlier bounded write-failure, same-second archive publication, missing-environment and restore checks still pass. Running apps remain healthy **9ae51a0**, restore utility **68809b3**, without restart or GitHub push. Cursor's work preserved.

Recovery remains QA pending. Offsite retrieval, interruption, real disk exhaustion, concurrent retention at capacity, backup/update overlap, version compatibility and independent operator acceptance remain open. Killed jobs can leave temporary files. No full-tool or Phase1 signoff; provider and broader AI gates remain.

Grok case27 over-balance refusal PASS5849688206 and case28 zero-credit refusal PASS5849910197, acknowledged5849906092. Invoice3051 / INV-1052 remains sent at75 cents due, CN-1013 issued. Cursor retains the browser queue; no duplicate assignment. Independent operator retest criteria posted, access pending.

Handoff: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-backup-overlap-handoff.md`. Finding: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5849923926. Sheet source **S50**, seven ranges/24 cells read back exactly; formulas, formatting and OverviewB2 preserved. The30-minute schedule remains unchanged.

## September 26 backup failure preservation, 20:24 UTC

Deployed backup utility **5862762** to the active nightly script and both installed copies with rollback copies. Failed same-second retries previously deleted successful archives. Private staging and unique publication now preserve the prior archive. GNU tar also now handles an absent optional .env. Two baseline regressions failed; final **908 passed, 1 GNU-only skip**. Actual GNU tar checks at all three installed copies passed a bounded write failure, same-second successes, missing-environment backup and restoration of all resulting archives. Fixture **QA-BACKUP-PUBLICATION-20260926** preserves 12345 cents and exact upload bytes. Apps remain healthy on **9ae51a0**; restore stays **68809b3**. No restart or GitHub push.

The write limit simulates a file-write failure, not real disk exhaustion. Snapshot and offsite transport were local doubles. Independent operator, real ENOSPC, interruption, shared-snapshot overlap, offsite and version gates remain open. Recovery stays QA pending, with no full tool or phase signoff.

Grok case25 is mail-client BLOCKED (5849382873), with no message reaching Coil. Case26 independently passed (5849479730): invoice3051 / INV-1052, CN-1013 for25 cents,75 cents outstanding, still sent. Cursor owns the next queue; no new assignment or acknowledgment inferred. No repeated ping or fixture mutation.

Handoff and deployment/test evidence: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-backup-publication-handoff.md`. Finding note: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5849595912. Sheet source S49 and seven ranges/24 cells verified, including recovery C05 at row16, case evidence and current gates. Existing formula and formatting preserved.

## September 26 restore integrity validation, 19:41 UTC

Deployed host restore utility68809b3 to testfirm and demo with rollback copies. Old code reported success for corrupt database archives when sqlite3 CLI was absent, including on the VPS. Python SQLite fallback now validates before success; if neither validator is available, restore refuses before extraction. Three baseline regressions failed; focused16/full906 passed. Synthetic QA-RESTORE-INTEGRITY-20260926 corrupt nightly/CLI archives were rejected and valid bytes preserved by both installed scripts. Prior nightly-producer compatibility checks also passed. Running apps remain healthy9ae51a0; no restart or GitHub push.

Recovery remains QA pending. This is not atomic restore: files extracted before failed validation remain for operator review. Independent operator, offsite, interrupted/disk-full/overlap and version checks remain open. Provider and broader AI gates still prevent Phase1 completion.

Grok Unicode case24 independently passed5849078483 at19:14:53, with message292/document128 on matter3088, original display name, unshared state and exact24-byte download/hash. Cursor case25 assigned5849215845, acknowledged5849259343 at19:37:58, result pending. No repeated ping or mail send. Cursor owns queue.

Handoff, hashes, backup paths and logs: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-restore-integrity-handoff.md`. Finding note: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5849282648. Sheet S48 and seven ranges/28 cells verified; recovery case C05 uses previously empty QA row16, preserving Cursor result rows203/204 and existing formulas. No full-tool or phase signoff.

## September 26 nightly restore compatibility, 18:59 UTC

Deployed host recovery utility ec3750c to testfirm and demo with script backups. Nightly root-layout archives previously failed to restore; an existing environment could be overwritten before failure. Restore now supports root and CLI data-prefix layouts, refuses ambiguous archives before writing, and preserves existing .env/database files. Three baseline failures reproduced; full suite902 passed. Actual producer/GNU tar/restore synthetic fixture QA-RESTORE-NIGHTLY-20260926 passed against both installed scripts, preserving row12345 cents and exact upload/PDF/environment bytes. Snapshot transport and offsite copy were mocked. Running apps remain healthy on9ae51a0 without restart. No GitHub push.

Grok case23 reported blocked5848899080 at18:49; server records show message292 and document128 on matter3088 appeared18:50:06. Document128 is24 bytes, Email folder, original Unicode display name and unshared. No resend/manual import. Cause of delay unverified. Existing-case browser/download and persistence retests assigned5848965387, acknowledgment pending; Cursor keeps queue. Recovery independent/operator, offsite, interrupted/disk-full/overlap/version gates remain. No full tool or phase completion.

Evidence, deployed hashes and backup paths: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-nightly-restore-handoff.md`. Thread: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5848965387. Sheet source S47 and recovery row204 synced and read back; Cursor concurrent G191/mail updates preserved. Final evidence: restore-sheet-final-readback.json. Cursor canonical follow-up case24 assigned19:01:54 (5848986099), acknowledgment pending.

## September 26 full-tool acceptance audit, 18:13 UTC

Corrected five Sheet labels that excluded required acceptance evidence: Payments is Blocked on Stripe test access; Multi-currency, HTTP MCP, Agent invoices and Screen-reader pass are QA pending. All individual completed-case fields, fixture IDs, evidence links and historical tested versions were preserved. Required gates: P2-CUR-02/03/04, P2-MCP-01/04/06, P2-INV-01/06 and P2-A11Y-02/05/06. No new product defect, app change, deployment or full-tool pass is claimed. Other existing complete labels were not re-certified.

Overview static counters were replaced with formulas tied to tool statuses, preserving existing formulas and formatting. All46 tool rows and completed-case fields were compared with the saved before snapshot. Phase1 now totals24:19 existing complete labels,2 pending,1 known defect,2 blocked. Phase2:4 pending,1 blocked,2 not built. Across46 tools:19 existing complete labels,7 pending,2 known defects,5 blocked,6 not built,7 not reviewed. These are tracker counts, not a new certification of the retained complete labels.

Grok acknowledged Cursor's Unicode attachment case23 at17:41 (5848411748); no result observed when this audit began. Cursor retains queue ownership. No unchanged ping, new assignment or fixture resend. Phase1 provider, portal issue49, broader AI and operational gates remain. The portal blocker is the intended capture-mail access boundary, not an established send-code defect; no credentials changed. Main remains unpushed.

Handoff: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-acceptance-status-audit-handoff.md`. Before snapshot, changes, readback and46-row arithmetic/preservation verification are adjacent `acceptance-audit-*` files. Sheet source S46 records this audit. Documentation/Sheet-only work, no source test suite needed or claimed.


## September 26 acceptance reconciliation, 17:38 UTC

Codex resumed after a usage-limit interruption and preserved Cursor's current Grok queue. Application release 9ae51a0, reviewed source 3608a21; no new application changes or deployment. The September 22 partial Sheet payload was archived and superseded by reconciliation against current cells, not replayed over Cursor edits. New Sheet evidence includes S44 and S45. Main remains unpushed.

New isolated email acceptance: raw MIME empty-only, mixed empty/control and nonempty control all filed correctly, preserving bodies and control bytes. Empty attachments created no document. Same-ID replay and replay after recreating the Flask app left three messages and two documents, with no duplicate audit. Three existing filing tests passed. This does not establish live IMAP delivery, crash recovery or independent acceptance. Grok's actual empty-attachment case remains BLOCKED by mail-client validation (5848305881). Cursor assigned Unicode case 23 (5848344500); no duplicate Codex assignment. Public PDF case remains passed: matter3088/message287/document127 on9ae51a0.

Previously pending independent results were read and retained: d7f7461 signer rejection (5783155698), positive contradiction3062/114/15 (5783078426), supported client previews3039/3043 (5783112776), research occurrence/party/encoding/pagination/publication (5807196739). The AI rejection paths were not exercised. Later Unicode/concurrent signing failures were fixed and retested through issues47/48, and API concurrency/layout through56/57. No duplicate repairs.

Acceptance audit is still required for later tool-wide labels. Screen-reader evidence is missing from the narrowed Sheet signoff despite P2-A11Y-02/05/06; actual MCP-client evidence, currency exports/splits and agent-invoice checklist cases are also separate outstanding requirements. Existing case passes and coordinator edits are preserved. Phase1 Stripe, handset SMS, portal issue49, broader AI and operational gates remain. No phase or new full-tool signoff. Sheet Phase1 counters currently total25 for24 tools and are flagged for reconciliation.

Evidence and limits: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-sep26-reconciliation-handoff.md`, `empty-mail-local.json`, `email-filing-existing-tests.log`, `sep26-sheet-readback.json`. Authorized thread note: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5848370713. A local direct health request returned403 before a body; no outage inferred and no fresh Codex health pass claimed. Cursor remains sole Grok queue coordinator.


Latest September 22 18:52 UTC: deployed d7f7461 rejects overlong signer names before any signature/hash/PDF, fixing a stored-name/hash mismatch. Full 858 and image 21 tests passed; English/Spanish public rejection fixtures 3060/3061 passed without mail. E-signature remains QA pending. Grok independently passed oversized document-source, three extraction-limit and saved builder-result cases (5781736123, 5781736360, 5781736539). Research and Invoicing remain QA pending. The model queue is queued, not blocked by a provider. See Phase 1 readiness and the signature-name handoff for limits, backups and next cases.

Current acceptance status, updated September 22, 2026: Phase 1 is still open. See [Phase 1 readiness](PHASE1-READINESS.md) for deployed commits and evidence, [Phase 2 checks](PHASE2-QA-CHECKLIST.md) and [Phase 3 checks](PHASE3-QA-CHECKLIST.md) for the later review queues. Provider prerequisites and independent Grok retests are not complete.

Current deposition acceptance: `1a33ddb` holds uncertain, identical or source-unresolved comparisons for review across page, note and PDF. Synthetic 3047/doc 91/deposition 14, internal note 31 and unshared PDF 97 passed Codex checks with source/draft unchanged; 778 local and 53 production-image tests passed. Broader meaning accuracy and independent retests remain open. Grok stopped the prior batch on the SHA change and has been retargeted to 1a33ddb: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5773994130. New acknowledgment and case results pending.

Current client-update acceptance: `87de283` holds selected absence/completeness claims and uses the full source-based template. Full 788 / production-image 50 tests passed; two actual previews on 3039 passed the supported-output sample. Rejection path is regression-tested, independent issue-45 retest pending. Broader AI factual accuracy remains defective. Handoff: `docs/PHASE1-READINESS.md`.

Current research acceptance: ac7edc1 stops unsupported text encodings before citation lookup/note creation. Full 847 / image 34 passed; live 3056/docs 105 to 111/control notes 35/36 and browser warning passed, sources preserved. Prior party-name, publication, pagination, occurrence, source limits and independent core/mobile/PDF evidence retained. Independent encoding retest: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5779235749. General extraction, OCR/MIME/DOCX, caption identity, other AI consumers and full acceptance remain open.

The per-tool descriptions below originated at `c547c9b` on September 12. They record earlier reports and follow-up ideas, not a current release signoff. Findings go to GitHub issues with the `QA finding` template.

**Proven** means: the launch checklist passed, the adversarial pass passed, every fix was
re-tested by Grok independently, and there is a test in the suite holding it. It does not
mean nothing will ever go wrong. It means what we know how to ask has been asked.

**Second accounts.** Any check below that says *needs a second user* or *needs a clean
firm*: create it. Grok has authority to create users on testfirm and to run first-run
setup on the clean instance Claude provisions. Never on demo.

---

## Phase 1: acceptance in progress

### Trust accounting
Overdraw refused on every route including the importer and the invoice. Cross-matter and
cross-client isolation. Reconciliation with every uncleared item listed. Backdating into a
reconciled period refused. Post-dated deposits not spendable. Apply to invoice.

Further checks worth running:
- A cheque that bounces after deposit. Is there a way to reverse a deposit that keeps the audit trail, and does the client balance go negative correctly rather than silently?
- A bank fee and an interest posting on the trust account, then reconcile. The three-way should still agree.
- A reconciliation where the bank statement is out by one cent. The page must say out of balance and by how much, not round it away.
- Transfer between two matters for the same client. Both sub-ledgers move, client total does not.
- Disbursement to the firm for fees larger than the fees actually earned on that matter. This is the classic bar complaint and nothing in the ledger stops it today; confirm what the screen says.

Inputs that could trip it: a memo line with commas and quotes (check the export), a duplicate deposit entered twice by two users, an amount typed with a trailing period or as "1,100" with no decimals.

### Invoicing
Create, send, resend, part and full payment, interest, void with the paid-invoice explanation, negative and absurd totals guarded, two-tab edits refused, PDFs including non-Latin names, split-payer groups.

Further checks:
- An invoice with 200 time entries. Does the PDF paginate cleanly and does page 2 carry the header?
- A time entry at a zero rate on a billable matter. It should appear at $0.00, not vanish.
- A discount larger than one line but smaller than the total, then a payment, then a void attempt.
- Interest applied in three consecutive months. Simple or compounding, and does the page say which?
- Resend an invoice that is already paid. What does the client receive?
- Tax. Is there a tax line, and does a jurisdiction with no sales tax on legal services get $0.00 or nothing?

Inputs that could trip it: a client called O'Brien (apostrophe in the PDF and the email subject), a matter name of 290 characters, a time entry description with line breaks, JPY or any currency with no minor unit.

### Payments and payment plans
Manual payment, plans, pause and resume and cancel, no-Stripe fallback with a real address.

Further checks:
- An overpayment. Where does the excess go, and is it visible?
- A payment recorded against a void invoice. Must refuse.
- A plan whose invoice balance changes mid-plan because a credit was applied. Do the remaining installments recompute?
- A one-installment plan. Should either work or say why not.
- A payment dated before the invoice was issued. Allowed, but the invoice page should not show it as early.

### Conflict check
Exact, fuzzy at 80% and above, alternate-names field, waiver gate, convert, buried single match found in 760 contacts.

Further checks, and these matter because a missed conflict is malpractice:
- Hyphenated surnames, Jr and Sr and III, middle initials present on one record and absent on the other.
- A company and an individual sharing a surname. Nordvale Freight and a Mr Nordvale.
- A person who is a client on one matter and adverse on another. The check must show both roles.
- A surname that is a common word: Lee, Brown, Long, Young. Fuzzy must not flood.
- A contact with only a company name and no person, matched against a person at that company.
- Names in Greek, Cyrillic and Vietnamese with diacritics, matched against the ASCII spelling.

Inputs that could trip it: contacts imported from CSV with trailing whitespace, a contact whose name was entered in ALL CAPS, the same person entered twice with different email addresses.

### Calendar, deadlines and court rules
Limitation date verified against the source document, chains land on business days, recurrence stops at its end, court rules honest about being generic, iCal correct across time zones and DST, deadlines in both feeds.

Further checks:
- A deadline chain that crosses a configured closure. Holiday rows and a federal-holiday load action are built; verify the relevant dates are configured and the court-specific set is complete. Empty configuration warns that only weekends are skipped. Synthetic forward/backward exclusion passed September27; jurisdictional completeness is not established.
- A trigger date on 29 February, and one on 31 January with a "one month" step.
- A trigger date in the past. Should compute, and every resulting deadline that is already overdue should say so.
- A rule that counts backwards from a hearing date.
- An event created on the day the clocks change, at 02:30 local.
- The iCal feed subscribed in Outlook, Google Calendar and Apple Calendar, not just parsed. Each has its own idea of DTEND on an all-day event.

Inputs that could trip it: an event title with an emoji, a location with a newline, a task due date typed as 13/09/2026 by a British user.

### Client portal
Cross-client isolation by URL tampering, one-use 30-minute magic links, Spanish, messaging, upload, pay page on a phone.

Further checks:
- Two contacts sharing one email address. Which one does the magic link log in, and does it say?
- Request a link, request another, use the first. Should be dead.
- iOS Safari in private browsing, where the cookie may not persist between the email tap and the page.
- A document shared to the portal, then unshared while the client has it open.
- A client whose matter was closed yesterday. What do they see, and is it polite?

### E-signature
Send, sign, certificate with who and when and IP and both hashes, immutable afterwards, signing survives a mail relay refusing the address.

Further checks:
- A signer name of 200 characters. The certificate and the PDF must both cope.
- Two people open the same link and both sign within seconds. One must win and the other must be told.
- Decline, then the firm re-sends. Does the old token die?
- An engagement letter whose body contains a table and the firm's logo. PDF fidelity.
- Sign from a phone. The typed-name box and the tick box must be usable at 390px.

### Intake, messages, documents
Intake with the conflict waiver gate. Portal messages round-trip; texts stored and clearly not sent without Twilio. Documents: fake extensions refused, downloads nosniff, versions linked to their root.

Further checks:
- A lead with the same email as an existing client. Convert should link, not duplicate.
- Convert the same lead twice, from two tabs.
- A client reply that quotes the whole thread. Does the message view show the new part first?
- A message on a closed matter. Allowed, but the matter should show it.
- A 25 MB file exactly, a zero-byte file, the same filename uploaded twice, a password-protected PDF (text extraction will fail; the page should say so).
- A random .zip renamed to .docx. The signature check accepts this today because both are zip containers; decide whether that matters.

### Personal injury
Settlement worksheet reconciles to the cent, demand package with exhibits, records and billing letters, lien reduction letters using the reduced figure.

Further checks:
- A lien larger than the settlement. The worksheet must refuse or show a negative net and say so.
- Two liens from one provider, one reduced and one not.
- A reduction to zero. The letter should still make sense.
- A demand package with 50 exhibits. Index and PDF size.
- A provider with records received but no bills. Specials should be $0.00 for them, not missing.

### Criminal defense
Charges with attorney-entered ranges, court date chain, speedy trial says what it counts from, disposition PDF.

Further checks:
- Three charges with different statutory maximums on one matter. The disposition must list each.
- Speedy trial with a tolling period. If tolling is not modelled, the page must say the count is unadjusted.
- A disposition after a plea to a lesser charge than the one filed.

### Discovery and depositions
Current deployed evidence: QA loop source-resolution fix 4fdb41b is included in 0438bad. Codex still sees the false scarlet-door/uncertainty contradiction on deposition 14, now with an ambiguity warning. Citation correction is not semantic acceptance. Issue 46 remains a known semantic defect; separate Grok retest assigned.

Current September 22 independent result: Grok confirmed false contradiction #46 on matter 3047/document 91/deposition 14. Citation and PDF case passes remain valid, but contradiction semantics are defective. Both statements need source-context validation; existing draft preserved. See current Phase 1 readiness.

Current September 22 evidence: `16c533f` fixed transcript request coverage and condensation truncation. `f5135a3` checks unique exact quotes against source markers and warns on absent/repeated quotes; old saved drafts receive the same checks on viewing/export. Public fixtures 3041/3042, depositions 12/13, notes 26/27 and PDFs 88/90 passed the documented short samples and artifact text checks. Full local 727 and deployment-image 128 tests passed. Repeated/OCR-modified quotes still require manual source review; cross-part contradiction quality and independent QA remain open. Narrative date attribution is defective. This tool has no complete acceptance signoff.

Earlier report: Contradictions caught, internal and external, 3 of 3 runs, cited to page and line. Summaries not wiped by an empty save.

Further checks:
- A transcript over 500 pages. Does it clip, and does the page say where?
- A transcript with page numbers that restart per volume. Citations must say which volume.
- A witness who contradicts himself and corrects it in the next answer. Should be reported as corrected, not as a contradiction.

### Research and cite check
Current independent acceptance: Grok passed 390px/320px and keyboard save/export on 146ed23, unshared memo 96. Doc 84's earlier 404 was the bare unsupported URL; actual download passed. Edge citations and complete-tool signoff remain open.

Current September 22 evidence: Grok passed keyboard search, court filter, opinion, save/note and literal memo text on 94d4c21, matter 3050/authority 2/document 94. Its 390px saved-authority overflow is fixed in `146ed23`, deployed to both sites. Codex passed 320px, 390px, 1280px and keyboard save/export; document 95 is unshared and its authenticated download preserves literal text. Full 752 and deployment-image 26 tests passed. Independent mobile retest is assigned, not yet acknowledged. Read-only current-release checks found reference document 84 present with working download and navigation links; documents 84/94/95 returned exact stored PDF bytes and literal notes, all unshared. Earlier 404 cause remains unestablished pending Grok's exact URL/session evidence. Edge citations and complete research signoff remain open.

Resolved, not found, and the wrong-case pincite trap all correct. States plainly that it cannot say whether a case is still good law.

Further checks:
- A citation to an unpublished opinion, a state intermediate court, a string cite of five cases, a reporter abbreviation with a typo (F.3d as F3d).
- Feed it a brief that the AI narrative tool itself drafted. Any citation it invented must come back not found.

### Exports and importer
Current September 21 evidence: CSV batches on `7e15867` passed 50,000 rows and browser pause/resume. ZIP recovery on `2e52988` passed 3,000 unique files and worker restart. Paged ZIP previews on `b98647e` passed 500 folders with mixed Word/PDF/text/email documents, saved choices and exact byte/text checks. Blank and ambiguous matter names now require a choice. Full local suite: 697 passed; deployment suites: 98 passed. Independent Grok browser checks remain open. See Phase 1 readiness for fixtures, limits and deployment details.

Contacts, matters, time, trust ledger, QuickBooks layouts, LEDES. Formula injection neutralised, negatives still numeric. Importer with preview, commit, failed-rows CSV, duplicate handling, concurrent-write lock fixed.

Further checks:
- A description with a newline inside a CSV cell. Excel and Sheets must show one row.
- Unicode in a CSV opened in Excel on Windows, which wants a BOM. Does José become JosÃ©?
- 50,000 time rows. Time to generate and file size.
- LEDES output run through a real e-billing validator, not just opened.
- Import a genuine Clio export with Clio's own column names, then a MyCase one. Not a hand-made CSV.
- A CSV with a BOM, one with Windows line endings, dates as DD/MM/YYYY, and 10,000 rows.

### Webhooks
Fire on task.completed and matter.closed, retry on failure, secret masked and hidden from readonly.

Further checks:
- An endpoint that returns 500 five times then recovers. How many retries, at what spacing, and does it give up loudly?
- An endpoint that takes 30 seconds to answer. Does the app wait, and does it block anything?
- Rotate the secret. In-flight deliveries and the next one.

### Backup, restore, self-update, install
All proven by doing them: backup lands before an update, a broken build pins the previous digest and holds, a good build unpins, restore boots on real data with the trust balance intact.

Further checks:
- Restore a backup onto a Coil that is two versions newer. Additive migrations should handle it; confirm.
- Restore onto a Coil that is older than the backup. Must refuse or warn, not corrupt.
- The nightly backup at 02:40 and the update at 03:17 on a slow machine where the backup is still running. Overlap behaviour.
- Disk full during a backup. Claude runs this one.

### Setup guide, settings, permissions, API and MCP, fee splits, offices, audit log, feedback
All passed, including permissions by POST rather than by hidden nav, redacted API tokens leaking no names, multi-office rates, and 1,743 audit entries spot-checked as an auditor would.

Further checks:
- Remove the last owner. Must refuse.
- Deactivate a user who owns open tasks and unbilled time. What happens to them?
- A paralegal POSTing to change their own role. Must refuse.
- A user with no office on a firm that has two.
- Delete an office that still has users.
- Fee splits that sum to 99%. Refuse or warn.
- An API token revoked while a request is in flight.
- A redacted token asked to find a matter by client name. Cannot see names, so what does it get?
- The audit log filtered by one user across a month, and exported.

---

## Phase 2: earlier evidence, current review open

**Conflict check speed: withdrawn.** Grok measured 11 to 14 seconds at 760 contacts and this register repeated it without reproducing it. Measured on the live database: the index builds in 0.15s, the scan runs in 0.03s, the full request including the results page is 0.19s, and the round trip from a browser through Cloudflare is 0.2 to 0.9s. Grok's figure was its own automation overhead, which is why it cost the same with 500 hits as with none. Re-measure at five thousand contacts once the volume fixture exists, timing the request rather than the tester.

**Non-USD currency.** Fixed in `72bc741` (matter page and raw exports). Grok re-tests: a CAD matter through invoice, PDF, payment, exports, reports and the public pay page, looking for a stray dollar sign.

**Draft invoice through the API and MCP.** Added in `c547c9b` after §S found the scope advertised but the tool missing. One test, no re-test yet. Grok: drive it end to end with an unredacted and a redacted token.

**Reports reconciled against their rows.** Done by Grok for §L on one firm state. Repeat after the two-user day in §O, so the figures have something to disagree about.

**Current AI acceptance, September 22:** matter isolation and complete summary inputs are deployed; `3cf4af4` also preserves whole client-update statements, bypasses the model for oversized input and separates file notes from work performed. Public 3043 retained a correction after the old cutoff; 3044 preserved the full overflow note in draft 144 with zero model calls. Factual acceptance is still defective: new live samples inferred recent receipt from an undated note on 3039 and asserted no other developments from selected records on 3043. Matter-summary date attribution is unchanged. Full local 734 and deployment-image 135 tests passed. See Phase 1 readiness for exact samples, test-fixture limitations and remaining acceptance gates. Release `500abb8` adds consistent internal/billing-text exclusions for work, completed/upcoming task titles and event titles before record limits. Public fixtures 3045/3046 passed selected-source, model/template exclusion and record-preservation checks, with draft 146 saved and no email sent. Full 746 and deployment 147 tests passed. General narrative reliability and independent acceptance remain open. Release `94d4c21` fixes concurrent document-date acceptance failures; 752 local and 153 deployment tests passed. Four public simultaneous submissions plus replay created exactly one task/event pair on matter 3049. Grok independently passed filter/fallback, citations/PDF and sequential date replay on 500abb8, without closing general narrative acceptance. Issue 45 remains defective; issue 44's quoted note-recency claim is supported by record metadata. See current Phase 1 readiness.

**AI output quality on clean inputs.** Audited once on M-1008; one real grounding gap fixed. Repeat on two other matters with different document sets. What matters is a confident sentence the sources do not support.

**Portal accessibility.** Keyboard and screen-reader pass on the invoice done; the portal half was blocked for lack of a session. *Needs a second client account with a magic link Grok can read.*

**Volume: measured and fixed (`b2d7f5a`).** testfirm now carries `ops/volume_fixture.py`: 3,013 matters, 31,288 time entries, 3,019 invoices, 3,940 trust rows. Before the fix the matters list took 21s, `matters.csv` 26s on 13,067 queries and `time.csv` 23s on 38,313, against a 30s gunicorn timeout. After: 0.22s, 0.86s on 8 queries, 3.6s on 4. Cause in every case was a query per row, including `Firm.get()` once per row through `Matter.currency_code` (the identity map holds weak references, so an instance read once and dropped is fetched again). `tests/test_volume.py` seeds the fixture and fails if any count grows. A second pass (`3bbd7ed`) caught the dashboard at 910 queries (the overdue card rendered every overdue invoice with a client lookup each; now the oldest twelve and a count) and the trust overview at 954 (one query per client for its matters); now 27 and 14. Every page on the daily path is flat. Grok re-runs the export exactness checks and §P at this size; the conflict check itself was never slow (0.19s), see below.

---

## Phase 3: hardest, or not yet possible

**§E, the AI failure modes.** What every AI tool does with a wrong key, an expired key, and a key with no credit. Three different failures a firm will hit in its first month, three messages. *Blocked on Ian: a restorable key.*

**§Q and §R, the setup wizard and the install key on a truly empty firm.** Every wizard test so far ran on demo data; the install key has never been tested on a first run because testfirm was already installed. *Claude provisions a clean instance; Grok runs first-run setup on it, which is the second account.* Issues #7 and #8.

**IMAP email filing.** Never exercised; testfirm has no mailbox. *Grok's own AgentMail address may support IMAP. If it does, point testfirm at it and this unblocks itself.*

**The voice line.** Needs Twilio configured and a deliberate switch-on. *Blocked on Ian.*

**Arabic and other right-to-left scripts in PDFs.** Renders now, but unshaped and in logical order. Legible, not correct. Needs a shaping library and a decision.

**Credit notes.** Decided (credit rather than void), explanation shipped, the instrument itself not built.

**Document-figure conflict scan.** A deterministic check that dollar figures in a matter's documents agree with the case record. Not built. Ian's call.

**A real firm.** Everything above is what two machines thought to ask. The first solo practitioner will do something neither imagined within a week. That is not a test; it is the reason to ship to one firm you can talk to before you ship to ten.

---

## Blocked on Ian, unchanged

The GHCR package is private, so nobody can install Coil. `github.com/orgs/Coil-Legal/packages`, web UI only.

## Invoice polish qualifier guard, September 22

Release `0438bad` holds suggestions that change protected English qualifier markers and rechecks Apply atomically. Full 770 / deployment 45 tests passed. Public invoice 3035/line 9832 preserved complete rows and audits on unsafe submission; one real browser preview retained the sample limits and negatives. This is bounded phrase validation, not general semantic equivalence. Independent retest and broader factual acceptance remain open. See current Phase 1 readiness.

Independent invoice update (2026-09-22 15:28 UTC): Grok passed qualifier preview, unsafe Apply rejection, faithful Apply and unchanged amounts on invoice 3035 / INV-1038 / line 9832, matter 3014, release 1589dda. Paid/sent controls disabled. Result: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5779159699. Broader semantic and full invoice acceptance remain open.

AI acceptance update (2026-09-22 16:11 UTC): Claude deployed 9d25324 with literal recently/recientemente review holds in client-update subject/body. Codex 32 targeted tests and two actual supported previews passed on 3039/3043, sources/messages unchanged. Live rejection not exercised; unlisted temporal claims and general factual accuracy remain open. Grok acknowledged the full queue on 9d25324 at 16:08. Evidence: /Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-recency-acceptance-handoff.md.

Grok reconfirmed date concurrency PASS at 16:10:35 UTC on 9d25324, with that same SHA recorded before and after: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5779871232. Existing synthetic 3055/doc104 retained task75/event24 and exactly two creation audit rows after simultaneous two-session replay (both 302). Source hashes and reference3049/93/74/23 preserved. The earlier provisional pass is now independently reconfirmed for this case; this is not whole-tool signoff. Grok reports deposition14 next, followed by its already acknowledged batch.

Invoice PDF acceptance (2026-09-22 16:52 UTC): unchanged 9d25324 passed two local 200-line variants and two public downloads on matter 3057 / invoice 3036 / lines 9833 to 10032. Six pages, all rows once, repeated headings/footers, zero-rate entries, exact 2475000-cent total and Greek/Cyrillic control preserved. Visually reviewed. Draft/unsent/unpaid. Independent case assigned: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5780473674. Full invoicing remains QA pending. Evidence: /Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-invoice-pagination-handoff.md.
