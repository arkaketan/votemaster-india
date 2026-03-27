"""
IndiaVotes.com Constituency Scraper
=====================================
Scrapes constituency-level results from IndiaVotes.com for past state assembly
elections. The site serves full HTML via POST to the election URL.

URL pattern:
  POST https://www.indiavotes.com/vidhan-sabha/{year}/{state_slug}/{election_id}/{state_id}

Response: full HTML page containing a DataTable with all AC results.
Columns: AC Name | AC No. | Type | District | Winning Candidate | Party |
         Total Electors | Total Votes | Poll% | Margin | Margin%

Note: Each row appears TWICE in the HTML (DataTables responsive mode).
      We deduplicate by AC Name.
"""

from __future__ import annotations
import re
import logging
import threading
from typing import Optional

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

_BASE = "https://www.indiavotes.com"

# ── Party colour map (full names as used on IndiaVotes) ─────────────────────
_PARTY_COLOURS: dict[str, str] = {
    # BJP variants
    "BHARATIYA JANTA PARTY":           "#FF9933",
    "BHARATIYA JANATA PARTY":          "#FF9933",
    "BJP":                             "#FF9933",
    # Congress variants
    "INDIAN NATIONAL CONGRESS":        "#19AF00",
    "INC":                             "#19AF00",
    "CONGRESS":                        "#19AF00",
    # TMC / AITC
    "ALL INDIA TRINAMOOL CONGRESS":    "#29ABE2",
    "AITC":                            "#29ABE2",
    "TMC":                             "#29ABE2",
    # AAP
    "AAM AADMI PARTY":                 "#2A3B8F",
    "AAP":                             "#2A3B8F",
    # BSP
    "BAHUJAN SAMAJ PARTY":             "#1565C0",
    "BSP":                             "#1565C0",
    # SP
    "SAMAJWADI PARTY":                 "#E53935",
    "SP":                              "#E53935",
    # CPI-M
    "COMMUNIST PARTY OF INDIA  (MARXIST)": "#CC0000",
    "COMMUNIST PARTY OF INDIA (MARXIST)":  "#CC0000",
    "CPI(M)":                          "#CC0000",
    "CPM":                             "#CC0000",
    "CPI-M":                           "#CC0000",
    "CPI":                             "#CC0000",
    # NCP
    "NATIONALIST CONGRESS PARTY":      "#4CAF50",
    "NCP":                             "#4CAF50",
    # Shiv Sena
    "SHIV SENA":                       "#FF7043",
    "SHS":                             "#FF7043",
    "SS":                              "#FF7043",
    # JDU
    "JANATA DAL (UNITED)":             "#E6C619",
    "JD(U)":                           "#E6C619",
    "JDU":                             "#E6C619",
    # RJD
    "RASHTRIYA JANATA DAL":            "#006400",
    "RJD":                             "#006400",
    # TDP
    "TELUGU DESAM PARTY":              "#FFD700",
    "TDP":                             "#FFD700",
    # BRS / TRS
    "BHARAT RASHTRA SAMITHI":          "#D4AC0D",
    "BRS":                             "#D4AC0D",
    "TELANGANA RASHTRA SAMITHI":       "#9ACD32",
    "TRS":                             "#9ACD32",
    # DMK
    "DRAVIDA MUNNETRA KAZHAGAM":       "#CC0000",
    "DMK":                             "#CC0000",
    # AIADMK
    "ALL INDIA ANNA DRAVIDA MUNNETRA KAZHAGAM": "#047A07",
    "AIADMK":                          "#047A07",
    "ADMK":                            "#047A07",
    # Kerala Congress
    "INDIAN UNION MUSLIM LEAGUE":      "#00A550",
    "IUML":                            "#00A550",
    # JMM
    "JHARKHAND MUKTI MORCHA":          "#27AE60",
    "JMM":                             "#27AE60",
    # BJD
    "BIJU JANATA DAL":                 "#0D47A1",
    "BJD":                             "#0D47A1",
    # AGP
    "ASOM GANA PARISHAD":              "#FF6600",
    "AGP":                             "#FF6600",
    # AIUDF
    "ALL INDIA UNITED DEMOCRATIC FRONT": "#16A085",
    "AIUDF":                           "#16A085",
    # YCP / YSRCP
    "YUVAJANA SRAMIKA RYTHU CONGRESS PARTY": "#004B87",
    "YSRCP":                           "#004B87",
    "YCP":                             "#004B87",
    # Independent
    "INDEPENDENT":                     "#7F8C8D",
    "IND":                             "#7F8C8D",
}


