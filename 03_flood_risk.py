# 03_flood_risk.py
# ═══════════════════════════════════════════
# خريطة خطر الفيضانات لبغداد
# ═══════════════════════════════════════════

import math
import random
import numpy as np
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
from config import PATHS, BAGHDAD_CENTER

def calculate_flood_risk_grid():
    """
    حساب شبكة خطر الفيضانات لبغداد
    دقة: شبكة 500م × 500م
    """
    print("🌊 حساب خريطة خطر الفيضانات...")

    # نهر دجلة — المؤثر الرئيسي
    tigris_points = [
        (33.190, 44.440), (33.220, 44.420),
        (33.250, 44.410), (33.290, 44.395),
        (33.315, 44.390), (33.345, 44.415),
        (33.370, 44.400), (33.400, 44.390),
    ]

    # مناطق منخفضة طبيعياً (بيانات DEM مبسّطة)
    low_elevation_zones = [
        (33.260, 44.380, 0.85),  # الدورة — منخفضة
        (33.290, 44.350, 0.65),  # سيدية
        (33.315, 44.395, 0.70),  # الكرادة — قرب النهر
        (33.345, 44.420, 0.75),  # الرصافة
        (33.400, 44.450, 0.60),  # الشعب
    ]

    records = []

    for lat in np.arange(33.05, 33.55, 0.008):
        for lon in np.arange(44.10, 44.60, 0.008):

            # المسافة من نهر دجلة
            min_river_dist = min(
                math.sqrt((lat - p[0])**2 + (lon - p[1])**2)
                for p in tigris_points
            )
            river_factor = max(0, 1 - (min_river_dist / 0.08))

            # تأثير المناطق المنخفضة
            elevation_factor = 0
            for zlat, zlon, zrisk in low_elevation_zones:
                dist = math.sqrt((lat - zlat)**2 + (lon - zlon)**2)
                if dist < 0.04:
                    elevation_factor = max(
                        elevation_factor,
                        zrisk * (1 - dist / 0.04)
                    )

            # ضعف البنية التحتية (أقدم الأحياء أكثر خطراً)
            infra_factor = random.uniform(0.1, 0.4)

            # حساب الخطر الكلي
            flood_risk = min(
                river_factor * 0.5 +
                elevation_factor * 0.35 +
                infra_factor * 0.15 +
                random.gauss(0, 0.05),
                1.0
            )
            flood_risk = max(0.0, flood_risk)

            records.append({
                "lat":        round(lat, 4),
                "lon":        round(lon, 4),
                "flood_risk": round(flood_risk, 3),
                "risk_level": (
                    "CRITICAL" if flood_risk > 0.75 else
                    "HIGH"     if flood_risk > 0.55 else
                    "MEDIUM"   if flood_risk > 0.35 else
                    "LOW"
                ),
                "river_proximity": round(river_factor, 3),
                "elevation_risk":  round(elevation_factor, 3)
            })

    df  = pd.DataFrame(records)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(r.lon, r.lat) for r in df.itertuples()],
        crs="EPSG:4326"
    )

    output_path = PATHS["data_processed"] + "flood_risk_grid.geojson"
    gdf.to_file(output_path, driver="GeoJSON")

    critical = len(df[df["flood_risk"] > 0.75])
    print(f"  ✅ {len(df):,} خلية شبكية محسوبة")
    print(f"  ⚠️  {critical} منطقة بخطر حرج")

    return gdf


if __name__ == "__main__":
    print("═" * 55)
    print("  مدينة+ — خريطة الفيضانات")
    print("═" * 55)
    calculate_flood_risk_grid()
    print("  ✅ خريطة الفيضانات جاهزة")