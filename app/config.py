import os

# --- Strategy V10: V6 + Day-of-Week Regime ---
# V6 base: Score-Filtered YES (6-12¢, score ≥ 60, TP 15¢, sin stop loss)
# V10 adds: different thresholds for weekdays vs weekends
#
# Observación: días de semana = alta volatilidad = YES sube a 15¢ = gana
#              fines de semana = baja volatilidad = YES no sube = pierde
#
# Por defecto: fines de semana BLOQUEADOS (WEEKEND_ENABLED=false)
# Si WEEKEND_ENABLED=true: usa umbrales WEEKEND_* (más conservadores)

# ── Day-of-week regime ────────────────────────────────────────────────────────
# Lunes=0 ... Viernes=4 = semana / Sábado=5, Domingo=6 = finde
WEEKEND_ENABLED = os.environ.get("WEEKEND_ENABLED", "false").lower() == "true"

# Weekday thresholds (lunes–viernes) — igual a V6
WEEKDAY_YES_MIN   = float(os.environ.get("WEEKDAY_YES_MIN",   0.06))
WEEKDAY_YES_MAX   = float(os.environ.get("WEEKDAY_YES_MAX",   0.12))
WEEKDAY_MIN_SCORE = int(os.environ.get("WEEKDAY_MIN_SCORE",   60))

# Weekend thresholds (sábado–domingo) — solo activo si WEEKEND_ENABLED=true
# Por defecto igual a V6 pero puedes subir el score mínimo para ser más selectivo
WEEKEND_YES_MIN   = float(os.environ.get("WEEKEND_YES_MIN",   0.06))
WEEKEND_YES_MAX   = float(os.environ.get("WEEKEND_YES_MAX",   0.10))   # rango más estrecho
WEEKEND_MIN_SCORE = int(os.environ.get("WEEKEND_MIN_SCORE",   75))     # score más alto

# Aliases usados en bot.py y scanner.py (apuntan a los valores de semana como defaults)
MIN_YES_PRICE   = WEEKDAY_YES_MIN
MAX_YES_PRICE   = WEEKDAY_YES_MAX
MIN_ENTRY_SCORE = WEEKDAY_MIN_SCORE

# ── Take profit ───────────────────────────────────────────────────────────────
TAKE_PROFIT_YES = float(os.environ.get("TAKE_PROFIT_YES", 0.15))
# Sin stop loss — posiciones pequeñas, se dejan correr hasta TP o resolución

# ── Volume thresholds for scoring ─────────────────────────────────────────────
SCORE_VOLUME_HIGH = float(os.environ.get("SCORE_VOLUME_HIGH", 500))  # +20 pts
SCORE_VOLUME_MID  = float(os.environ.get("SCORE_VOLUME_MID",  300))  # +15 pts
SCORE_VOLUME_LOW  = float(os.environ.get("SCORE_VOLUME_LOW",  200))  # +10 pts

# ── Price history ─────────────────────────────────────────────────────────────
PRICE_HISTORY_TTL = int(os.environ.get("PRICE_HISTORY_TTL", 3600))

# ── Position sizing (1.0%–2.0% inversamente proporcional al YES price) ────────
POSITION_SIZE_MIN = float(os.environ.get("POSITION_SIZE_MIN", 0.010))  # 1.0%
POSITION_SIZE_MAX = float(os.environ.get("POSITION_SIZE_MAX", 0.020))  # 2.0%

# ── Shared scan parameters ────────────────────────────────────────────────────
MIN_VOLUME        = float(os.environ.get("MIN_VOLUME", 200))
MONITOR_INTERVAL  = int(os.environ.get("MONITOR_INTERVAL", 30))
SCAN_DAYS_AHEAD   = int(os.environ.get("SCAN_DAYS_AHEAD", 1))
MIN_LOCAL_HOUR    = int(os.environ.get("MIN_LOCAL_HOUR", 11))
MAX_POSITIONS     = int(os.environ.get("MAX_POSITIONS", 20))
PRICE_UPDATE_INTERVAL = int(os.environ.get("PRICE_UPDATE_INTERVAL", 10))

# ── Geographic correlation limits ─────────────────────────────────────────────
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

# ── Capital ───────────────────────────────────────────────────────────────────
INITIAL_CAPITAL = float(os.environ.get("INITIAL_CAPITAL", 100.0))
AUTO_MODE       = os.environ.get("AUTO_MODE", "true").lower() == "true"
AUTO_START      = os.environ.get("AUTO_START", "true").lower() == "true"

# ── API ───────────────────────────────────────────────────────────────────────
GAMMA = os.environ.get("GAMMA_API", "https://gamma-api.polymarket.com")

# ── City UTC offsets — hardcoded (no tzdata on Railway slim Docker) ───────────
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
