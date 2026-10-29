# State-first runs and recovery

Run `LinkedIn All 79 Roles` for the complete catalog, or `LinkedIn Procurement
Keywords` for the six broad queries. Buyer remains a keyword but is not one of
79 strict titles. Optional range entries cover 1–23, 24–44 and 45–79.

Each selected role starts directly with all 50 states and DC, using a reusable
51-region matrix. One region per worker means a slow state cannot consume
another state's runtime budget. Two roles advance concurrently; the runner
setting bounds their combined concurrency. Keyword runs use four region workers.

There is no local 1,000-result pagination cutoff: the next page is requested if
LinkedIn continues serving data. LinkedIn can still refuse offsets near 1,000 or
return incomplete results. Source caps remain explicitly reported; removing a
constant does not expose postings hidden behind a source-side cap. A capped
state requires narrower validated searches before exhaustive coverage is possible.
Guest work-type filters are not used as a workaround because they were ignored.

Listings and successful detail responses are journaled before cursor advances.
Partial task journals/checkpoints are uploaded on handled exits. Abrupt runner
destruction before cleanup still requires an external durable sink for guaranteed
recovery. No finite runner can promise uninterrupted execution forever.

Pending regions and missing JDs trigger follow-up runs automatically, preserving
this run's results and selection/window. Improving runs continue; three retries
without improvement pause and preserve the backlog. Source caps and unexpected
planning/export errors do not cause endless blind retries. Disable auto_continue
on dispatch to opt out. previous_remaining and continuation_stalls are internal
counters; leave blank on the initial run. Manual recovery uses resume_run_id from
an earlier run in this repository. Relative publication windows move with time.

Jobs deduplicate by LinkedIn posting ID, preserving different postings with the
same title/employer/location. Thin updates cannot erase full descriptions.

Each workflow exports an all-jobs workbook (All and Strict_79_Roles sheets) and
a strict-only workbook. Strict matching compares the full title against all 79
catalog titles, normalizing Unicode, case and whitespace only. Extra suffixes,
seniority changes, substrings and fuzzy matches do not qualify. Keyword membership
tabs remain in the all-jobs keyword workbook. matched_catalog_role identifies
which exact catalog title qualified each strict row.

Excel text above 32,767 characters continues in additional _part_N columns;
rows beyond the sheet limit continue in numbered sheets. Raw CSV and journals
keep full text. Artifacts request 30-day retention, subject to repository policy.
No database import or deletion is performed.

Exports include search_state: the US state(s) whose searches returned the posting.
Merged postings retain all matching search states, separated by semicolons. This
is search provenance, not the physical job location, which remains in location.
Legacy rows are backfilled from search_location when available.

all_job_links preserves every distinct observed job/application URL across merged
records and resumed runs. Original URL fields remain; a discovered external
apply_url is not replaced by a later LinkedIn listing fallback. This retains
observed links; it does not invent application URLs that the source never supplied.
