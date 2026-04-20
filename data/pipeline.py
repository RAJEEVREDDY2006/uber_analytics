# ============================================================
#  data/pipeline.py — FINAL (ADVANCED TIME SEGMENTS)
# ============================================================

import pandas as pd
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "cleaned_uber_data_apr14.csv")


def load_and_prepare():
    print("🔄 Loading data pipeline...")

    if not os.path.exists(DATA_PATH):
        raise FileNotFoundError(f"Dataset not found at: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)

    # ── Datetime ─────────────────────────────────────────────
    df['Date/Time'] = pd.to_datetime(df['Date/Time'], errors='coerce')
    df = df.dropna(subset=['Date/Time'])

    # ── Features ─────────────────────────────────────────────
    df['hour'] = df['Date/Time'].dt.hour
    df['weekday'] = df['Date/Time'].dt.day_name()

    df['is_weekend'] = df['weekday'].isin(['Saturday', 'Sunday'])

    # 🔥 ADVANCED TIME SEGMENTS
    df['time_period'] = df['hour'].apply(lambda x:
        'Late Night (12AM–5AM)' if x < 6 else
        'Morning (6AM–11AM)' if x < 12 else
        'Afternoon (12PM–4PM)' if x < 17 else
        'Evening (5PM–9PM)' if x < 22 else
        'Night (10PM–11PM)'
    )

    # ── Core Lookup ──────────────────────────────────────────
    grouped_data = df.groupby(['hour', 'weekday']).size().to_dict()

    # ── Stats ────────────────────────────────────────────────
    hourly_series = df.groupby('hour').size()
    avg_demand = float(hourly_series.mean())
    std_demand = float(hourly_series.std())

    total_rides = len(df)
    peak_hour = int(hourly_series.idxmax())
    peak_rides = int(hourly_series.max())

    weekday_avg = float(df[~df['is_weekend']].groupby('hour').size().mean())
    weekend_avg = float(df[df['is_weekend']].groupby('hour').size().mean())
    weekend_lift = round(((weekend_avg - weekday_avg) / weekday_avg) * 100, 1)

    # ── Charts ───────────────────────────────────────────────
    hourly_chart = {
        "labels": [f"{h:02d}:00" for h in range(24)],
        "data": [int(hourly_series.get(h, 0)) for h in range(24)],
    }

    days_order = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']
    weekday_series = df.groupby('weekday').size()

    weekday_chart = {
        "labels": days_order,
        "data": [int(weekday_series.get(d, 0)) for d in days_order],
    }

    # ── WEEKEND vs WEEKDAY ───────────────────────────────────
    weekend_data = df[df['is_weekend']].groupby('hour').size()
    weekday_data = df[~df['is_weekend']].groupby('hour').size()

    weekend_vs_weekday = {
        "labels": [f"{h:02d}" for h in range(24)],
        "weekday": [int(weekday_data.get(h, 0)) for h in range(24)],
        "weekend": [int(weekend_data.get(h, 0)) for h in range(24)]
    }

    # ── DAY vs NIGHT (NOW MULTI-CATEGORY) ─────────────────────
    order = [
        'Late Night (12AM–5AM)',
        'Morning (6AM–11AM)',
        'Afternoon (12PM–4PM)',
        'Evening (5PM–9PM)',
        'Night (10PM–11PM)'
    ]

    time_share = df.groupby('time_period').size().reindex(order)

    time_share_chart = {
        "labels": list(time_share.index),
        "data": [int(x) for x in time_share.values]
    }

    # ── Heatmap ──────────────────────────────────────────────
    heatmap_raw = df.groupby(['hour', 'weekday']).size().unstack(fill_value=0)
    heatmap_raw = heatmap_raw.reindex(columns=days_order, fill_value=0)

    heatmap_matrix = heatmap_raw.values.tolist()

    print(f"✅ Pipeline complete — {total_rides:,} rides loaded.")

    return {
        "df": df,
        "grouped_data": grouped_data,
        "avg_demand": avg_demand,
        "std_demand": std_demand,
        "total_rides": total_rides,
        "peak_hour": peak_hour,
        "peak_rides": peak_rides,
        "weekend_lift": weekend_lift,

        "hourly_chart": hourly_chart,
        "weekday_chart": weekday_chart,
        "weekend_vs_weekday": weekend_vs_weekday,

        # 🔥 UPDATED PIE
        "time_share_chart": time_share_chart,

        "heatmap_matrix": heatmap_matrix,
        "heatmap_days": days_order,
    }