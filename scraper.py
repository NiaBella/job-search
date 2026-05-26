"""
Main job scraper.

Workflow:
1. Load list of jobs we've already seen (seen_jobs.json)
2. For each enabled source: fetch its URLs, parse via source-specific parser
3. Apply filters (filters.py)
4. Score and rank
5. Compare against seen_jobs.json - anything new gets reported
6. Send email digest (top 10) and write HTML page (all)
7. Update seen_jobs.json
"""

import json
import os
import smtplib
import ssl
import sys
import time
import hashlib
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import requests

from sources import SOURCES, SECTOR_WEIGHTS
from filters import passes_filters, score
import parsers


# ============================================================
# CONFIG
# ============================================================
SEEN_FILE = "seen_jobs.json"
OUTPUT_HTML = "docs/index.html"
DIGEST_TOP_N = 10
REQUEST_TIMEOUT = 30

# Realistic browser headers (some sites block default Python user agents)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}

# Email config from environment variables (set in GitHub Secrets)
SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
EMAIL_FROM = os.environ.get("EMAIL_FROM", "")
EMAIL_TO = os.environ.get("EMAIL_TO", "")
EMAIL_APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")
PAGES_URL = os.environ.get("PAGES_URL", "")


# ============================================================
# PARSER REGISTRY
# ============================================================
# Maps the 'parser' field in sources.py to the actual function
PARSER_REGISTRY = {
    "jobsacuk_rss": parsers.parse_jobsacuk_rss,
    "charityjob_html": parsers.parse_charityjob_html,
    "guardianjobs_html": parsers.parse_guardianjobs_html,
    "findajob_html": parsers.parse_findajob_html,
    # Future parsers added here as we build them
}


# ============================================================
# DEDUPING
# ============================================================
def job_id(job):
    """Stable identifier for a job (used for dedup + 'have I seen this?')."""
    key = (job.get("title", "") + "|" + job.get("url", "")).lower().strip()
    return hashlib.sha1(key.encode()).hexdigest()[:16]


def load_seen():
    if os.path.exists(SEEN_FILE):
        try:
            with open(SEEN_FILE) as f:
                return set(json.load(f))
        except Exception:
            return set()
    return set()


def save_seen(seen_set):
    with open(SEEN_FILE, "w") as f:
        json.dump(sorted(seen_set), f, indent=2)


