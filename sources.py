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

    # ---------- CharityJob.co.uk - charity sector roles ----------
    {
        "name": "CharityJob - Remote",
        "parser": "charityjob_html",
        "urls": [
            "https://www.charityjob.co.uk/jobs?workplace=remote",
        ],
        "sector": "charity",
        "enabled": True,
    },
    {
        "name": "CharityJob - Hybrid",
        "parser": "charityjob_html",
        "urls": [
            "https://www.charityjob.co.uk/jobs?workplace=hybrid",
        ],
        "sector": "charity",
        "enabled": True,
    },

    # ---------- Guardian Jobs ----------
    # Guardian Jobs is powered by Madgex software. Category URLs return ~20
    # listings each. We target categories most relevant to digital content
    # /accessibility/policy work.
    {
        "name": "Guardian Jobs - Charities",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/charities/",
        ],
        "sector": "charity",
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Marketing & PR",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/marketing-and-pr/",
        ],
        "sector": "charity",  # Most charity/public sector marketing roles
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Media",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/media/",
        ],
        "sector": "charity",
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Government & Politics",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/government-and-politics/",
        ],
        "sector": "civil_service",
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Homeworking",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/homeworking/",
        ],
        "sector": "charity",  # Guardian Jobs leans heavily charity
        "enabled": True,
    },
    {
        "name": "Guardian Jobs - Wales",
        "parser": "guardianjobs_html",
        "urls": [
            "https://jobs.theguardian.com/jobs/wales/",
        ],
        "sector": "charity",
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
