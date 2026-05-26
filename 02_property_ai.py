# 02_property_ai.py
# ═══════════════════════════════════════════
# نموذج AI لتقييم العقارات
# ═══════════════════════════════════════════

import os
import pickle
import pandas as pd
import numpy as np
import geopandas as gpd
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import mean_absolute_error, r2_score
from config import PATHS, COLORS

def train_property_model():
    """تدريب نموذج تقييم العقارات"""
    print("🏠 تدريب نموذج تقييم العقارات...")

    # تحميل البيانات
    gdf = gpd.read_file(
        PATHS["data_processed"] + "baghdad_districts.geojson"
    )

    # المميزات (Features)
    features = [
        "population",
        "infrastructure_age",
        "flood_risk",
        "infrastructure_score",
        "crime_index"
    ]
    target = "avg_property_price"

    X = gdf[features].values
    y = gdf[target].values

    # تقسيم البيانات
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # تطبيع البيانات
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # تدريب النموذج
    model = GradientBoostingRegressor(
        n_estimators=200,
        learning_rate=0.1,
        max_depth=4,
        random_state=42
    )
    model.fit(X_train_scaled, y_train)

    # تقييم النموذج
    y_pred = model.predict(X_test_scaled)
    mae    = mean_absolute_error(y_test, y_pred)
    r2     = r2_score(y_test, y_pred)

    print(f"  📊 MAE: {mae:,.0f} دينار")
    print(f"  📊 R²:  {r2:.3f}")

    # حفظ النموذج
    os.makedirs(PATHS["models"], exist_ok=True)
    with open(PATHS["models"] + "property_model.pkl", "wb") as f:
        pickle.dump({"model": model, "scaler": scaler,
                     "features": features}, f)

    print("  ✅ النموذج محفوظ")
    return model, scaler, features


def predict_all_complexes():
    """تطبيق النموذج على جميع المجمعات"""
    print("🔮 تطبيق التقييم على المجمعات...")

    # تحميل النموذج
    with open(PATHS["models"] + "property_model.pkl", "rb") as f:
        saved = pickle.load(f)
    model   = saved["model"]
    scaler  = saved["scaler"]

    # تحميل بيانات المجمعات
    complexes_gdf = gpd.read_file(
        PATHS["data_processed"] + "baghdad_complexes.geojson"
    )
    districts_gdf = gpd.read_file(
        PATHS["data_processed"] + "baghdad_districts.geojson"
    )

    # دمج بيانات الحي مع المجمع
    merged = complexes_gdf.merge(
        districts_gdf[[
            "name", "population", "infrastructure_age",
            "flood_risk", "infrastructure_score", "crime_index"
        ]],
        left_on="district",
        right_on="name",
        suffixes=("", "_district")
    )

    features = [
        "population", "infrastructure_age",
        "flood_risk", "infrastructure_score", "crime_index"
    ]

    X      = merged[features].fillna(0).values
    X_s    = scaler.transform(X)
    prices = model.predict(X_s)

    complexes_gdf["predicted_unit_price"] = prices.astype(int)
    complexes_gdf["total_value_estimate"] = (
        complexes_gdf["predicted_unit_price"] *
        complexes_gdf["total_units"]
    )

    # تصنيف الاستثمار
    def investment_grade(price):
        if price > 4_000_000:
            return "A+ ممتاز"
        elif price > 3_000_000:
            return "A جيد جداً"
        elif price > 2_000_000:
            return "B جيد"
        else:
            return "C متوسط"

    complexes_gdf["investment_grade"] = \
        complexes_gdf["predicted_unit_price"].apply(investment_grade)

    # حفظ النتائج
    output_path = PATHS["data_processed"] + "complexes_with_ai.geojson"
    complexes_gdf.to_file(output_path, driver="GeoJSON")
    print(f"  ✅ تقييم {len(complexes_gdf)} مجمع اكتمل")

    return complexes_gdf


if __name__ == "__main__":
    print("═" * 55)
    print("  مدينة+ — الذكاء العقاري")
    print("═" * 55)
    train_property_model()
    predict_all_complexes()
    print("  ✅ الوحدة العقارية جاهزة")