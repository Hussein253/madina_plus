# config.py
# ═══════════════════════════════════════════
# إعدادات مشروع مدينة+ — ETC Edition
# ═══════════════════════════════════════════

# مركز بغداد
BAGHDAD_CENTER = {
    "lat": 33.3152,
    "lon": 44.3661
}

# مركز العامرية (موقع ETC)
AMIRIYA_CENTER = {
    "lat": 33.3150,
    "lon": 44.2880
}

# مجلدات المشروع
PATHS = {
    "data_raw":       "data/raw/",
    "data_processed": "data/processed/",
    "geojson":        "data/geojson/",
    "models":         "models/",
    "outputs":        "outputs/"
}

# إعدادات الخريطة
MAP_CONFIG = {
    "zoom_start":    12,
    "zoom_amiriya":  15,
    "tiles_dark":    "CartoDB dark_matter",
    "tiles_normal":  "OpenStreetMap",
    "tiles_satellite": (
        "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        "Google Satellite"
    )
}

# ألوان النظام
COLORS = {
    "critical":  "#FF2200",
    "high":      "#FF8800",
    "medium":    "#FFD700",
    "low":       "#00FF88",
    "info":      "#00BFFF",
    "neutral":   "#888888",
    "etc_brand": "#FF6600"
}

# أنواع المناطق
ZONE_TYPES = {
    "RESIDENTIAL": "سكني",
    "COMMERCIAL":  "تجاري",
    "INDUSTRIAL":  "صناعي",
    "GOVERNMENT":  "حكومي",
    "MEDICAL":     "طبي",
    "EDUCATIONAL": "تعليمي"
}

print("✅ config.py — جاهز")