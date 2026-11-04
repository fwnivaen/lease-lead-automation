# Configure a Facebook lead campaign

The workflow can serve any lead niche whose signals appear in Facebook group posts. Changing the niche requires changing the target groups, qualification rules, and output fields. The repository supplies templates and offline checks; configure and test the external services separately.

## Choose source groups

Edit `apify-task-input.json` and replace `YOUR_TARGET_GROUP` with the name or numeric ID of a group relevant to your campaign. Add one `{"url": "https://www.facebook.com/groups/<group-id-or-name>/"}` entry per group. Select groups the actor can access; offline validation cannot check access or existence.

The template uses a 25-post limit, chronological sorting, and a four-day lookback. Adjust limits and lookback for your volume and collection cadence, accounting for cost, overlap, and gaps. Scheduling happens in Apify, not this JSON file. The 11-group housing config in `examples/housing-apify-task-input.json` is a historical example, not the default target list or a guarantee that those groups still work.

Run `python3 scripts/validate_config.py`, then import the edited input into a saved Apify task. Use a campaign-specific name, such as `service-leads`, rather than assuming the original task's name or schedule.

## Define qualification in Make

Write down what a useful lead means before creating filters:

| Decision | What to specify | Illustrative local-services campaign |
| --- | --- | --- |
| Positive signals | Expressions that indicate relevant demand | "looking for a cleaner", "need a plumber" |
| Exclusions | Posts outside the campaign's purpose | A provider advertising services, unrelated sales |
| Categories | Your product, service, or lead types | Cleaning, plumbing, electrical |
| Intent | The action the author is seeking | Requesting a service, offering a service, unclear |
| Optional attributes | Fields to extract only when stated | Area, budget, requested date |
| Review rule | How to handle uncertain/conflicting signals | Keep for review with a reason |

These sample phrases are illustrative, not a supplied or tested classifier. Housing-keyword filters from the old scenario must be replaced for a different campaign. Avoid broad exclusions that discard useful posts; check relevant examples with and without each exclusion. Leave unknown values blank or mark them for review.

Build a Make scenario with this flow:

1. Receive the Apify event and accept only successful runs into the lead route.
2. Fetch the event run's dataset, paginate through all items with explicit bounds, and validate required source fields.
3. Apply the campaign's qualification rules. Count qualified, irrelevant, and review items separately.
4. Use a stable source post ID or canonical permalink for deduplication across runs and any weekly tabs. Keep campaigns in separate namespaces if their deduplication should be independent.
5. Write accepted leads to the Sheet and record delivery state only after a confirmed write. Serialize the lookup/write path or use a durable uniqueness mechanism; recover ambiguous writes before retrying.
6. Reconcile retrieved, skipped, duplicate, review, failed, and written counts. Alert on failed or incomplete delivery.

No importable Make blueprint or executable qualification engine is included. The [operations audit](operations.md) records retrieval, deduplication, concurrency, and credit issues found in the original scenario. Use it when building or adapting yours.

## Sheet fields

Import [`examples/lead-sheet-template.tsv`](../examples/lead-sheet-template.tsv) into Google Sheets using a tab separator. It contains headers only, with no personal data or formulas. Map the actual actor output in Make; this table describes logical fields, not guaranteed actor JSON property names.

| Column | Purpose |
| --- | --- |
| `lead_id` | Stable post ID or canonical permalink; optionally include a campaign namespace |
| `collected_at` | Timestamp of collection or processing, using a documented convention |
| `post_created_at` | Source post timestamp, if available |
| `author` | Source display name, if available; never use it as unique post identity |
| `post_text` | Source text written as literal text |
| `permalink` | Link back to the source post |
| `group` | Source group title or URL |
| `category` | Campaign-specific category, or blank if unknown |
| `intent` | Campaign-specific intent, or `unclear` |
| `status` | Review/work status, such as `new`, `review`, or `closed` |
| `notes` | Qualification reason or human notes |

Add columns such as service type, location, budget, role, or move date only when useful to your campaign. College and lease direction are examples of optional fields for housing. Formula-based enrichment belongs in separate columns with controlled formulas; scraped text must not be interpreted as a formula.

A single leads tab is sufficient. If you use weekly tabs, define whether the week follows post time, run time, or processing time and use the same timestamp for tab creation and row insertion. Deduplication must persist across tabs.

## Verify before relying on it

Use synthetic inputs and a separate test destination to check:

- A relevant request is accepted with the expected category and intent.
- An irrelevant post is skipped and an ambiguous post reaches review.
- A relevant post containing an exclusion phrase is handled deliberately.
- Missing optional attributes remain unknown rather than invented.
- Repeated events, edited posts, concurrent runs, and week rollover do not duplicate or lose leads.
- A dataset larger than one page is fully accounted for, including items beyond the old 200-item cap.
- Interrupted writes recover safely and formula-like source text stays literal.

Record the observed counts and service settings privately. Passing repository checks only establishes config structure; it does not prove live collection, qualification quality, Sheet delivery, or replay safety. Follow the full [acceptance checklist](operations.md#end-to-end-acceptance-check) for a live deployment.

## Adapting the original housing deployment

Use a separate test task, scenario, and Sheet while adapting existing services. Preserve the original schedules, queued events, deduplication state, and source data. A repo rename or template edit does not migrate those resources. Budget a funded test run and resolve the audited gaps before switching production traffic.
