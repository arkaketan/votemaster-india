"""
ECI (Election Commission of India) Results Scraper
Scrapes https://results.eci.gov.in for live election data.

URL patterns discovered:
  - Main:         https://results.eci.gov.in/
  - Party-wise:   https://results.eci.gov.in/{election_id}/partywisewinresult-{id}S{code}.htm
  - Statewise:    https://results.eci.gov.in/{election_id}/statewiseS{code}.htm
  - Constituency: https://results.eci.gov.in/{election_id}/ConstituencywiseS{code}.htm
"""

import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-IN,en;q=0.9",
    "Referer": "https://results.eci.gov.in/",
}

BASE_URL = "https://results.eci.gov.in"

# Party colour map for the UI
PARTY_COLOURS = {
    "BJP":     "#FF6B35",
    "INC":     "#1565C0",
    "AAP":     "#2196F3",
    "TMC":     "#1ABC9C",
    "DMK":     "#E53935",
    "AIADMK":  "#4CAF50",
    "CPM":     "#B71C1C",
    "CPI":     "#D32F2F",
    "NCP":     "#FF9800",
    "SS":      "#FF5722",
    "RJD":     "#9C27B0",
    "JDU":     "#3F51B5",
    "SP":      "#E91E63",
    "BSP":     "#607D8B",
    "TDP":     "#FFC107",
    "YCP":     "#009688",
    "BRS":     "#795548",
    "SHS":     "#FF9800",
    "IND":     "#9E9E9E",
    "OTH":     "#757575",
}

def _colour_for(party: str) -> str:
    for key, colour in PARTY_COLOURS.items():
        if key.upper() in party.upper():
            return colour
    return "#757575"


