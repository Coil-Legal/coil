# Coil Phase 1 completion pass

## Latest: citation party-name review, September 22

Both sites run `1589dda`. The real provider and browser previously marked Zyx v. Arizona and Miranda v. Qwerty resolved against Miranda v. Arizona, 384 U.S. 436. A shared token anywhere in a caption hid a changed opposing party. Recognized captions now require a normalized name overlap on each corresponding side; partial/short/reversed comparisons that cannot meet this check receive name_uncertain and found=false. Page, internal note and audit counts retain the review status. Wholly different names keep their existing separate warning. No schema or provider-setting changes.

Baseline 7 failures / 4 controls; focused 50, full 839 (126 warnings, 148.08 seconds), production-image 50 passed. Actual public original/reversed/Unicode four-case checks returned one resolved, two name reviews and one wrong case. Synthetic 3054 (QA-CITE-PARTIES), unshared document 103, internal note 34, audit 2671: warnings persisted and source row/bytes unchanged. Browser prior three-case sample now shows one resolved/two reviews. Zero model calls or external messages. Both sites healthy with backups, four exact hashes each, SQLite OK, zero restarts. All 421 staged tracked files matched the tested Git tree before deployment. Claude's unfinished ai.py and test_client_update_claims.py changes were preserved and excluded.

Grok acknowledged all previous cases and publication extension at 14:11:47 on 1bf98d6 (5778068395). No concrete result arrived by the final check. New party-name retest assigned after that queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5778526975. Prior release transitions authorized; existing priorities preserved. The earlier invoice-result/blocker request was not repeated. This remains a bounded token comparison, not general case identity or good-law verification. Caption variants, shared words within both parties, extraction/OCR, broader AI facts and external prerequisites remain open. No tool or Phase 1 signoff. Handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-party-handoff.md`. Main unpushed.

## Latest: unpublished research coverage, September 22

Both sites run `1bf98d6`. Search promised published and unpublished opinions but omitted CourtListener's explicit status flags, so the provider default excluded unpublished results. Regular search and search_cluster now request both categories. No routes, templates, schema or provider settings changed.

Two baseline failures; focused 28 / full 828 (126 warnings, 140.95 seconds) / production-image 28 passed. Actual provider comparison: Miranda, ca9, 2024, newest first returned 28 published-only results versus 80 with unpublished included. Browser exact cluster search formerly returned zero for Cruz Carmona v. Garland (10287881, opinion 10754469). Final public HTTPS reached all 80 distinct results over four pages with filters preserved, including 52 Unpublished badges; exact search and full reader passed in the browser. No matter writes or model calls. Prior c22e439 20-plus-8 pagination totals are historical, not the expected total on this inclusive release.

Both sites healthy, three matching file hashes each, SQLite OK, zero restarts, data/source backups and environment/Compose preserved. Slow full transfer replaced with a delta; all 420 tracked files matched the tested Git tree before deployment. Initial provider timeout and incomplete public harness attempt are distinguished from final passing evidence in the handoff.

Grok acknowledged c22e439 and the earlier queue at 13:32:44 (5777468272), still no concrete results at final check. Asked for the first invoice result or exact blocker (5777597099). Publication coverage extends the existing final search retest: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5777816150. New release authorized for prior unchanged cases; extension assigned, not acknowledged. No whole-tool or Phase 1 signoff. Loose case-name comparison, extraction/OCR, broader AI accuracy and provider prerequisites remain open. Handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-publication-handoff.md`. GitHub main unpushed.

## Latest: filtered research pagination, September 22

Release `c22e439` deployed to both sites. The live Miranda search for ca9 opinions filed during 2024, newest first, reported 28 results but Next page failed with Not found on CourtListener. The provider URL's escaped cursor was encoded twice. Parsing its query value once fixes the round trip through the HTML link and requests client. Only _courtlistener.py and new pagination tests changed.

Baseline 3 failures / 3 passes; final focused 26, full 826 (126 warnings, 137.84 seconds), production-image 26 passed. Public HTTPS and browser now return 20 then 8 distinct results with court/date/order preserved and no final Next page link. No matter writes or model calls. Both sites healthy, two hashes each match, SQLite OK, zero restarts, data/source backups and configuration preserved.

Additional live provider samples on prior 60d3acd: Miranda plus Brown resolve separately; 999 F.3d 9999 is not found; 2018 Ohio 1739 resolves to State v. Edwards (cluster 4495611). Pincite 384 U.S. 444 remains ambiguous with zero resolved; provider returned duplicate candidate links to cluster 107252, so this does not prove two distinct cases. Browser review warning passed. Actual Edwards search status is Published, unlike the canned Unpublished fixture, so live unpublished coverage remains unverified.

Grok acknowledged eight cases, including the source-limit extension, at 12:58:12 UTC (comment 5776936229). No concrete results arrived. New read-only pagination retest remains assigned after those eight: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5776937790. Known release transition authorized for prior cases. No full-tool or Phase 1 signoff; remaining AI facts, provider prerequisites, extraction/OCR and independent acceptance stay open. Handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-research-pagination-handoff.md`. GitHub main unpushed.

## Latest: citation document extraction limits, September 22

Release `60d3acd` deployed to both sites. Reproduced three partial-source paths: PDFs over 200 pages, plain-text-like files over the 400,000-byte read limit, and PDFs over 200,000 raw text characters before whitespace normalization. Each could leave fewer than 64,000 indexed characters and omit a later citation. The citation route now stops known-limited or unverifiable PDF sources before provider lookup or note creation. Complete pasted text still takes priority. Existing extraction behavior remains unchanged; page/byte constants are shared. The form explicitly discloses scan/image extraction gaps.

Baseline route regressions: 2 failures. Initial full 818 pass superseded after raw-PDF limit addition. Final focused 50 / full 819 (126 warnings, 138.26 seconds) / production-image 50 passed. Actual local generated PDFs reproduced page and raw-character truncation. Public synthetic matter 3053 (QA-CITE-EXTRACTION), unshared documents 100,101,102: correct explicit stops, zero notes and source rows/bytes preserved. Short pasted provider control passed; browser document 100 warning and retained selection passed. Both sites healthy, five exact hashes each, SQLite OK, zero restarts. Data/source backups and configuration preserved.

Grok acknowledged all seven prior cases at 11:47:51 UTC: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5775896132. No concrete case result observed this run. Source-limit extension assigned after them, not acknowledged: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5776247656. Known new release authorized for all existing cases. This is not OCR, automatic chunking, full DOCX/encoding extraction or general AI/citation correctness. Other tools' extraction contracts remain separate. No whole-tool or Phase 1 signoff. Handoff, hashes and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-cite-source-limits-handoff.md`. GitHub main unpushed.