def _party_colour(name: str) -> str:
    if not name:
        return "#7F8C8D"
    upper = name.upper().strip()
    # Exact match first
    if upper in _PARTY_COLOURS:
        return _PARTY_COLOURS[upper]
    # Partial match
    for key, clr in _PARTY_COLOURS.items():
        if key in upper or upper in key:
            return clr
    return "#7F8C8D"


# ── Election registry ────────────────────────────────────────────────────────
# Format: election_key -> (year_text, state_slug, indiavotes_election_id, state_id)
#
# Election IDs sourced from IndiaVotes API: POST /ac/get_year/{state_id}
# State IDs: WB=9, KL=28, TN=40, KA=43, RJ=14, MP=59, CG=54, TG=61,
#            MH=30, JH=53, DL=57, UP=60, PB=7, GA=51, GJ=29, HP=22,
#            UA=56, AS=1, BR=58
ELECTIONS: dict[str, tuple[str, str, int, int]] = {
    # ── 2025 ──────────────────────────────────────────────────────────
    "DL2025": ("2025", "delhi",          302, 57),
    "BR2025": ("2025", "bihar",          303, 58),
    # ── 2024 ──────────────────────────────────────────────────────────
    "MH2024": ("2024", "maharashtra",    300, 30),
    "JH2024": ("2024", "jharkhand",      301, 53),
    # ── 2023 ──────────────────────────────────────────────────────────
    "KA2023": ("2023", "karnataka",      292, 43),
    "RJ2023": ("2023", "rajasthan",      297, 14),
    "MP2023": ("2023", "madhya-pradesh", 295, 59),
    "CG2023": ("2023", "chhattisgarh",   293, 54),
    "TG2023": ("2023", "telangana",      296, 61),
    # ── 2022 ──────────────────────────────────────────────────────────
    "UP2022": ("2022", "uttar-pradesh",  289, 60),
    "PB2022": ("2022", "punjab",         286,  7),
    "GA2022": ("2022", "goa",            285, 51),
    "GJ2022": ("2022", "gujarat",        290, 29),
    "HP2022": ("2022", "himachal-pradesh", 291, 22),
    "UA2022": ("2022", "uttarakhand",    287, 56),
    # ── 2021 ──────────────────────────────────────────────────────────
    "WB2021": ("2021", "west-bengal",    284,  9),
    "KL2021": ("2021", "kerala",         281, 28),
    "TN2021": ("2021", "tamil-nadu",     283, 40),
    "AS2021": ("2021", "assam",          280,  1),
    # ── 2020 ──────────────────────────────────────────────────────────
    "BR2020": ("2020", "bihar",          279, 58),
    "DL2020": ("2020", "delhi",          277, 57),
    # ── 2019 ──────────────────────────────────────────────────────────
    # IndiaVotes labels JH 2019 election results under year "2020"
    "JH2019": ("2020", "jharkhand",      278, 53),
    "MH2019": ("2019", "maharashtra",    276, 30),
    # ── 2018 ──────────────────────────────────────────────────────────
    "KA2018": ("2018", "karnataka",      258, 43),
    "RJ2018": ("2018", "rajasthan",      268, 14),
    "MP2018": ("2018", "madhya-pradesh", 267, 59),
    "CG2018": ("2018", "chhattisgarh",   260, 54),
    "TG2018": ("2018", "telangana",      266, 61),
    # ── 2017 ──────────────────────────────────────────────────────────
    "UP2017": ("2017", "uttar-pradesh",  255, 60),
    "PB2017": ("2017", "punjab",         251,  7),
    "GJ2017": ("2017", "gujarat",        257, 29),
    "HP2017": ("2017", "himachal-pradesh", 256, 22),
    "UA2017": ("2017", "uttarakhand",    252, 56),
    "GA2017": ("2017", "goa",            253, 51),
    # ── 2016 ──────────────────────────────────────────────────────────
    "WB2016": ("2016", "west-bengal",    249,  9),
    "KL2016": ("2016", "kerala",         248, 28),
    "TN2016": ("2016", "tamil-nadu",     250, 40),
    "AS2016": ("2016", "assam",          247,  1),
}


# ── In-memory cache ──────────────────────────────────────────────────────────
_cache: dict[str, list[dict]] = {}
_cache_lock = threading.Lock()


