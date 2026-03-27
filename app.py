"""
India Election Monitor 2026 — Flask Backend
Run:  python app.py
Then open http://localhost:5000
"""

import os
import re
import logging
import threading
from datetime import datetime

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS

from scrapers.eci_scraper                    import ECIScraper
from scrapers.news_scraper                   import NewsScraper
from scrapers.historical_scraper             import HistoricalScraper, HISTORICAL_ELECTIONS
from scrapers.opinion_poll_scraper           import OpinionPollScraper
from scrapers.historical_constituency_scraper import HistoricalConstituencyScraper

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app  = Flask(__name__)
CORS(app)

eci         = ECIScraper(timeout=15)
news        = NewsScraper(max_per_feed=20, timeout=10)
historical  = HistoricalScraper()
opinion     = OpinionPollScraper()
hist_const  = HistoricalConstituencyScraper(timeout=20)

_lock = threading.Lock()
store = {
    "live_elections":  [],
    "partywise":       {},
    "constituents":    {},
    "news":            [],
    "last_updated":    None,
    "is_refreshing":   False,
}


# ── Background refresh ───────────────────────────────────────────────
def _do_refresh():
    with _lock:
        if store["is_refreshing"]:
            return
        store["is_refreshing"] = True
    try:
        logger.info("Refreshing live ECI elections…")
        live = eci.get_elections()

        logger.info("Refreshing news feeds…")
        articles = news.get_election_news(filter_keywords=False)

        with _lock:
            store["live_elections"] = live
            store["news"]           = articles
            store["last_updated"]   = datetime.utcnow().isoformat() + "Z"

        for idx, election in enumerate(live[:3]):
            pw  = eci.get_partywise_results(election)
            con = eci.get_constituency_results(election)
            with _lock:
                store["partywise"][idx]    = pw
                store["constituents"][idx] = con

        logger.info("Refresh complete — %d live elections, %d articles",
                    len(live), len(articles))
    except Exception as exc:
        logger.exception("Refresh failed: %s", exc)
    finally:
        with _lock:
            store["is_refreshing"] = False


def refresh_async():
    t = threading.Thread(target=_do_refresh, daemon=True)
    t.start()


# ── Routes ──────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── Live ECI elections ───────────────────────────────────────────────

@app.route("/api/elections")
def api_elections():
    with _lock:
        return jsonify({"data": store["live_elections"],
                        "last_updated": store["last_updated"]})


@app.route("/api/partywise")
def api_partywise():
    idx = request.args.get("idx", 0, type=int)
    with _lock:
        data = store["partywise"].get(idx)
    if data is None:
        with _lock:
            elections = store["live_elections"]
        if idx < len(elections):
            data = eci.get_partywise_results(elections[idx])
            with _lock:
                store["partywise"][idx] = data
        else:
            data = []
    is_demo = any(r.get("demo") for r in (data or []))
    return jsonify({"data": data, "demo": is_demo})


@app.route("/api/constituencies")
def api_constituencies():
    idx = request.args.get("idx", 0, type=int)
    with _lock:
        data = store["constituents"].get(idx)
    if data is None:
        with _lock:
            elections = store["live_elections"]
        if idx < len(elections):
            data = eci.get_constituency_results(elections[idx])
            with _lock:
                store["constituents"][idx] = data
        else:
            data = []
    is_demo = any(r.get("demo") for r in (data or []))
    return jsonify({"data": data, "demo": is_demo})


# ── Historical elections ─────────────────────────────────────────────

@app.route("/api/historical/elections")
def api_hist_elections():
    elections = historical.get_all_elections()
    return jsonify({"data": elections})


@app.route("/api/historical/partywise")
def api_hist_partywise():
    eid      = request.args.get("id", "")
    use_wiki = request.args.get("wiki", "false").lower() == "true"
    election = historical.get_election(eid)
    if not election:
        return jsonify({"error": "Election not found"}), 404

    partywise = historical.get_partywise(eid, try_wikipedia=use_wiki)
    return jsonify({
        "data":      partywise,
        "alliances": election.get("alliances"),
        "meta": {
            "id":           election["id"],
            "name":         election["name"],
            "date":         election["date"],
            "total_seats":  election["total_seats"],
            "majority":     election["majority"],
            "winner":       election["winner"],
            "type":         election["type"],
        }
    })