## Latest: repeated citation source attribution, September 22

Release `74bc9db` deployed to both sites. A real CourtListener probe reproduced a false pass: the same reporter citation beneath a fabricated second case inherited the first case's name. Verified provider offsets now identify each occurrence. Missing/invalid offsets use only a unique exact match; unresolved source occurrence gets an explicit review status in the page, internal note and audit.

Baseline regression: four failures. Focused 49 passed; full 811 passed (126 warnings, 137.78 seconds); production image 49 passed. Public real-provider original/reversed/Unicode cases each returned one resolved and one wrong-case result. Synthetic matter 3052 (QA-CITE-OCCURRENCES), unshared document 99 and internal note 33: warning preserved, original source and document row unchanged. Browser result also passed. Source SHA256 8f1cd86cf70bc788b33e1d972b9c1723ef9b4c52fee51bd23dc67aa2cdebc0f8. Both sites healthy, four hashes each match, SQLite OK, zero restarts, source/data backups and settings preserved.

Grok's existing five-case acknowledgment remains 10:04 UTC, with long-input citation case assigned afterward and no new concrete results seen this run. Occurrence retest assigned after those six, not yet acknowledged: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5775571758. Known release transition explicitly authorized for existing cases. Source-occurrence fallback uses controlled provider tests; no production response injection. Existing loose shared-name heuristic, extraction/OCR, unusual reporters, database coverage and good-law status are not signed off. General AI accuracy and provider gates remain open; no tool or Phase 1 signoff. Handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-cite-occurrence-handoff.md`. GitHub main unpushed.

## Latest: complete citation-check input, September 22

Both sites run `6807843`. Citation lookup previously discarded text after 64,000 characters and could save a complete-looking result for the truncated source. Oversized pasted/document input now stops before provider lookup with an explicit length message and no result note. The form retains pasted text, source documents stay unchanged and the UI specifies the character limit. Staff must split sources into complete sections; automatic chunking is not built. A token-boundary assertion also prevents case-name parsing from restarting inside long unbroken tokens.

Corrected baseline: 3 failures / 2 passes. Final focused 25 passed in 3.16 seconds; full 794 passed with 126 warnings in 133.53 seconds; production-image 25 passed in 15.02 seconds. Initial baseline interrupted on the parser slowdown, and pre-parser-fix focused run took 54.99 seconds; no general complexity guarantee is claimed.

Public matter 3051 (QA-CITE-COMPLETE), unshared document 98: both 69,326-character pasted input and 69,325-character extracted document stopped without a result note. Exact source bytes and ending citation preserved. An initial checker assumption about whitespace was corrected after inspecting the original fixture; no duplicate fixture or source rewrite. Normal CourtListener lookup resolved 384 U.S. 436 and saved internal note 32. Browser warning/selection passed. Zero model calls or messages. Both sites healthy, all four hashes match, SQLite OK, zero restarts, source/data backups and configuration preserved.

Grok's prior five cases were acknowledged at 10:04; no concrete results observed during this run. Known 6807843 transition authorized for those unchanged cases; asked for a result or blocker instead of repeat acknowledgments. New citation retest is lower priority: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5775079741. Assigned, independent result pending. No Phase 1 or tool signoff; broader AI accuracy, provider prerequisites, extraction completeness and remaining research edge cases stay open. Handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-cite-completeness-handoff.md`. No GitHub push.

## Latest: client-update completeness claims held for review, September 22

Both sites run `87de283`. Client-update generation now holds selected English/Spanish absence or completeness claims in the subject/body and supplies the source-based template in the editable fields. The proposal remains escaped and inspectable separately. Complete eligible source statements and later corrections stay intact. The prompt no longer encourages filler for sparse records. This is a bounded phrase guard, not semantic validation; unlisted wording, incident-date inferences and unsupported positive claims remain open. Existing manual edits and saved messages are not rewritten.

Nine corrected baseline cases failed, one supported-output control passed. Final focused 37 and full 788 tests passed; production-image suite 50 passed. Initial test-harness dependency and script-count assumptions were corrected before these final results. Two live provider previews on synthetic matter 3039 returned only the supported documents-received fact without a completeness/receipt-date claim. Neither triggered rejection; controlled route tests cover the held path. Scripted preview kept source records and messages unchanged. No email sent. Browser source disclosure showed note 21 and the incomplete-history explanation.