class IndiaVotesScraper:
    """Scrapes constituency-level results from IndiaVotes.com."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Referer": "https://www.indiavotes.com/",
            "Origin": "https://www.indiavotes.com",
        })

    def is_available(self, election_key: str) -> bool:
        return election_key in ELECTIONS

    def get_constituencies(self, election_key: str) -> list[dict]:
        """
        Return constituency-level results for a given election key (e.g. 'WB2021').
        Returns an empty list if not found or fetch fails.
        Results are cached in memory.
        """
        with _cache_lock:
            if election_key in _cache:
                return _cache[election_key]

        if election_key not in ELECTIONS:
            return []

        results = self._fetch(election_key)
        with _cache_lock:
            _cache[election_key] = results

        return results

    def _fetch(self, election_key: str) -> list[dict]:
        year_text, state_slug, elec_id, state_id = ELECTIONS[election_key]
        base_url = f"{_BASE}/vidhan-sabha/{year_text}/{state_slug}/{elec_id}/{state_id}"
        # IndiaVotes requires ?cache=yes AND X-Requested-With: XMLHttpRequest
        # (jQuery AJAX signature) to return the full ~475 KB constituency HTML.
        # Without these the server returns only a partial ~21 KB summary page.
        # We also GET the page first so the session has valid cookies.
        post_url = base_url + "?cache=yes"

        try:
            logger.info("[IndiaVotes] Fetching %s → %s", election_key, base_url)
            # Step 1: GET the page to acquire session cookies
            self._session.get(base_url, timeout=self.timeout)
            # Step 2: POST with jQuery AJAX signature + cache flag
            resp = self._session.post(
                post_url,
                headers={
                    "Referer":          base_url,
                    "X-Requested-With": "XMLHttpRequest",
                },
                timeout=self.timeout,
            )
            resp.raise_for_status()
            parsed = self._parse(resp.text)
            if parsed:
                logger.info("[IndiaVotes] %s → %d constituencies", election_key, len(parsed))
            else:
                logger.warning("[IndiaVotes] %s → no data parsed", election_key)
            return parsed
        except Exception as exc:
            logger.warning("[IndiaVotes] Error fetching %s: %s", election_key, exc)
            return []

    def _parse(self, html: str) -> list[dict]:
        """
        Parse IndiaVotes HTML to extract constituency results.

        The page has a DataTable with columns:
          AC Name | AC No. | Type | District | Winning Candidate |
          Party | Total Electors | Total Votes | Poll% | Margin | Margin%

        Each constituency appears TWICE (responsive DataTables). We deduplicate
        by AC Name.
        """
        soup = BeautifulSoup(html, "lxml")
        results: list[dict] = []
        seen: set[str] = set()

        # Find the constituency results table.
        # Identify by looking for headers: "AC Name", "Winning Candidate", "Party"
        target_table = None
        for tbl in soup.find_all("table"):
            header_cells = tbl.find_all("th")
            header_text = " ".join(th.get_text(strip=True) for th in header_cells)
            if "AC Name" in header_text and "Winning Candidate" in header_text:
                target_table = tbl
                break

        if target_table is None:
            # Fallback: take the largest table
            tables = soup.find_all("table")
            if tables:
                target_table = max(tables, key=lambda t: len(t.find_all("tr")))
            else:
                return []

        for tr in target_table.find_all("tr"):
            cells = [
                td.get_text(separator=" ", strip=True).replace("\xa0", " ")
                for td in tr.find_all("td")
            ]

            if len(cells) < 6:
                continue

            ac_name = cells[0].strip()

            # Skip blank/header rows
            if not ac_name or ac_name.upper() in (
                "AC NAME", "CONSTITUENCY", "SEAT", "NO DATA AVAILABLE ."
            ):
                continue

            # Skip duplicate rows (DataTables responsive)
            if ac_name in seen:
                continue
            seen.add(ac_name)

            party_name = cells[5].strip() if len(cells) > 5 else ""

            # Clean up margin: remove commas, keep digits
            margin_raw = cells[9].strip() if len(cells) > 9 else ""
            margin_num = 0
            try:
                margin_num = int(re.sub(r"[^\d]", "", margin_raw))
            except (ValueError, TypeError):
                pass

            results.append({
                "constituency":       ac_name,
                "ac_no":              cells[1].strip() if len(cells) > 1 else "",
                "type":               cells[2].strip() if len(cells) > 2 else "",
                "district":           cells[3].strip() if len(cells) > 3 else "",
                "leading_candidate":  cells[4].strip() if len(cells) > 4 else "",
                "leading_party":      party_name,
                "trailing_candidate": "",   # IndiaVotes summary doesn't show runner-up
                "trailing_party":     "",
                "margin":             margin_num,
                "margin_pct":         cells[10].strip() if len(cells) > 10 else "",
                "total_electors":     cells[6].strip() if len(cells) > 6 else "",
                "total_votes":        cells[7].strip() if len(cells) > 7 else "",
                "poll_pct":           cells[8].strip() if len(cells) > 8 else "",
                "status":             "Won",
                "colour":             _party_colour(party_name),
            })

        return results
