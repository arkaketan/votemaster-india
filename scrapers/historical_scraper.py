"""
Historical Indian Election Results
Provides verified party-wise seat data for major elections (2019–2025).
Primary source: hardcoded from official ECI data.
Secondary source: Wikipedia (attempted via requests + BeautifulSoup).
"""

import re
import logging
import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; ElectionMonitor/1.0)"
}

# ── Party colour map ─────────────────────────────────────────────────
COLOURS = {
    "BJP":      "#FF6B35", "INC":     "#1565C0", "AAP":    "#2196F3",
    "TMC":      "#1ABC9C", "DMK":     "#E53935", "AIADMK": "#4CAF50",
    "CPM":      "#B71C1C", "CPI":     "#D32F2F", "NCP":    "#FF9800",
    "SS":       "#FF5722", "RJD":     "#9C27B0", "JDU":    "#3F51B5",
    "SP":       "#E91E63", "BSP":     "#607D8B", "TDP":    "#FFC107",
    "YCP":      "#009688", "BRS":     "#795548", "SHS":    "#FF9800",
    "JMM":      "#4CAF50", "RLD":     "#AB47BC", "YSRCP":  "#009688",
    "SAD":      "#FFB300", "CPI(M)":  "#B71C1C", "ZPM":    "#00ACC1",
    "AIMIM":    "#FF6F00", "BAP":     "#7B1FA2", "INDIA":  "#1565C0",
    "NDA":      "#FF6B35", "LDF":     "#B71C1C", "UDF":    "#1565C0",
    "IND":      "#9E9E9E", "OTH":     "#757575",
}

def _col(party: str) -> str:
    for k, v in COLOURS.items():
        if k.upper() in party.upper():
            return v
    return "#757575"

def _p(party, full, won, vote_pct=None, alliance=None):
    return {
        "party": party, "full": full,
        "won": won, "leading": 0, "total": won,
        "vote_pct": vote_pct, "alliance": alliance,
        "colour": _col(party),
    }


# ══════════════════════════════════════════════════════════════════════
#  HARDCODED HISTORICAL DATABASE
# ══════════════════════════════════════════════════════════════════════