Both sites healthy, all three hashes match, SQLite integrity OK, zero restarts, with source/data backups and preserved configuration. Grok acknowledged the prior four cases at 09:41; no results observed by 09:58. Before deployment it was authorized to use 1a33ddb or 87de283 for unchanged invoice/date/deposition cases. The new issue-45 case requires 87de283: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5774531372. Assigned, new-case acknowledgment pending. Phase 1 remains open; provider gates and broader factual accuracy are not signed off. Handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-update-claims-handoff.md`. GitHub main remains unpushed.

## Latest: deposition comparisons held for review, September 22

Checked September 22, 2026 09:16 UTC. Both sites deployed `1a33ddb5f78e020dea75ee6b5d84960b1d16061e`.

Saved deposition comparisons are now divided into Possible contradictions and Comparisons needing review on the page and in newly generated notes/PDFs. Full-string English uncertainty expressions, identical statements, missing statements, unresolved internal quote sources and unknown comparison types are held for review with explanations. Both original statements remain visible. Uniquely sourced first testimony gets its own source citation. Saved draft JSON is not rewritten and old notes/PDFs are not retroactively changed. Existing source-resolution work from `4fdb41b` is preserved.

This is a bounded guard. Unique quotes do not prove shared context, shared time, opposing facts or general AI accuracy. External chronology/PI comparisons keep their prior source handling. Unlisted uncertainty wording, cross-chunk relationships and broader semantic accuracy remain review work. Issue 46's specific presentation is fixed in Codex's sample, with independent retest pending. No whole-tool or Phase 1 signoff.

Seven baseline regressions failed. Final full suite: 778 passed, 126 warnings in 130.32 seconds. Production-image affected suites: 53 passed, 22 warnings in 38.08 seconds. A later eighth regression verifies identical statements are held. The pre-final focused suite passed 40 tests. No new dependencies or schema changes.

Public acceptance on synthetic matter 3047 / document 91 / deposition 14: uncertainty pair retained under Comparisons needing review, no Conflicts with label, first citation Vol. I 1:2, repeated second quote has ambiguity warning. New internal note 31 and unshared PDF 97 preserve the classification and exact quotes. The entire original deposition/source rows and source SHA256 `6fbd7429f754c73a0b0157ffe23c3ddad053cb67a6dd084af80c9019c01b4b1a` stayed unchanged. Zero model calls in this acceptance run. Browser DOM confirmed both sections and explanations. PDF rendered to PNG and visually checked: readable single page, no clipped text.

Both sites healthy, all three changed file hashes match, SQLite integrity OK and zero restarts. Environment and Compose files unchanged. Data backups: testfirm `coil-backup-20260922-091038.tar.gz`, demo `coil-backup-20260922-091251.tar.gz`. Source archives `/home/deploy/backups/coil/<domain>/source-before-1a33ddb.tar.gz`; rollback images `<project>:before-1a33ddb`.

Changed files: `app/blueprints/discovery.py`, `app/templates/discovery/deposition_detail.html`, `tests/test_deposition_review_gates.py`. Isolated checkout `/private/tmp/coil-deposition-review-gates`, baseline `67ca414`, integrated into shared repository after checking for concurrent edits. GitHub main remains unpushed.

Grok acknowledged the prior invoice/concurrency/deposition batch at 08:39 UTC, then reported all cases BLOCKED at 09:13 after detecting the release changed from 0438bad to 1a33ddb. No cases ran and no fixtures were mutated. Blocker report: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5773982836. The new release retains invoice/date fixes unchanged. Retargeted all cases and added deposition page/note/PDF plus a fresh positive-control comparison: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5773994130. Assigned, new acknowledgment and results pending. No duplicate unchanged ping. Fresh synthetic fixtures explicitly allowed; preserve existing references.

Next: Grok's four results; independent Phase 1 review of unsupported client-update claims in issue 45; broader AI factual accuracy and provider prerequisites. Stripe test access and authentic handset checks stay blocked. Phase 2/3 checklist work remains after executable Phase 1 cases. Logs, scripts, PDF and PNG are in the task outputs directory with deposition-review-gates in their names. Google Sheet synchronization is recorded separately.

## Latest: invoice qualifier guards and independent QA outcomes, September 22

Both sites run `0438bad`. Grok reproduced invoice-polish meaning changes on draft invoice 3035 / line 9832: the proposal dropped `only` and added `at this time`. Prior invoice 3034 / line 9831 had acquired an unsupported purpose. The new guard retains the original editable description when English negation/scope/uncertainty markers or selected timing/purpose phrases change. The rejected suggestion and reasons remain inspectable. Apply repeats the check and rejects the whole batch before any line changes. Only time lines can be changed through this workflow. The prompt now asks for the recorded work only, removing the invitation to explain why it mattered.

This is conservative phrase checking, not semantic validation. It can hold legitimate paraphrases and miss unsupported facts outside its patterns or changes in which clause a negation applies to. The UI says factual review is still required. Intentional changes to facts use the normal invoice editor. Previously saved wording is not rewritten automatically. No full AI or invoice-tool signoff is claimed.

Two baseline route tests reproduced unsafe preview and unsafe Apply; eleven new helper-level cases initially failed because the guard did not exist. Focused suite before final validation-message refinement: 34 passed. Final full suite: 770 passed, 126 existing warnings in 129.20 seconds. Deployment-image suite: 45 passed, one existing warning in 22.82 seconds. Both sites healthy, all three file hashes match, SQLite integrity OK and zero restarts. Source/database backups and rollback images exist; environment and Compose files stayed unchanged.

Public authenticated check on invoice 3035/line 9832 rejected Grok's exact unsafe wording and restored the original editable field. Complete invoice/line rows and invoice audit count stayed unchanged, including on unchanged replay. This rejection test made zero model calls. Separately, one real browser model preview produced `We reviewed the demand letter only. No strategy advice was provided, and the client did not approve a settlement.` It preserved the sample qualifiers. Browser editing to the bad wording and Enter on Apply showed Original retained, both scope/timing reasons and an expandable rejected suggestion, without an AI-unavailable message. No invoice was sent or paid; the original is preserved.

Grok independently passed research mobile at 390px and 320px with keyboard save/export on 146ed23, matter 3050/authority 2/new unshared memo 96. It resolved the earlier document 84 404 as the unsupported bare route `/documents/84`; actual Download links and `/documents/84/download` passed with the matching hash and literal note. Results: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5772917075 and clarification https://github.com/Coil-Legal/coil/issues/12#issuecomment-5772916941.

Grok reported simultaneous date QA blocked because it thought a fresh fixture was forbidden. A NEW synthetic matter and copied document are now explicitly authorized, retaining reference 3049/doc 93/task 74/event 23: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5773256348. No new acknowledgment/result yet. The independent invoice retest on `0438bad` is assigned here: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5773377456. Multiple independent cases remain available; unchanged assignments were not reposted as new work.

The QA loop completed and deployed contradiction-source patch `4fdb41b`, with its handoff reporting 757 tests. That committed release is preserved. Codex read-only browser verification on `0438bad` found deposition 14 still pairs scarlet-door testimony with `I am not sure` under Possible contradictions, now with `Quote occurs more than once. Select the source passage before use.` The fabricated citation is replaced, but the false contradiction remains. Issue 46's semantic acceptance remains defective despite its qa:fixed label. Grok was asked for separate citation and semantic verdicts, preserving 3047/doc 91/depo 14. Issue 45 and the provider prerequisites remain open. GitHub main remains unpushed.

## Latest: research PDF persistence and Grok acknowledgment, September 22

Read-only public acceptance on deployed `146ed23` confirms synthetic research PDFs 84 (matter 3035), 94 and 95 (matter 3050) are present and downloadable. Each authenticated `/documents/<id>/download` returned HTTP 200, with downloaded SHA-256 equal to the stored file. Each remains unshared. Exact notes survived PDF extraction: document 84 contains `Reviewed <full record> & comparison. Amount <500.`; 94 and 95 contain `Note: duty <duty> & scope <scope>`. Document 84 has its original September 21 creation record and only its creation audit in the document audit trail. This establishes current availability; it does not disprove a historical/transient failure or prove the historical file hash.

Both `/documents?matter_id=3035` and `/matters/3035?tab=documents` rendered working `/documents/84/download` links. Bare `/documents/84` returned 404 because no detail route is implemented. Grok's earlier report did not include the failing URL, so its cause remains unestablished. Asked Grok for exact URL/release/session role and an actual Download-link retest: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5772831538. No restoration, replacement, sharing or deletion was performed. Evidence: `outputs/research-persistence-check.json`; repeatable checker: `outputs/coil-research-persistence-check.py` in the Codex task workspace.

Grok acknowledged the mobile research and invoice meaning batch at 07:10 UTC on September 22, confirming release `146ed23`: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5772552011. Those cases are acknowledged/in progress, not passed. Simultaneous date acceptance remains queued. No duplicate unchanged assignment was posted.

The shared uncommitted `app/blueprints/discovery.py` and `tests/test_deposition_contradiction_review.py` patch remains another participant's unfinished work, with no completed handoff observed. Static review shows quote-location resolution plus a prompt refinement, which does not itself establish semantic contradiction correctness. Do not integrate, deploy or duplicate it until a completed handoff is available. Issue 46 and unsupported narrative claim issue 45 remain open. Phase 1 has no complete tool signoff; Stripe test access and authentic handset acceptance remain blocked.

No application edits or deployment in this run. Prior release checks remain 752 local tests and 26 deployment research tests; they were not rerun for this read-only acceptance and documentation update. Current shared application working changes were left untouched. GitHub main remains unpushed.

## Latest: research mobile fix and confirmed contradiction defect, September 22

Both sites run `146ed23`. Grok reported an offscreen Export as memo control on the saved-authorities page. Codex reproduced a 689px page at a 390px viewport, with the button starting at x=528.83. The saved-authority table and matter selector inflated the page. The isolated template fix constrains the main grid child, wraps the selector controls, and stacks labelled authority fields below 760px. Desktop retains its table. Notes now have case-specific accessible names. No schema, routes or provider configuration changed.

Full local suite: 752 passed, 126 existing warnings in 128.42 seconds. Deployment-image research suites: 26 passed in 11.73 seconds. Both sites healthy with matching template hashes, SQLite integrity OK and zero restarts. Data/source backups and rollback images were created before deployment; environment and Compose files remained unchanged.

Codex live browser checks: 390px page width 375px and 320px page width 305px (viewport scrollbar excluded); every filter, export, note, save and delete control stays within the viewport. Export starts at x=47 instead of x=528.83. At 1280px, page width is 1280px and the table stays a table. Keyboard Tab reached Save note and Enter preserved the exact note on matter 3050 / authority 2. Keyboard export created unshared document 95. Authenticated public download returned 200 and the PDF contains `Note: duty <duty> & scope <scope>` verbatim. The temporary viewport was reset. These are viewport and keyboard checks, not actual handset or screen-reader certification.

Grok acknowledged the prior batch at 06:11 UTC and reported at 06:20 UTC on September 22, release 94d4c21: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5772070678. Invoice 3034 / line 9831 preserved date, quantity, rate and cents through two applies; invoice 1623's paid guard blocked Apply. The second rewrite added purpose wording, so financial preservation is credited separately from semantic acceptance. Research keyboard/search/court/save/note/export passed on matter 3050, authority 2 and unshared document 94. Grok reported reference document 84 already returned 404; its cause remains unestablished and should be investigated without recreating or overwriting the reference.

Grok confirmed false contradiction issue 46 on matter 3047 / document 91 / deposition 14. Scarlet door testimony was paired with uncertainty about a badge or a later observation, and the source pointed to the scarlet testimony itself. This is a known defect. Code review shows key-testimony quotes call `_source_testimony`, while contradiction objects at `app/blueprints/discovery.py` lines 980 onward are accepted directly from the model; quote validation does not establish logical contradiction. Next fix needs distinct source context for both statements and conservative treatment of uncertainty/corrections, with regression and independent live tests. Existing draft remains unchanged. Issue 45's unsupported client-update completeness claim also remains open.

New independent Grok batch: mobile research retest and invoice meaning-preservation case, with existing concurrency retest still visible: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5772422531. Assigned, not yet acknowledged. Concurrent acceptance fixture remains matter 3049 / document 93 / task 74 / event 23. No duplicate unchanged ping was sent. Phase 1 stays open; provider Stripe/handset prerequisites remain blocked, and no tool-wide QA signoff is claimed. GitHub main remains unpushed.

## Latest: concurrent date acceptance and Grok results, September 22

Both sites run `94d4c21`. Concurrent document-date acceptance now rolls back and retries the complete transaction, including the duplicate checks. This fixes a reproduced SQLite lock failure when independent requests accept the same dates. Exhausted retries show a clear 503 without retaining partial rows. Unrelated database errors are not retried. No schema or AI-generation changes.

Five baseline cases failed; one unrelated-error check already passed. Focused suite: 43 passed. Full suite: 752 passed, 126 existing warnings in 137.03 seconds. Deployment-image affected suite: 153 passed. Both sites healthy, two changed-file hashes match per site, SQLite integrity OK and zero restarts. Environment and Compose settings stayed unchanged.

Public synthetic matter 3049 (`QA-DATE-CONCURRENT`), document 93: four simultaneous authenticated HTTPS submissions and a later replay all redirected successfully. Exactly one task 74, one event 23 and two creation audit rows remain. Deselection and exact source download bytes were preserved. Zero model calls, no messages or payments. Local tests force the collision; the public run verifies concurrent submission behavior without claiming every request hit the collision window.

Grok independently passed the prior filter/fallback, citation/PDF/keyboard and document-date sequential-replay cases on `500abb8`, with fresh fixtures 3047/document 91/deposition 14 and 3048/document 92/tasks 72,73/event 22. These case passes do not establish whole-tool readiness. Issue 45's no-new-developments claim remains defective. Issue 44's specific note-recency wording is supported by note 28 being created September 22 at 03:40 UTC and the 30-day source selection; that does not date the underlying incident. General narrative date accuracy remains open, as does the alleged false contradiction on deposition 14.

Grok's next batch covers invoice narrative polish, research workflow and contradiction triage. New concurrency retest and wording clarification: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5771990099. The Google Sheet records the case outcomes and open work. Handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-date-concurrency-handoff.md`. GitHub main remains unpushed.

