# ============================================================
#  analytics/anomaly.py — Anomaly & Spike Detection
# ============================================================

import pandas as pd
import numpy as np
from scipy import stats
from config import ANOMALY_Z_THRESHOLD


def detect_anomalies(df: pd.DataFrame) -> pd.DataFrame:
    """
    Detect anomalous demand spikes using Z-score per hour.
    Returns a DataFrame with anomaly flags and severity.
    """
    hourly = df.groupby(['hour', 'weekday']).size().reset_index(name='rides')

    # Z-score across all hour-day combos
    hourly['z_score']    = stats.zscore(hourly['rides'])
    hourly['is_anomaly'] = hourly['z_score'].abs() > ANOMALY_Z_THRESHOLD

    # Severity label
    def severity(z):
        az = abs(z)
        if az > 4.0:   return "Critical"
        if az > 3.0:   return "High"
        if az > ANOMALY_Z_THRESHOLD: return "Medium"
        return "Normal"

    hourly['severity'] = hourly['z_score'].apply(severity)
    return hourly


def get_anomaly_alerts(df: pd.DataFrame, top_n: int = 5) -> list[dict]:
    """
    Return top N anomaly alerts as a list of dicts for the dashboard.
    """
    anomalies_df = detect_anomalies(df)
    anomalies    = anomalies_df[anomalies_df['is_anomaly']].copy()
    anomalies    = anomalies.sort_values('z_score', ascending=False).head(top_n)

    alerts = []
    for _, row in anomalies.iterrows():
        direction = "spike" if row['z_score'] > 0 else "drop"
        alerts.append({
            "hour"     : int(row['hour']),
            "weekday"  : row['weekday'],
            "rides"    : int(row['rides']),
            "z_score"  : round(float(row['z_score']), 2),
            "severity" : row['severity'],
            "direction": direction,
            "message"  : (
                f"⚠️ {row['severity']} demand {direction} detected — "
                f"{row['weekday']} {int(row['hour']):02d}:00 "
                f"({int(row['rides']):,} rides, z={round(float(row['z_score']),2)})"
            )
        })
    return alerts


def check_current_anomaly(rides: int, avg_demand: float, std_demand: float) -> dict:
    """
    Check if a specific (hour, day) combo is anomalous.
    """
    if std_demand == 0:
        return {"is_anomaly": False}

    z = (rides - avg_demand) / std_demand
    is_anomaly = abs(z) > ANOMALY_Z_THRESHOLD
    return {
        "is_anomaly": is_anomaly,
        "z_score"   : round(z, 2),
        "severity"  : ("Critical" if abs(z)>4 else "High" if abs(z)>3
                        else "Medium" if is_anomaly else "Normal"),
        "message"   : (
            f"🚨 Anomaly detected! This slot is {abs(round(z,1))}σ "
            f"{'above' if z>0 else 'below'} normal."
        ) if is_anomaly else None
    }