"""
Filtering logic - decides which jobs to keep and how to rank them.

The pipeline:
1. INCLUDE_KEYWORDS: at least one must appear in the title or description
2. EXCLUDE_TITLE_TERMS: if any appear in the title, drop the job
3. WELSH_ESSENTIAL: drop if Welsh language is required (not just desirable)
4. LOCATION: keep if remote / North Wales / Chester / Manchester+ if hybrid
5. RANK: by sector weight + location match + keyword strength
"""

import re


# ============================================================
# KEYWORDS - jobs need at least one of these in title/description
# ============================================================
INCLUDE_KEYWORDS = [
    "copywrit",            # copywriter, copywriting
    "seo",
    "search optimisation",
    "search optimization",
    "digital content",
    "web content",
    "content officer",
    "content manager",
    "content producer",
    "content strategist",
    "content design",
    "digital compliance",
    "accessibility",
    "wcag",
    "digital marketing",
    "digital campaign",
    "campaign manager",
    "campaign officer",
    "web manag",            # web manager, web management
    "website manag",
    "web officer",
    "digital communications",
    "social media",
    "policy officer",
    "policy manager",
    "policy adviser",
    "policy advisor",
    "policy and",
    "digital officer",
    "digital engagement",
    "online engagement",
    "editor",
    "editorial",
]


# ============================================================
# EXCLUSIONS - if any of these are in the TITLE, drop the job
# ============================================================
EXCLUDE_TITLE_TERMS = [
    "hr ",
    "human resources",
    " hr",
    "teacher",
    "teaching",
    "lecturer",
    "training officer",
    "training manager",
    "training coordinator",
    "learning officer",
    "learning and development",
    "l&d",
    "education and training",
    "frontline",
    "front-line",
    "front line",
    "regional organiser",
    "regional organizer",
    "regional coordinator",
    "regional co-ordinator",
    "assistant",        # mostly junior admin roles - removable if too strict
    "apprentice",
    "intern",
    "graduate scheme",
    "nurse",
    "nursing",
    "doctor",
    "clinical",
    "surgeon",
    "cleaner",
    "porter",
    "chef",
    "driver",
    "warehouse",
    "phlebotomist",
    "midwife",
    "physiotherap",
    "occupational therap",
    "support worker",
    "care worker",
    "social worker",
    "caretaker",
    "receptionist",
]


# ============================================================
# WELSH LANGUAGE - drop if "essential"
# ============================================================
WELSH_ESSENTIAL_PATTERNS = [
    r"welsh\s+(?:speaker|language)\s+(?:is\s+)?essential",
    r"welsh\s+essential",
    r"fluent\s+welsh",
    r"cymraeg\s+hanfodol",
    r"essential.{0,30}welsh",
]


# ============================================================
# LOCATIONS - included automatically (with auto-fitness)
# ============================================================

# Always include if location mentions these
LOCATION_INCLUDE_TERMS = [
    "remote",
    "home-based",
    "home based",
    "homebased",
    "work from home",
    "fully remote",
    "anywhere",
    "uk-wide",
    "uk wide",
    "nationwide",
    # Commute zone
    "bangor",
    "conwy",
    "llandudno",
    "colwyn",
    "abergele",
    "rhyl",
    "old colwyn",
    "north wales",
    "gwynedd",
    "denbighshire",
    "chester",
    "wrexham",  # bit of a stretch but worth flagging
]

# Auto-EXCLUDE if location is one of these AND not hybrid/remote
LOCATION_EXCLUDE_TERMS = [
    "cardiff",
    "swansea",
    "newport",
    "aberystwyth",
    "bristol",
    "liverpool",
    "leeds",
    "sheffield",
    "newcastle",
    "edinburgh",
    "glasgow",
    "belfast",
    "birmingham",
    "southampton",
    "portsmouth",
    "brighton",
    "nottingham",
    "exeter",
    "plymouth",
    "cornwall",
    "kent",
    "essex",
    "norfolk",
    "suffolk",
]

# Cities where hybrid is acceptable (occasional travel)
HYBRID_OK_CITIES = [
    "london",
    "manchester",
]


def _text(job):
    """Combine title and description for keyword search."""
    return (job.get("title", "") + " " + job.get("description", "")).lower()


def has_include_keyword(job):
    """Job must have at least one inclusion keyword."""
    text = _text(job)
    return any(kw in text for kw in INCLUDE_KEYWORDS)


def has_exclude_title_term(job):
    """Drop if title contains an exclusion term."""
    title = job.get("title", "").lower()
    return any(term in title for term in EXCLUDE_TITLE_TERMS)


def welsh_essential(job):
    """Drop if Welsh language is essential (not just desirable)."""
    text = _text(job)
    return any(re.search(p, text, re.IGNORECASE) for p in WELSH_ESSENTIAL_PATTERNS)


def location_decision(job):
    """
    Return one of:
      'include'     - definitely show
      'include_flag' - show but flag as 'check location'
      'exclude'     - don't show
    """
    location = job.get("location", "").lower()
    text = _text(job)
    full = location + " " + text

    # Strongly remote / commute zone
    if any(term in full for term in LOCATION_INCLUDE_TERMS):
        return "include"

    # Hybrid in acceptable city = flag for manual review
    if "hybrid" in full or "flexible" in full:
        if any(city in full for city in HYBRID_OK_CITIES):
            return "include_flag"

    # Explicitly in a city that's too far
    if any(city in full for city in LOCATION_EXCLUDE_TERMS):
        return "exclude"

    # Couldn't determine — flag for manual review rather than miss it
    return "include_flag"


def passes_filters(job):
    """Apply all filters. Returns (keep: bool, reason: str)."""
    if not has_include_keyword(job):
        return False, "no inclusion keyword"
    if has_exclude_title_term(job):
        return False, "excluded title term"
    if welsh_essential(job):
        return False, "Welsh essential"
    loc = location_decision(job)
    if loc == "exclude":
        return False, "location out of range"
    return True, loc  # 'include' or 'include_flag'


def score(job, sector_weights):
    """
    Score a job for ranking. Higher = shown first.
    Combines sector weight + location match + keyword strength.
    """
    sector = job.get("sector", "unknown")
    sector_score = sector_weights.get(sector, 3)

    # Bonus if title (not just description) contains include keyword
    title = job.get("title", "").lower()
    title_keyword_bonus = sum(2 for kw in INCLUDE_KEYWORDS if kw in title)

    # Location bonus
    loc = job.get("location", "").lower()
    if "remote" in loc or "home" in loc:
        location_bonus = 5
    elif any(term in loc for term in ["bangor", "conwy", "llandudno", "colwyn", "chester", "north wales"]):
        location_bonus = 4
    else:
        location_bonus = 0

    return sector_score * 3 + title_keyword_bonus + location_bonus