## Latest: client-update filtering across record types, September 22

Both sites run `500abb8`. Internal-prefix and known billing-text exclusions now cover work descriptions, completed task titles, upcoming task titles and calendar titles, as well as notes. Filtering happens before count limits, so excluded records do not crowd out eligible activity. Task/event candidates are fetched in batches. Original records stay unchanged. The preview explains the checks and their limitations.

Twelve baseline regressions failed. The focused suite passed 36 tests; the full isolated suite passed 746 tests with 126 existing warnings in 130.12 seconds. The deployment-image suite passed 147 tests. Both sites are healthy with matching hashes for all three changed files, SQLite integrity OK and zero restarts. Environment and Compose settings were preserved.

Public synthetic fixtures: matter 3045 (`QA-UPDATE-FILTER`) and matter 3046 (`QA-UPDATE-FILTER-FALLBACK`), overflow note 30, saved draft message 146. Each has internal, invoice and hours text plus an eligible record in each of the four affected source types. One real provider preview and one oversized template preview excluded those marked records, preserved eligible sources and left all original text unchanged. The overflow case made zero model calls and saved the exact draft. No email was sent. Exact record IDs and the model response are in the handoff evidence.

These are text heuristics, not a guarantee that all sensitive content is removed. English billing keywords can miss material or exclude useful descriptions, and arbitrary unmarked attorney analysis remains a review responsibility. Existing saved drafts are not rewritten. The previously reproduced unsupported narrative timing/status claims remain open. Provider prerequisites and independent QA still prevent full Phase 1 signoff.

