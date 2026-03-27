"""
Historical Constituency Scraper
================================
Scrapes constituency-level results for past state assembly elections.

Strategy (in order of preference):
  1. IndiaVotes.com  — POST to election page, parse embedded DataTable
  2. ECI Archive     — GET statewiseS{code}.htm from results.eci.gov.in

IndiaVotes URL pattern:
  POST https://www.indiavotes.com/vidhan-sabha/{year}/{state_slug}/{elec_id}/{state_id}

ECI archive URL pattern:
  https://results.eci.gov.in/{SLUG}/statewiseS{STATE_CODE}.htm
"""

from __future__ import annotations
import re
import logging
import threading
from typing import Optional

import requests
from bs4 import BeautifulSoup

# Import IndiaVotes scraper as primary source
from scrapers.indiavotes_scraper import IndiaVotesScraper

logger = logging.getLogger(__name__)

# ── Party colour palette (same as used in historical_scraper.py) ────────────
_PARTY_COLOURS: dict[str, str] = {
    "BJP":    "#FF9933",  "NDA":    "#FF9933",
    "INC":    "#3498db",  "CONG":   "#3498db",
    "AITC":   "#1E90FF",  "TMC":    "#1E90FF",
    "SP":     "#e74c3c",  "BSP":    "#3498db",
    "AAP":    "#00bfff",
    "DMK":    "#e74c3c",  "ADMK":   "#8e44ad",  "AIADMK": "#8e44ad",
    "CPI(M)": "#e74c3c",  "CPM":    "#e74c3c",
    "CPI":    "#e74c3c",
    "SS":     "#FF9933",  "SHS":    "#FF9933",
    "NCP":    "#27ae60",
    "JDU":    "#27ae60",  "JD(U)":  "#27ae60",
    "TRS":    "#e74c3c",  "BRS":    "#e74c3c",
    "TDP":    "#FFD700",
    "YSRCP":  "#27ae60",  "YCP":    "#27ae60",
    "BJD":    "#27ae60",
    "AGP":    "#FF9933",
    "AIUDF":  "#16a085",
    "JMM":    "#27ae60",
    "SJP":    "#e74c3c",
    "RJD":    "#e74c3c",
    "LJP":    "#3498db",
    "NOTA":   "#6b7280",
    "IND":    "#7f8c8d",
}

def _party_colour(party: str) -> str:
    pu = (party or "").upper().strip()
    for key, clr in _PARTY_COLOURS.items():
        if key in pu:
            return clr
    return "#7f8c8d"