HISTORICAL_ELECTIONS = [

    # ── 2024 Lok Sabha ────────────────────────────────────────────────
    {
        "id": "LS2024", "type": "general",
        "name": "Lok Sabha General Election 2024",
        "short": "Lok Sabha 2024",
        "date": "2024-06-04", "total_seats": 543, "majority": 272,
        "winner": "NDA (BJP-led)",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2024_Indian_general_election",
        "keywords": ["lok sabha 2024", "general election 2024", "modi", "rahul gandhi",
                     "india bloc", "nda", "2024 election"],
        "partywise": [
            _p("BJP",      "Bharatiya Janata Party",        240, 36.56, "NDA"),
            _p("INC",      "Indian National Congress",       99, 21.19, "INDIA"),
            _p("SP",       "Samajwadi Party",                37,  9.34, "INDIA"),
            _p("AITC",     "All India Trinamool Congress",   29,  7.63, "INDIA"),
            _p("DMK",      "Dravida Munnetra Kazhagam",      22,  2.52, "INDIA"),
            _p("TDP",      "Telugu Desam Party",             16,  1.62, "NDA"),
            _p("JDU",      "Janata Dal (United)",            12,  1.28, "NDA"),
            _p("SS(UBT)",  "Shiv Sena (Uddhav)",              9,  0.96, "INDIA"),
            _p("NCP(SP)",  "NCP (Sharad Pawar)",              8,  0.73, "INDIA"),
            _p("CPI(M)",   "Communist Party of India (M)",    4,  0.64, "INDIA"),
            _p("YSRCP",    "YSR Congress Party",              4,  0.91, "OPP"),
            _p("INC(T)",   "Shiv Sena (Eknath Shinde)",       7,  0.52, "NDA"),
            _p("RJD",      "Rashtriya Janata Dal",            4,  0.45, "INDIA"),
            _p("IND",      "Independents",                    7,   None, None),
            _p("OTH",      "Other Parties",                  25,   None, None),
        ],
        "alliances": {
            "NDA":   {"seats": 293, "colour": "#FF6B35"},
            "INDIA": {"seats": 234, "colour": "#1565C0"},
            "Other": {"seats":  16, "colour": "#757575"},
        },
    },

    # ── 2024 Maharashtra ──────────────────────────────────────────────
    {
        "id": "MH2024", "type": "state",
        "name": "Maharashtra Assembly Election 2024",
        "short": "Maharashtra 2024",
        "date": "2024-11-23", "total_seats": 288, "majority": 145,
        "winner": "Mahayuti (BJP+SS+NCP)",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2024_Maharashtra_Legislative_Assembly_election",
        "keywords": ["maharashtra 2024", "maharashtra election", "mahayuti", "mva",
                     "fadnavis", "shinde", "ajit pawar"],
        "partywise": [
            _p("BJP",     "Bharatiya Janata Party",   132, 26.77, "Mahayuti"),
            _p("SS(SH)",  "Shiv Sena (Shinde)",        57,  9.96, "Mahayuti"),
            _p("NCP(AP)", "NCP (Ajit Pawar)",           41,  8.88, "Mahayuti"),
            _p("INC",     "Indian National Congress",   37, 11.97, "MVA"),
            _p("SS(UBT)", "Shiv Sena (Uddhav)",         20,  9.96, "MVA"),
            _p("NCP(SP)", "NCP (Sharad Pawar)",          10,  6.87, "MVA"),
            _p("SP",      "Samajwadi Party",              2,   None, "MVA"),
            _p("IND",     "Independents",                 8,   None, None),
            _p("OTH",     "Other Parties",                1,   None, None),
        ],
        "alliances": {
            "Mahayuti": {"seats": 230, "colour": "#FF6B35"},
            "MVA":      {"seats":  50, "colour": "#1565C0"},
            "Other":    {"seats":   8, "colour": "#757575"},
        },
    },

    # ── 2024 Jharkhand ────────────────────────────────────────────────
    {
        "id": "JH2024", "type": "state",
        "name": "Jharkhand Assembly Election 2024",
        "short": "Jharkhand 2024",
        "date": "2024-11-23", "total_seats": 81, "majority": 41,
        "winner": "JMM-led INDIA Bloc",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2024_Jharkhand_Legislative_Assembly_election",
        "keywords": ["jharkhand 2024", "jharkhand election", "hemant soren", "jmm"],
        "partywise": [
            _p("JMM",    "Jharkhand Mukti Morcha",     34, 23.44, "INDIA"),
            _p("INC",    "Indian National Congress",   16, 12.65, "INDIA"),
            _p("RJD",    "Rashtriya Janata Dal",         4,  4.31, "INDIA"),
            _p("CPI(ML)","CPI (Marxist-Leninist)",       2,  1.42, "INDIA"),
            _p("BJP",    "Bharatiya Janata Party",      21, 33.18, "NDA"),
            _p("AJSU",   "All Jharkhand Students Union", 1,  4.09, "NDA"),
            _p("JDU",    "Janata Dal (United)",          1,  1.10, "NDA"),
            _p("IND",    "Independents",                 2,   None, None),
        ],
        "alliances": {
            "INDIA": {"seats": 56, "colour": "#1565C0"},
            "NDA":   {"seats": 23, "colour": "#FF6B35"},
            "Other": {"seats":  2, "colour": "#757575"},
        },
    },

    # ── 2023 Rajasthan ────────────────────────────────────────────────
    {
        "id": "RJ2023", "type": "state",
        "name": "Rajasthan Assembly Election 2023",
        "short": "Rajasthan 2023",
        "date": "2023-12-03", "total_seats": 200, "majority": 101,
        "winner": "BJP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2023_Rajasthan_Legislative_Assembly_election",
        "keywords": ["rajasthan 2023", "rajasthan election", "gehlot", "vasundhara raje"],
        "partywise": [
            _p("BJP",  "Bharatiya Janata Party",   115, 41.69, None),
            _p("INC",  "Indian National Congress",  69, 39.53, None),
            _p("BAP",  "Bharat Adivasi Party",       3,  1.87, None),
            _p("RLP",  "Rashtriya Loktantrik Party", 0,  0.52, None),
            _p("IND",  "Independents",               9,   None, None),
            _p("OTH",  "Other Parties",              4,   None, None),
        ],
        "alliances": None,
    },

    # ── 2023 Madhya Pradesh ───────────────────────────────────────────
    {
        "id": "MP2023", "type": "state",
        "name": "Madhya Pradesh Assembly Election 2023",
        "short": "Madhya Pradesh 2023",
        "date": "2023-12-03", "total_seats": 230, "majority": 116,
        "winner": "BJP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2023_Madhya_Pradesh_Legislative_Assembly_election",
        "keywords": ["madhya pradesh 2023", "mp election 2023", "shivraj", "kamal nath"],
        "partywise": [
            _p("BJP",  "Bharatiya Janata Party",   163, 48.55, None),
            _p("INC",  "Indian National Congress",  66, 40.40, None),
            _p("BSP",  "Bahujan Samaj Party",        0,  2.48, None),
            _p("IND",  "Independents",               1,   None, None),
        ],
        "alliances": None,
    },

    # ── 2023 Chhattisgarh ─────────────────────────────────────────────
    {
        "id": "CG2023", "type": "state",
        "name": "Chhattisgarh Assembly Election 2023",
        "short": "Chhattisgarh 2023",
        "date": "2023-12-03", "total_seats": 90, "majority": 46,
        "winner": "BJP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2023_Chhattisgarh_Legislative_Assembly_election",
        "keywords": ["chhattisgarh 2023", "chhattisgarh election", "bhupesh baghel", "arun saw"],
        "partywise": [
            _p("BJP",  "Bharatiya Janata Party",   54, 46.27, None),
            _p("INC",  "Indian National Congress", 35, 42.23, None),
            _p("GGP",  "Gondwana Gantantra Party",  1,  0.51, None),
            _p("OTH",  "Other Parties",             0,   None, None),
        ],
        "alliances": None,
    },

    # ── 2023 Telangana ────────────────────────────────────────────────
    {
        "id": "TG2023", "type": "state",
        "name": "Telangana Assembly Election 2023",
        "short": "Telangana 2023",
        "date": "2023-12-03", "total_seats": 119, "majority": 60,
        "winner": "INC",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2023_Telangana_Legislative_Assembly_election",
        "keywords": ["telangana 2023", "telangana election", "revanth reddy", "brs", "kcr"],
        "partywise": [
            _p("INC",   "Indian National Congress", 64, 39.40, None),
            _p("BRS",   "Bharat Rashtra Samithi",   39, 37.35, None),
            _p("BJP",   "Bharatiya Janata Party",    8,  13.89, None),
            _p("AIMIM", "All India Majlis-e-Ittehadul Muslimeen", 7, 2.79, None),
            _p("IND",   "Independents",              1,   None, None),
        ],
        "alliances": None,
    },

    # ── 2023 Karnataka ────────────────────────────────────────────────
    {
        "id": "KA2023", "type": "state",
        "name": "Karnataka Assembly Election 2023",
        "short": "Karnataka 2023",
        "date": "2023-05-13", "total_seats": 224, "majority": 113,
        "winner": "INC",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2023_Karnataka_Legislative_Assembly_election",
        "keywords": ["karnataka 2023", "karnataka election", "siddaramaiah", "bommai"],
        "partywise": [
            _p("INC",  "Indian National Congress", 135, 42.88, None),
            _p("BJP",  "Bharatiya Janata Party",    66, 36.00, None),
            _p("JD(S)","Janata Dal (Secular)",       19, 13.29, None),
            _p("IND",  "Independents",               4,   None, None),
        ],
        "alliances": None,
    },

    # ── 2022 Uttar Pradesh ────────────────────────────────────────────
    {
        "id": "UP2022", "type": "state",
        "name": "Uttar Pradesh Assembly Election 2022",
        "short": "Uttar Pradesh 2022",
        "date": "2022-03-10", "total_seats": 403, "majority": 202,
        "winner": "BJP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2022_Uttar_Pradesh_Legislative_Assembly_election",
        "keywords": ["uttar pradesh 2022", "up election 2022", "yogi", "akhilesh"],
        "partywise": [
            _p("BJP",  "Bharatiya Janata Party (+ allies)", 255, 41.29, None),
            _p("SP",   "Samajwadi Party (+ allies)",        111, 32.06, None),
            _p("BSP",  "Bahujan Samaj Party",                 1, 12.88, None),
            _p("INC",  "Indian National Congress",            2,  2.33, None),
            _p("RLD",  "Rashtriya Lok Dal",                   8,   None, None),
            _p("IND",  "Independents",                       15,   None, None),
            _p("OTH",  "Other Parties",                      11,   None, None),
        ],
        "alliances": None,
    },

    # ── 2022 Punjab ───────────────────────────────────────────────────
    {
        "id": "PB2022", "type": "state",
        "name": "Punjab Assembly Election 2022",
        "short": "Punjab 2022",
        "date": "2022-03-10", "total_seats": 117, "majority": 59,
        "winner": "AAP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2022_Punjab_Legislative_Assembly_election",
        "keywords": ["punjab 2022", "punjab election 2022", "bhagwant mann", "aap punjab"],
        "partywise": [
            _p("AAP",  "Aam Aadmi Party",               92, 42.01, None),
            _p("INC",  "Indian National Congress",       18, 22.98, None),
            _p("SAD",  "Shiromani Akali Dal",             3, 18.38, None),
            _p("BJP",  "Bharatiya Janata Party",          2,  6.60, None),
            _p("BSP",  "Bahujan Samaj Party",             1,  1.44, None),
            _p("IND",  "Independents",                    1,   None, None),
        ],
        "alliances": None,
    },

    # ── 2022 Goa ──────────────────────────────────────────────────────
    {
        "id": "GA2022", "type": "state",
        "name": "Goa Assembly Election 2022",
        "short": "Goa 2022",
        "date": "2022-03-10", "total_seats": 40, "majority": 21,
        "winner": "BJP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2022_Goa_Legislative_Assembly_election",
        "keywords": ["goa 2022", "goa election 2022"],
        "partywise": [
            _p("BJP",  "Bharatiya Janata Party",   20, 33.35, None),
            _p("INC",  "Indian National Congress", 11, 23.46, None),
            _p("AAP",  "Aam Aadmi Party",           2, 6.77,  None),
            _p("MGP",  "Maharashtrawadi Gomantak",  2,  None,  None),
            _p("GFP",  "Goa Forward Party",         1,  None,  None),
            _p("IND",  "Independents",               4,  None,  None),
        ],
        "alliances": None,
    },

    # ── 2021 West Bengal ──────────────────────────────────────────────
    {
        "id": "WB2021", "type": "state",
        "name": "West Bengal Assembly Election 2021",
        "short": "West Bengal 2021",
        "date": "2021-05-02", "total_seats": 294, "majority": 148,
        "winner": "TMC",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2021_West_Bengal_legislative_assembly_election",
        "keywords": ["west bengal 2021", "bengal election 2021", "mamata", "tmc 2021"],
        "partywise": [
            _p("TMC",  "All India Trinamool Congress",  213, 47.94, None),
            _p("BJP",  "Bharatiya Janata Party",          77, 38.13, None),
            _p("ISF",  "Indian Secular Front",             5,  None, None),
            _p("INC",  "Indian National Congress",         0,  2.94, None),
            _p("CPI(M)","Communist Party of India (M)",    0,  4.87, None),
            _p("IND",  "Independents",                     1,  None, None),
        ],
        "alliances": None,
    },

    # ── 2021 Tamil Nadu ───────────────────────────────────────────────
    {
        "id": "TN2021", "type": "state",
        "name": "Tamil Nadu Assembly Election 2021",
        "short": "Tamil Nadu 2021",
        "date": "2021-05-02", "total_seats": 234, "majority": 118,
        "winner": "DMK Alliance",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2021_Tamil_Nadu_legislative_assembly_election",
        "keywords": ["tamil nadu 2021", "tn election 2021", "dmk 2021", "stalin", "aiadmk"],
        "partywise": [
            _p("DMK",    "Dravida Munnetra Kazhagam",    133, 37.00, "DMK Alliance"),
            _p("INC",    "Indian National Congress",      18,  None, "DMK Alliance"),
            _p("CPI",    "Communist Party of India",       2,  None, "DMK Alliance"),
            _p("CPI(M)", "Communist Party of India (M)",   2,  None, "DMK Alliance"),
            _p("VCK",    "Viduthalai Chiruthaigal Katchi", 4,  None, "DMK Alliance"),
            _p("AIADMK", "All India Anna DMK",             66, 33.28, "AIADMK Alliance"),
            _p("BJP",    "Bharatiya Janata Party",          4,  2.59, "AIADMK Alliance"),
            _p("PMK",    "Pattali Makkal Katchi",           5,  None, "AIADMK Alliance"),
            _p("IND",    "Independents",                    0,  None, None),
        ],
        "alliances": {
            "DMK Alliance":    {"seats": 159, "colour": "#E53935"},
            "AIADMK Alliance": {"seats":  75, "colour": "#4CAF50"},
        },
    },

    # ── 2021 Kerala ───────────────────────────────────────────────────
    {
        "id": "KL2021", "type": "state",
        "name": "Kerala Assembly Election 2021",
        "short": "Kerala 2021",
        "date": "2021-05-02", "total_seats": 140, "majority": 71,
        "winner": "LDF (Left)",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2021_Kerala_legislative_assembly_election",
        "keywords": ["kerala 2021", "kerala election 2021", "ldf", "udf", "pinarayi"],
        "partywise": [
            _p("CPI(M)",  "Communist Party of India (M)",  62, 25.72, "LDF"),
            _p("CPI",     "Communist Party of India",       17, None,  "LDF"),
            _p("JD(S)",   "Janata Dal (Secular)",            1, None,  "LDF"),
            _p("NCP",     "Nationalist Congress Party",      2, None,  "LDF"),
            _p("LDF-OTH", "LDF Others",                     17, None,  "LDF"),
            _p("INC",     "Indian National Congress",        21, 25.84, "UDF"),
            _p("IUML",    "Indian Union Muslim League",      15, None,  "UDF"),
            _p("KC(M)",   "Kerala Congress (M)",              5, None,  "UDF"),
            _p("UDF-OTH", "UDF Others",                      0, None,  "UDF"),
            _p("BJP",     "Bharatiya Janata Party",           1, 12.47, None),
        ],
        "alliances": {
            "LDF": {"seats": 99, "colour": "#B71C1C"},
            "UDF": {"seats": 41, "colour": "#1565C0"},
            "BJP/Other": {"seats": 1, "colour": "#FF6B35"},
        },
    },

    # ── 2021 Assam ────────────────────────────────────────────────────
    {
        "id": "AS2021", "type": "state",
        "name": "Assam Assembly Election 2021",
        "short": "Assam 2021",
        "date": "2021-05-02", "total_seats": 126, "majority": 64,
        "winner": "BJP Alliance",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2021_Assam_legislative_assembly_election",
        "keywords": ["assam 2021", "assam election 2021", "himanta", "bjp assam"],
        "partywise": [
            _p("BJP",   "Bharatiya Janata Party",   60, 33.22, "NDA"),
            _p("AGP",   "Asom Gana Parishad",         9,  7.97, "NDA"),
            _p("UPPL",  "United People's Party Liberal", 6, None, "NDA"),
            _p("INC",   "Indian National Congress",   29, 29.67, "MGB"),
            _p("AIUDF", "All India United Democratic Front", 16, 9.29, "MGB"),
            _p("CPI(M)","Communist Party of India (M)", 1, None, "MGB"),
            _p("BPF",   "Bodoland People's Front",    4,  None, None),
            _p("IND",   "Independents",               1,  None, None),
        ],
        "alliances": {
            "NDA (BJP-led)": {"seats": 75, "colour": "#FF6B35"},
            "MGB (INC-led)": {"seats": 50, "colour": "#1565C0"},
            "Other":         {"seats":  1, "colour": "#757575"},
        },
    },

    # ── 2020 Delhi ────────────────────────────────────────────────────
    {
        "id": "DL2020", "type": "state",
        "name": "Delhi Assembly Election 2020",
        "short": "Delhi 2020",
        "date": "2020-02-11", "total_seats": 70, "majority": 36,
        "winner": "AAP",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2020_Delhi_legislative_assembly_election",
        "keywords": ["delhi 2020", "delhi election 2020", "kejriwal", "aap delhi"],
        "partywise": [
            _p("AAP",  "Aam Aadmi Party",            62, 53.57, None),
            _p("BJP",  "Bharatiya Janata Party",       8, 38.51, None),
            _p("INC",  "Indian National Congress",     0,  4.26, None),
            _p("IND",  "Independents",                 0,   None, None),
        ],
        "alliances": None,
    },

    # ── 2019 Lok Sabha ────────────────────────────────────────────────
    {
        "id": "LS2019", "type": "general",
        "name": "Lok Sabha General Election 2019",
        "short": "Lok Sabha 2019",
        "date": "2019-05-23", "total_seats": 543, "majority": 272,
        "winner": "NDA (BJP-led)",
        "wikipedia_url": "https://en.wikipedia.org/wiki/2019_Indian_general_election",
        "keywords": ["lok sabha 2019", "general election 2019", "2019 election", "modi 2019"],
        "partywise": [
            _p("BJP",    "Bharatiya Janata Party",        303, 37.36, "NDA"),
            _p("INC",    "Indian National Congress",       52, 19.49, "UPA"),
            _p("DMK",    "Dravida Munnetra Kazhagam",      24,  2.26, "UPA"),
            _p("AITC",   "All India Trinamool Congress",   22,  4.07, None),
            _p("YSRCP",  "YSR Congress Party",             22,  2.53, None),
            _p("SS",     "Shiv Sena",                      18,  2.10, "NDA"),
            _p("JDU",    "Janata Dal (United)",             16,  1.46, "NDA"),
            _p("BSP",    "Bahujan Samaj Party",             10,  3.63, None),
            _p("TRS",    "Telangana Rashtra Samithi",        9,  1.30, None),
            _p("LJP",    "Lok Janshakti Party",              6,  0.58, "NDA"),
            _p("NCP",    "Nationalist Congress Party",       5,  2.36, "UPA"),
            _p("SP",     "Samajwadi Party",                  5,  2.55, None),
            _p("IND",    "Independents",                     4,   None, None),
            _p("OTH",    "Other Parties",                   47,   None, None),
        ],
        "alliances": {
            "NDA":   {"seats": 353, "colour": "#FF6B35"},
            "UPA":   {"seats":  91, "colour": "#1565C0"},
            "Other": {"seats":  99, "colour": "#757575"},
        },
    },
]


