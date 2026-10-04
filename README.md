# Lease Lead Automation

Lead collector for a college lease-takeover broker. It finds students posting in off-campus housing Facebook groups who want to get into or out of a lease, and lands them in a Google Sheet sorted by college and by direction (taking over vs. leaving).

## Pipeline

```
Apify task "lease-leads-daily"  --(run succeeded webhook)-->  Make.com scenario  -->  Google Sheet "Lease Leads"
 (Facebook Groups Scraper,                                     (classify post,           (one row per lead,
  13 university housing groups,                                 drop "Skip" posts,        by college + in/out)
  posts from the last 4 days,                                   map fields)
  scheduled daily)
```

1. **Scrape** – An Apify saved task runs the Facebook Groups Scraper on a schedule over 13 housing groups (Penn State, Texas A&M, UGA, USF, UT Austin, UT Dallas and others). Config: [`apify-task-input.json`](apify-task-input.json).
2. **Trigger** – On run success/failure, an Apify HTTP-request integration posts to a Make.com custom webhook (`MAKE_WEBHOOK_URL`, see `.env.example`).
3. **Classify and load** – The Make scenario pulls the run's dataset, classifies each post (lease in / lease out / Skip), excludes Skip posts, and writes the rest to the "Lease Leads" sheet.

Example run: 56 requests, 56 succeeded, 118 results, about 24 seconds, $0.83 of Apify usage.

## Roadmap
- Speed-to-lead: instant outreach when a new lead lands
- Public website for the broker

## Data handling
Scraped leads are real people's posts. No lead data is committed to this repo; `.gitignore` blocks CSV exports.