# ── ECI archive: election_id → (slug, state_code) ───────────────────────────
# slug: path component after results.eci.gov.in/
# state_code: numeric ECI state code used in statewiseS{code}.htm
# Set state_code=None if the election page uses plain statewiseS.htm
ECI_ARCHIVE: dict[str, dict] = {
    # ── 2024 ──────────────────────────────────────────────────────────────
    "MH2024": {"slug": "ResultAcGenNov2024MH", "state_code": 27},
    "JH2024": {"slug": "ResultAcGenNov2024JH", "state_code": 20},
    "AP2024": {"slug": "ResultAcGenJune2024AP", "state_code": 37},
    "OD2024": {"slug": "ResultAcGenJune2024OD", "state_code": 21},
    "AR2024": {"slug": "ResultAcGenJune2024AR", "state_code": 12},
    "SK2024": {"slug": "ResultAcGenJune2024SK", "state_code": 11},
    # ── 2023 ──────────────────────────────────────────────────────────────
    "KA2023": {"slug": "ResultAcGenMay2023KA",  "state_code": 29},
    "MZ2023": {"slug": "ResultAcGenNov2023MZ",  "state_code": 15},
    "MP2023": {"slug": "ResultAcGenNov2023MP",  "state_code": 23},
    "RJ2023": {"slug": "ResultAcGenNov2023RJ",  "state_code":  8},
    "CG2023": {"slug": "ResultAcGenNov2023CG",  "state_code": 22},
    "TG2023": {"slug": "ResultAcGenNov2023TG",  "state_code": 36},
    "MN2023": {"slug": "ResultAcGenFeb2023MN",  "state_code": 14},
    "NL2023": {"slug": "ResultAcGenFeb2023NL",  "state_code": 13},
    "MG2023": {"slug": "ResultAcGenFeb2023MG",  "state_code": 17},
    "TR2023": {"slug": "ResultAcGenFeb2023TR",  "state_code": 16},
    # ── 2022 ──────────────────────────────────────────────────────────────
    "UP2022": {"slug": "ResultAcGenMar2022UP",  "state_code":  9},
    "PB2022": {"slug": "ResultAcGenMar2022PB",  "state_code":  3},
    "GA2022": {"slug": "ResultAcGenMar2022GA",  "state_code": 30},
    "UA2022": {"slug": "ResultAcGenMar2022UA",  "state_code":  5},
    "MN2022": {"slug": "ResultAcGenMar2022MN",  "state_code": 14},
    "HP2022": {"slug": "ResultAcGenDec2022HP",  "state_code":  2},
    "GJ2022": {"slug": "ResultAcGenDec2022GJ",  "state_code": 24},
    # ── 2021 ──────────────────────────────────────────────────────────────
    "WB2021": {"slug": "ResultAcGenMay2021WB",  "state_code": 19},
    "TN2021": {"slug": "ResultAcGenMay2021TN",  "state_code": 33},
    "KL2021": {"slug": "ResultAcGenMay2021KL",  "state_code": 32},
    "AS2021": {"slug": "ResultAcGenMay2021AS",  "state_code": 18},
    # ── 2020 ──────────────────────────────────────────────────────────────
    "DL2020": {"slug": "ResultAcGenFeb2020DL",  "state_code":  7},
    "BR2020": {"slug": "ResultAcGenNov2020BR",  "state_code": 10},
    # ── 2019 ──────────────────────────────────────────────────────────────
    "HR2019": {"slug": "ResultAcGenOct2019HR",  "state_code":  6},
    "MH2019": {"slug": "ResultAcGenOct2019MH",  "state_code": 27},
    "JH2019": {"slug": "ResultAcGenDec2019JH",  "state_code": 20},
}

_ECI_BASE = "https://results.eci.gov.in"

# ── In-memory cache: election_id → list[dict]  ──────────────────────────────
_cache: dict[str, list[dict]] = {}
_cache_lock = threading.Lock()
_CACHE_TTL = 3600  # seconds