# ══════════════════════════════════════════════════════════════════════
#  Wikipedia scraper (optional enhancement)
# ══════════════════════════════════════════════════════════════════════

def _scrape_wikipedia_results(url: str, election: dict) -> list[dict] | None:
    """
    Attempt to scrape party-wise results from a Wikipedia election page.
    Returns None on failure (caller falls back to hardcoded data).
    """
    try:
        resp = requests.get(url, headers=HEADERS, timeout=12)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # Find results table — Wikipedia election pages typically have a
        # "wikitable" with party rows containing seats/vote data.
        for table in soup.find_all("table", class_=re.compile("wikitable")):
            headers = [th.get_text(" ", strip=True).lower()
                       for th in table.find_all(["th"])]
            joined = " ".join(headers)
            # Must have both party and seats columns
            if not ("party" in joined or "alliance" in joined):
                continue
            if not ("seat" in joined or "won" in joined):
                continue

            rows = []
            for tr in table.find_all("tr")[1:]:
                cells = tr.find_all(["td", "th"])
                if len(cells) < 3:
                    continue
                texts = [c.get_text(" ", strip=True) for c in cells]
                # Try to extract party name and seats won
                party_name = texts[0] if texts else ""
                # Look for a numeric seats column
                seats = 0
                vote_pct = None
                for t in texts[1:]:
                    t_clean = t.replace(",", "").replace("+", "").replace("−", "").strip()
                    if re.match(r"^\d+$", t_clean):
                        seats = int(t_clean)
                        break
                # Look for vote %
                for t in texts:
                    m = re.search(r"(\d+\.\d+)\s*%", t)
                    if m:
                        vote_pct = float(m.group(1))
                        break

                if not party_name or party_name.lower() in ("total", "party", "alliance"):
                    continue
                if seats == 0 and vote_pct is None:
                    continue

                rows.append({
                    "party":    party_name[:30],
                    "full":     party_name,
                    "won":      seats,
                    "leading":  0,
                    "total":    seats,
                    "vote_pct": vote_pct,
                    "colour":   _col(party_name),
                })

            if rows:
                rows.sort(key=lambda r: r["total"], reverse=True)
                return rows[:15]

    except Exception as exc:
        logger.debug("Wikipedia scrape failed for %s: %s", url, exc)
    return None