Grok's new bounded retest queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5771205527. Handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-update-filter-handoff.md`.

## Latest: complete client-update sources, September 22

Both sites run `3cf4af4`. Client-update requests preserve complete selected statements instead of clipping sources at 9,000 characters. When the full request exceeds the provider cap, no model call is made and the template keeps complete eligible notes, including later corrections. English and Spanish templates separate file notes from recorded work instead of treating recently recorded notes as work performed recently. Note creation timestamps and the injected current date are omitted from model facts. The preview exposes the source records and selection limits for review.

Six baseline cases failed. Seven new regression cases are included in the final full suite: 734 passed, 126 existing warnings in 129.57 seconds in a fresh temporary checkout with byte-identical changed files. Two earlier full runs had seed-fixture SQLite lock errors (QA headers, then setup guide); logs are retained and the cause is not established. The header module passed alone. Deployment-image affected suite: 135 passed, 28 existing warnings in 67.54 seconds. Both sites have matching hashes for all three changed files, SQLite integrity OK and zero restarts.

Public fixtures: matter 3043 (`QA-UPDATE-CONTEXT`), note 28, 9,618 characters; matter 3044 (`QA-UPDATE-OVERFLOW`), note 29, 13,938 characters. One actual model sample retained the correction from green to red after the old cutoff. The oversized case made zero model calls, retained the complete correction and unknown incident date, and saved unchanged as draft message 144. No email was sent. Browser generation and Enter-key source expansion passed on 3044, with the final correction visible.

**AI factual accuracy remains defective.** The 3043 sample claimed there were no other recent developments, which the selected source records do not establish. A second actual model sample on existing matter 3039 still said documents were received recently, although note 21 supplies no receipt date. Removing exact metadata dates did not eliminate unsupported relative timing. The same draft asserted no immediate next steps, another inference from absence in the selected records. Matter-summary date attribution is unchanged. These are open findings, not a full narrative or Phase 1 signoff.

The template can be long and still requires staff review of eligible note content before sending. History limits, provider prerequisites, independent acceptance and the remaining Phase 1 reviews stay open. Grok's new fixture-specific queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5770889250. Handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-update-context-handoff.md`.

## Latest: deposition quotes checked against sources, September 22

Both sites run `f5135a3`. Absent and repeated quotes now receive an explicit warning without a guessed citation. Unique exact quotes use supported page/line/volume markers from the extracted transcript; model numbers are not trusted. Timestamps inside testimony do not replace recognized line markers. Malformed testimony entries no longer crash a good summary. Existing saved drafts are checked on viewing and export without rewriting them. The page no longer tells staff to paste citations directly into briefs.

Seven corrected baseline cases failed. Ten new regressions are included in the final 727-test local suite; all 128 deployment-image tests passed. Both sites are healthy with matching hashes for all three changed files, SQLite integrity OK and zero restarts. Shared environment and Compose configuration stayed unchanged.

Public synthetic matter 3042 (`QA-CITATION-SOURCE`), transcript 89 and deposition 13 intentionally contain a saved draft with bad references. The repeated answer and absent quote display warnings; two unique quotes correctly resolve to Vol. II 3:3 and 3:4. Internal note 27 and unshared PDF 90 preserve the warnings and correct references. The stored draft remains unchanged. No model call was made for this seeded fixture. Existing real-provider deposition 12 still displays Vol. I 1:3 and Vol. II 1:2. Browser desktop content/layout checks passed; a 390px width check showed no horizontal overflow. PDF text was verified; full PDF layout, mobile navigation and keyboard acceptance remain pending.

Exact matching may flag legitimate OCR, whitespace or punctuation differences. Repeated quotes still require manual source review, and a passage-selection editor is not built. Previously saved notes/PDFs are not rewritten. This is citation source checking, not a factual guarantee for summaries or contradictions. Narrative date attribution, cross-part contradiction quality, provider prerequisites and independent QA remain open. Phase 1 is not complete.

Grok has the new three-case retest queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5770542319. Handoff, limitations and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-deposition-citations-handoff.md`.

## Latest: deposition coverage and volume attribution, September 22

Both sites run `16c533f`. Three confirmed defects are fixed: transcript chunks now fit after counting instructions and matter facts; oversized condensation preserves the part summaries instead of losing later text; and a quote before a new volume marker keeps the volume carried from the prior chunk. Three corrected baseline regressions failed. Final full suite: 717 passed; deployment-image suite: 118 passed. Both sites healthy with matching changed-file hashes and SQLite integrity OK.

One real public model call on synthetic matter 3041 (`QA-DEPOSITION-CITATIONS`), transcript 87, deposition 12 passed the short factual/citation sample. The accepted correction from 9:00 to 10:00 was summarized as corrected testimony. The separate green-signal account was flagged against the red-signal PI facts. Exact quotes cited Volume I 1:3 and Volume II 1:2. Internal note 26 and unshared PDF 88 preserved those citations and the discrepancy.

This is sampled acceptance, not a guarantee of factual accuracy. Matter facts retain their existing 1,500-character limit; ambiguous repeated or paraphrased quotes, cross-chunk contradictions, browser/mobile checks and independent QA remain open. Summary/client-update date attribution remains defective. Stripe test access and authentic handset SMS are still required. Phase 1 is not complete.

Grok has the new fixtures and boundary retests: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5770205483. The earlier fixture instruction was corrected: external deposition comparisons use PI facts and confirmed chronology, not ordinary matter notes. Full evidence and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-deposition-context-handoff.md`.


## Latest: public document-date acceptance, September 22

Application release remains `6f3da92`; no code changes or deployment in this run. Synthetic matter 3040 (`QA-DOCUMENT-DATES`) and unshared documents 85/86 were exercised through public authenticated HTTPS with two actual model calls.