@app.route("/api/historical/search")
def api_hist_search():
    q = request.args.get("q", "")
    return jsonify({"data": historical.search_elections(q)})


# ── News ─────────────────────────────────────────────────────────────

@app.route("/api/news")
def api_news():
    with _lock:
        articles = list(store["news"])

    election_id = request.args.get("election_id", "")
    keywords    = request.args.get("keywords", "")

    if election_id:
        election = historical.get_election(election_id)
        if election:
            kws = election.get("keywords", [])
            articles = [
                a for a in articles
                if any(kw in (a["title"] + a.get("summary", "")).lower() for kw in kws)
            ]

    if keywords:
        kws = [k.strip().lower() for k in keywords.split(",") if k.strip()]
        articles = [
            a for a in articles
            if any(kw in (a["title"] + a.get("summary", "")).lower() for kw in kws)
        ]

    if not articles:
        articles = store["news"]

    return jsonify({"data": articles, "last_updated": store["last_updated"]})


# ── Opinion Polls ─────────────────────────────────────────────────────

@app.route("/api/polls")
def api_polls():
    """
    Return opinion polls.
    ?election_id=WB2026  → polls for that election + aggregate
    (no param)           → all polls grouped by election
    """
    election_id = request.args.get("election_id", "")

    if election_id:
        polls     = opinion.get_polls(election_id)
        aggregate = opinion.get_aggregate(election_id)
        return jsonify({
            "election_id": election_id,
            "polls":       polls,
            "aggregate":   aggregate,
        })

    # All elections that have polls
    elections = opinion.get_elections_with_polls()
    all_polls = opinion.get_polls()
    return jsonify({
        "elections": elections,
        "polls":     all_polls,
    })


# ── Map data ─────────────────────────────────────────────────────────