# ══════════════════════════════════════════════════════════════════════
#  Public API
# ══════════════════════════════════════════════════════════════════════

class HistoricalScraper:

    def get_all_elections(self) -> list[dict]:
        """Return all historical elections (metadata only, no partywise)."""
        return [
            {k: v for k, v in e.items() if k != "partywise"}
            for e in HISTORICAL_ELECTIONS
        ]

    def get_election(self, election_id: str) -> dict | None:
        """Get a single election by ID, including partywise data."""
        for e in HISTORICAL_ELECTIONS:
            if e["id"] == election_id:
                return e
        return None

    def get_partywise(self, election_id: str, try_wikipedia: bool = False) -> list[dict]:
        """
        Return party-wise results for a historical election.
        Optionally tries Wikipedia first; falls back to hardcoded.
        """
        election = self.get_election(election_id)
        if not election:
            return []

        if try_wikipedia and election.get("wikipedia_url"):
            wiki_data = _scrape_wikipedia_results(
                election["wikipedia_url"], election
            )
            if wiki_data:
                logger.info("Using Wikipedia data for %s", election_id)
                return wiki_data

        # Return hardcoded data
        return election.get("partywise", [])

    def search_elections(self, query: str) -> list[dict]:
        """Search elections by keyword."""
        q = query.lower()
        results = []
        for e in HISTORICAL_ELECTIONS:
            if q in e["name"].lower() or q in e["id"].lower():
                results.append(e)
            elif any(q in kw for kw in e.get("keywords", [])):
                results.append(e)
        return results