# ============================================================
# FETCH
# ============================================================
def fetch(url):
    """Fetch a URL with error handling."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=REQUEST_TIMEOUT)
        r.raise_for_status()
        return r.text
    except Exception as e:
        print(f"  ! fetch failed for {url}: {e}", file=sys.stderr)
        return None


def scrape_source(source):
    """Fetch and parse one source. Returns a list of jobs."""
    if not source.get("enabled", True):
        return []

    parser_name = source.get("parser")
    parser_fn = PARSER_REGISTRY.get(parser_name)
    if not parser_fn:
        print(f"  ! No parser registered for '{parser_name}' (source: {source['name']})")
        return []

    jobs = []
    for url in source.get("urls", []):
        print(f"  Fetching {source['name']}")
        content = fetch(url)
        if content:
            parsed = parser_fn(content, source)
            jobs.extend(parsed)
        time.sleep(1)  # polite delay between requests

    # Dedupe by URL within source
    seen_urls = set()
    unique = []
    for j in jobs:
        if j.get("url") and j["url"] not in seen_urls:
            seen_urls.add(j["url"])
            unique.append(j)

    print(f"  -> {len(unique)} jobs from {source['name']}")
    return unique


# ============================================================
# EMAIL
# ============================================================
def build_email_html(new_jobs, all_jobs_today, pages_url):
    """Build the HTML body for the digest email."""
    today = datetime.now(timezone.utc).strftime("%A %d %B %Y")
    top = new_jobs[:DIGEST_TOP_N]

    parts = [
        f"""<html><body style="font-family: Arial, sans-serif; max-width: 700px; margin: 0 auto; padding: 20px; color: #1a1a1a;">""",
        f"<h1 style='font-size:20px;'>Job digest - {today}</h1>",
        f"<p>Found <strong>{len(new_jobs)} new roles</strong> today (out of {len(all_jobs_today)} matching today).</p>",
    ]

    if not new_jobs:
        parts.append("<p>Nothing new to report. The scraper ran successfully.</p>")
    else:
        parts.append(f"<h2 style='font-size:16px; border-top: 1px solid #ccc; padding-top:12px;'>Top {len(top)}:</h2>")
        for job in top:
            flag_html = ""
            if job.get("_loc_status") == "include_flag":
                flag_html = " <span style='background:#fff3cd; padding:1px 6px; font-size:11px; border-radius:3px;'>check location</span>"
            parts.append(f"""
            <div style="border-bottom: 1px solid #eee; padding: 10px 0;">
                <div><a href="{job['url']}" style="font-weight:bold; color:#1a4480; text-decoration:none;">{_escape(job['title'])}</a>{flag_html}</div>
                <div style="font-size:12px; color:#555;">{_escape(job.get('location',''))} &middot; {_escape(job['source'])}</div>
            </div>""")

        if len(new_jobs) > DIGEST_TOP_N:
            parts.append(f"<p>And <strong>{len(new_jobs) - DIGEST_TOP_N} more</strong> - see the full list:</p>")

    if pages_url:
        parts.append(f'<p><a href="{pages_url}" style="display:inline-block; background:#1a4480; color:white; padding:8px 16px; text-decoration:none; border-radius:4px;">View all results &rarr;</a></p>')

    parts.append("<p style='font-size:11px; color:#888; margin-top:30px;'>Automated daily job digest. Edit filters by updating filters.py in the repo.</p>")
    parts.append("</body></html>")
    return "\n".join(parts)


def send_email(new_jobs, all_jobs_today):
    """Send the digest email via Gmail SMTP."""
    if not (EMAIL_FROM and EMAIL_TO and EMAIL_APP_PASSWORD):
        print("Email credentials not set - skipping email send.")
        return

    today = datetime.now(timezone.utc).strftime("%d %b %Y")
    if new_jobs:
        subject = f"[Jobs] {len(new_jobs)} new roles - {today}"
    else:
        subject = f"[Jobs] No new roles - {today}"

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = EMAIL_FROM
    msg["To"] = EMAIL_TO

    html = build_email_html(new_jobs, all_jobs_today, PAGES_URL)
    msg.attach(MIMEText(html, "html"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context) as server:
        server.login(EMAIL_FROM, EMAIL_APP_PASSWORD)
        server.send_message(msg)
    print(f"Email sent to {EMAIL_TO}")


# ============================================================
# HTML PAGE
# ============================================================
def write_html_page(all_jobs_today):
    """Generate the GitHub Pages HTML showing today's results."""
    os.makedirs("docs", exist_ok=True)
    today = datetime.now(timezone.utc).strftime("%A %d %B %Y, %H:%M UTC")

    rows = []
    for job in all_jobs_today:
        flag = ""
        if job.get("_loc_status") == "include_flag":
            flag = '<span class="flag">check location</span>'
        rows.append(f"""
        <tr data-sector="{_escape(job['sector'])}" data-loc-status="{job.get('_loc_status','')}">
            <td><a href="{_escape(job['url'])}" target="_blank">{_escape(job['title'])}</a> {flag}</td>
            <td>{_escape(job.get('location',''))}</td>
            <td>{_escape(job['source'])}</td>
            <td>{_escape(job.get('sector',''))}</td>
            <td>{job.get('score', '')}</td>
        </tr>""")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>Job results - {today}</title>
