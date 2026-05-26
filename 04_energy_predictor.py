# 04_energy_predictor.py
# تنبؤ استهلاك الطاقة بـ Prophet
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json, os
from config import PATHS

def predict_energy_demand():
    print("⚡ تدريب نموذج تنبؤ الطاقة...")

    # تحميل البيانات التاريخية
    df = pd.read_csv(
        PATHS["data_processed"] + "energy_timeseries.csv"
    )
    df["datetime"] = pd.to_datetime(df["datetime"])

    # تجميع يومي
    daily = df.groupby("date").agg(
        total_consumption=("consumption_mw", "sum"),
        avg_voltage=("voltage", "mean"),
        outage_count=("outage", "sum")
    ).reset_index()

    daily["date"] = pd.to_datetime(daily["date"])
    daily = daily.sort_values("date")

    # حساب الاتجاه بدون Prophet (أبسط وأسرع)
    daily["day_num"] = range(len(daily))
    daily["rolling_avg"] = daily["total_consumption"].rolling(
        7, min_periods=1
    ).mean()

    # توليد تنبؤات 7 أيام قادمة
    last_date  = daily["date"].max()
    last_avg   = daily["rolling_avg"].iloc[-1]
    predictions = []

    for i in range(1, 8):
        future_date = last_date + timedelta(days=i)
        is_weekend  = future_date.weekday() >= 4
        is_summer   = future_date.month in [6, 7, 8, 9]

        multiplier = 1.0
        if is_summer:   multiplier *= 1.35
        if is_weekend:  multiplier *= 0.88

        pred_value = last_avg * multiplier
        risk_level = (
            "CRITICAL" if pred_value > 700 else
            "HIGH"     if pred_value > 600 else
            "MEDIUM"   if pred_value > 500 else "LOW"
        )
        predictions.append({
            "date":            future_date.strftime("%Y-%m-%d"),
            "day":             future_date.strftime("%A"),
            "predicted_mw":    round(pred_value, 1),
            "risk_level":      risk_level,
            "outage_prob":     round(
                min(0.05 + (pred_value - 400) / 2000, 0.95), 2
            ),
            "is_weekend":      is_weekend,
            "is_summer":       is_summer
        })

    # حفظ النتائج
    output = {
        "generated_at":    datetime.now().isoformat(),
        "model":           "Rolling Average + Seasonal",
        "accuracy_note":   "Prophet upgrade in v2.0",
        "historical_days": len(daily),
        "forecast_days":   7,
        "predictions":     predictions,
        "summary": {
            "avg_consumption": round(
                float(daily["total_consumption"].mean()), 1
            ),
            "peak_day":    str(
                daily.loc[
                    daily["total_consumption"].idxmax(), "date"
                ].date()
            ),
            "total_outages": int(daily["outage_count"].sum())
        }
    }

    os.makedirs(PATHS["data_processed"], exist_ok=True)
    with open(
        PATHS["data_processed"] + "energy_forecast.json",
        "w", encoding="utf-8"
    ) as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print("  ✅ تنبؤ 7 أيام قادمة:")
    for p in predictions[:3]:
        print(f"     {p['date']}: {p['predicted_mw']} MW"
              f" — {p['risk_level']}")
    print("     ...")
    print(f"  💾 محفوظ: energy_forecast.json")
    return output

if __name__ == "__main__":
    predict_energy_demand()