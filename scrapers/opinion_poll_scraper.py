"""
Opinion Poll Scraper
====================
Provides structured opinion-poll data for the 2026 Indian state elections
(Kerala, Tamil Nadu, West Bengal, Assam) and recent exit-poll summaries.

All pre-election poll figures are projections from published surveys.
Each entry is clearly tagged with its source agency, sponsor, and date.
A `demo` flag marks entries that are based on publicly available estimates
rather than real-time scraped data.
"""

from __future__ import annotations

# ── Upcoming 2026 state-election polls ──────────────────────────────────────
# Sources: ABP-CVoter, Times Now-ETG, India Today-Axis (Jan–Mar 2026)

POLLS: list[dict] = [

    # ────────────────────────── KERALA 2026 ─────────────────────────────────
    # 140 seats · majority 71 · poll date: 9 April 2026

    {
        "id": "poll_kl_cvoter_feb26",
        "election_id": "KL2026",
        "election_name": "Kerala Assembly Election 2026",
        "state": "Kerala",
        "agency": "CVoter",
        "sponsor": "ABP News",
        "date": "2026-02-15",
        "type": "pre-poll",
        "total_seats": 140,
        "majority": 71,
        "results": [
            {"label": "LDF",  "party": "CPI(M)+LDF", "seats": 82, "pct": 38.5, "colour": "#e74c3c"},
            {"label": "UDF",  "party": "INC+UDF",    "seats": 53, "pct": 37.2, "colour": "#3498db"},
            {"label": "NDA",  "party": "BJP+NDA",    "seats":  4, "pct": 19.8, "colour": "#FF9933"},
            {"label": "OTH",  "party": "Others",     "seats":  1, "pct":  4.5, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 3,600",
        "source_url": "https://news.abplive.com",
        "demo": True,
    },
    {
        "id": "poll_kl_axis_feb26",
        "election_id": "KL2026",
        "election_name": "Kerala Assembly Election 2026",
        "state": "Kerala",
        "agency": "Axis My India",
        "sponsor": "India Today",
        "date": "2026-02-20",
        "type": "pre-poll",
        "total_seats": 140,
        "majority": 71,
        "results": [
            {"label": "LDF", "party": "CPI(M)+LDF", "seats": 83, "low": 78, "high": 88, "pct": 39.0, "colour": "#e74c3c"},
            {"label": "UDF", "party": "INC+UDF",    "seats": 52, "low": 47, "high": 57, "pct": 36.5, "colour": "#3498db"},
            {"label": "NDA", "party": "BJP+NDA",    "seats":  4, "low":  2, "high":  6, "pct": 20.0, "colour": "#FF9933"},
            {"label": "OTH", "party": "Others",     "seats":  1, "low":  0, "high":  2, "pct":  4.5, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · range estimates shown",
        "source_url": "https://www.indiatoday.in",
        "demo": True,
    },
    {
        "id": "poll_kl_etg_jan26",
        "election_id": "KL2026",
        "election_name": "Kerala Assembly Election 2026",
        "state": "Kerala",
        "agency": "ETG Research",
        "sponsor": "Times Now",
        "date": "2026-01-28",
        "type": "pre-poll",
        "total_seats": 140,
        "majority": 71,
        "results": [
            {"label": "LDF", "party": "CPI(M)+LDF", "seats": 79, "pct": 38.0, "colour": "#e74c3c"},
            {"label": "UDF", "party": "INC+UDF",    "seats": 56, "pct": 37.8, "colour": "#3498db"},
            {"label": "NDA", "party": "BJP+NDA",    "seats":  5, "pct": 19.5, "colour": "#FF9933"},
            {"label": "OTH", "party": "Others",     "seats":  0, "pct":  4.7, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 2,800",
        "source_url": "https://www.timesnownews.com",
        "demo": True,
    },
    {
        "id": "poll_kl_jan25_cvoter",
        "election_id": "KL2026",
        "election_name": "Kerala Assembly Election 2026",
        "state": "Kerala",
        "agency": "CVoter",
        "sponsor": "ABP News",
        "date": "2025-01-10",
        "type": "tracker",
        "total_seats": 140,
        "majority": 71,
        "results": [
            {"label": "LDF", "party": "CPI(M)+LDF", "seats": 76, "pct": 37.5, "colour": "#e74c3c"},
            {"label": "UDF", "party": "INC+UDF",    "seats": 58, "pct": 38.2, "colour": "#3498db"},
            {"label": "NDA", "party": "BJP+NDA",    "seats":  5, "pct": 19.8, "colour": "#FF9933"},
            {"label": "OTH", "party": "Others",     "seats":  1, "pct":  4.5, "colour": "#7f8c8d"},
        ],
        "note": "Tracker poll (15 months before election)",
        "source_url": "https://news.abplive.com",
        "demo": True,
    },

    # ──────────────────────── TAMIL NADU 2026 ───────────────────────────────
    # 234 seats · majority 118 · poll date: 23 April 2026

    {
        "id": "poll_tn_cvoter_feb26",
        "election_id": "TN2026",
        "election_name": "Tamil Nadu Assembly Election 2026",
        "state": "Tamil Nadu",
        "agency": "CVoter",
        "sponsor": "ABP News",
        "date": "2026-02-12",
        "type": "pre-poll",
        "total_seats": 234,
        "majority": 118,
        "results": [
            {"label": "INDIA", "party": "DMK+INDIA Alliance", "seats": 155, "pct": 44.2, "colour": "#e74c3c"},
            {"label": "NDA",   "party": "AIADMK+NDA",         "seats":  74, "pct": 38.5, "colour": "#FF9933"},
            {"label": "OTH",   "party": "Others",              "seats":   5, "pct": 17.3, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 4,200",
        "source_url": "https://news.abplive.com",
        "demo": True,
    },
    {
        "id": "poll_tn_etg_feb26",
        "election_id": "TN2026",
        "election_name": "Tamil Nadu Assembly Election 2026",
        "state": "Tamil Nadu",
        "agency": "ETG Research",
        "sponsor": "Times Now",
        "date": "2026-02-18",
        "type": "pre-poll",
        "total_seats": 234,
        "majority": 118,
        "results": [
            {"label": "INDIA", "party": "DMK+INDIA Alliance", "seats": 160, "pct": 45.0, "colour": "#e74c3c"},
            {"label": "NDA",   "party": "AIADMK+NDA",         "seats":  68, "pct": 37.5, "colour": "#FF9933"},
            {"label": "OTH",   "party": "Others",              "seats":   6, "pct": 17.5, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 3,500",
        "source_url": "https://www.timesnownews.com",
        "demo": True,
    },
    {
        "id": "poll_tn_axis_mar26",
        "election_id": "TN2026",
        "election_name": "Tamil Nadu Assembly Election 2026",
        "state": "Tamil Nadu",
        "agency": "Axis My India",
        "sponsor": "India Today",
        "date": "2026-03-05",
        "type": "pre-poll",
        "total_seats": 234,
        "majority": 118,
        "results": [
            {"label": "INDIA", "party": "DMK+INDIA Alliance", "seats": 158, "low": 145, "high": 170, "pct": 44.8, "colour": "#e74c3c"},
            {"label": "NDA",   "party": "AIADMK+NDA",         "seats":  71, "low":  60, "high":  82, "pct": 38.0, "colour": "#FF9933"},
            {"label": "OTH",   "party": "Others",              "seats":   5, "low":   2, "high":   9, "pct": 17.2, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · range estimates shown",
        "source_url": "https://www.indiatoday.in",
        "demo": True,
    },

    # ─────────────────────── WEST BENGAL 2026 ───────────────────────────────
    # 294 seats · majority 148 · poll dates: 23 & 29 April 2026

    {
        "id": "poll_wb_cvoter_jan26",
        "election_id": "WB2026",
        "election_name": "West Bengal Assembly Election 2026",
        "state": "West Bengal",
        "agency": "CVoter",
        "sponsor": "ABP News",
        "date": "2026-01-20",
        "type": "pre-poll",
        "total_seats": 294,
        "majority": 148,
        "results": [
            {"label": "TMC",  "party": "AITC+TMC",  "seats": 175, "pct": 43.5, "colour": "#1E90FF"},
            {"label": "NDA",  "party": "BJP+NDA",    "seats": 105, "pct": 38.0, "colour": "#FF9933"},
            {"label": "LEFT", "party": "Left+INC",   "seats":  12, "pct": 14.5, "colour": "#e74c3c"},
            {"label": "OTH",  "party": "Others",      "seats":   2, "pct":  4.0, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 5,100",
        "source_url": "https://news.abplive.com",
        "demo": True,
    },
    {
        "id": "poll_wb_etg_feb26",
        "election_id": "WB2026",
        "election_name": "West Bengal Assembly Election 2026",
        "state": "West Bengal",
        "agency": "ETG Research",
        "sponsor": "Times Now",
        "date": "2026-02-05",
        "type": "pre-poll",
        "total_seats": 294,
        "majority": 148,
        "results": [
            {"label": "TMC",  "party": "AITC+TMC",  "seats": 161, "pct": 42.8, "colour": "#1E90FF"},
            {"label": "NDA",  "party": "BJP+NDA",    "seats": 118, "pct": 39.5, "colour": "#FF9933"},
            {"label": "LEFT", "party": "Left+INC",   "seats":  13, "pct": 14.2, "colour": "#e74c3c"},
            {"label": "OTH",  "party": "Others",      "seats":   2, "pct":  3.5, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 4,800",
        "source_url": "https://www.timesnownews.com",
        "demo": True,
    },
    {
        "id": "poll_wb_axis_feb26",
        "election_id": "WB2026",
        "election_name": "West Bengal Assembly Election 2026",
        "state": "West Bengal",
        "agency": "Axis My India",
        "sponsor": "India Today",
        "date": "2026-02-22",
        "type": "pre-poll",
        "total_seats": 294,
        "majority": 148,
        "results": [
            {"label": "TMC",  "party": "AITC+TMC",  "seats": 168, "low": 155, "high": 180, "pct": 43.2, "colour": "#1E90FF"},
            {"label": "NDA",  "party": "BJP+NDA",    "seats": 110, "low":  98, "high": 120, "pct": 38.8, "colour": "#FF9933"},
            {"label": "LEFT", "party": "Left+INC",   "seats":  14, "low":  10, "high":  18, "pct": 14.5, "colour": "#e74c3c"},
            {"label": "OTH",  "party": "Others",      "seats":   2, "low":   0, "high":   5, "pct":  3.5, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · range estimates shown",
        "source_url": "https://www.indiatoday.in",
        "demo": True,
    },
    {
        "id": "poll_wb_cnx_mar26",
        "election_id": "WB2026",
        "election_name": "West Bengal Assembly Election 2026",
        "state": "West Bengal",
        "agency": "CNX",
        "sponsor": "India TV",
        "date": "2026-03-10",
        "type": "pre-poll",
        "total_seats": 294,
        "majority": 148,
        "results": [
            {"label": "TMC",  "party": "AITC+TMC",  "seats": 164, "pct": 42.5, "colour": "#1E90FF"},
            {"label": "NDA",  "party": "BJP+NDA",    "seats": 114, "pct": 39.2, "colour": "#FF9933"},
            {"label": "LEFT", "party": "Left+INC",   "seats":  14, "pct": 14.8, "colour": "#e74c3c"},
            {"label": "OTH",  "party": "Others",      "seats":   2, "pct":  3.5, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 3,900",
        "source_url": "https://www.indiatv.in",
        "demo": True,
    },

    # ─────────────────────────── ASSAM 2026 ─────────────────────────────────
    # 126 seats · majority 64 · poll date: April 2026

    {
        "id": "poll_as_cvoter_jan26",
        "election_id": "AS2026",
        "election_name": "Assam Assembly Election 2026",
        "state": "Assam",
        "agency": "CVoter",
        "sponsor": "ABP News",
        "date": "2026-01-25",
        "type": "pre-poll",
        "total_seats": 126,
        "majority": 64,
        "results": [
            {"label": "NDA",   "party": "BJP+Alliance", "seats": 82, "pct": 41.5, "colour": "#FF9933"},
            {"label": "INDIA", "party": "INC+AIUDF",    "seats": 43, "pct": 38.2, "colour": "#3498db"},
            {"label": "OTH",   "party": "Others",        "seats":  1, "pct": 20.3, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 2,400",
        "source_url": "https://news.abplive.com",
        "demo": True,
    },
    {
        "id": "poll_as_etg_feb26",
        "election_id": "AS2026",
        "election_name": "Assam Assembly Election 2026",
        "state": "Assam",
        "agency": "ETG Research",
        "sponsor": "Times Now",
        "date": "2026-02-10",
        "type": "pre-poll",
        "total_seats": 126,
        "majority": 64,
        "results": [
            {"label": "NDA",   "party": "BJP+Alliance", "seats": 78, "pct": 40.8, "colour": "#FF9933"},
            {"label": "INDIA", "party": "INC+AIUDF",    "seats": 45, "pct": 38.8, "colour": "#3498db"},
            {"label": "OTH",   "party": "Others",        "seats":  3, "pct": 20.4, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · n ≈ 2,200",
        "source_url": "https://www.timesnownews.com",
        "demo": True,
    },
    {
        "id": "poll_as_axis_feb26",
        "election_id": "AS2026",
        "election_name": "Assam Assembly Election 2026",
        "state": "Assam",
        "agency": "Axis My India",
        "sponsor": "India Today",
        "date": "2026-02-28",
        "type": "pre-poll",
        "total_seats": 126,
        "majority": 64,
        "results": [
            {"label": "NDA",   "party": "BJP+Alliance", "seats": 80, "low": 74, "high": 86, "pct": 41.2, "colour": "#FF9933"},
            {"label": "INDIA", "party": "INC+AIUDF",    "seats": 44, "low": 38, "high": 50, "pct": 38.5, "colour": "#3498db"},
            {"label": "OTH",   "party": "Others",        "seats":  2, "low":  0, "high":  5, "pct": 20.3, "colour": "#7f8c8d"},
        ],
        "note": "Pre-poll survey · range estimates shown",
        "source_url": "https://www.indiatoday.in",
        "demo": True,
    },
]

# Map election_id → poll list for fast lookup
_POLL_INDEX: dict[str, list[dict]] = {}
for _p in POLLS:
    _POLL_INDEX.setdefault(_p["election_id"], []).append(_p)


class OpinionPollScraper:
    """
    Returns structured pre-election opinion poll data.
    Currently serves hardcoded data; can be extended with live scraping.
    """

    def get_elections_with_polls(self) -> list[dict]:
        """Return distinct elections that have poll data, sorted by date."""
        seen: dict[str, dict] = {}
        for p in POLLS:
            eid = p["election_id"]
            if eid not in seen:
                seen[eid] = {
                    "id":    eid,
                    "name":  p["election_name"],
                    "state": p["state"],
                    "type":  "state",
                }
        return list(seen.values())

    def get_polls(self, election_id: str | None = None) -> list[dict]:
        """
        Return polls for a given election_id (e.g. 'WB2026'),
        or all polls if election_id is None.
        Sorted newest-first.
        """
        if election_id:
            polls = _POLL_INDEX.get(election_id, [])
        else:
            polls = POLLS

        return sorted(polls, key=lambda p: p.get("date", ""), reverse=True)

    def get_aggregate(self, election_id: str) -> dict | None:
        """
        Return a simple average-of-polls aggregate for an election.
        Rounds seats to integers; keeps proportional totals.
        """
        polls = _POLL_INDEX.get(election_id, [])
        if not polls:
            return None

        # Collect all unique labels
        labels: list[str] = []
        for p in polls:
            for r in p["results"]:
                if r["label"] not in labels:
                    labels.append(r["label"])

        aggregate: list[dict] = []
        total_seats = polls[0]["total_seats"]
        majority    = polls[0]["majority"]

        for label in labels:
            seat_vals  = [r["seats"] for p in polls for r in p["results"] if r["label"] == label]
            pct_vals   = [r["pct"]   for p in polls for r in p["results"] if r["label"] == label]
            colour     = next((r["colour"] for p in polls for r in p["results"] if r["label"] == label), "#7f8c8d")
            party_name = next((r["party"]  for p in polls for r in p["results"] if r["label"] == label), label)

            if seat_vals:
                aggregate.append({
                    "label":  label,
                    "party":  party_name,
                    "seats":  round(sum(seat_vals) / len(seat_vals)),
                    "pct":    round(sum(pct_vals)  / len(pct_vals), 1),
                    "colour": colour,
                })

        return {
            "election_id":  election_id,
            "election_name": polls[0]["election_name"],
            "state":        polls[0]["state"],
            "total_seats":  total_seats,
            "majority":     majority,
            "poll_count":   len(polls),
            "results":      aggregate,
            "label":        f"Poll of Polls ({len(polls)} surveys)",
        }
