# 01_data_collector.py
# ═══════════════════════════════════════════
# جمع بيانات بغداد من مصادر مفتوحة
# ═══════════════════════════════════════════

import json
import os
import random
import math
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point, Polygon
from datetime import datetime, timedelta
from config import PATHS, BAGHDAD_CENTER, AMIRIYA_CENTER

def generate_baghdad_districts():
    """
    إنشاء بيانات أحياء بغداد الواقعية
    في المشروع الحقيقي: نجلبها من OSM
    """
    print("🗺️  جاري إنشاء بيانات أحياء بغداد...")

    districts = [
        # (الاسم، lat، lon، النوع، السكان، العمر)
        ("العامرية",      33.315, 44.288, "RESIDENTIAL", 85000,  35),
        ("الكرادة",       33.315, 44.395, "COMMERCIAL",  120000, 60),
        ("المنصور",       33.340, 44.360, "RESIDENTIAL", 95000,  50),
        ("الزعفرانية",    33.260, 44.430, "INDUSTRIAL",  60000,  40),
        ("الكاظمية",      33.380, 44.320, "RESIDENTIAL", 110000, 100),
        ("الرصافة",       33.345, 44.420, "COMMERCIAL",  140000, 70),
        ("الدورة",        33.265, 44.380, "RESIDENTIAL", 90000,  45),
        ("سيدية",         33.290, 44.340, "RESIDENTIAL", 75000,  30),
        ("حي الجامعة",    33.350, 44.280, "EDUCATIONAL", 40000,  55),
        ("المدينة الطبية",33.270, 44.400, "MEDICAL",     25000,  45),
        ("الشعب",         33.400, 44.450, "RESIDENTIAL", 130000, 40),
        ("الوزيرية",      33.355, 44.415, "GOVERNMENT",  30000,  80),
        ("البياع",        33.295, 44.295, "RESIDENTIAL", 88000,  25),
        ("أبو غريب",     33.295, 44.185, "RESIDENTIAL", 70000,  20),
        ("المحمودية",     33.070, 44.396, "RESIDENTIAL", 55000,  30),
    ]

    records = []
    for name, lat, lon, zone_type, pop, age in districts:

        # حساب درجة الخطر بناءً على العوامل
        flood_risk   = round(random.uniform(0.1, 0.9), 2)
        infra_score  = max(0, 1.0 - (age / 120) - random.uniform(0, 0.2))
        crime_index  = round(random.uniform(0.1, 0.7), 2)
        prop_price   = int(
            2_000_000 + (infra_score * 3_000_000) -
            (flood_risk * 1_000_000) + random.randint(-200000, 200000)
        )

        records.append({
            "name":             name,
            "lat":              lat,
            "lon":              lon,
            "zone_type":        zone_type,
            "population":       pop,
            "infrastructure_age": age,
            "flood_risk":       flood_risk,
            "infrastructure_score": round(infra_score, 2),
            "crime_index":      crime_index,
            "avg_property_price": max(prop_price, 500_000),
            "has_complex_plus": random.choice([True, False]),
            "last_maintenance": (
                datetime.now() -
                timedelta(days=random.randint(30, 500))
            ).strftime("%Y-%m-%d")
        })

    df = pd.DataFrame(records)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(r.lon, r.lat) for r in df.itertuples()],
        crs="EPSG:4326"
    )

    # حفظ البيانات
    os.makedirs(PATHS["data_processed"], exist_ok=True)
    output_path = PATHS["data_processed"] + "baghdad_districts.geojson"
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"  ✅ {len(df)} حي محفوظ في: {output_path}")
    return gdf


