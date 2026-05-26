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

import html
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
            # Some feeds return literal <br /> tags, others HTML-entity-encoded
            # (&lt;br /&gt;). Decode entities first, then strip tags.
            desc_text = html.unescape(description)
            desc_text = re.sub(r"<br\s*/?>", " | ", desc_text, flags=re.IGNORECASE)
            desc_text = re.sub(r"<[^>]+>", "", desc_text)  # strip any other HTML
            desc_text = desc_text.strip()
            employer = ""
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


# ============================================================
# CharityJob.co.uk - HTML parser
# ============================================================
def parse_charityjob_html(content, source_meta):
    """
    CharityJob.co.uk job listing pages.

    Real job listings match URL pattern:
        /jobs/{org-slug}/{job-slug}/{numeric-id}?tsId=N
    
    We anchor on those links and then look up to find the parent
    container, then look around it for org name, location, salary.
    """
    jobs = []
    if not content:
        return jobs

    try:
        soup = BeautifulSoup(content, "html.parser")

        # Find all links matching the job-URL pattern
        # Pattern: /jobs/SOMETHING/SOMETHING/DIGITS
        job_link_pattern = re.compile(r"/jobs/[^/]+/[^/]+/\d+(?:\?|$)")

        seen_urls = set()
        for link in soup.find_all("a", href=True):
            href = link["href"]
            if not job_link_pattern.search(href):
                continue

            # Get title first - skip links that are image-only wrappers
            title = link.get_text(strip=True)
            if not title or len(title) < 4:
                continue

            # Normalise URL and dedup
            if href.startswith("/"):
                href = "https://www.charityjob.co.uk" + href
            href_clean = href.split("?")[0]
            if href_clean in seen_urls:
                continue
            seen_urls.add(href_clean)

            # Walk up to find a parent container with location/salary info
            # CharityJob structures vary - look in nearby ancestors
            container = link
            for _ in range(6):  # up to 6 levels
                container = container.parent
                if container is None:
                    break
                txt = container.get_text(" ", strip=True)
                # Detect a real job container by looking for these signals
                if ("Remote" in txt or "Hybrid" in txt or "On-site" in txt
                        or "per year" in txt or "per annum" in txt
                        or "Posted" in txt):
                    break

            container_text = ""
            org_name = ""
            location_text = ""

            if container is not None:
                container_text = container.get_text(" | ", strip=True)[:600]

                # Org name: usually the link immediately before the title link
                # or the alt text of a logo image
                logo = container.find("img", alt=True)
                if logo and logo.get("alt"):
                    org_name = logo["alt"].replace(" logo", "").strip()

                # Location detection - look for these strings
                lower = container_text.lower()
                if "remote" in lower:
                    location_text = "Remote"
                elif "hybrid" in lower:
                    location_text = "Hybrid"
                elif "on-site" in lower or "on site" in lower:
                    location_text = "On-site"

            jobs.append({
                "title": title,
                "url": href_clean,
                "description": container_text,
                "location": location_text,
                "source": source_meta["name"],
                "sector": source_meta["sector"],
                "posted": "",
                "employer": org_name,
            })
    except Exception as e:
        print(f"  ! charityjob parse error: {e}")

    return jobs
