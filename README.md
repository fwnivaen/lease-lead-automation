# Lease Lead Automation

Collect public Facebook housing-group posts for a college lease-takeover broker. Apify scrapes the posts; Make.com filters posts and writes leads to Google Sheets, where formulas classify college and direction.

## Current setup

```text
Apify saved task lease-leads-daily → Make.com webhook → keyword filter / deduplication → Lease Leads sheet formulas
```

- Actor: [apify/facebook-groups-scraper](https://apify.com/apify/facebook-groups-scraper).
- Input: [`apify-task-input.json`](apify-task-input.json), aligned with the live task observed October 22, 2026: **11 groups**, **25-post limit**, **4-day lookback**, chronological sorting.
- Despite the task name, the live schedule runs **Monday and Thursday at 10:00 AM America/New_York**, not daily.
- Observed live run options: $2 maximum cost per run, 900-second timeout, 4 GB memory, `latest` build. These are configured in Apify, not in the input JSON.
- Apify's HTTP integration receives terminal run events. Make must route successful runs to dataset processing and failures to error handling.

This repository stores scraper input and maintenance checks. It does **not** deploy the schedule, webhook, Make scenario, classification rules, or Sheet mappings. Editing this repository does not update those services.

## Live status (October 22, 2026)

Apify scraping and webhook dispatch succeeded. Make is paused because its free credits are exhausted; the owner chose to wait for the displayed reset in eight days. The live Make scenario also has a 200-item dataset cap despite recent 226–276-item datasets. See the operations guide for credit-budget, deduplication, literal-text, and replay findings. The pipeline is **not yet verified end to end**.

## Check the repository

Requires Python 3.10+; no extra packages or credentials:

```sh
python3 scripts/validate_config.py
python3 -m unittest discover -s tests -v
```

GitHub Actions runs both commands on pushes and pull requests. Checks enforce this project's bounded chronological scrape policy and reject malformed or duplicate group URLs. They do not prove that groups remain public or that live delivery works. The validator deliberately supports a narrower policy than the [actor input schema](https://apify.com/apify/facebook-groups-scraper/input-schema).

## Live verification and recovery

See [`docs/operations.md`](docs/operations.md) for the audit results, duplicate-prevention requirements, and end-to-end verification steps. A successful scrape or webhook HTTP response alone does not prove a row reached Google Sheets.

## Data handling

Do not commit scraped leads, real webhook URLs, credentials, or unsanitized Make exports. `.gitignore` excludes environment files, CSV/XLSX exports, `leads/`, and `exports/`; `.env.example` is a placeholder only. No local program currently reads it. JSON exports must also be reviewed before committing.

## Roadmap

- Save a sanitized Make scenario blueprint, classification contract, and Sheet column mapping.
- Verify replay-safe deduplication across weekly Sheet tabs.
- Speed-to-lead outreach and a broker website are future work.