def generate_complexes_data(districts_gdf):
    """
    إنشاء بيانات مجمعات سكنية (عملاء Complex+)
    """
    print("🏗️  جاري إنشاء بيانات المجمعات السكنية...")

    complexes = []
    complex_id = 1

    for _, district in districts_gdf.iterrows():
        # كل حي يحتوي 3-8 مجمعات
        n_complexes = random.randint(3, 8)

        for i in range(n_complexes):
            # إضافة offset عشوائي حول مركز الحي
            offset_lat = random.uniform(-0.015, 0.015)
            offset_lon = random.uniform(-0.015, 0.015)

            total_units   = random.randint(40, 350)
            occupied      = int(total_units * random.uniform(0.65, 0.98))
            monthly_fee   = random.randint(50_000, 200_000)
            risk_score    = round(
                district["flood_risk"] * 0.4 +
                (1 - district["infrastructure_score"]) * 0.4 +
                random.uniform(0, 0.2), 2
            )

            complexes.append({
                "complex_id":      f"BGD-CPX-{complex_id:04d}",
                "name":            f"مجمع {district['name']} {i+1}",
                "district":        district["name"],
                "lat":             district["lat"] + offset_lat,
                "lon":             district["lon"] + offset_lon,
                "total_units":     total_units,
                "occupied_units":  occupied,
                "occupancy_rate":  round(occupied / total_units, 2),
                "monthly_fee_iqd": monthly_fee,
                "monthly_revenue": occupied * monthly_fee,
                "risk_score":      risk_score,
                "risk_level":      (
                    "CRITICAL" if risk_score > 0.7 else
                    "HIGH"     if risk_score > 0.5 else
                    "MEDIUM"   if risk_score > 0.3 else
                    "LOW"
                ),
                "complex_plus_connected": district["has_complex_plus"],
                "last_inspection": (
                    datetime.now() -
                    timedelta(days=random.randint(7, 200))
                ).strftime("%Y-%m-%d"),
                "amenities": random.sample(
                    ["مسبح", "جيم", "حديقة", "موقف", "أمن", "مولد"],
                    k=random.randint(2, 5)
                )
            })
            complex_id += 1

    df = pd.DataFrame(complexes)
    gdf = gpd.GeoDataFrame(
        df,
        geometry=[Point(r.lon, r.lat) for r in df.itertuples()],
        crs="EPSG:4326"
    )

    output_path = PATHS["data_processed"] + "baghdad_complexes.geojson"
    gdf.to_file(output_path, driver="GeoJSON")
    print(f"  ✅ {len(df)} مجمع محفوظ في: {output_path}")
    return gdf


def generate_energy_timeseries():
    """
    توليد سلسلة زمنية لبيانات الطاقة
    (في الواقع: من شبكة العدادات الذكية)
    """
    print("⚡ جاري توليد بيانات الطاقة التاريخية...")

    records = []
    base_date = datetime.now() - timedelta(days=90)

    for day in range(90):
        current_date = base_date + timedelta(days=day)
        is_summer    = current_date.month in [6, 7, 8, 9]
        is_weekend   = current_date.weekday() >= 4

        for hour in range(24):
            # نمط الاستهلاك الحقيقي
            base_load = 450
            if hour in [7, 8, 9]:
                base_load *= 1.3
            elif hour in [14, 15, 16, 17, 18]:
                base_load *= 1.6 if is_summer else 1.4
            elif hour in [0, 1, 2, 3, 4]:
                base_load *= 0.5

            if is_summer:
                base_load *= 1.4
            if is_weekend:
                base_load *= 0.85

            noise   = random.gauss(0, 20)
            voltage = round(220 + random.gauss(0, 8), 1)

            records.append({
                "datetime":    current_date.replace(hour=hour),
                "date":        current_date.strftime("%Y-%m-%d"),
                "hour":        hour,
                "day_of_week": current_date.weekday(),
                "is_summer":   int(is_summer),
                "is_weekend":  int(is_weekend),
                "consumption_mw": round(base_load + noise, 2),
                "voltage":     voltage,
                "outage":      int(random.random() < 0.08)
            })

    df = pd.DataFrame(records)
    output_path = PATHS["data_processed"] + "energy_timeseries.csv"
    df.to_csv(output_path, index=False)
    print(f"  ✅ {len(df):,} سجل طاقة محفوظ في: {output_path}")
    return df


if __name__ == "__main__":
    print("═" * 55)
    print("  مدينة+ — جمع البيانات")
    print("═" * 55)

    os.makedirs(PATHS["data_processed"], exist_ok=True)
    os.makedirs(PATHS["outputs"],        exist_ok=True)
    os.makedirs(PATHS["models"],         exist_ok=True)

    districts  = generate_baghdad_districts()
    complexes  = generate_complexes_data(districts)
    energy_df  = generate_energy_timeseries()

    print()
    print("═" * 55)
    print("  ✅ جمع البيانات اكتمل — جاهز للمرحلة التالية")
    print("═" * 55)