class HistoricalConstituencyScraper:

    def __init__(self, timeout: int = 20):
        self.timeout  = timeout
        self.session  = requests.Session()
        self.session.headers.update({
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        })
        # IndiaVotes is used as primary source; ECI archive is the fallback
        self._iv = IndiaVotesScraper(timeout=timeout)

    # ── Public API ───────────────────────────────────────────────────────────

    def get_constituencies(self, election_id: str) -> list[dict]:
        """
        Return constituency-level results for a historical election.
        Tries IndiaVotes.com first, then falls back to the ECI archive.
        Returns [] if neither source has data.
        """
        with _cache_lock:
            if election_id in _cache:
                return _cache[election_id]

        results: list[dict] = []

        # ── 1. Try IndiaVotes.com (primary) ──────────────────────────────────
        if self._iv.is_available(election_id):
            logger.info("[HistConst] Trying IndiaVotes for %s", election_id)
            results = self._iv.get_constituencies(election_id)
            if results:
                logger.info("[HistConst] IndiaVotes returned %d rows for %s",
                            len(results), election_id)

        # ── 2. Fall back to ECI archive ───────────────────────────────────────
        if not results:
            archive = ECI_ARCHIVE.get(election_id)
            if archive:
                logger.info("[HistConst] Falling back to ECI archive for %s", election_id)
                results = self._fetch(archive["slug"], archive["state_code"])
                if results:
                    logger.info("[HistConst] ECI archive returned %d rows for %s",
                                len(results), election_id)

        with _cache_lock:
            _cache[election_id] = results

        return results

    def is_available(self, election_id: str) -> bool:
        return (self._iv.is_available(election_id) or
                election_id in ECI_ARCHIVE)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _fetch(self, slug: str, state_code: Optional[int]) -> list[dict]:
        """Try several URL patterns and return parsed results."""
        candidates: list[str] = []

        if state_code is not None:
            candidates.append(f"{_ECI_BASE}/{slug}/statewiseS{state_code:02d}.htm")
            candidates.append(f"{_ECI_BASE}/{slug}/statewiseS{state_code}.htm")

        # Fallback: plain statewiseS.htm (works for single-state elections)
        candidates.append(f"{_ECI_BASE}/{slug}/statewiseS.htm")
        # Some elections use partywisewinresult.htm only
        candidates.append(f"{_ECI_BASE}/{slug}/partywisewinresult.htm")

        for url in candidates:
            try:
                logger.info("Fetching historical constituency data: %s", url)
                resp = self.session.get(url, timeout=self.timeout)
                if resp.status_code != 200:
                    continue
                parsed = self._parse(resp.text)
                if parsed:
                    logger.info("  → %d constituencies from %s", len(parsed), url)
                    return parsed
            except Exception as exc:
                logger.warning("  Fetch failed %s: %s", url, exc)
                continue

        logger.warning("No constituency data found for slug: %s", slug)
        return []

    def _parse(self, html: str) -> list[dict]:
        """Parse the ECI constituency results table."""
        soup = BeautifulSoup(html, "lxml")
        results: list[dict] = []

        # ECI table has class "table" or is the main content table
        tables = soup.find_all("table")
        best_table = None
        best_rows  = 0

        for tbl in tables:
            rows = tbl.find_all("tr")
            if len(rows) > best_rows:
                # Heuristic: look for "Constituency" or "AC Name" in header
                header_text = " ".join(
                    th.get_text() for th in rows[0].find_all(["th", "td"])
                ).upper() if rows else ""
                if any(kw in header_text for kw in
                       ["CONSTITUENCY", "AC NAME", "CANDIDATE", "LEADING", "MARGIN"]):
                    best_table = tbl
                    best_rows  = len(rows)

        if best_table is None:
            return []

        rows = best_table.find_all("tr")

        for row in rows[1:]:  # skip header
            cells = [td.get_text(separator=" ", strip=True)
                     for td in row.find_all(["td", "th"])]
            if len(cells) < 6:
                continue

            # Determine column layout based on cell count
            # Typical: AC_No | AC_Name | Cand1 | Party1 | Cand2 | Party2 | Margin | Status
            # Some layouts: State | AC_No | AC_Name | ...
            if len(cells) >= 8:
                # Shift by 1 if first column looks like a state name
                offset = 1 if re.match(r'^[A-Za-z\s]+$', cells[0]) and len(cells[0]) > 3 and not cells[0].strip().isdigit() else 0
                ac_no      = cells[offset]
                ac_name    = cells[offset + 1]
                cand1      = cells[offset + 2]
                party1     = cells[offset + 3]
                cand2      = cells[offset + 4]
                party2     = cells[offset + 5]
                margin     = cells[offset + 6] if offset + 6 < len(cells) else ""
                status_raw = cells[offset + 7] if offset + 7 < len(cells) else "Won"
            elif len(cells) == 7:
                ac_name = cells[1]; cand1 = cells[2]; party1 = cells[3]
                cand2   = cells[4]; party2 = cells[5]
                margin  = cells[6]; status_raw = "Won"
            elif len(cells) == 6:
                ac_name = cells[0]; cand1 = cells[1]; party1 = cells[2]
                cand2   = cells[3]; party2 = cells[4]
                margin  = cells[5]; status_raw = "Won"
            else:
                continue

            # Skip header rows that slipped through
            if not ac_name or ac_name.upper() in ("AC NAME", "CONSTITUENCY", "SEAT"):
                continue

            # Normalise margin
            margin_num = 0
            try:
                margin_num = int(re.sub(r"[^\d]", "", margin))
            except (ValueError, TypeError):
                pass

            status = "Won" if "won" in status_raw.lower() else "Leading"

            results.append({
                "constituency":      ac_name.strip(),
                "leading_candidate": cand1.strip(),
                "leading_party":     party1.strip(),
                "trailing_candidate": cand2.strip(),
                "trailing_party":    party2.strip(),
                "margin":            margin_num,
                "status":            status,
                "colour":            _party_colour(party1.strip()),
            })

        return results
