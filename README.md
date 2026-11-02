# Lease Lead Automation

Collect public Facebook housing-group posts for a college lease-takeover broker. Apify scrapes the posts; Make.com filters posts and writes leads to Google Sheets, where formulas classify college and direction (taking over a lease vs. leaving one).

[![Validate configuration](https://github.com/fwnivaen/lease-lead-automation/actions/workflows/validate.yml/badge.svg)](https://github.com/fwnivaen/lease-lead-automation/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

This repository is the **config and offline-validation layer** for a three-service pipeline. It does not itself run the scrape, the webhook, or the Sheet write — those live in your own Apify, Make.com, and Google accounts. What's here:

- The scraper's input config (`apify-task-input.json`), with an offline validator and tests that catch malformed or duplicate group URLs before you push a config change live.
- A full operational write-up (`docs/operations.md`) from a real audit of the pipeline: exact scenario wiring, a confirmed dataset-retrieval cap, deduplication weaknesses, and an end-to-end verification checklist. Read this before you touch the live services — it documents real, specific failure modes this pipeline has hit.

## Pipeline

```text
Apify saved task "lease-leads-daily"  --(run succeeded webhook)-->  Make.com scenario  -->  Google Sheet "Lease Leads"
 (Facebook Groups Scraper,                                           (dataset fetch, keyword                (one row per lead,
  11 university housing groups,                                      filter, dedup check,                    weekly tab, college +
  25-post limit, 4-day lookback,                                      write row)                               direction via formulas)
  Mon/Thu 10:00 AM America/New_York)
```

1. **Scrape** — An Apify saved task runs the [Facebook Groups Scraper](https://apify.com/apify/facebook-groups-scraper) over the groups listed in [`apify-task-input.json`](apify-task-input.json). The schedule, cost cap, timeout, and memory are set in Apify itself, not in this file.
2. **Trigger** — On run success/failure, an Apify HTTP integration posts to a Make.com custom webhook (`MAKE_WEBHOOK_URL`; see [Configuration](#configuration)).
3. **Classify and load** — The Make scenario fetches the run's dataset, applies a keyword filter and a post-text-hash deduplication check, and appends surviving rows to the current week's tab in the "Lease Leads" Google Sheet. College and direction (lease in / lease out) are derived by **Sheet formulas**, not inside Make.

See [`docs/operations.md`](docs/operations.md) for the exact Make scenario wiring, known gaps (a 200-item dataset retrieval cap, weak deduplication, no write-confirmation/replay safety), and the steps to verify the pipeline end to end before relying on it.

## Status for a new owner

**This pipeline is not verified end to end**, and Make.com was paused for exhausted free-tier credits as of the last audit. Before you rely on this for real leads:

1. Resolve the credit budget (the audit estimates ~400 credits per run, which exceeds a 1,000-credit/month free allowance at the Monday/Thursday cadence) — either upgrade the Make plan or reduce run frequency/cost.
2. Fix the 200-item dataset retrieval cap in Make (recent runs return 226–276 items; anything past 200 is silently dropped).
3. Replace the post-text-hash deduplication with a stable post ID or permalink before trusting the "no duplicate leads" guarantee.
4. Walk the [end-to-end acceptance checklist](docs/operations.md#end-to-end-acceptance-check) with synthetic data in a test destination before pointing it at the real Sheet.

None of this requires code changes in this repository — it's configuration and testing inside your own Apify and Make accounts.

## Tech stack

| Layer | Technology |
| --- | --- |
| Scraping | [Apify](https://apify.com/) saved task running the `apify/facebook-groups-scraper` actor |
| Orchestration / delivery | [Make.com](https://www.make.com/) scenario (webhook trigger → dataset fetch → filter → Sheets write) |
| Storage / classification | Google Sheets, with formulas for college and lease direction |
| Config validation | Python 3 standard library, `unittest` |
| CI | GitHub Actions (`validate.yml`) |

## Prerequisites

To actually run this pipeline, you need accounts of your own — nothing here is shared or transferable:

- An [Apify](https://apify.com/) account with billing enabled (the Facebook Groups Scraper actor costs ~$1–2 per run at this scale) and your own API token.
- A [Make.com](https://www.make.com/) account on a plan with enough operations/credits for your run cadence (see [Status for a new owner](#status-for-a-new-owner)).
- A Google account with a Sheet you control, shared with your Make scenario.
- Python **3.10+** — only needed to run the offline config validator and tests, not the live pipeline.

## Setup

```sh
git clone https://github.com/fwnivaen/lease-lead-automation.git
cd lease-lead-automation
cp .env.example .env   # fill in your own Make webhook URL — see Configuration
python3 scripts/validate_config.py
python3 -m unittest discover -s tests -v
```

The validator and tests only check `apify-task-input.json` for structural correctness (clean HTTPS Facebook group URLs, no duplicates, a bounded chronological lookback). They don't contact Apify, Make, or Google — standing up the live pipeline is a separate, manual process:

1. **Apify** — create an account, add the `apify/facebook-groups-scraper` actor, and create a saved task using [`apify-task-input.json`](apify-task-input.json) as the input. Set your own schedule, cost cap, timeout, and memory limit in the Apify console (these are not stored in this repo). Add an HTTP integration that posts run-success/failure events to your Make webhook.
2. **Make.com** — create a scenario with a custom webhook trigger, and build the fetch → filter → deduplicate → write-row flow described in [`docs/operations.md`](docs/operations.md). Copy the webhook URL into your own `.env` (see [Configuration](#configuration)).
3. **Google Sheets** — create a sheet with the columns described in the "Sheet mapping" section of `docs/operations.md` (date, author, post text, permalink, group title, status, college/direction formulas, extracted phone/email formulas, a duplicate-flag formula), and connect it to your Make scenario.

## Configuration

This repo stores one secret-shaped value, your Make webhook URL, as an environment variable. Copy the template and fill in your own:

```sh
cp .env.example .env
```

| Variable | Purpose |
| --- | --- |
| `MAKE_WEBHOOK_URL` | Your own Make.com custom webhook that receives Apify run-success/failure events. Never commit the real value — `.gitignore` excludes `.env` and only tracks `.env.example`. |

No script in this repository currently reads `.env` — it documents the one value Apify's HTTP integration needs, so you can paste it directly into your own Apify integration config. Apify API tokens, Make API keys, and Google service-account credentials are configured directly in those services' consoles, not in this repository.

## Usage

```sh
python3 scripts/validate_config.py        # check apify-task-input.json is well-formed
python3 -m unittest discover -s tests -v  # run the config test suite
```

Edit [`apify-task-input.json`](apify-task-input.json) to change group coverage, the post limit, or the lookback window, then re-run the validator before pushing the change to your live Apify task. GitHub Actions runs both commands on every push and pull request.

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `validate_config.py` fails on a group URL | Group URLs must be plain `https://www.facebook.com/groups/<id-or-name>/` or `https://facebook.com/groups/<id-or-name>/` — no post paths, query strings, or auth-embedded URLs. |
| Validator reports a duplicate group | The same group was added under both a vanity name and its numeric ID, or with/without a trailing slash. Keep one entry per group. |
| Leads stop appearing in the Sheet | Check your Make.com credit balance first — a paused scenario still shows "Active" in the UI. See [Status for a new owner](#status-for-a-new-owner). |
| Dataset has more items than Sheet rows | The Make scenario's dataset fetch step has a retrieval cap; recent runs can exceed it. See the "Confirmed retrieval cap" finding in `docs/operations.md`. |
| Suspected duplicate or missing leads | Current deduplication hashes post text, not post identity — review the "Deduplication" section of `docs/operations.md` before trusting counts. |
| Scraper returns 0 results for a group | The group may have gone private, been merged, or renamed. Verify the URL still resolves in a browser before assuming a scraper bug. |

## Data handling

Do not commit scraped leads, real webhook URLs, credentials, or unsanitized Make exports. `.gitignore` excludes `.env` files, CSV/XLSX exports, `leads/`, and `exports/`. Treat every scraped post as a real person's data.

## Roadmap

- Save a sanitized Make scenario blueprint, classification contract, and Sheet column mapping to this repo.
- Verify replay-safe deduplication across weekly Sheet tabs.
- Speed-to-lead outreach and a public website for the broker are future work.

## License

[MIT](LICENSE)
