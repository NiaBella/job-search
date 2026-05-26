"""
Sources configuration for the job scraper.

Each source has:
- name: human-readable name (shows in emails)
- parser: which parser function to use (see parsers.py)
- urls: list of URLs to fetch (some sources need multiple)
- sector: used for ranking (charity, university, public, union, etc.)
- enabled: set False to skip a source without deleting it

History note: the original generic HTML scraper produced too much noise
(navigation links treated as job titles, e.g. "sign in" rows from
Guardian Jobs). We replaced that with source-specific parsers in
parsers.py. Each source is only enabled once it has a tested parser.
"""

SOURCES = [
    {
        "name": "jobs.ac.uk - Wales",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/wales/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - Northern England",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/northern-england/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - PR/Marketing/Communications",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/pr-marketing-sales-and-communication/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - Legal/Compliance/Policy",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/legal-compliance-and-policy/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - Web Design & Development",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/web-design-and-development/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - IT Services",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/it-services/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - Sustainability",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/sustainability/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },
    {
        "name": "jobs.ac.uk - Library/Data/Info Mgmt",
        "parser": "jobsacuk_rss",
        "urls": [
            "https://www.jobs.ac.uk/jobs/library-services-data-and-information-management/?format=rss",
        ],
        "sector": "university",
        "enabled": True,
    },

    # ---------- CharityJob.co.uk - all charity sector roles ----------
    # Three pages of newest-first jobs (~25 per page = ~75 total).
    # Keyword + location filters in filters.py do the narrowing. User
    # filters out unwanted causes (animal farming, religious, right-wing
    # political) by eye in the email.
    {
        "name": "CharityJob - All",
        "parser": "charityjob_html",
        "urls": [
            "https://www.charityjob.co.uk/jobs",
            "https://www.charityjob.co.uk/jobs?page=2",
            "https://www.charityjob.co.uk/jobs?page=3",
        ],
        "sector": "charity",
        "enabled": True,
    },

    # ---------- DWP Find a Job - UK government's official board ----------
    # Covers NHS, Civil Service, councils, and private sector. Used by
    # DWP/JSA themselves. Targeted searches by keyword + location to
    # keep volume manageable (the firehose is 175k+ jobs).
    # NOTE: First deployment - parser built defensively against best-guess
    # HTML structure. May need iteration after first run.
    {
        "name": "Find a Job - Digital/Content (local)",
        "parser": "findajob_html",
        "urls": [
            "https://findajob.dwp.gov.uk/search?q=digital+content&w=Colwyn+Bay&r=30&sort=date",
        ],
        "sector": "unknown",
        "enabled": True,
    },
    {
        "name": "Find a Job - Accessibility (UK-wide)",
        "parser": "findajob_html",
        "urls": [
            "https://findajob.dwp.gov.uk/search?q=accessibility&sort=date",
            "https://findajob.dwp.gov.uk/search?q=WCAG&sort=date",
        ],
        "sector": "accessibility_specialist",
        "enabled": True,
    },
    {
        "name": "Find a Job - Communications (local)",
        "parser": "findajob_html",
        "urls": [
            "https://findajob.dwp.gov.uk/search?q=communications&w=Colwyn+Bay&r=30&sort=date",
        ],
        "sector": "unknown",
        "enabled": True,
    },
    {
        "name": "Find a Job - Policy/Compliance (UK-wide)",
        "parser": "findajob_html",
        "urls": [
            "https://findajob.dwp.gov.uk/search?q=policy+officer&sort=date",
            "https://findajob.dwp.gov.uk/search?q=digital+compliance&sort=date",
        ],
        "sector": "unknown",
        "enabled": True,
    },

    # ---------- Guardian Jobs ----------
    # Guardian Jobs is powered by Madgex software. Category URLs return ~20
    # listings each. We target categories most relevant to digital content
    # /accessibility/policy work.
    # delay=5 because Guardian started returning 403 to rapid requests on
    # 26 May 2026 - slowing down to look more like a real user.
    {
        "name": "Guardian Jobs - Charities",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/charities/",
        ],
        "sector": "charity",
        "delay": 5,
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Marketing & PR",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/marketing-and-pr/",
        ],
        "sector": "charity",  # Most charity/public sector marketing roles
        "delay": 5,
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Media",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/media/",
        ],
        "sector": "charity",
        "delay": 5,
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Government & Politics",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/government-and-politics/",
        ],
        "sector": "civil_service",
        "delay": 5,
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Homeworking",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/homeworking/",
        ],
        "sector": "charity",  # Guardian Jobs leans heavily charity
        "delay": 5,
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Wales",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/wales/",
        ],
        "sector": "charity",
        "delay": 5,
        "enabled": True,
    },

    # ---------- DISABLED until proper parsers are written ----------
    {
        "name": "NHS Jobs",
        "parser": "TODO",
        "urls": [],
        "sector": "nhs",
        "enabled": False,
    },
    {
        "name": "Civil Service Jobs",
        "parser": "TODO",
        "urls": [],
        "sector": "civil_service",
        "enabled": False,
    },
    {
        "name": "a11yjobs.com",
        "parser": "TODO",
        "urls": [],
        "sector": "accessibility_specialist",
        "enabled": False,
    },
    {
        "name": "DWP Find a Job",
        "parser": "TODO",
        "urls": [],
        "sector": "public",
        "enabled": False,
    },
]


# Sector weighting for ranking (higher = shown first in digest)
SECTOR_WEIGHTS = {
    "nhs": 10,
    "charity": 10,
    "university": 9,
    "civil_service": 9,
    "public": 9,
    "union": 9,
    "accessibility_specialist": 8,
    "council": 9,
    "unknown": 3,
    "private": 1,
}