The short source returned exactly the October 12 hearing, October 15 response deadline and October 20 meeting. It skipped the historical letter date and a service-based deadline whose anchor was unknown. The reviewed submission deselected the meeting and changed the filing deadline to October 16. Tasks 54/55 saved correctly; repeating the same submission kept exactly two tasks. Creating the meeting separately produced all-day event 13; repeating it kept exactly one event. The 11,916-character file returned no date from beyond character 10,500 and showed the scan-limit warning.

These sampled extraction, edited-selection, sequential-replay and disclosure checks passed. Concurrent submissions, jurisdictional calculations and independent keyboard/mobile acceptance are not established by this run. The prior 714-test local and 115-test deployment suites still describe the unchanged code and were not repeated. The initial harness whitespace expectation was corrected to match extraction behavior; exact uploaded bytes were verified separately.

Grok received the prepared fixtures for the existing independent case: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5769916333. Handoff and evidence: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-document-dates-handoff.md`. Next executable review: deposition factual/citation acceptance and source-linked date handling. Summary/client-update date attribution remains defective; Stripe test access, authentic handset SMS and independent QA are still required. Phase 1 is not complete.


## Latest: analysis notes excluded from client drafts, September 22

Both sites run `6f3da92`. Saved deposition summaries and PI case overviews now carry the internal marker. Their original generated formats are also recognized for existing notes, without changing stored content. These notes previously entered the source material for client-update drafts. Ordinary progress notes remain eligible.

Eight baseline cases failed. Final local suite: 714 passed. Deployment-image suite: 115 passed. Both sites healthy with matching changed-file hashes and SQLite integrity OK. Public synthetic matter 3039 (`QA-NOTE-PRIVACY`), deposition 11, notes 21 to 25 verified all four analysis notes remained available to staff while only routine note 21 entered client-update facts. One public client-update preview omitted the analysis. No email was sent.

**Date attribution remains defective in summaries and client updates.** The preview treated the routine note timestamp as the document-receipt date, which the note body did not supply. Source-exclusion checks are not full factual acceptance. Document-date and deposition factual/citation acceptance, Grok's independent checks, Stripe test access and authentic handset SMS remain open. Phase 1 is not complete.

New actionable Grok retest: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5769677525. No new independent findings preceded this run, and previous queues remain pending. Full evidence, exact file list and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-deposition-note-handoff.md`.


## Latest: complete summary inputs, September 22

Both sites run `0a21924`. AI summaries no longer silently cut messages at character 300 or cut the full prompt midway through a record. Oversized requests stop with a clear explanation and make no provider call. This limits large-matter summaries until a verified whole-record selection or chunking workflow exists. The review page shows its existing record-count limits and an expandable copy of the source context.

Full local suite: 705 passed. Deployment-image suite: 93 passed. Both sites healthy, all three changed-file hashes match and SQLite integrity is OK. Four regression cases failed before the fix. Public fixture 3038 (`QA-AI-OVERFLOW`) returned the limit explanation with zero new model calls. Browser keyboard generation and source expansion passed on fixture 3037 (`QA-AI-CONTEXT`), retaining the full 512-character message and its later red-light correction.

**Date attribution remains defective.** The latest live sample preserved the unknown incident date but assigned the message-record date to the earlier account and correction. Showing sources helps staff review; it is not an automatic factual validator. No full AI acceptance or Phase 1 completion is claimed. Next work is source-linked output design plus the remaining date-extraction/deposition checks.

Grok has two new actionable retests: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5769344162. The earlier eight-case queue remains pending. Handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-summary-context-handoff.md`. Stripe test access, authentic handset SMS and independent acceptance gates are unchanged. The user-facing QA workbook is a dated snapshot at `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-qa-tracker/Coil-Legal-QA-Tracker.xlsx`.


## Latest: AI source isolation and research exports, September 21

Both sites run `c2a413c`, including the `98ee5ca` fixes. Matter summaries use only messages filed to that matter, preventing another matter for the same client from supplying facts or displacing relevant messages. Research PDFs now preserve literal angle brackets and ampersands in names, notes and excerpts. No schema or provider changes.

Final local full suite: 701 passed. Deployment Python 3.12 affected suites: 89 passed. Both sites are healthy, three changed file hashes match, SQLite integrity is OK and restart counts are zero. Four regression cases failed before the fixes. The exported PDF was visually checked as well as text-extracted.

Six live summaries used synthetic matters 3035 (`QA-AI-ISOLATION-A`) and 3036 (`QA-AI-ISOLATION-B`) for the same client. Every sample excluded B's $98,765.43 settlement and retained A's unfavorable witness account, $1,234.56 estimate and provider record statuses. Estimated usage increased six cents. Public research save/edit/export/download passed for authority 1 and document 84, which remains unshared. Codex browser keyboard search, Supreme Court filtering and full opinion display also passed on the same research code.

**AI date attribution remains defective.** One first-round sample turned a report date into the incident date and invented a trial-scheduling recommendation. Explicit instructions improved the result but did not solve date attribution: one of three final samples still shifted the report date into the incident timeline. Do not mark AI factual acceptance complete. Next engineering work is source-event attribution and output validation, followed by remaining date extraction/deposition samples.

Ian requested more Grok work. The queue now has eight concrete cases: matter isolation, date grounding, PDF text, research browser flow, document date extraction and duplicate prevention, deposition citations/corrections, invoice narrative preservation, and client-update draft isolation. Queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5768649227; independent results pending. Full handoff, fixture details, limitations and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-ai-research-handoff.md`. Stripe test-mode access, authentic handset SMS and remaining independent acceptance still block Phase 1 completion.


## Latest: many-folder and mixed-document ZIP acceptance, September 21

Both sites run `b98647e`. ZIP previews show 25 folders per page and one shared matter-number picker. Saved choices persist across page changes; importing covers all pages. Unknown numbers stop the operation with a clear message. Blank names and ambiguous name/number matches require a choice rather than filing to an unrelated or first matching matter. No schema or provider changes.

Local full suite: 697 passed. Deployment Python 3.12 affected suites: 98 passed. A 500-folder/1,000-matter local preview decreased from 35,535,275 bytes and 500,500 options to 92,481 bytes and 1,000 shared options. Matching uses one database snapshot rather than one query per folder.

Public lab job 1 tested 500 folders across 20 pages with Word, twelve-page PDF, text and email files. The preview was 84,239 bytes with 1,002 matter suggestions. A page-one skip and page-two matter change survived returning to page one. The full import created 499 documents, skipped one and had zero errors in 25 batches, maximum request 0.358 seconds. Every stored file and four public downloads matched exact bytes. A separate read-only check verified all 499 document identifiers/amounts in extracted text and the final-page text in 125 PDFs. No files were shared to the portal.

