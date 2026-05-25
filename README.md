# job-search

Automated daily job alerts for digital content, accessibility, communications,
and policy roles in mission-driven organisations (charities, universities,
NHS, civil service, unions).

## What it does

Every morning at 08:00 UK time:

1. Fetches new listings from job boards (jobs.ac.uk, NHS Jobs, Civil Service
   Jobs, Guardian Jobs, DWP Find a Job, a11yjobs.com)
2. Filters by keyword (digital content, accessibility, web, etc.), title
   exclusions (HR, teaching, frontline, etc.), and location (commute zone,
   remote, or hybrid in flexible cities)
3. Ranks roles by sector weighting (charities, universities, public sector first)
4. Compares against yesterday's results to identify what's new
5. Sends an email digest with the top 10 plus a link to the full list
6. Publishes the full list as a webpage at the configured GitHub Pages URL

## Files

- `scraper.py` — main script
- `sources.py` — list of job sources and how to query each
- `filters.py` — keyword + location + sector filtering rules
- `requirements.txt` — Python dependencies
- `.github/workflows/daily.yml` — GitHub Actions schedule
- `seen_jobs.json` — auto-generated record of jobs already seen (don't edit)
- `docs/index.html` — auto-generated daily webpage

## To change the filters

Edit `filters.py` — clearly commented sections for inclusion keywords,
exclusion title terms, locations, and Welsh language rules.

## To add or remove a job source

Edit `sources.py`. Set `"enabled": False` to silence a source without
deleting it.

## Secrets required (set in repo Settings → Secrets and variables → Actions)

- `EMAIL_FROM` — Gmail address the scraper sends from
- `EMAIL_TO` — your inbox
- `EMAIL_APP_PASSWORD` — Gmail app password (not your normal password)
- `PAGES_URL` — URL of the published GitHub Pages site (used in the email)
