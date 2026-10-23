# Operations and audit

## Audit: October 22, 2026

Verified through the signed-in Apify console:

- Saved task `lease-leads-daily` uses 11 groups, a 25-post limit, and a 4-day lookback. Repository input was stale (13 groups / 30 posts) and has been aligned with the observed live settings. Chronological sorting is explicit in the repository and displayed as New posts in the console.
- Schedule is enabled for Monday and Thursday at 10:00 AM America/New_York. Next scheduled run shown: October 26, 2026 at 10:00 AM.
- Latest run `66cB7r4iQ0uOJkgsS` succeeded October 22: 97 requests succeeded, 0 failed, 234 dataset results, approximately 45 seconds, $1.17 usage. All seven retained runs shown succeeded. Dataset results are not necessarily qualified leads.
- HTTP integration is enabled. Its last dispatch was marked Succeeded on October 22. This confirms dispatch acceptance, not completed Make processing or Sheet delivery. The destination URL is intentionally omitted.
- Make.com was signed out, so classification, scenario status, retries, and Sheet writes could not be verified.
- The Google Sheets connector returned permission denied for the existing workbook. The browser showed weekly tabs through October 12 and a last-edit indicator of six days ago. That is a reason to investigate downstream delivery, not proof of a broken pipeline.
- No Make blueprint, classifier, Sheet mapping, previous tests, or CI existed in the repository. No live execution or paid test run was triggered during this audit.

## End-to-end acceptance check

1. Sign in to Make and inspect the scenario receiving the existing Apify integration. Confirm it is active and find the execution corresponding to the latest run ID above.
2. On a successful event, fetch the dataset belonging to that event's run. Follow pagination until all items have been read; do not assume a single response contains the entire dataset. Failure/abort/timeout events must not enter the lead-write route.
3. Verify required source fields before classification. Keep unknown college or ambiguous intent for review rather than inventing values. Check synthetic examples for lease in, lease out, irrelevant posts, and ambiguous posts against the actual classifier.
4. Verify the target workbook, current weekly tab, column mapping, permissions, and error handling. Write untrusted post text as plain text, not executable formulas. Reconcile dataset items with skipped, duplicate, rejected, failed, and written counts.
5. Prove replay safety with synthetic fixtures in a test destination: processing the same event twice and the same post from a second run must not add duplicate leads. Test week rollover as well.
6. Inspect failed executions and retry behavior before replaying production data. Record the final counts and successful Sheet delivery without committing personal data.

## Duplicate prevention

Monday/Thursday collection with a four-day lookback overlaps. Deduplication must persist across runs and across weekly tabs. Use a stable source post ID (or canonical post permalink if no ID exists), not author name or post text. A per-run ID alone will not prevent cross-run duplicates.

Serialize the lookup/write path or use a durable store with uniqueness guarantees so concurrent deliveries cannot both append a row. Do not permanently mark a lead complete before its Sheet write succeeds; store enough delivery state to reconcile an interrupted write before retrying. A blind search-then-append flow is vulnerable to concurrent duplicates. These requirements remain unverified until the Make scenario can be inspected.

## Configuration changes

The live task is the observed baseline for this cleanup. To change group coverage, limits, or cadence, review cost and collection gaps, update Apify and this repository together, and verify the next scheduled run. Preserve the four-day window unless the schedule is changed deliberately. Keep real service identifiers and secrets in private operational records; commit only sanitized blueprints and synthetic fixtures.
