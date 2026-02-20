import os

# --- Strategy V6: Score-Filtered YES (híbrido V3 + V4) ---
# V3 aporta: MarketScorer (4 señales, score 0-100) — solo entrar si score ≥ 60
# V4 aporta: lado YES (6-12¢), sizing pequeño, sin stop loss, jackpot potencial

# Entry range (YES side — mismo que V4)
MIN_YES_PRICE = float(os.environ.get("MIN_YES_PRICE", 0.06))
MAX_YES_PRICE = float(os.environ.get("MAX_YES_PRICE", 0.12))

# Score threshold (de V3)
MIN_ENTRY_SCORE = int(os.environ.get("MIN_ENTRY_SCORE", 60))

# Take profit (de V4 — = stop de V1 invertido)
TAKE_PROFIT_YES = float(os.environ.get("TAKE_PROFIT_YES", 0.15))
# Sin stop loss — posiciones pequeñas, se dejan correr hasta TP o resolución

# Volume thresholds for scoring (de V3)
SCORE_VOLUME_HIGH = float(os.environ.get("SCORE_VOLUME_HIGH", 500))  # +20 pts
SCORE_VOLUME_MID  = float(os.environ.get("SCORE_VOLUME_MID",  300))  # +15 pts
SCORE_VOLUME_LOW  = float(os.environ.get("SCORE_VOLUME_LOW",  200))  # +10 pts

# Price history
PRICE_HISTORY_TTL = int(os.environ.get("PRICE_HISTORY_TTL", 3600))

# Position sizing (de V4: 0.5%-1.0% inversamente proporcional al YES price)
POSITION_SIZE_MIN = float(os.environ.get("POSITION_SIZE_MIN", 0.005))  # 0.5%
POSITION_SIZE_MAX = float(os.environ.get("POSITION_SIZE_MAX", 0.010))  # 1.0%

# Shared scan parameters
MIN_VOLUME        = float(os.environ.get("MIN_VOLUME", 200))
MONITOR_INTERVAL  = int(os.environ.get("MONITOR_INTERVAL", 30))
SCAN_DAYS_AHEAD   = int(os.environ.get("SCAN_DAYS_AHEAD", 1))
MIN_LOCAL_HOUR    = int(os.environ.get("MIN_LOCAL_HOUR", 11))
MAX_POSITIONS     = int(os.environ.get("MAX_POSITIONS", 20))
PRICE_UPDATE_INTERVAL = int(os.environ.get("PRICE_UPDATE_INTERVAL", 10))

# Geographic correlation limits
MAX_REGION_EXPOSURE = float(os.environ.get("MAX_REGION_EXPOSURE", 0.25))

REGION_MAP = {
    "chicago": "midwest",       "denver": "midwest",
    "dallas": "south",          "houston": "south",
    "atlanta": "south",         "miami": "south",         "phoenix": "south",
    "boston": "northeast",      "nyc": "northeast",
    "seattle": "pacific",       "los-angeles": "pacific",
    "london": "europe",         "paris": "europe",        "ankara": "europe",
    "wellington": "southern",   "buenos-aires": "southern", "sao-paulo": "southern",
    "seoul": "asia",            "toronto": "north_america",
}

# Capital
INITIAL_CAPITAL = float(os.environ.get("INITIAL_CAPITAL", 100.0))
AUTO_MODE       = os.environ.get("AUTO_MODE", "true").lower() == "true"
AUTO_START      = os.environ.get("AUTO_START", "false").lower() == "true"

# API
GAMMA = os.environ.get("GAMMA_API", "https://gamma-api.polymarket.com")

# City UTC offsets — hardcoded (no tzdata on Railway slim Docker)
CITY_UTC_OFFSET = {
    "chicago":      -6,
    "dallas":       -6,
    "atlanta":      -5,
    "miami":        -5,
    "nyc":          -5,
    "boston":       -5,
    "toronto":      -5,
    "seattle":      -8,
    "los-angeles":  -8,
    "houston":      -6,
    "phoenix":      -7,
    "denver":       -7,
    "london":        0,
    "paris":         1,
    "ankara":        3,
    "seoul":         9,
    "wellington":   13,
    "sao-paulo":    -3,
    "buenos-aires": -3,
}

WEATHER_CITIES = [
    "chicago", "dallas", "atlanta", "miami", "nyc",
    "seattle", "london", "wellington", "toronto", "seoul",
    "ankara", "paris", "sao-paulo", "buenos-aires",
    "los-angeles", "houston", "phoenix", "denver", "boston",
]
