"""
Source-specific parsers.

Each source has its own parser function because every site structures
its job listings differently. A generic parser produces junk - we
learned this the hard way.

Each parser takes (content, source_meta) and returns a list of jobs in
the standard format:
    {
        "title": str,
        "url": str,
        "description": str,
        "location": str,
        "source": str,
        "sector": str,
        "posted": str,
    }
"""

import re
import xml.etree.ElementTree as ET
from urllib.parse import urljoin

from bs4 import BeautifulSoup


# ============================================================
# jobs.ac.uk - RSS feed parser
# ============================================================
def parse_jobsacuk_rss(content, source_meta):
    """
    jobs.ac.uk RSS format:
        <item>
            <title>Job title</title>
            <link>https://www.jobs.ac.uk/job/...</link>
            <description>Employer name - department<br />Salary: £X to £Y</description>
        </item>

    We extract employer name from description for location inference.
    """
    jobs = []
    if not content:
        return jobs

    try:
        # ElementTree handles RSS XML reliably
        root = ET.fromstring(content)
        # RSS structure: rss > channel > item
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            description = (item.findtext("description") or "").strip()

            if not title or not link:
                continue

            # Description format: "Employer - Department<br />Salary: ..."
            # Extract just the employer for cleaner display
            employer = ""
            desc_text = re.sub(r"<br\s*/?>", " | ", description)
            desc_text = re.sub(r"<[^>]+>", "", desc_text)  # strip any other HTML
            parts = desc_text.split(" | ", 1)
            if parts:
                # Employer is everything before the first " - " in the first chunk
                employer_chunk = parts[0]
                if " - " in employer_chunk:
                    employer = employer_chunk.split(" - ", 1)[0].strip()
                else:
                    employer = employer_chunk.strip()

            # Location inference from employer name
            location = _infer_location_from_employer(employer)

            # Use the cleaned description directly - it already starts with employer
            full_description = desc_text

            jobs.append({
                "title": title,
                "url": link,
                "description": full_description[:1000],
                "location": location,
                "source": source_meta["name"],
                "sector": source_meta["sector"],
                "posted": "",
                "employer": employer,
            })
    except ET.ParseError as e:
        print(f"  ! jobs.ac.uk RSS parse error: {e}")
    except Exception as e:
        print(f"  ! jobs.ac.uk unexpected error: {e}")

    return jobs


def _infer_location_from_employer(employer):
    """
    Best-effort location guess from employer name.
    jobs.ac.uk doesn't give us location directly, but the university
    name usually tells us.
    """
    employer_lower = employer.lower()
    location_map = {
        "bangor university": "Bangor, North Wales",
        "university of chester": "Chester",
        "open university": "Remote/UK-wide",
        "cardiff university": "Cardiff",
        "swansea university": "Swansea",
        "aberystwyth": "Aberystwyth",
        "university of south wales": "South Wales",
        "trinity saint david": "South Wales",
        "wrexham university": "Wrexham",
        "wrexham glyndwr": "Wrexham",
        "public health wales": "Wales",
        "university of manchester": "Manchester",
        "manchester metropolitan": "Manchester",
        "university of liverpool": "Liverpool",
        "liverpool john moores": "Liverpool",
        "lancaster university": "Lancaster",
        "university of cumbria": "Cumbria",
        "edge hill": "Lancashire",
    }
    for key, loc in location_map.items():
        if key in employer_lower:
            return loc
    return employer  # fall back to employer name


# ============================================================
# Future parsers go here.
# For now I'm only implementing jobs.ac.uk - other sources stay
# disabled until I write proper parsers for them.
# ============================================================