<style>
    body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Arial, sans-serif;
            max-width: 1100px; margin: 0 auto; padding: 20px; color: #1a1a1a; }}
    h1 {{ font-size: 22px; }}
    .meta {{ color: #666; font-size: 13px; margin-bottom: 16px; }}
    .filters {{ background: #f5f5f0; padding: 12px; border-radius: 6px; margin-bottom: 16px; }}
    .filters label {{ margin-right: 16px; font-size: 14px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th {{ background: #1a1a1a; color: white; text-align: left; padding: 8px; font-size: 13px; }}
    td {{ padding: 8px; border-bottom: 1px solid #eee; font-size: 14px; vertical-align: top; }}
    tr:nth-child(even) td {{ background: #fafaf7; }}
    a {{ color: #1a4480; text-decoration: none; }}
    a:hover {{ text-decoration: underline; }}
    .flag {{ background: #fff3cd; padding: 1px 6px; font-size: 11px; border-radius: 3px; }}
</style>
</head>
<body>
<h1>Job digest</h1>
<div class="meta">Last updated: {today} - {len(all_jobs_today)} roles matching filters</div>

<div class="filters">
    <strong>Filter:</strong>
    <label><input type="checkbox" id="hideFlagged"> Hide "check location" roles</label>
    <label>Sector:
        <select id="sectorFilter">
            <option value="">All</option>
            <option value="university">University</option>
            <option value="nhs">NHS</option>
            <option value="charity">Charity</option>
            <option value="civil_service">Civil Service</option>
            <option value="public">Public sector</option>
            <option value="accessibility_specialist">Accessibility specialist</option>
        </select>
    </label>
</div>

<table>
<thead>
<tr><th>Title</th><th>Location</th><th>Source</th><th>Sector</th><th>Score</th></tr>
</thead>
<tbody id="results">
{''.join(rows)}
</tbody>
</table>

<script>
const hideFlagged = document.getElementById('hideFlagged');
const sectorFilter = document.getElementById('sectorFilter');
function applyFilters() {{
    const rows = document.querySelectorAll('#results tr');
    const hideF = hideFlagged.checked;
    const sect = sectorFilter.value;
    rows.forEach(r => {{
        const isFlagged = r.dataset.locStatus === 'include_flag';
        const rowSector = r.dataset.sector;
        let show = true;
        if (hideF && isFlagged) show = false;
        if (sect && rowSector !== sect) show = false;
        r.style.display = show ? '' : 'none';
    }});
}}
hideFlagged.addEventListener('change', applyFilters);
sectorFilter.addEventListener('change', applyFilters);
</script>
</body>
</html>"""

    with open(OUTPUT_HTML, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Wrote {OUTPUT_HTML}")


def _escape(s):
    """Minimal HTML escaping."""
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                  .replace(">", "&gt;").replace('"', "&quot;"))


# ============================================================
# MAIN
# ============================================================
def main():
    print(f"Job scraper run: {datetime.now(timezone.utc).isoformat()}")
    seen = load_seen()
    print(f"Loaded {len(seen)} previously seen job IDs")

    all_jobs = []
    for source in SOURCES:
        try:
            all_jobs.extend(scrape_source(source))
        except Exception as e:
            print(f"  ! {source['name']} failed entirely: {e}", file=sys.stderr)

    print(f"\nTotal raw jobs fetched: {len(all_jobs)}")

    # Apply filters
    kept = []
    for job in all_jobs:
        passes, info = passes_filters(job)
        if passes:
            job["_loc_status"] = info
            kept.append(job)

    print(f"After filtering: {len(kept)}")

    # Dedupe across sources
    by_id = {}
    for job in kept:
        jid = job_id(job)
        if jid not in by_id or (
            SECTOR_WEIGHTS.get(job.get("sector"), 0) >
            SECTOR_WEIGHTS.get(by_id[jid].get("sector"), 0)
        ):
            by_id[jid] = job

    deduped = list(by_id.values())
    print(f"After dedup: {len(deduped)}")

    # Score and sort
    for job in deduped:
        job["score"] = score(job, SECTOR_WEIGHTS)
    deduped.sort(key=lambda j: j["score"], reverse=True)

    # Identify new jobs
    new_jobs = [j for j in deduped if job_id(j) not in seen]
    print(f"New (unseen) jobs: {len(new_jobs)}")

    # Write outputs
    write_html_page(deduped)
    send_email(new_jobs, deduped)

    # Update seen
    for job in deduped:
        seen.add(job_id(job))
    save_seen(seen)
    print(f"Saved {len(seen)} seen IDs")


if __name__ == "__main__":
    main()