class ECIScraper:
    def __init__(self, timeout: int = 15):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(HEADERS)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_elections(self) -> list[dict]:
        """Return a list of elections currently available on results.eci.gov.in."""
        try:
            resp = self.session.get(BASE_URL, timeout=self.timeout)
            resp.raise_for_status()
            return self._parse_elections(resp.text)
        except Exception as exc:
            logger.warning("get_elections failed: %s — returning demo data", exc)
            return _demo_elections()

    def get_partywise_results(self, election: dict) -> list[dict]:
        """
        Return party-wise seat tallies for a given election dict
        (as returned by get_elections).
        """
        url = election.get("partywise_url") or election.get("url")
        if not url:
            return _demo_partywise()
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            rows = self._parse_partywise(resp.text)
            return rows if rows else _demo_partywise()
        except Exception as exc:
            logger.warning("get_partywise_results failed: %s", exc)
            return _demo_partywise()

    def get_constituency_results(self, election: dict) -> list[dict]:
        """Return constituency-wise leading/winning candidates."""
        url = election.get("constituency_url") or election.get("url")
        if not url:
            return _demo_constituencies()
        try:
            resp = self.session.get(url, timeout=self.timeout)
            resp.raise_for_status()
            rows = self._parse_constituency(resp.text)
            return rows if rows else _demo_constituencies()
        except Exception as exc:
            logger.warning("get_constituency_results failed: %s", exc)
            return _demo_constituencies()

    # ------------------------------------------------------------------
    # Parsers
    # ------------------------------------------------------------------

    def _parse_elections(self, html: str) -> list[dict]:
        soup = BeautifulSoup(html, "lxml")
        elections = []

        # ECI main page lists elections as anchor links whose href contains a
        # known prefix pattern.  We capture the election id slug from the href.
        pattern = re.compile(
            r"/(Result[A-Za-z0-9]+|AcResult[A-Za-z0-9]+)/", re.IGNORECASE
        )

        seen = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            m = pattern.search(href)
            if not m:
                continue
            slug = m.group(1)
            if slug in seen:
                continue
            seen.add(slug)

            name = a.get_text(" ", strip=True) or slug
            base = f"{BASE_URL}/{slug}"

            # Try to find partywise / constituency links nearby
            partywise_url = f"{base}/partywisewinresult.htm"
            constituency_url = f"{base}/ConstituencywiseResult.htm"

            elections.append({
                "id":               slug,
                "name":             name,
                "url":              base + "/index.htm",
                "partywise_url":    partywise_url,
                "constituency_url": constituency_url,
                "scraped_at":       datetime.utcnow().isoformat(),
            })

        # Also explicitly add the most recent known elections so the dashboard
        # always has something to show even if the main page structure changes.
        known = [
            {
                "id":            "ResultAcGenNov2025",
                "name":          "Assembly General Elections – Nov 2025",
                "url":           f"{BASE_URL}/ResultAcGenNov2025/index.htm",
                "partywise_url": f"{BASE_URL}/ResultAcGenNov2025/partywisewinresult-1420S04.htm",
                "constituency_url": f"{BASE_URL}/ResultAcGenNov2025/statewiseS0411.htm",
                "scraped_at":    datetime.utcnow().isoformat(),
            },
            {
                "id":            "AcResultByeNov2025",
                "name":          "Bye Elections – Nov 2025",
                "url":           f"{BASE_URL}/AcResultByeNov2025/index.htm",
                "partywise_url": f"{BASE_URL}/AcResultByeNov2025/partywisewinresult.htm",
                "constituency_url": f"{BASE_URL}/AcResultByeNov2025/ConstituencywiseS2961.htm",
                "scraped_at":    datetime.utcnow().isoformat(),
            },
        ]
        known_ids = {e["id"] for e in elections}
        for k in known:
            if k["id"] not in known_ids:
                elections.insert(0, k)

        return elections if elections else _demo_elections()

    def _parse_partywise(self, html: str) -> list[dict]:
        """Parse an ECI party-wise results HTML page."""
        soup = BeautifulSoup(html, "lxml")
        rows = []

        # ECI tables typically look like:
        # | S.No | Party | Won | Leading | Total |
        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not any(h in headers for h in ["party", "won", "leading", "total"]):
                continue
            for tr in table.find_all("tr")[1:]:
                cols = [td.get_text(strip=True) for td in tr.find_all("td")]
                if len(cols) < 3:
                    continue
                # Flexible column mapping
                party_name = ""
                won = leading = total = 0
                try:
                    if len(cols) >= 5:
                        party_name = cols[1]
                        won     = int(cols[2]) if cols[2].isdigit() else 0
                        leading = int(cols[3]) if cols[3].isdigit() else 0
                        total   = int(cols[4]) if cols[4].isdigit() else 0
                    elif len(cols) == 4:
                        party_name = cols[0]
                        won     = int(cols[1]) if cols[1].isdigit() else 0
                        leading = int(cols[2]) if cols[2].isdigit() else 0
                        total   = int(cols[3]) if cols[3].isdigit() else 0
                    elif len(cols) == 3:
                        party_name = cols[0]
                        won     = int(cols[1]) if cols[1].isdigit() else 0
                        total   = int(cols[2]) if cols[2].isdigit() else 0
                except ValueError:
                    pass

                if not party_name or party_name.lower() in ("total", "s.no", "#"):
                    continue

                rows.append({
                    "party":   party_name,
                    "won":     won,
                    "leading": leading,
                    "total":   total,
                    "colour":  _colour_for(party_name),
                })

        return sorted(rows, key=lambda r: r["total"], reverse=True)

    def _parse_constituency(self, html: str) -> list[dict]:
        """Parse an ECI statewise / constituency-wise HTML page."""
        soup = BeautifulSoup(html, "lxml")
        rows = []

        for table in soup.find_all("table"):
            headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
            if not any(h in headers for h in ["constituency", "candidate", "leading"]):
                continue
            for tr in table.find_all("tr")[1:]:
                cols = [td.get_text(" ", strip=True) for td in tr.find_all("td")]
                if len(cols) < 4:
                    continue
                try:
                    rows.append({
                        "constituency":       cols[1] if len(cols) > 1 else cols[0],
                        "leading_candidate":  cols[2] if len(cols) > 2 else "—",
                        "leading_party":      cols[3] if len(cols) > 3 else "—",
                        "trailing_candidate": cols[4] if len(cols) > 4 else "—",
                        "trailing_party":     cols[5] if len(cols) > 5 else "—",
                        "margin":             cols[6] if len(cols) > 6 else "—",
                        "status":             cols[7] if len(cols) > 7 else "—",
                        "colour":             _colour_for(cols[3] if len(cols) > 3 else ""),
                    })
                except (IndexError, ValueError):
                    pass
        return rows


# ------------------------------------------------------------------
# Demo / Fallback data  (shown when live scraping fails or elections
# haven't started yet — mimics the 2026 election candidates)
# ------------------------------------------------------------------

