# ============================================================
#  analytics/demand.py — Demand Classification Engine
# ============================================================

import pandas as pd
import numpy as np
from config import (
    HIGH_DEMAND_THRESHOLD, MEDIUM_DEMAND_THRESHOLD,
    AVG_RIDES_PER_DRIVER, SURGE_BASE_MULTIPLIER,
    DISCOUNT_RATE_LOW, DISCOUNT_RATE_MEDIUM
)


def classify_demand(rides: int, avg_demand: float) -> dict:
    """
    Classify demand level and return a rich result dict with
    level, insight, action, confidence, surge multiplier,
    recommended drivers, ROI estimate, and comparison.
    """

    # --- Demand Level ---
    if rides > HIGH_DEMAND_THRESHOLD:
        level   = "High"
        color   = "danger"
        emoji   = "🔴"
        insight = "Peak demand — riders are surging. Every unmatched ride is lost revenue."
    elif rides > MEDIUM_DEMAND_THRESHOLD:
        level   = "Medium"
        color   = "warning"
        emoji   = "🟡"
        insight = "Moderate demand — steady flow. Small optimisations can lift conversion."
    else:
        level   = "Low"
        color   = "success"
        emoji   = "🟢"
        insight = "Low demand — riders are sparse. Stimulate supply-side engagement."

    # --- Surge Multiplier ---
    surge = round(max(SURGE_BASE_MULTIPLIER, rides / max(avg_demand, 1)), 2)

    # --- Recommended Drivers ---
    recommended_drivers = max(1, round(rides / AVG_RIDES_PER_DRIVER))

    # --- Smart Action ---
    if level == "High":
        action = (
            f"Deploy {recommended_drivers} drivers immediately. "
            f"Enable surge pricing ({surge}×). "
            "Focus on Zone 3 & Zone 7 (historically highest density)."
        )
    elif level == "Medium":
        action = (
            f"Maintain {recommended_drivers} drivers on standby. "
            f"Apply a {int(DISCOUNT_RATE_MEDIUM*100)}% loyalty promo "
            "to convert hesitant riders."
        )
    else:
        action = (
            f"Reduce active fleet to {recommended_drivers} drivers. "
            f"Launch a {int(DISCOUNT_RATE_LOW*100)}% discount campaign. "
            "Target airport & transit corridors."
        )

    # --- Comparison vs Average ---
    if rides > avg_demand:
        pct_diff   = round(((rides - avg_demand) / avg_demand) * 100, 1)
        comparison = f"▲ {pct_diff}% above hourly average"
    else:
        pct_diff   = round(((avg_demand - rides) / avg_demand) * 100, 1)
        comparison = f"▼ {pct_diff}% below hourly average"

    # --- ROI Estimate (avg NYC Uber fare ~$18) ---
    avg_fare       = 18
    unmet_estimate = max(0, rides - (recommended_drivers * AVG_RIDES_PER_DRIVER))
    roi_estimate   = round(unmet_estimate * avg_fare)

    # --- Confidence (based on sample richness) ---
    confidence = min(99, int(70 + (min(rides, 20000) / 20000) * 29))

    return {
        "level"               : level,
        "color"               : color,
        "emoji"               : emoji,
        "insight"             : insight,
        "action"              : action,
        "comparison"          : comparison,
        "surge"               : surge,
        "recommended_drivers" : recommended_drivers,
        "roi_estimate"        : roi_estimate,
        "confidence"          : confidence,
    }


def scenario_simulate(rides: int, avg_demand: float,
                       demand_multiplier: float = 1.0,
                       extra_drivers: int = 0) -> dict:
    """
    What-if scenario: scale rides by a multiplier and see how
    recommendations change. Returns a scenario result dict.
    """
    simulated_rides = int(rides * demand_multiplier) + (extra_drivers * AVG_RIDES_PER_DRIVER)
    result = classify_demand(simulated_rides, avg_demand)
    result["simulated_rides"]      = simulated_rides
    result["demand_multiplier"]    = demand_multiplier
    result["extra_drivers_added"]  = extra_drivers
    return result