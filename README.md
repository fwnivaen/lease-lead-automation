# Facebook Lead Automation

Turn Facebook group posts into a lead pipeline for your business. Collect posts with Apify, qualify them with campaign-specific filters in Make.com, and track leads in Google Sheets. Use the same workflow for service requests, product inquiries, real estate, recruiting, or another lead niche by changing the groups, qualification rules, and Sheet fields.

[![Validate configuration](https://github.com/fwnivaen/facebook-lead-automation/actions/workflows/validate.yml/badge.svg)](https://github.com/fwnivaen/facebook-lead-automation/actions/workflows/validate.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Overview

This repository provides **configuration, setup guides, and offline validation** for an Apify → Make.com → Google Sheets workflow. Scraping, filtering, and delivery run in your own service accounts; this is not a standalone scraper or a hosted lead service.

- **Configurable sources:** select the Facebook groups relevant to your campaign and bound the scrape's post limit and lookback window.
- **Campaign-specific qualification:** define the buying signals, exclusions, categories, and intent that matter to your business in Make and Sheets.
- **A reusable lead tracker:** start with a neutral [Sheet template](examples/lead-sheet-template.tsv) and add niche-specific columns as needed.
- **Offline checks and CI:** validate group URLs, duplicate URLs, limits, and chronological collection before importing a config into Apify.
- **Operational guidance:** documented pagination, deduplication, credit budgeting, and recovery requirements, based on a real deployment audit.

The included actor collects **Facebook group posts**. Other Facebook surfaces, such as Marketplace, Pages, and Lead Ads, need a suitable collector and their own field mapping; they are not implemented here. Qualification is rule-based in the external workflow, not an included AI classifier.

## Pipeline

```text
Facebook groups → Apify saved task → successful-run webhook → Make.com → Google Sheets
                  bounded scrape                            fetch all   lead tracker
                                                            qualify     custom fields
                                                            deduplicate
```

1. **Scrape** — An Apify saved task runs the [Facebook Groups Scraper](https://apify.com/apify/facebook-groups-scraper) over the groups listed in [`apify-task-input.json`](apify-task-input.json). The schedule, cost cap, timeout, and memory are set in Apify itself, not in this file.
2. **Trigger** — An Apify HTTP integration posts run events to your Make.com custom webhook (`MAKE_WEBHOOK_URL`; see [Configuration](#configuration)). Route successful runs to lead processing; send failure/abort/timeout events to an error path.
3. **Qualify and load** — Build a Make scenario to fetch the complete dataset, validate fields, apply your campaign's rules, check stable post identity, and write leads to your Sheet. Add formulas or manual review for any custom categories or intent fields.

The [campaign guide](docs/customization.md) explains how to adapt each layer. The [operations guide](docs/operations.md) preserves the original deployment audit and its known gaps; the desired flow above is not a claim that those live gaps have been fixed.

## Example campaigns

| Campaign | Example signal | Optional fields |
| --- | --- | --- |
| Local services | Someone looking for a cleaner, contractor, or tutor | Service type, area, requested date |
| Products | A buyer asking where to find a product | Product category, quantity, budget |
| Real estate | A request for a rental, roommate, or property | Location, property type, move date |
| Recruiting | A hiring request or candidate availability | Role, skills, location, availability |

These are adaptation examples, not prebuilt classifiers or verified live campaigns. College lease takeovers were the original use case; that source list is retained in [`examples/housing-apify-task-input.json`](examples/housing-apify-task-input.json).

## Status for a new owner

**Live delivery remains unverified end to end.** The October 22, 2026 audit observed a housing-specific deployment, a Make credit pause, and delivery defects. Those historical findings are retained below; current account balances and service state have not been rechecked for this generalization. Before relying on a deployment:

1. Resolve the credit budget (the audit estimates ~400 credits per run, which exceeds a 1,000-credit/month free allowance at the Monday/Thursday cadence) — either upgrade the Make plan or reduce run frequency/cost.
2. Fix the 200-item dataset retrieval cap in Make (recent runs return 226–276 items; anything past 200 is silently dropped).
3. Replace the post-text-hash deduplication with a stable post ID or permalink before trusting the "no duplicate leads" guarantee.
4. Walk the [end-to-end acceptance checklist](docs/operations.md#end-to-end-acceptance-check) with synthetic data in a test destination before pointing it at the real Sheet.

These changes are made and verified in your own Apify, Make, and Google accounts. This repository does not include a Make scenario export or provision the services for you.

## Tech stack

| Layer | Technology |
| --- | --- |
| Scraping | [Apify](https://apify.com/) saved task running the `apify/facebook-groups-scraper` actor |
| Orchestration / delivery | [Make.com](https://www.make.com/) scenario (webhook trigger → dataset fetch → filter → Sheets write) |
| Storage / classification | Google Sheets, with campaign-specific columns, optional formulas, and review status |
| Config validation | Python 3 standard library, `unittest` |
| CI | GitHub Actions (`validate.yml`) |

## Prerequisites

To actually run this pipeline, you need accounts of your own — nothing here is shared or transferable:

- An [Apify](https://apify.com/) account with access to the actor and enough usage budget. The original audited run cost $1.17; your cost depends on current pricing and campaign volume.
- A [Make.com](https://www.make.com/) account on a plan with enough operations/credits for your run cadence (see [Status for a new owner](#status-for-a-new-owner)).
- A Google account with a Sheet you control, shared with your Make scenario.
- Python **3.10+** — only needed to run the offline config validator and tests, not the live pipeline.

## Setup

```sh
git clone https://github.com/fwnivaen/facebook-lead-automation.git
cd facebook-lead-automation
cp .env.example .env   # fill in your own Make webhook URL — see Configuration
python3 scripts/validate_config.py
python3 -m unittest discover -s tests -v
```

Replace `YOUR_TARGET_GROUP` in [`apify-task-input.json`](apify-task-input.json) with your selected group's ID or name; add more URL entries for additional groups. The committed file is a general template, not a ready-to-run list of live targets. The validator checks structure only: it accepts the template but cannot verify that a group exists or that you can collect its posts.

The tests and validator don't contact Apify, Make, or Google. Standing up the live pipeline is a separate process:

1. **Apify** — create an account, add the `apify/facebook-groups-scraper` actor, and create a saved task using [`apify-task-input.json`](apify-task-input.json) as the input. Set your own schedule, cost cap, timeout, and memory limit in the Apify console (these are not stored in this repo). Add an HTTP integration that posts run-success/failure events to your Make webhook.
2. **Make.com** — create a scenario with a custom webhook trigger, and build the fetch → qualify → deduplicate → write-row flow described in the [campaign guide](docs/customization.md). Copy the webhook URL into your own `.env` (see [Configuration](#configuration)). No importable Make blueprint is included.
3. **Google Sheets** — import [`examples/lead-sheet-template.tsv`](examples/lead-sheet-template.tsv) into a Sheet you control and connect it to Make. Map the source fields and add your campaign's optional columns using the [field mapping](docs/customization.md#sheet-fields). No college or lease-direction columns are required.
4. **Verify** — run the [acceptance checklist](docs/operations.md#end-to-end-acceptance-check) in a test destination before enabling real collection or replaying existing events.

## Configuration

The repo contains a placeholder for your Make webhook URL. Store the real value locally or directly in Apify's integration settings:

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

Edit [`apify-task-input.json`](apify-task-input.json) to change group coverage, the post limit, or the lookback window, then re-run the validator before importing it into your Apify task. Change qualification rules and Sheet mappings in those services as described in the [campaign guide](docs/customization.md). GitHub Actions runs the offline checks on every push and pull request. A GitHub push does not update the live task, scenario, Sheet, or schedule.

## Troubleshooting

| Symptom | Likely cause / fix |
| --- | --- |
| `validate_config.py` fails on a group URL | Group URLs must be plain `https://www.facebook.com/groups/<id-or-name>/` or `https://facebook.com/groups/<id-or-name>/` — no post paths, query strings, or auth-embedded URLs. |
| Validator reports a duplicate group | The same URL path was repeated, including variants with/without `www` or a trailing slash. Keep one entry per group; the offline check cannot resolve different vanity/numeric URLs to the same real group. |
| Leads stop appearing in the Sheet | Check your Make.com credit balance first — a paused scenario still shows "Active" in the UI. See [Status for a new owner](#status-for-a-new-owner). |
| Dataset has more items than Sheet rows | The Make scenario's dataset fetch step has a retrieval cap; recent runs can exceed it. See the "Confirmed retrieval cap" finding in `docs/operations.md`. |
| Suspected duplicate or missing leads | Current deduplication hashes post text, not post identity — review the "Deduplication" section of `docs/operations.md` before trusting counts. |
| Scraper returns 0 results for a group | The group may have gone private, been merged, or renamed. Verify the URL still resolves in a browser before assuming a scraper bug. |

## Data handling

Do not commit scraped leads, real webhook URLs, credentials, or unsanitized Make exports. `.gitignore` excludes `.env` files, CSV/XLSX exports, `leads/`, and `exports/`. The committed TSV is an empty header template. Treat every scraped post as a real person's data and write source text to Sheets as literal text. This workflow collects and tracks leads; it does not automatically contact people.

## Roadmap

- Save a sanitized, importable Make scenario blueprint with a tested qualification contract.
- Verify replay-safe deduplication across weekly Sheet tabs.
- Add verified example campaigns beyond the original housing deployment.

## License

[MIT](LICENSE)
