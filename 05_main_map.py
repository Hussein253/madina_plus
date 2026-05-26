# 05_main_map.py
# ═══════════════════════════════════════════
# الخريطة الرئيسية المتكاملة لـ مدينة+ v1.1
# ═══════════════════════════════════════════

import json
import os
import folium
import pandas as pd
import geopandas as gpd
from folium.plugins import (
    HeatMap, MiniMap, Fullscreen,
    LocateControl, MarkerCluster, MeasureControl
)
from datetime import datetime
from config import PATHS, BAGHDAD_CENTER, MAP_CONFIG


def build_madina_plus_map():
    print("🏛️  بناء خريطة مدينة+ المتكاملة v1.1...")

    # ══════════════════════════════════════
    # تحميل البيانات
    # ══════════════════════════════════════
    districts  = gpd.read_file(
        PATHS["data_processed"] + "baghdad_districts.geojson"
    )
    complexes  = gpd.read_file(
        PATHS["data_processed"] + "complexes_with_ai.geojson"
    )
    flood_grid = gpd.read_file(
        PATHS["data_processed"] + "flood_risk_grid.geojson"
    )

    # تحميل تنبؤ الطاقة إذا وُجد
    energy_forecast = None
    energy_path = PATHS["data_processed"] + "energy_forecast.json"
    if os.path.exists(energy_path):
        with open(energy_path, "r", encoding="utf-8") as f:
            energy_forecast = json.load(f)
        print("  ⚡ تنبؤ الطاقة محمّل")
    else:
        print("  ⚠️  energy_forecast.json غير موجود — شغّل 04 أولاً")

    # ══════════════════════════════════════
    # إحصائيات الـ Dashboard
    # ══════════════════════════════════════
    total_complexes    = len(complexes)
    connected          = int(complexes["complex_plus_connected"].sum())
    critical_flood     = len(flood_grid[flood_grid["flood_risk"] > 0.75])
    total_revenue      = int(complexes["monthly_revenue"].sum())

    avg_price = 0
    if "predicted_unit_price" in complexes.columns:
        avg_price = int(complexes["predicted_unit_price"].mean())

    # مؤشر صحة المدينة
    avg_risk    = float(complexes["risk_score"].mean())
    city_health = int((1 - avg_risk) * 100)
    health_color = (
        "#FF2200" if city_health < 40 else
        "#FF8800" if city_health < 60 else
        "#FFD700" if city_health < 75 else
        "#00FF88"
    )
    health_label = (
        "حرجة"       if city_health < 40 else
        "تحتاج تدخل" if city_health < 60 else
        "متوسطة"     if city_health < 75 else
        "جيدة"
    )

    # بيانات الطاقة للـ Dashboard
    energy_section_html = ""
    if energy_forecast:
        next_day   = energy_forecast["predictions"][0]
        peak_day   = energy_forecast["predictions"][4]
        e_color    = {
            "CRITICAL": "#FF2200", "HIGH": "#FF8800",
            "MEDIUM": "#FFD700",   "LOW":  "#00FF88"
        }.get(next_day["risk_level"], "#888")

        energy_section_html = f"""
        <div style="background:#050a05;border:1px solid #006600;
                    border-radius:8px;padding:10px;margin-bottom:10px">
          <div style="font-size:9px;color:#00AA44;letter-spacing:2px;
                      margin-bottom:6px">⚡ تنبؤ الطاقة — الأيام القادمة</div>
          <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px">
            <div style="text-align:center">
              <div style="font-size:16px;font-weight:bold;color:{e_color}">
                {next_day['predicted_mw']} MW
              </div>
              <div style="font-size:8px;color:#555">غداً</div>
            </div>
            <div style="text-align:center">
              <div style="font-size:11px;font-weight:bold;
                          color:{e_color};padding-top:4px">
                {next_day['risk_level']}
              </div>
              <div style="font-size:8px;color:#555">مستوى الخطر</div>
            </div>
          </div>
          <div style="margin-top:6px;font-size:9px;color:#444">
            ذروة الأسبوع: {peak_day['date']} —
            {peak_day['predicted_mw']} MW
          </div>
        </div>
        """

    # ══════════════════════════════════════
    # بناء الخريطة
    # ══════════════════════════════════════
    m = folium.Map(
        location=[BAGHDAD_CENTER["lat"], BAGHDAD_CENTER["lon"]],
        zoom_start=MAP_CONFIG["zoom_start"],
        tiles=None
    )

    # طبقات الخريطة الأساسية
    folium.TileLayer(
        "CartoDB dark_matter", name="🌑 مظلمة"
    ).add_to(m)
    folium.TileLayer(
        "OpenStreetMap", name="🗺️ عادية", show=False
    ).add_to(m)
    folium.TileLayer(
        tiles="https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
        attr="Google", name="🛰️ قمر صناعي", show=False
    ).add_to(m)

    # ══════════════════════════════════════
    # الطبقة 1 — HeatMap الفيضانات
    # ══════════════════════════════════════
    flood_group = folium.FeatureGroup(
        name="🌊 خطر الفيضانات", show=True
    )
    flood_points = [
        [r.lat, r.lon, r.flood_risk]
        for r in flood_grid[flood_grid["flood_risk"] > 0.3].itertuples()
    ]
    HeatMap(
        flood_points,
        min_opacity=0.3,
        radius=18, blur=14,
        gradient={
            0.3: "#0000FF", 0.5: "#00FFFF",
            0.7: "#FFFF00", 0.85: "#FF4400", 1.0: "#FF0000"
        }
    ).add_to(flood_group)
    flood_group.add_to(m)

    # ══════════════════════════════════════
    # الطبقة 2 — أحياء بغداد
    # ══════════════════════════════════════
    district_group = folium.FeatureGroup(
        name="🏙️ أحياء بغداد", show=True
    )
    risk_colors = {
        "CRITICAL": "#FF2200", "HIGH":   "#FF8800",
        "MEDIUM":   "#FFD700", "LOW":    "#00FF88"
    }

    for _, d in districts.iterrows():
        infra = d["infrastructure_score"]
        risk  = (
            "CRITICAL" if infra < 0.3 else
            "HIGH"     if infra < 0.5 else
            "MEDIUM"   if infra < 0.7 else "LOW"
        )
        color = risk_colors[risk]

        popup_html = f"""
        <div style='font-family:monospace;background:#0d0d0d;
                    color:#e0e0e0;padding:12px;border-radius:8px;
                    min-width:230px;border:1px solid {color}'>
          <b style='color:{color};font-size:14px'>{d['name']}</b>
          <hr style='border-color:#333;margin:6px 0'>
          👥 السكان: <b>{d['population']:,}</b><br>
          🏗️ عمر البنية: <b>{d['infrastructure_age']} سنة</b><br>
          🌊 خطر الفيضان: <b>{int(d['flood_risk']*100)}%</b><br>
          💰 متوسط العقار: <b>{d['avg_property_price']:,} د.ع</b><br>
          🔧 نقاط البنية: <b>{int(d['infrastructure_score']*100)}%</b><br>
          📊 الحالة: <b style='color:{color}'>{risk}</b>
        </div>
        """
        folium.CircleMarker(
            location=[d["lat"], d["lon"]],
            radius=14, color=color,
            fill=True, fill_color=color, fill_opacity=0.25,
            popup=folium.Popup(popup_html, max_width=260),
            tooltip=f"🏙️ {d['name']} — انقر للتفاصيل"
        ).add_to(district_group)

    district_group.add_to(m)

    # ══════════════════════════════════════
    # الطبقة 3 — المجمعات مع Cluster
    # ══════════════════════════════════════
    cluster = MarkerCluster(
        name="🏗️ المجمعات السكنية",
        overlay=True, control=True,
        options={
            "maxClusterRadius":   50,
            "spiderfyOnMaxZoom":  True,
            "showCoverageOnHover": True
        }
    )

    for _, c in complexes.iterrows():
        risk_c = c.get("risk_level", "LOW")
        color  = risk_colors.get(risk_c, "#888")
        price  = int(c.get("predicted_unit_price", 0) or 0)
        grade  = c.get("investment_grade", "—") or "—"
        connected_icon = "✅" if c["complex_plus_connected"] else "❌"

        icon_color = {
            "CRITICAL": "red",   "HIGH":   "orange",
            "MEDIUM":   "beige", "LOW":    "green"
        }.get(risk_c, "blue")

        popup_html = f"""
        <div style='font-family:monospace;background:#0d0d0d;
                    color:#e0e0e0;padding:12px;border-radius:8px;
                    min-width:240px;border:1px solid {color}'>
          <b style='color:{color}'>{c['name']}</b>
          <hr style='border-color:#333;margin:6px 0'>
          🏠 الوحدات: <b>{c['total_units']}</b><br>
          👤 الإشغال: <b>{int(c['occupancy_rate']*100)}%</b><br>
          💰 سعر الوحدة: <b>{price:,} د.ع</b><br>
          📊 تقييم: <b style='color:{color}'>{grade}</b><br>
          ⚠️ درجة الخطر: <b>{int(c['risk_score']*100)}%</b><br>
          🔗 Complex+: <b>{connected_icon}</b><br>
          📅 آخر فحص: <b>{c['last_inspection']}</b>
        </div>
        """
        folium.Marker(
            location=[c["lat"], c["lon"]],
            popup=folium.Popup(popup_html, max_width=270),
            tooltip=f"🏗️ {c['name']}",
            icon=folium.Icon(
                color=icon_color, icon="building", prefix="fa"
            )
        ).add_to(cluster)

    cluster.add_to(m)

    # ══════════════════════════════════════
    # الإضافات الاحترافية
    # ══════════════════════════════════════
    Fullscreen(
        position="topleft",
        title="ملء الشاشة",
        title_cancel="تصغير"
    ).add_to(m)

    LocateControl(
        position="topleft",
        strings={"title": "موقعي الحالي"},
        flyTo=True
    ).add_to(m)

    MeasureControl(
        position="topleft",
        primary_length_unit="kilometers",
        secondary_length_unit="meters",
        primary_area_unit="sqkilometers"
    ).add_to(m)

    MiniMap(
        position="bottomright",
        width=160, height=160,
        toggle_display=True,
        tile_layer="CartoDB dark_matter"
    ).add_to(m)

    folium.LayerControl(
        position="topright", collapsed=False
    ).add_to(m)

    # ══════════════════════════════════════
    # لوحة التحكم الاحترافية الكاملة
    # ══════════════════════════════════════
    modules_html = "".join(f"""
      <div style="background:#0a0a0a;border-radius:6px;
                  padding:7px 6px;border:1px solid #1a1a1a;
                  display:flex;align-items:center;gap:6px">
        <span style="font-size:13px">{icon}</span>
        <div>
          <div style="font-size:10px;color:#ccc">{name}</div>
          <div style="font-size:8px;color:#00FF88;
                      letter-spacing:1px">● ACTIVE</div>
        </div>
      </div>
    """ for icon, name in [
        ("🏗️", "Complex+ Link"),
        ("🌊", "Flood AI"),
        ("💰", "Property AI"),
        ("⚡", "Energy Pred"),
        ("🛰️", "Satellite"),
        ("📊", "Analytics")
    ])

    dashboard_html = f"""
<div id="madina-dashboard" style="
    position:fixed; top:15px; right:15px; width:310px;
    z-index:9999; font-family:'Consolas','Courier New',monospace;
    background:rgba(5,5,10,0.97); color:#d0d0d0;
    border-radius:12px; overflow:hidden;
    box-shadow:0 20px 60px rgba(0,0,0,0.95),
               0 0 0 1px rgba(255,100,0,0.2);
    border:1px solid rgba(255,100,0,0.4)">

  <!-- ترويسة ETC -->
  <div style="background:linear-gradient(135deg,#1a0800,#0a0a0f);
              padding:13px 15px;border-bottom:1px solid #1a1a1a">
    <div style="font-size:9px;color:#FF4400;letter-spacing:3px;
                margin-bottom:3px">
      ETC — ENGINEERED TRANSFORMATION CO.
    </div>
    <div style="font-size:17px;color:#fff;font-weight:bold;
                letter-spacing:1px">🏛️ مدينة+</div>
    <div style="font-size:9px;color:#444;margin-top:1px">
      Baghdad Urban Intelligence Platform v1.1
    </div>
    <div style="margin-top:8px;display:inline-block;
                background:rgba(0,255,136,0.1);
                border:1px solid #00FF88;border-radius:4px;
                padding:3px 8px;font-size:9px;color:#00FF88;
                letter-spacing:2px">
      ● LIVE ANALYSIS ACTIVE
    </div>
  </div>

  <div style="padding:13px">

    <!-- KPIs الرئيسية -->
    <div style="display:grid;grid-template-columns:1fr 1fr;
                gap:7px;margin-bottom:12px">
      <div style="background:#0a0a0a;border-radius:8px;
                  padding:9px;border:1px solid #1a1a1a;
                  text-align:center">
        <div style="font-size:22px;font-weight:bold;
                    color:#FF6600">{total_complexes}</div>
        <div style="font-size:8px;color:#555;
                    letter-spacing:1px;margin-top:2px">
          مجمع سكني
        </div>
      </div>
      <div style="background:#0a0a0a;border-radius:8px;
                  padding:9px;border:1px solid #1a1a1a;
                  text-align:center">
        <div style="font-size:22px;font-weight:bold;
                    color:#00FF88">{connected}</div>
        <div style="font-size:8px;color:#555;
                    letter-spacing:1px;margin-top:2px">
          Complex+ مرتبط
        </div>
      </div>
      <div style="background:#0a0a0a;border-radius:8px;
                  padding:9px;border:1px solid #1a1a1a;
                  text-align:center">
        <div style="font-size:22px;font-weight:bold;
                    color:#FF2200">{critical_flood}</div>
        <div style="font-size:8px;color:#555;
                    letter-spacing:1px;margin-top:2px">
          منطقة خطر فيضان
        </div>
      </div>
      <div style="background:#0a0a0a;border-radius:8px;
                  padding:9px;border:1px solid #1a1a1a;
                  text-align:center">
        <div style="font-size:20px;font-weight:bold;
                    color:#FFD700">{len(districts)}</div>
        <div style="font-size:8px;color:#555;
                    letter-spacing:1px;margin-top:2px">
          حي مراقب
        </div>
      </div>
    </div>

    <!-- مؤشر صحة المدينة -->
    <div style="background:#0a0a0a;border:1px solid {health_color};
                border-radius:8px;padding:11px;margin-bottom:11px">
      <div style="font-size:9px;color:#555;letter-spacing:2px;
                  margin-bottom:7px">🏙️ صحة المدينة الإجمالية</div>
      <div style="display:flex;align-items:center;gap:10px">
        <div style="font-size:28px;font-weight:bold;
                    color:{health_color}">{city_health}%</div>
        <div>
          <div style="font-size:11px;color:{health_color};
                      font-weight:bold">{health_label}</div>
          <div style="font-size:8px;color:#444;margin-top:2px">
            بناءً على {total_complexes} مجمع
          </div>
        </div>
      </div>
      <div style="margin-top:8px;height:5px;
                  background:#1a1a1a;border-radius:3px">
        <div style="width:{city_health}%;height:100%;
                    border-radius:3px;
                    background:linear-gradient(90deg,
                      #FF2200,{health_color})">
        </div>
      </div>
    </div>

    <!-- الإيراد الشهري -->
    <div style="background:linear-gradient(135deg,#050a05,#0a0a0a);
                border:1px solid #006600;border-radius:8px;
                padding:10px;margin-bottom:11px">
      <div style="font-size:9px;color:#00AA44;letter-spacing:2px;
                  margin-bottom:5px">💰 الإيراد الشهري للمجمعات</div>
      <div style="font-size:17px;color:#00FF88;font-weight:bold">
        {total_revenue:,}
      </div>
      <div style="font-size:8px;color:#444;margin-top:2px">
        دينار عراقي — {total_complexes} مجمع
      </div>
    </div>

    <!-- تنبؤ الطاقة -->
    {energy_section_html if energy_section_html else '''
    <div style="background:#0a0505;border:1px dashed #333;
                border-radius:8px;padding:10px;margin-bottom:11px;
                text-align:center">
      <div style="font-size:9px;color:#444">
        ⚡ شغّل 04_energy_predictor.py<br>لتفعيل تنبؤ الطاقة
      </div>
    </div>
    '''}

    <!-- الوحدات النشطة -->
    <div style="font-size:9px;color:#333;letter-spacing:2px;
                margin-bottom:7px">ACTIVE MODULES</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;
                gap:6px;margin-bottom:12px">
      {modules_html}
    </div>

    <!-- سعر العقار المتوقع -->
    <div style="background:#0a0a0a;border:1px solid #1a1a1a;
                border-radius:8px;padding:9px;margin-bottom:11px">
      <div style="font-size:9px;color:#555;letter-spacing:2px;
                  margin-bottom:4px">🏠 متوسط سعر الوحدة (AI)</div>
      <div style="font-size:15px;color:#FFD700;font-weight:bold">
        {avg_price:,} د.ع
      </div>
    </div>

    <!-- التوقيت -->
    <div style="text-align:center;font-size:8px;color:#2a2a2a;
                border-top:1px solid #111;padding-top:9px;
                letter-spacing:1px">
      {datetime.now().strftime("%Y-%m-%d %H:%M:%S")} | ETC v1.1
    </div>
  </div>
</div>
"""

    m.get_root().html.add_child(folium.Element(dashboard_html))

    # ══════════════════════════════════════
    # الحفظ
    # ══════════════════════════════════════
    os.makedirs(PATHS["outputs"], exist_ok=True)
    output_path = PATHS["outputs"] + "madina_plus.html"
    m.save(output_path)

    print(f"""
  ✅ الخريطة محفوظة: {output_path}
  📊 الإحصائيات:
     • المجمعات: {total_complexes}
     • المرتبطة بـ Complex+: {connected}
     • مناطق الفيضان الحرجة: {critical_flood}
     • صحة المدينة: {city_health}% ({health_label})
     • الإيراد الشهري: {total_revenue:,} د.ع
    """)
    return output_path


if __name__ == "__main__":
    print("═" * 55)
    print("  مدينة+ — الخريطة الرئيسية v1.1")
    print("═" * 55)
    build_madina_plus_map()