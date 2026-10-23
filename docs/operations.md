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

## Follow-up: signed-in Make inspection, October 22

The user chose to wait for the credit reset rather than purchase credits. Make's dashboard reports approximately 1,252 / 1,000 credits used, -252 remaining, and a reset in eight days. It explicitly says scenarios are paused. The scenario is marked Active but that does not override the organization credit pause. No paid run, replay, purchase, or live configuration change was made.

Observed scenario: **Integration Apify, Google Sheets**, ID `6463445`.

- Latest history entry: October 15, successful, 401 credits; October 12 used 396 credits. The scenario shows two queued records and no currently active run. Queue contents have not been reconciled with the two later Apify runs.
- Flow: Watch Task Runs → Google Sheets batchUpdate (duplicate weekly template) → Get Dataset Items → Real leads only filter → `lease_seen_posts` existence check → Add a Row → mark record in `lease_seen_posts`. A Resume error route is attached to weekly tab creation.
- **Confirmed retrieval cap:** Get Dataset Items maps the event's `defaultDatasetId`, JSON/Clean, limit **200**, no offset. Recent datasets contain 226–276 items. The scenario has no visible pagination stage; posts beyond the cap are not passed through the lead filter. Add complete dataset retrieval/pagination with explicit bounds and count reconciliation before calling delivery complete; simply increasing the cap does not guarantee future completeness and increases credit use.
- **Credit budget:** the two latest Make executions cost roughly 400 credits each. At eight runs per month that is approximately 3,200 credits, already above the observed 1,000-credit allowance. Reset alone will not make this cadence sustainable. Measure operations per unique lead, reduce redundant per-post operations, then choose a sustainable cadence or allowance with the owner.
- **Deduplication:** both lookup and final record use an MD5 of a lowercased, punctuation-stripped prefix of post text (150 characters), not post identity. Distinct posts sharing that prefix can be suppressed, and edited posts can appear new. The Sheet also marks repeated post URLs or author names within the current tab as DUP; an author name is not unique post identity. Preserve the existing store during any migration; introduce a versioned stable post-ID/permalink key and explicitly reconcile old records before replaying.
- **Concurrency/recovery:** Process data in order is No; Store incomplete executions is No. Lookup followed by append is therefore not a uniqueness guarantee under concurrent delivery. Configure and verify serialization plus recovery/reconciliation before replay tests. Do not clear the data store or queued events to make testing easier.
- **Sheet mapping:** Add a Row targets the expected workbook and a dynamic `Week of YYYY-MM-DD` tab. Date, author, post text, permalink, group title, status, college/direction formulas, extracted phone/email formulas, and a DUP formula are mapped. Classification occurs in Sheet formulas after a broad Make keyword filter, so the old description of classification entirely inside Make was inaccurate.
- **Untrusted text:** Add a Row uses User entered for the whole row, including direct author/text/title mappings. Those source strings can be interpreted as formulas. Preserve intended generated formulas while writing scraped strings as literal text, then test leading `=`, `+`, `-`, and `@` fixtures in a separate test destination.
- **Delayed replay/week rollover:** both weekly tab creation and row insertion calculate the week from `now`. Queued historical runs will be placed in the processing week's tab. Decide whether grouping should follow post date, run date, or processing date before replay; derive both steps from the same chosen timestamp.
- **Filters:** a positive housing-keyword regex plus two exclusion regexes runs before deduplication. Direction and college remain heuristic formulas. Changes need synthetic acceptance cases and owner review, especially where exclusions could remove valid leads.

### Before resuming after the reset

1. Resolve the 200-item cap, sustainable credit budget, source-text handling, and replay-safe deduplication/recovery in a testable scenario copy.
2. Reconcile queued event IDs with Apify datasets before allowing automatic backlog processing. Preserve original data and state; verify retention before planning a delayed replay.
3. Test pagination boundaries, repeated events, concurrent deliveries, interrupted Sheet writes, and weekly rollover using synthetic inputs. Compare actual counts with expected writes/skips/duplicates.
4. Only then resume/replay production events and verify the resulting Sheet rows. Until these steps pass, the pipeline is not end-to-end verified.