Both sites are healthy with three matching changed-file hashes, SQLite integrity OK and zero restarts. The temporary lab was removed; public and origin routes return 404. Grok queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5768157971; independent results are pending. Full handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-zip-preview-handoff.md`. Next executable work is broader AI/research acceptance. Provider access and independent browser gates remain open, so Phase 1 is not complete.

## Earlier: ZIP batching and recovery, September 21

Both sites run `2e52988`. ZIP imports start saved jobs and process up to 20 entries or 25 MB of uncompressed data per request. Counts, document records and progress commit together. Repeated starts/cursors do not duplicate work. A file manifest supports cleanup after a failed save or worker exit while preserving committed documents. Recovery after an abrupt exit happens when the job resumes. Upload and guide limits now match: 48 MB per ZIP, 25 MB per document.

Local full suite: 690 passed. Deployment Python 3.12 affected suites: 91 passed. Tests include actual subprocess exit after writing bytes, checkpoint rollback, same-cursor/start concurrency, post-commit preservation, missing archive recovery and permissions. A real multipart check accepted a 46 MB ZIP for preview and gave a clear split-file message for 49 MB.

A separate authenticated firm imported 3,000 unique synthetic text documents through Cloudflare in 150 batches. Maximum batch request: 0.284 seconds. Every stored file matched its expected bytes; three public downloads matched. After restarting workers at file 1,000, a fresh login and replay resumed without duplicates. Lab job 1 completed with 3,000 created, zero errors and 1,931,700 stored bytes. The temporary lab was removed and both public/origin paths return 404.

Both sites are healthy, six changed file hashes match, SQLite integrity is OK and restart counts are zero. Grok's independent browser queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5767641831. Full handoff/backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-zip-resume-handoff.md`. Mixed Office/PDF archives, many-folder previews, wider AI/research samples, provider access and independent browser acceptance remain open. Phase 1 is not complete.

## Earlier: ZIP mapping and identity verification, September 21

Both sites run `27c6bd3`. Explicit folder skips survive saving and commit. Windows ZIP paths import their original bytes. Long paths no longer collide at 120 characters; ambiguous legacy shortened references require review. Duplicate member paths, including slash/backslash aliases, are reported and skipped. No schema or provider changes.

Six new regression cases failed before the fix. Final local suite: 682 passed; deployment Python 3.12 affected suites: 74 passed. The initial full run hit a SQLite lock in an unrelated fixture; that fixture passed alone and a fresh full suite passed. Both sites are healthy with three matching file hashes, SQLite integrity OK and zero restarts.

Public Cloudflare job 27 imported Windows and two long-path files while preserving a saved skip choice: documents 80, 81 and 82 on synthetic matter 3033. Exact downloaded bytes matched. Repeat job 28 created nothing and skipped four. Job 29 created unique document 83 and skipped both ambiguous duplicate members. No files were shared to the portal. Grok's independent retest is queued at https://github.com/Coil-Legal/coil/issues/12#issuecomment-5767064351; acknowledgment/results are pending.

Full handoff and backups: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-zip-review-handoff.md`. ZIP imports remain synchronous; volume, interruption, concurrent commits and cleanup after failed database writes are still open. Phase 1 is not complete. The provider, AI/research and independent browser gates below remain applicable.

## Earlier: resumable CSV verification, September 21

Both sites now run `7e15867`. Large CSVs use owner-authenticated batches with atomic saved progress. Previews clearly sample the first 200 rows. Local suite: 676 passed. Deployment-image affected tests: 68 passed. Both sites are healthy, files match, SQLite integrity is OK and containers have zero restarts.

The 50,000-row import now passes through the actual Cloudflare proxy into a disposable firm. Preview: 0.955 seconds; maximum batch request: 1.655 seconds; total import: 493.843 seconds. All 50,000 rows, 300,000 minutes and 30,000,000 cents reconcile in storage and export. Reconnection and replay passed. The temporary authenticated route was removed after testing.

Actual browser testfirm job 26 passed pause at 1,400, keyboard resume, close/reopen and completion at 5,001 rows. It repeatedly updated one synthetic contact (1809), leaving 1 created, 5,000 updated and 0 errors. Grok's independent verification is still pending: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5766422082.

Full handoff, file list, evidence and recovery paths: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-import-resume-handoff.md`. Phase 1 is still open for provider access and remaining acceptance checks. Large ZIP imports retain their old flow and need separate volume verification.

## Earlier September 21 evidence

Both sites now run `2b21f25`. Portal uploads use staff file validation and text extraction; signing and document delivery verify the sent file hash; the invoice API rejects malformed dates before creating drafts. Full suite: 670 passed. Deployment Python 3.12 affected tests: 117 passed. Both sites have matching hashes, SQLite integrity OK and zero restarts. Public testfirm rejected invalid files and completed valid document 79/signature 6 with a PDF certificate.

Phase 1 still needs the acceptance gates below. Large-import public-proxy behavior is particularly important: the direct 425.5-second commit exceeds Cloudflare's documented default 125-second read timeout. Actual zone behavior is not yet measured; do not count the direct HTTP result as a public browser pass.

Grok's current release queue is https://github.com/Coil-Legal/coil/issues/12#issuecomment-5756766063. No new independent result since September 20 at 03:45 UTC. A recurring review follow-up is active every 30 minutes. Full evidence and recovery paths: `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/coil-phase-review-handoff.md`. Phase 2 progress and Phase 3 prerequisites are recorded in their QA checklists.

## September 20 evidence

2026-09-20. Deployed release `475b50fb72fd7e62ba7b21b990047515389bf6d7` on testfirm and demo. Phase 1 still needs Stripe test-mode checks, authentic SMS delivery and Grok's browser signoff.

Completed application fixes:

- Realization includes receipts from every split payer and uses actual invoice cents, preserving rounding.
- New unbilled work on an already invoiced matter stays WIP instead of becoming a write-down.
- Portal uploads use unique storage names. Two same-name uploads in one second preserve both documents.

Files: `app/blueprints/reports.py`, `app/blueprints/portal.py`, `app/templates/reports/realization.html`, `tests/test_financial_completion.py`, `tests/test_portal_upload_preservation.py`. No schema changes. Shared checkout `/Users/iandolan/General/solo-practice`; isolated implementation `/Users/iandolan/Documents/Codex/2026-09-19/reve/work/coil-money-review`. GitHub main was not pushed.

Validation:

