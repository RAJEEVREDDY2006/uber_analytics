# ============================================================
#  app.py — Uber Demand Dashboard (FINAL UPDATED VERSION)
# ============================================================

import json
import sys
import os

print("🚀 App starting...")

sys.path.insert(0, os.path.dirname(__file__))

from flask import Flask, render_template, request, jsonify
import pandas as pd

from config import SECRET_KEY, DEBUG, PORT
from data.pipeline import load_and_prepare
from analytics.demand import classify_demand, scenario_simulate
from analytics.anomaly import get_anomaly_alerts, check_current_anomaly
from analytics.forecast import train_and_forecast, get_next_6h_sparkline
from analytics.zones import build_folium_map, get_zone_stats


# ── App Init ─────────────────────────────────────────────────
app = Flask(__name__)
app.secret_key = SECRET_KEY


# ── Load Data ────────────────────────────────────────────────
print("🔄 Loading data pipeline...")
STORE = load_and_prepare()
print("✅ Data loaded.")


# ── Skip heavy forecast at startup ───────────────────────────
FORECAST_DATA = None


# ── Zones ────────────────────────────────────────────────────
print("📍 Computing zones...")
try:
    ZONE_STATS = get_zone_stats(STORE["df"])
except Exception as e:
    print("Zone error:", e)
    ZONE_STATS = []


# ── Anomalies ────────────────────────────────────────────────
print("🚨 Detecting anomalies...")
try:
    ANOMALY_ALERTS = get_anomaly_alerts(STORE["df"], top_n=5)
except Exception as e:
    print("Anomaly error:", e)
    ANOMALY_ALERTS = []


# ============================================================
# HOME ROUTE
# ============================================================

@app.route('/', methods=['GET', 'POST'])
def home():

    result = None
    anomaly = None
    sparkline = []

    if request.method == 'POST':
        hour = int(request.form['hour'])
        day = request.form['day']

        rides = STORE["grouped_data"].get((hour, day), 0)

        result = classify_demand(rides, STORE["avg_demand"])
        result.update({
            "hour": hour,
            "day": day,
            "rides": rides
        })

        anomaly = check_current_anomaly(
            rides,
            STORE["avg_demand"],
            STORE["std_demand"]
        )

        sparkline = get_next_6h_sparkline(STORE["df"], hour)

    return render_template(
        'index.html',

        # Core
        result=result,
        anomaly=anomaly,
        sparkline=json.dumps(sparkline),

        # Alerts & zones
        anomaly_alerts=ANOMALY_ALERTS,
        zone_stats=ZONE_STATS,

        # Charts (IMPORTANT: JSON SAFE)
        hourly_chart=json.dumps(STORE.get("hourly_chart", {})),
        weekday_chart=json.dumps(STORE.get("weekday_chart", {})),
        weekend_vs_weekday=json.dumps(STORE.get("weekend_vs_weekday", {})),
        day_night_chart=json.dumps(STORE.get("day_night_chart", {})),
        time_share_chart=json.dumps(STORE.get("time_share_chart", {})),

        # Optional
        heatmap_data=json.dumps(STORE.get("heatmap_matrix", [])),
        heatmap_days=json.dumps(STORE.get("heatmap_days", [])),

        forecast_data=None,

        # KPI
        kpi={
            "total_rides": f"{STORE['total_rides']:,}",
            "peak_hour": f"{STORE['peak_hour']:02d}:00",
            "peak_rides": f"{STORE['peak_rides']:,}",
            "weekend_lift": f"{STORE['weekend_lift']}%",
        }
    )


# ============================================================
# API ROUTES
# ============================================================

@app.route('/api/demand')
def api_demand():
    try:
        hour = int(request.args.get('hour', 17))
        day = request.args.get('day', 'Friday')

        rides = STORE["grouped_data"].get((hour, day), 0)
        result = classify_demand(rides, STORE["avg_demand"])

        result.update({
            "hour": hour,
            "day": day,
            "rides": rides,
            "status": "ok"
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/scenario')
def api_scenario():
    try:
        hour = int(request.args.get('hour', 17))
        day = request.args.get('day', 'Friday')
        multiplier = float(request.args.get('multiplier', 1.0))
        extra = int(request.args.get('extra_drivers', 0))

        rides = STORE["grouped_data"].get((hour, day), 0)

        result = scenario_simulate(
            rides,
            STORE["avg_demand"],
            multiplier,
            extra
        )

        result.update({
            "hour": hour,
            "day": day,
            "original_rides": rides,
            "status": "ok"
        })

        return jsonify(result)

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route('/api/anomalies')
def api_anomalies():
    return jsonify({
        "status": "ok",
        "alerts": ANOMALY_ALERTS,
        "count": len(ANOMALY_ALERTS)
    })


@app.route('/api/forecast')
def api_forecast():
    global FORECAST_DATA

    if FORECAST_DATA is None:
        print("🔮 Running forecast...")
        try:
            FORECAST_DATA = train_and_forecast(STORE["df"])
        except Exception as e:
            return jsonify({"status": "error", "message": str(e)}), 500

    return jsonify({"status": "ok", **FORECAST_DATA})


@app.route('/api/zones')
def api_zones():
    return jsonify({"status": "ok", "zones": ZONE_STATS})


@app.route('/api/kpi')
def api_kpi():
    return jsonify({
        "status": "ok",
        "total_rides": STORE["total_rides"],
        "peak_hour": STORE["peak_hour"],
        "peak_rides": STORE["peak_rides"],
        "weekend_lift": STORE["weekend_lift"],
        "avg_demand": round(STORE["avg_demand"], 2),
    })


# ============================================================
# MAP
# ============================================================

@app.route('/map')
def map_view():
    hour_filter = request.args.get('hour', type=int)

    try:
        map_html = build_folium_map(STORE["df"], hour_filter)
    except Exception as e:
        map_html = f"<p>Map unavailable: {e}</p>"

    return render_template(
        'map.html',
        map_html=map_html,
        hour_filter=hour_filter
    )


# ============================================================
# RUN APP
# ============================================================

if __name__ == '__main__':
    print(f"\n🚖 Uber Dashboard running → http://127.0.0.1:{PORT}\n")
    app.run(debug=DEBUG, port=PORT)