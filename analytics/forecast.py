# ============================================================
#  analytics/forecast.py — FIXED & SAFE VERSION
# ============================================================

import pandas as pd
import numpy as np

# 🔥 FIX: Avoid dependency on config.py
FORECAST_HOURS = 24

# Try Prophet (optional)
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    print("Prophet not installed. Using fallback forecasting.")


# ────────────────────────────────────────────────────────────
# Convert data for Prophet
# ────────────────────────────────────────────────────────────
def _build_prophet_df(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df['Date/Time'] = pd.to_datetime(df['Date/Time'])
    df['ds'] = df['Date/Time'].dt.floor('H')
    prophet_df = df.groupby('ds').size().reset_index(name='y')
    return prophet_df


# ────────────────────────────────────────────────────────────
# MAIN FUNCTION (IMPORTANT)
# ────────────────────────────────────────────────────────────
def train_and_forecast(df: pd.DataFrame) -> dict:
    print("Forecast module running...")

    # If Prophet not available → fallback
    if not PROPHET_AVAILABLE:
        return _fallback_forecast(df)

    try:
        prophet_df = _build_prophet_df(df)

        model = Prophet(
            changepoint_prior_scale=0.05,
            seasonality_mode='multiplicative',
            daily_seasonality=True,
            weekly_seasonality=True,
        )

        model.fit(prophet_df)

        future = model.make_future_dataframe(periods=FORECAST_HOURS, freq='H')
        forecast = model.predict(future)

        actual_tail = prophet_df.tail(48)
        forecast_tail = forecast.tail(FORECAST_HOURS)

        return {
            "labels": (
                list(actual_tail['ds'].dt.strftime('%a %H:%M')) +
                list(forecast_tail['ds'].dt.strftime('%a %H:%M'))
            ),
            "actual": list(actual_tail['y'].astype(int)) + [None]*FORECAST_HOURS,
            "predicted": [None]*len(actual_tail) + list(forecast_tail['yhat'].clip(0).astype(int)),
            "lower": [None]*len(actual_tail) + list(forecast_tail['yhat_lower'].clip(0).astype(int)),
            "upper": [None]*len(actual_tail) + list(forecast_tail['yhat_upper'].clip(0).astype(int)),
            "peak_forecast_hour": int(forecast_tail.loc[forecast_tail['yhat'].idxmax(), 'ds'].hour),
            "peak_forecast_rides": int(forecast_tail['yhat'].max()),
        }

    except Exception as e:
        print(f"Prophet failed: {e}")
        return _fallback_forecast(df)


# ────────────────────────────────────────────────────────────
# FALLBACK FORECAST (SAFE)
# ────────────────────────────────────────────────────────────
def _fallback_forecast(df: pd.DataFrame) -> dict:
    hourly = df.groupby('hour').size().reset_index(name='rides')
    rides = list(hourly['rides'])

    labels = [f"{h:02d}:00" for h in range(24)] * 3

    return {
        "labels": labels[:72],
        "actual": rides * 2 + [None]*24,
        "predicted": [None]*48 + rides,
        "lower": [None]*48 + [int(r * 0.8) for r in rides],
        "upper": [None]*48 + [int(r * 1.2) for r in rides],
        "peak_forecast_hour": int(hourly.loc[hourly['rides'].idxmax(), 'hour']),
        "peak_forecast_rides": int(hourly['rides'].max()),
    }


# ────────────────────────────────────────────────────────────
# SPARKLINE FUNCTION
# ────────────────────────────────────────────────────────────
def get_next_6h_sparkline(df: pd.DataFrame, current_hour: int) -> list[int]:
    hourly = df.groupby('hour').size()
    return [int(hourly.get((current_hour + i) % 24, 0)) for i in range(1, 7)]