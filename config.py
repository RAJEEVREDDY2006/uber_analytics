# ============================================================
#  config.py — Central Configuration (Tunable Constants)
# ============================================================

# --- Data ---
DATA_PATH = "data/cleaned_uber_data_apr14.csv"

# --- Demand Thresholds ---
HIGH_DEMAND_THRESHOLD   = 15000
MEDIUM_DEMAND_THRESHOLD = 5000

# --- Driver Supply ---
AVG_RIDES_PER_DRIVER = 8          # How many rides 1 driver handles per hour
SURGE_BASE_MULTIPLIER = 1.0       # Base pricing multiplier

# --- Anomaly Detection ---
ANOMALY_Z_THRESHOLD = 2.5         # Z-score threshold for spike detection

# --- Forecasting ---
FORECAST_HOURS = 24               # How many hours to forecast ahead

# --- Discount Strategy ---
DISCOUNT_RATE_LOW    = 0.15       # 15% discount during low demand
DISCOUNT_RATE_MEDIUM = 0.05       # 5% discount during medium demand

# --- Zone Clustering ---
N_ZONES = 6                       # KMeans clusters for geo-zones

# --- App ---
SECRET_KEY = "uber-dashboard-secret-2024"
DEBUG = True
PORT  = 5000