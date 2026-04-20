# ============================================================
#  analytics/zones.py — Geo-Zone Clustering & Heatmap
# ============================================================

import pandas as pd
import numpy as np
import json
from sklearn.cluster import KMeans
from config import N_ZONES

try:
    import folium
    from folium.plugins import HeatMap
    FOLIUM_AVAILABLE = True
except ImportError:
    FOLIUM_AVAILABLE = False


def cluster_zones(df: pd.DataFrame) -> pd.DataFrame:
    """
    KMeans cluster lat/lon into N_ZONES demand zones.
    Returns df with 'zone' column added.
    """
    coords = df[['Lat', 'Lon']].dropna()
    km     = KMeans(n_clusters=N_ZONES, random_state=42, n_init=10)
    df = df.copy()
    df.loc[coords.index, 'zone'] = km.fit_predict(coords)
    df['zone'] = df['zone'].fillna(-1).astype(int)
    return df, km.cluster_centers_


def get_zone_stats(df: pd.DataFrame) -> list[dict]:
    """
    Returns per-zone ride counts, center coordinates, and demand level.
    """
    df_zoned, centers = cluster_zones(df)
    zone_counts = df_zoned.groupby('zone').size().reset_index(name='rides')

    max_rides = zone_counts['rides'].max()

    stats = []
    for _, row in zone_counts.iterrows():
        z    = int(row['zone'])
        if z == -1:
            continue
        pct  = round((row['rides'] / max_rides) * 100)
        lat, lon = centers[z]
        stats.append({
            "zone"  : z + 1,
            "rides" : int(row['rides']),
            "lat"   : round(float(lat), 4),
            "lon"   : round(float(lon), 4),
            "pct"   : pct,
            "level" : "High" if pct > 66 else "Medium" if pct > 33 else "Low"
        })

    return sorted(stats, key=lambda x: x['rides'], reverse=True)


def build_folium_map(df: pd.DataFrame, hour_filter: int = None) -> str:
    """
    Build a Folium HeatMap as an HTML string.
    Optionally filter by hour.
    """
    if not FOLIUM_AVAILABLE:
        return "<p>Folium not installed. Run: pip install folium</p>"

    df_map = df.copy()
    if hour_filter is not None:
        df_map = df_map[df_map['hour'] == hour_filter]

    sample = df_map[['Lat', 'Lon']].dropna().sample(min(5000, len(df_map)), random_state=42)

    m = folium.Map(
        location=[sample['Lat'].mean(), sample['Lon'].mean()],
        zoom_start=12,
        tiles='CartoDB dark_matter'
    )

    HeatMap(
        sample.values.tolist(),
        radius=10,
        blur=15,
        gradient={0.2: '#1a1a2e', 0.4: '#16213e', 0.6: '#0f3460',
                  0.8: '#e94560', 1.0: '#ffffff'}
    ).add_to(m)

    # Add zone markers
    zone_stats = get_zone_stats(df_map)
    for z in zone_stats[:N_ZONES]:
        folium.CircleMarker(
            location=[z['lat'], z['lon']],
            radius=10,
            color='#1dbf73',
            fill=True,
            fill_color='#1dbf73',
            fill_opacity=0.7,
            popup=f"Zone {z['zone']}: {z['rides']:,} rides ({z['level']} demand)",
            tooltip=f"Zone {z['zone']}"
        ).add_to(m)

    return m._repr_html_()


def get_heatmap_data(df: pd.DataFrame) -> list[list]:
    """
    Returns lat/lon/weight list for Chart.js or client-side heatmap.
    """
    sample = df[['Lat', 'Lon']].dropna().sample(min(3000, len(df)), random_state=7)
    return sample.values.tolist()