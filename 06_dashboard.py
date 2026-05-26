# 06_dashboard.py
# ═══════════════════════════════════════════
# المُشغّل الرئيسي — يبني كل شيء بأمر واحد
# ═══════════════════════════════════════════

import os
from datetime import datetime

def run_full_pipeline():
    print()
    print("╔══════════════════════════════════════════════════════╗")
    print("║         مدينة+ — Baghdad Urban Intelligence          ║")
    print("║         ETC — Engineered Transformation Co.         ║")
    print("╚══════════════════════════════════════════════════════╝")
    print()

    steps = [
         ("01_data_collector", "جمع البيانات"),
    ("02_property_ai",    "تدريب نموذج العقارات"),
    ("03_flood_risk",     "حساب خطر الفيضانات"),
    ("04_energy_predictor", "تنبؤ الطاقة"),  # ← أضف هذا
    ("05_main_map",       "بناء الخريطة المتكاملة"),
    ]

    for module_name, description in steps:
        print(f"▶ {description}...")
        module = __import__(module_name)

        if module_name == "01_data_collector":
            districts = module.generate_baghdad_districts()
            module.generate_complexes_data(districts)
            module.generate_energy_timeseries()

        elif module_name == "02_property_ai":
            module.train_property_model()
            module.predict_all_complexes()

        elif module_name == "03_flood_risk":
            module.calculate_flood_risk_grid()

        elif module_name == "05_main_map":
            output = module.build_madina_plus_map()
        elif module_name == "04_energy_predictor":
            output = module.predict_energy_demand()   
        print(f"  ✅ {description} — اكتمل")
        print()

    print("╔══════════════════════════════════════════════════════╗")
    print("║  ✅ مدينة+ جاهز بالكامل!                            ║")
    print("║                                                      ║")
    print("║  افتح هذا الملف في المتصفح:                          ║")
    print("║  outputs/madina_plus.html                           ║")
    print("╚══════════════════════════════════════════════════════╝")


if __name__ == "__main__":
    run_full_pipeline()