def _demo_elections() -> list[dict]:
    return [
        {
            "id":   "WB2026",
            "name": "West Bengal Assembly Election 2026 (Counting: 4 May)",
            "url":  f"{BASE_URL}/ResultAcGenApril2026WB/index.htm",
            "partywise_url":    f"{BASE_URL}/ResultAcGenApril2026WB/partywisewinresult.htm",
            "constituency_url": f"{BASE_URL}/ResultAcGenApril2026WB/statewiseresult.htm",
            "scraped_at": datetime.utcnow().isoformat(),
            "demo": True,
        },
        {
            "id":   "KL2026",
            "name": "Kerala Assembly Election 2026 (Counting: 4 May)",
            "url":  f"{BASE_URL}/ResultAcGenApril2026KL/index.htm",
            "partywise_url":    f"{BASE_URL}/ResultAcGenApril2026KL/partywisewinresult.htm",
            "constituency_url": f"{BASE_URL}/ResultAcGenApril2026KL/statewiseresult.htm",
            "scraped_at": datetime.utcnow().isoformat(),
            "demo": True,
        },
        {
            "id":   "TN2026",
            "name": "Tamil Nadu Assembly Election 2026 (Counting: 4 May)",
            "url":  f"{BASE_URL}/ResultAcGenApril2026TN/index.htm",
            "partywise_url":    f"{BASE_URL}/ResultAcGenApril2026TN/partywisewinresult.htm",
            "constituency_url": f"{BASE_URL}/ResultAcGenApril2026TN/statewiseresult.htm",
            "scraped_at": datetime.utcnow().isoformat(),
            "demo": True,
        },
        {
            "id":   "ResultAcGenNov2025",
            "name": "Assembly General Elections – Nov 2025 (Completed)",
            "url":  f"{BASE_URL}/ResultAcGenNov2025/index.htm",
            "partywise_url":    f"{BASE_URL}/ResultAcGenNov2025/partywisewinresult-1420S04.htm",
            "constituency_url": f"{BASE_URL}/ResultAcGenNov2025/statewiseS0411.htm",
            "scraped_at": datetime.utcnow().isoformat(),
            "demo": False,
        },
    ]


def _demo_partywise() -> list[dict]:
    """Illustrative data shown when live results are unavailable."""
    data = [
        ("TMC",     "All India Trinamool Congress", 147, 8),
        ("BJP",     "Bharatiya Janata Party",        85, 10),
        ("INC",     "Indian National Congress",      25,  3),
        ("CPM",     "Communist Party of India (M)",  18,  2),
        ("AITC(M)", "AITC (Maha)",                    5,  1),
        ("IND",     "Independent",                    8,  1),
        ("OTH",     "Others",                         6,  0),
    ]
    return [
        {
            "party":   short,
            "full":    full,
            "won":     won,
            "leading": leading,
            "total":   won + leading,
            "colour":  _colour_for(short),
            "demo":    True,
        }
        for short, full, won, leading in data
    ]


def _demo_constituencies() -> list[dict]:
    seats = [
        ("Kolkata North",    "Sudip Bandyopadhyay",  "TMC",  "Rahul Sinha",       "BJP",   18240, "Won"),
        ("Kolkata South",    "Mala Roy",              "TMC",  "Debasree Chaudhuri","BJP",   21340, "Won"),
        ("Howrah",           "Prasun Banerjee",       "TMC",  "Rantidev Sengupta", "BJP",   14200, "Won"),
        ("Bardhaman East",   "Sunil Kumar Mondal",    "BJP",  "Supriyo Mondal",    "TMC",    5670, "Leading"),
        ("Asansol",          "Shatrughan Sinha",      "TMC",  "SS Ahluwalia",      "BJP",   31200, "Won"),
        ("Midnapore",        "Dilip Ghosh",           "BJP",  "June Malia",        "TMC",    8900, "Leading"),
        ("Jadavpur",         "Saayoni Ghosh",         "TMC",  "Anupam Hazra",      "BJP",   26150, "Won"),
        ("Diamond Harbour",  "Abhishek Banerjee",     "TMC",  "Srikanta Mahato",   "BJP",   37000, "Won"),
        ("Durgapur",         "Kirti Azad",            "TMC",  "SS Dhaliwal",       "BJP",   12800, "Leading"),
        ("Barasat",          "Kakoli Ghosh",          "TMC",  "Mrinal Kanti Das",  "BJP",   29400, "Won"),
    ]
    return [
        {
            "constituency":       c,
            "leading_candidate":  lc,
            "leading_party":      lp,
            "trailing_candidate": tc,
            "trailing_party":     tp,
            "margin":             str(m),
            "status":             st,
            "colour":             _colour_for(lp),
            "demo":               True,
        }
        for c, lc, lp, tc, tp, m, st in seats
    ]