def _norm(s: str) -> str:
    """Normalize a constituency name for fuzzy matching."""
    s = (s or "").upper()
    s = re.sub(r"^\d+\s*[-–.]\s*", "", s)
    s = re.sub(r"[^A-Z0-9 ]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


# ── Election ID → datta07 INDIAN-SHAPEFILES state folder name ────────
# Assembly (Vidhan Sabha) elections use the state folder.
# Lok Sabha (national) elections use None → India-level PC GeoJSON.
_STATE_SLUG: dict[str, str | None] = {
    # ── 2026 upcoming ──
    "WB2026": "WEST BENGAL",
    "KL2026": "KERALA",
    "TN2026": "TAMIL NADU",
    "AS2026": "ASSAM",
    # ── 2024 ──
    "MH2024": "MAHARASHTRA",
    "JH2024": "JHARKHAND",
    "AP2024": "ANDHRA PRADESH",
    "OD2024": "ODISHA",
    "AR2024": "ARUNACHAL PRADESH",
    "SK2024": "SIKKIM",
    "LS2024": None,          # Lok Sabha → India state-level choropleth
    # ── 2023 ──
    "RJ2023": "RAJASTHAN",
    "MP2023": "MADHYA PRADESH",
    "CG2023": "CHHATTISGARH",
    "TG2023": "TELANGANA",
    "KA2023": "KARNATAKA",
    "MZ2023": "MIZORAM",
    "NL2023": "NAGALAND",
    "MN2023": "MANIPUR",
    "MG2023": "MEGHALAYA",
    "TR2023": "TRIPURA",
    # ── 2022 ──
    "UP2022": "UTTAR PRADESH",
    "PB2022": "PUNJAB",
    "GA2022": "GOA",
    "UA2022": "UTTARAKHAND",
    "HP2022": "HIMACHAL PRADESH",
    "GJ2022": "GUJARAT",
    # ── 2021 ──
    "WB2021": "WEST BENGAL",
    "KL2021": "KERALA",
    "TN2021": "TAMIL NADU",
    "AS2021": "ASSAM",
    # ── 2020 ──
    "DL2020": "DELHI",
    "BR2020": "BIHAR",
    # ── 2019 ──
    "HR2019": "HARYANA",
    "MH2019": "MAHARASHTRA",
    "JH2019": "JHARKHAND",
    "LS2019": None,          # Lok Sabha → India state-level choropleth
}

# GeoJSON URL templates
_ASSEMBLY_GEOJSON = (
    "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES"
    "/master/STATES/{state}/{state}_ASSEMBLY.geojson"
)
# India states outline for Lok Sabha choropleth
_INDIA_STATES_GEOJSON = (
    "https://raw.githubusercontent.com/datta07/INDIAN-SHAPEFILES"
    "/master/INDIA/India_State_Boundary.geojson"
)

# ── State-wise LS results for choropleth colouring ────────────────────
# Leading party per state in the 2024 Lok Sabha election
_LS2024_STATE = {
    "ANDHRA PRADESH":   {"party": "TDP",    "seats": 16, "total": 25, "colour": "#FFD700"},
    "ARUNACHAL PRADESH":{"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "ASSAM":            {"party": "BJP",    "seats":  9, "total": 14, "colour": "#FF9933"},
    "BIHAR":            {"party": "NDA",    "seats": 30, "total": 40, "colour": "#FF9933"},
    "CHHATTISGARH":     {"party": "BJP",    "seats":  10, "total": 11, "colour": "#FF9933"},
    "GOA":              {"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "GUJARAT":          {"party": "BJP",    "seats": 26, "total": 26, "colour": "#FF9933"},
    "HARYANA":          {"party": "BJP",    "seats":  5, "total": 10, "colour": "#FF9933"},
    "HIMACHAL PRADESH": {"party": "INC",    "seats":  4, "total":  4, "colour": "#3498db"},
    "JHARKHAND":        {"party": "JMM",    "seats":  3, "total": 14, "colour": "#27ae60"},
    "KARNATAKA":        {"party": "INC",    "seats": 9, "total": 28, "colour": "#3498db"},
    "KERALA":           {"party": "INC",    "seats": 18, "total": 20, "colour": "#3498db"},
    "MADHYA PRADESH":   {"party": "BJP",    "seats": 29, "total": 29, "colour": "#FF9933"},
    "MAHARASHTRA":      {"party": "MVP",    "seats": 17, "total": 48, "colour": "#FF9933"},
    "MANIPUR":          {"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "MEGHALAYA":        {"party": "NPP",    "seats":  2, "total":  2, "colour": "#8e44ad"},
    "MIZORAM":          {"party": "ZPM",    "seats":  1, "total":  1, "colour": "#16a085"},
    "NAGALAND":         {"party": "NDPP",   "seats":  1, "total":  1, "colour": "#2c3e50"},
    "ODISHA":           {"party": "BJD",    "seats": 12, "total": 21, "colour": "#27ae60"},
    "PUNJAB":           {"party": "AAP",    "seats":  7, "total": 13, "colour": "#00bfff"},
    "RAJASTHAN":        {"party": "BJP",    "seats": 14, "total": 25, "colour": "#FF9933"},
    "SIKKIM":           {"party": "SKM",    "seats":  1, "total":  1, "colour": "#8e44ad"},
    "TAMIL NADU":       {"party": "DMK",    "seats": 22, "total": 39, "colour": "#e74c3c"},
    "TELANGANA":        {"party": "INC",    "seats":  8, "total": 17, "colour": "#3498db"},
    "TRIPURA":          {"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "UTTAR PRADESH":    {"party": "SP",     "seats": 37, "total": 80, "colour": "#e74c3c"},
    "UTTARAKHAND":      {"party": "BJP",    "seats":  5, "total":  5, "colour": "#FF9933"},
    "WEST BENGAL":      {"party": "TMC",    "seats": 29, "total": 42, "colour": "#1E90FF"},
    "DELHI":            {"party": "BJP",    "seats":  7, "total":  7, "colour": "#FF9933"},
    "JAMMU & KASHMIR":  {"party": "INC",    "seats":  2, "total":  5, "colour": "#3498db"},
    "LADAKH":           {"party": "IND",    "seats":  1, "total":  1, "colour": "#7f8c8d"},
}

_LS2019_STATE = {
    "ANDHRA PRADESH":   {"party": "YSRCP",  "seats": 22, "total": 25, "colour": "#27ae60"},
    "ARUNACHAL PRADESH":{"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "ASSAM":            {"party": "BJP",    "seats":  9, "total": 14, "colour": "#FF9933"},
    "BIHAR":            {"party": "NDA",    "seats": 39, "total": 40, "colour": "#FF9933"},
    "CHHATTISGARH":     {"party": "BJP",    "seats":  9, "total": 11, "colour": "#FF9933"},
    "GOA":              {"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "GUJARAT":          {"party": "BJP",    "seats": 26, "total": 26, "colour": "#FF9933"},
    "HARYANA":          {"party": "BJP",    "seats": 10, "total": 10, "colour": "#FF9933"},
    "HIMACHAL PRADESH": {"party": "BJP",    "seats":  4, "total":  4, "colour": "#FF9933"},
    "JHARKHAND":        {"party": "BJP",    "seats": 11, "total": 14, "colour": "#FF9933"},
    "KARNATAKA":        {"party": "BJP",    "seats": 25, "total": 28, "colour": "#FF9933"},
    "KERALA":           {"party": "INC",    "seats": 15, "total": 20, "colour": "#3498db"},
    "MADHYA PRADESH":   {"party": "BJP",    "seats": 28, "total": 29, "colour": "#FF9933"},
    "MAHARASHTRA":      {"party": "BJP",    "seats": 23, "total": 48, "colour": "#FF9933"},
    "MANIPUR":          {"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "MEGHALAYA":        {"party": "NPP",    "seats":  2, "total":  2, "colour": "#8e44ad"},
    "MIZORAM":          {"party": "MNF",    "seats":  1, "total":  1, "colour": "#16a085"},
    "NAGALAND":         {"party": "NDPP",   "seats":  1, "total":  1, "colour": "#2c3e50"},
    "ODISHA":           {"party": "BJD",    "seats": 12, "total": 21, "colour": "#27ae60"},
    "PUNJAB":           {"party": "INC",    "seats":  8, "total": 13, "colour": "#3498db"},
    "RAJASTHAN":        {"party": "BJP",    "seats": 24, "total": 25, "colour": "#FF9933"},
    "SIKKIM":           {"party": "SKM",    "seats":  1, "total":  1, "colour": "#8e44ad"},
    "TAMIL NADU":       {"party": "ADMK",   "seats": 23, "total": 39, "colour": "#8e44ad"},
    "TELANGANA":        {"party": "TRS",    "seats":  9, "total": 17, "colour": "#e74c3c"},
    "TRIPURA":          {"party": "BJP",    "seats":  2, "total":  2, "colour": "#FF9933"},
    "UTTAR PRADESH":    {"party": "BJP",    "seats": 62, "total": 80, "colour": "#FF9933"},
    "UTTARAKHAND":      {"party": "BJP",    "seats":  5, "total":  5, "colour": "#FF9933"},
    "WEST BENGAL":      {"party": "BJP",    "seats": 18, "total": 42, "colour": "#FF9933"},
    "DELHI":            {"party": "BJP",    "seats":  7, "total":  7, "colour": "#FF9933"},
    "JAMMU & KASHMIR":  {"party": "BJP",    "seats":  3, "total":  6, "colour": "#FF9933"},
}

_LS_STATE_DATA = {
    "LS2024": _LS2024_STATE,
    "LS2019": _LS2019_STATE,
}


@app.route("/api/map-data/<election_id>")
def api_map_data(election_id):
    """
    Return constituency results + GeoJSON URL for the map panel.

    For Vidhan Sabha (state) elections: Assembly-constituency GeoJSON.
    For Lok Sabha (national) elections: India state-boundary GeoJSON
      coloured by leading party per state.
    """
    state_slug = _STATE_SLUG.get(election_id)
    is_ls      = election_id.startswith("LS")

    # ── Lok Sabha: India state-level choropleth ──────────────────────
    if is_ls:
        ls_state_data = _LS_STATE_DATA.get(election_id, {})
        # Build result_map keyed by normalised state name
        result_map: dict[str, dict] = {}
        for state_name, d in ls_state_data.items():
            key = _norm(state_name)
            result_map[key] = {
                "constituency":      state_name,
                "leading_candidate": f"{d['seats']} seats",
                "leading_party":     d["party"],
                "trailing_candidate": f"out of {d['total']} seats",
                "trailing_party":    "",
                "margin":            "",
                "status":            "Won",
                "colour":            d["colour"],
            }
        return jsonify({
            "election_id":   election_id,
            "state":         "INDIA",
            "geojson_url":   _INDIA_STATES_GEOJSON,
            "result_map":    result_map,
            "party_colours": {},
            "type":          "lok_sabha",
            "map_note":      "Each state is coloured by its leading party. Tooltip shows seats won.",
        })

    # ── Vidhan Sabha (state) election ────────────────────────────────
    geojson_url = None
    if state_slug:
        geojson_url = _ASSEMBLY_GEOJSON.format(
            state=state_slug.replace(" ", "%20")
        )

    is_historical = bool(historical.get_election(election_id))

    # Build constituency result lookup
    result_map: dict[str, dict] = {}

    if not is_historical:
        # ── Live election: read from ECI store ───────────────────────
        with _lock:
            live = store["live_elections"]
        for idx, e in enumerate(live):
            if e.get("id") == election_id:
                with _lock:
                    const_data = store["constituents"].get(idx)
                if const_data is None:
                    const_data = eci.get_constituency_results(e)
                for r in (const_data or []):
                    key = _norm(r.get("constituency", ""))
                    if key:
                        result_map[key] = r
                break
    else:
        # ── Historical election: try ECI archive ─────────────────────
        const_data = hist_const.get_constituencies(election_id)
        for r in (const_data or []):
            key = _norm(r.get("constituency", ""))
            if key:
                result_map[key] = r

    # Party colour map (for styling unknown constituencies in historical elections)
    party_colours: dict[str, str] = {}
    if is_historical:
        elec = historical.get_election(election_id)
        for p in (elec or {}).get("partywise", []):
            party_colours[p["party"]] = p["colour"]

    has_archive = hist_const.is_available(election_id)
    map_note: str | None = None
    if is_historical and not result_map:
        if has_archive:
            map_note = "Fetching ECI archive data — may take a moment on first load"
        else:
            map_note = "Constituency data not available for this election"

    return jsonify({
        "election_id":   election_id,
        "state":         state_slug,
        "geojson_url":   geojson_url,
        "result_map":    result_map,
        "party_colours": party_colours,
        "type":          "historical" if is_historical else "live",
        "map_note":      map_note,
        "has_archive":   has_archive,
    })


# ── Control ──────────────────────────────────────────────────────────

@app.route("/api/refresh", methods=["POST"])
def api_refresh():
    with _lock:
        already = store["is_refreshing"]
    if already:
        return jsonify({"status": "already_refreshing"})
    refresh_async()
    return jsonify({"status": "started"})


@app.route("/api/status")
def api_status():
    with _lock:
        return jsonify({
            "live_elections":  len(store["live_elections"]),
            "historical":      len(HISTORICAL_ELECTIONS),
            "news":            len(store["news"]),
            "last_updated":    store["last_updated"],
            "is_refreshing":   store["is_refreshing"],
        })


# ── Entry point ──────────────────────────────────────────────────────
if __name__ == "__main__":
    logger.info("Starting India Election Monitor…")
    _do_refresh()
    logger.info("Ready — visit http://localhost:5000")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False, threaded=True)