- Full local suite: 655 passed, 114 existing warnings. Log `phase1-completion-full.log`.
- Deployment Python 3.12 affected suites: 64 passed, 7 warnings. Server log `/home/deploy/backups/coil/testfirm.coil.legal/tests-475b50f.log`.
- Both sites healthy on `475b50f`; all five deployed hashes match; both SQLite integrity checks pass.
- Two synthetic portal clients authenticated using actual captured emails. Used links returned 410. Both uploads downloaded identical bytes; other-client downloads returned 404; other-client uploads added no document; private messages stayed isolated.
- Three live summaries retained the unfavorable witness account, exact $1,234.56 estimate and each provider's record status. Actual configured provider was OpenRouter with google/gemini-2.5-flash. Estimated usage rose by 3 cents. CourtListener search and full opinion retrieval worked. The known citation resolved to the same opinion, and the wrong-party-name example returned name_mismatch with found=false. This is sample-based evidence, not a guarantee of every AI answer.
- Direct HTTP import: 50,000 activities, zero errors, 300,000 minutes and 30,000,000 cents. Export matched rows, minutes and cents. Upload 1.7 seconds, preview 122.2 seconds, commit 425.5 seconds, export 5.1 seconds. Public proxy/browser behavior at that duration remains unverified.
- Backup restored all 50,000 records, the 500,000-cent seeded trust balance, upload/PDF hashes and environment into a separate healthy app. Existing-database overwrite was refused. The PDF fixture tested byte preservation, not rendering.
- Actual Docker self-update: a deliberately unhealthy image rolled back; a repeated bad channel stayed pinned; a healthy successor unpinned and started. Backup archives were created before changes.
- Full financial chain in the updated disposable lab: $120 time plus $30 expense invoiced and sent through capture SMTP; $100 deposited to trust; $50 applied; $60 received by check; $40 credited. Result: total $150, paid $110, credit $40, due $0, status paid, remaining trust $50. Revenue CSV showed $110, payment CSV had exactly the two receipts, PDF returned successfully.
- Testfirm's reconciled-through-today guard correctly rejected the same-day deposit. Its reconciliation was preserved. Synthetic testfirm matter QAF1001 (3034), invoice 3033 remains sent at $150 with no payment; the completed accounting chain is in the disposable lab, matter 3/invoice 1.

Email setup:

- Owner-only capture inbox: https://testfirm.coil.legal/qa-mail/. Use an existing owner session. Anonymous and non-owner requests return 403. SMTP uses authentication and STARTTLS. All testfirm mail is captured; demo mail settings are unchanged.
- Synthetic portal clients: phase1-client-a@coil.test (contact 1807, matter 3032) and phase1-client-b@coil.test (1808, 3033). QA staff/owner passwords remain in a protected server file and are not in this report.
- Receiving alias ian+coil-qa@iandolan.com verified in Gmail. Existing receiving account grok-coil-github@agentmail.to authenticates to AgentMail IMAP. One synthetic incoming message was imported once, duplicate import was skipped, and message 125 was manually filed to matter 3032. The custom QA-P1-A number does not match the existing automatic email matter-number pattern.
- Existing Gmail SMTP authentication failed with 535. Working AgentMail SMTP was verified using the already configured inbox credentials. Coil sent a synthetic message and attachment to Ian's receiving alias: Gmail message `1a0c0d3c76faea88`.
- A captured message was delivered externally by a QA-only helper: Gmail message `1a0c0db2ed0f79dc`. Helper location `/home/deploy/apps/coil-qa-mail/send-qa-mail.py`, source `outputs/coil-qa-send-external.py`. Run inside the testfirm container with a captured message ID and either approved QA address. It rewrites MIME recipients and SMTP recipients, preserves attachments, and refuses all other addresses.
- Mailpit's experimental manual relay was disabled after AgentMail retained the original MIME recipient despite the changed SMTP envelope. Capture is the final default. The server helper is the supported external QA path.
- Official configuration references: https://docs.agentmail.to/imap-smtp and https://mailpit.axllent.org/docs/configuration/smtp-relay/.

Infrastructure and recovery:

- Private inbox: `/home/deploy/apps/coil-qa-mail`. SMTP/UI secrets and external relay credential file are protected server files. No public host SMTP port. Original testfirm environment backup is `testfirm-env-before-qa-mail` in that directory.
- Disposable labs: `/home/deploy/apps/coil-phase1-lab`, `coil-phase1-restored`, `coil-phase1-recovery`. Registry and lab containers were stopped after testing; data and evidence remain. The final financial lab uses only the private capture SMTP, no payment credentials.
- Both releases have rollback tags `<project>:before-475b50f` and source archives `/home/deploy/backups/coil/<domain>/source-before-475b50f.tar.gz`. Environment and Compose hashes were preserved by deployment.

Remaining acceptance gates:

- [ ] Ian signs into the open Stripe Chrome tab. Install test keys and the correct signed webhook subscription, then verify successful/declined cards, saved-card retries, installments and real provider redelivery. Current live keys were not used for charges.
- [ ] Authentic Twilio inbound SMS and reply from an authorized external handset. Credentials and webhook configuration are valid; number ending 7961 targets testfirm. Carrier delivery is not yet verified.
- [ ] Grok independently checks report examples, upload preservation, unsharing, signatures and final email/PDF artifacts, client separation, mobile layouts and keyboard behavior.
- [x] Codex CSV proxy/browser checks: 50,000 unique rows through Cloudflare and a 5,001-row browser pause/resume fixture passed on `7e15867`. Independent Grok verification remains part of the browser signoff above.
- [x] Synthetic text ZIP volume and recovery: 3,000 unique files through the public proxy, worker restart, replay, exact stored/downloaded bytes and cleanup verified on `2e52988`.
- [x] Mixed Word/PDF/text/email ZIP sample with 500 matter folders, page-choice persistence, exact bytes and extracted identifiers/amounts on `b98647e`.
- [ ] Grok's independent ZIP preview, keyboard and pause/resume browser checks.
- [ ] Broaden AI factual samples and research browser workflows beyond the successful provider search, opinion and citation checks.
- [ ] Production branded SMTP configuration, offsite recovery and other launch operations need their own signoff. The QA mail setup does not change demo's sender.

Evidence lives in `/Users/iandolan/Documents/Codex/2026-09-19/reve/outputs/`: financial and portal regression logs, `coil-large-import-http.log`, `coil-backup-restore-lab.log`, `coil-recovery-lab.log`, `coil-ai-live.log`, `coil-financial-lab-workflow.json`, inbound and external mail records, release logs and file-hash checks. Earlier failed harness attempts are retained alongside the final evidence; they are not acceptance failures.

Grok queue: https://github.com/Coil-Legal/coil/issues/12#issuecomment-5753024092.
