"""
Sources configuration for the job scraper.

Each source has:
- name: human-readable name (shows in emails)
- type: 'rss', 'html', or 'json' (tells scraper how to parse it)
- url: the search/feed URL (with keywords baked in where possible)
- sector: used for ranking (charity, university, public, union, etc.)
- enabled: set False to skip a source without deleting it
"""

# Keywords to use when building search URLs
# Kept broad on purpose — narrow filtering happens in filters.py
SEARCH_KEYWORDS = [
    "digital content",
    "digital accessibility",
    "web content",
    "digital communications",
    "digital compliance",
    "copywriter",
    "SEO",
    "digital marketing",
    "policy officer",
    "policy manager",
    "social media",
    "web manager",
    "accessibility",
]


SOURCES = [
    {
        "name": "jobs.ac.uk (universities)",
        "type": "rss",
        # jobs.ac.uk supports keyword search with format=rss
        # We'll do one feed per keyword and dedupe later
        "url_template": "https://www.jobs.ac.uk/search/?keywords={keyword}&format=rss",
        "sector": "university",
        "enabled": True,
        "iterate_keywords": True,
    },
    {
        "name": "NHS Jobs",
        "type": "html",
        "url_template": "https://www.jobs.nhs.uk/candidate/search/results?keyword={keyword}",
        "sector": "nhs",
        "enabled": True,
        "iterate_keywords": True,
    },
    {
        "name": "Civil Service Jobs",
        "type": "html",
        # Covers UK gov departments, Welsh Government bodies often appear here
        "url_template": "https://www.civilservicejobs.service.gov.uk/csr/index.cgi?pageaction=search&what={keyword}",
        "sector": "civil_service",
        "enabled": True,
        "iterate_keywords": True,
    },
    {
        "name": "Guardian Jobs",
        "type": "html",
        "url_template": "https://jobs.theguardian.com/jobs/?Keywords={keyword}",
        "sector": "charity",  # Guardian Jobs is heavy on charities
        "enabled": True,
        "iterate_keywords": True,
    },
    {
        "name": "a11yjobs.com",
        "type": "html",
        # Single page of all accessibility jobs - no keyword needed
        "url_template": "https://www.a11yjobs.com/",
        "sector": "accessibility_specialist",
        "enabled": True,
        "iterate_keywords": False,
    },
    {
        "name": "DWP Find a Job",
        "type": "html",
        # location: ll29 = Old Colwyn postcode area
        "url_template": "https://findajob.dwp.gov.uk/search?q={keyword}&loc=LL29&r=100",
        "sector": "public",
        "enabled": True,
        "iterate_keywords": True,
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
