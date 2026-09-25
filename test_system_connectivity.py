"""
DataViz V6 - Master Inter-Module Wiring & Connectivity Verification
Runs full suite of unit and integration tests against all backend Blueprint routes
and verifies contract compatibility with frontend ES6 modules.
"""

import logging
import os
import sys
from typing import Any

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

from app import app

logging.basicConfig(level=logging.WARNING)


def j(res: Any) -> dict[str, Any]:
    """Type-safe JSON dictionary extractor for Flask TestResponse."""
    data = res.get_json(silent=True)
    return data if isinstance(data, dict) else {}


def run_tests():
    print("=" * 70)
    print("🚀 MASTER ENTEGRASYON VE BAĞLANTI TESTLERİ BAŞLIYOR")
    print("=" * 70)

    client = app.test_client()
    passed = 0
    total = 0

    def assert_test(name: str, condition: bool, extra_info: str = ""):
        nonlocal passed, total
        total += 1
        if condition:
            passed += 1
            print(f"  ✅ [TEST {total:02d}] {name} - BAŞARILI {extra_info}")
        else:
            print(f"  ❌ [TEST {total:02d}] {name} - BAŞARISIZ! {extra_info}")
            sys.exit(1)

    # 1. Health Endpoint
    res = client.get("/health")
    d = j(res)
    assert_test(
        "Sistem Sağlık Kontrolü (GET /health)",
        res.status_code == 200 and d.get("status") == "ok",
    )

    # 2. Load Sample Dataset
    res = client.post("/load_sample")
    d = j(res)
    assert_test(
        "Örnek Veri Seti Yükleme (POST /load_sample)",
        res.status_code == 200 and d.get("success") is True,
        f"Satır: {d.get('total_rows')}, Sütun: {d.get('total_cols')}",
    )

    # 3. Check Health
    res = client.get("/check_health")
    d = j(res)
    assert_test(
        "Veri Kalite Kontrolü (GET /check_health)",
        res.status_code == 200 and "has_issues" in d,
    )

    # 4. Column Slicer GET (Query Parameter)
    res = client.get("/get_column_unique_values?column=Sat%C4%B1%C5%9F_Tutar%C4%B1")
    d = j(res)
    assert_test(
        "Dinamik Dilimleyici GET Sorgusu (GET /get_column_unique_values?column=...)",
        res.status_code == 200 and d.get("type") == "num" and "min" in d and "max" in d,
    )

    # 5. Column Slicer POST (JSON Body)
    res = client.post("/get_column_unique_values", json={"column": "Kategori"})
    d = j(res)
    assert_test(
        "Kategorik Dilimleyici POST Sorgusu (POST /get_column_unique_values)",
        res.status_code == 200
        and d.get("type") == "cat"
        and len(d.get("categories", [])) > 0,
    )

    # 6. Add Calculated Column (Frontend format: op, new_col_name, scalar)
    res = client.post(
        "/add_calculated_column",
        json={
            "col1": "Satış_Tutarı",
            "op": "*",
            "scalar": 1.20,
            "new_col_name": "KDVli_Satis",
        },
    )
    d = j(res)
    assert_test(
        "Hesaplanan Sütun - Frontend Formatı (POST /add_calculated_column)",
        res.status_code == 200 and d.get("new_column") == "KDVli_Satis",
    )

    # 7. Create Calculated Column (Backend format: operator, new_column_name, col2)
    res = client.post(
        "/create_calculated_column",
        json={
            "col1": "Satış_Tutarı",
            "operator": "-",
            "col2": "Maliyet",
            "new_column_name": "Brut_Kar",
        },
    )
    d = j(res)
    assert_test(
        "Hesaplanan Sütun - Backend Formatı (POST /create_calculated_column)",
        res.status_code == 200 and d.get("new_column") == "Brut_Kar",
    )

    # 8. Chart Data - Bar Chart
    res = client.post(
        "/get_chart_data",
        json={
            "chart_type": "bar",
            "x": "Kategori",
            "y": ["Satış_Tutarı"],
            "agg_func": "sum",
        },
    )
    d = j(res)
    assert_test(
        "Grafik Verisi - Çubuk Grafik (POST /get_chart_data)",
        res.status_code == 200 and d.get("success") is True and "agg" in d,
    )

    # 9. Chart Data - Scatter Chart
    res = client.post(
        "/get_chart_data",
        json={"chart_type": "scatter", "x": "Satış_Tutarı", "y": ["Kar"]},
    )
    d = j(res)
    assert_test(
        "Grafik Verisi - Dağılım Grafiği (POST /get_chart_data)",
        res.status_code == 200 and d.get("success") is True and "raw" in d,
    )

    # 10. Regression Curve & Correlation
    res = client.post(
        "/get_regression_curve",
        json={
            "x_col": "Satış_Tutarı",
            "y_col": "Kar",
            "model_type": "linear",
            "corr_method": "pearson",
        },
    )
    d = j(res)
    assert_test(
        "Canlı Regresyon ve Korelasyon Eğrisi (POST /get_regression_curve)",
        res.status_code == 200
        and d.get("success") is True
        and "regression" in d
        and "correlation" in d,
    )

    # 11. KPI Summary
    res = client.post("/get_kpi_summary", json={})
    d = j(res)
    assert_test(
        "KPI Özeti (POST /get_kpi_summary)",
        res.status_code == 200 and "total_rows" in d,
    )

    # 12. Statistical Metrics
    res = client.post("/get_stats", json={"column": "Satış_Tutarı"})
    d = j(res)
    assert_test(
        "İstatistiksel Metrikler (POST /get_stats)",
        res.status_code == 200 and "stats" in d,
    )

    # 13. AI Insight - /get_ai_insight (Frontend endpoint)
    res = client.post(
        "/get_ai_insight",
        json={
            "chart_type": "bar",
            "x": "Kategori",
            "y": ["Satış_Tutarı"],
            "stats": {
                "Satış_Tutarı": {
                    "mean": 25000,
                    "median": 24000,
                    "min": 1000,
                    "max": 50000,
                    "std": 12000,
                }
            },
        },
    )
    d = j(res)
    assert_test(
        "AI Yorumlayıcı Frontend Uç Noktası (POST /get_ai_insight)",
        res.status_code == 200 and "insight" in d,
    )

    # 14. AI Insight - /generate_insight (Backend endpoint)
    res = client.post(
        "/generate_insight",
        json={
            "chart_type": "scatter",
            "x_col": "Satış_Tutarı",
            "y_cols": ["Kar"],
            "stats": {
                "Kar": {
                    "mean": 5000,
                    "median": 4500,
                    "min": 200,
                    "max": 15000,
                    "std": 3000,
                }
            },
        },
    )
    d = j(res)
    assert_test(
        "AI Yorumlayıcı Backend Uç Noktası (POST /generate_insight)",
        res.status_code == 200 and "insight" in d,
    )

    # 15. Pivot Studio Matrix
    res = client.post(
        "/get_pivot_data",
        json={
            "rows": ["Kategori"],
            "cols": ["Bölge"],
            "values": ["Satış_Tutarı"],
            "agg_func": "sum",
        },
    )
    d = j(res)
    assert_test(
        "Pivot Tablosu Matrisi (POST /get_pivot_data)",
        res.status_code == 200 and "rows" in d and "column_headers" in d,
    )

    # 16. Data Cleaning & Repair
    res = client.post(
        "/repair_column_anomalies",
        json={"column": "__all__", "repair_mode": "smart_heal"},
    )
    d = j(res)
    assert_test(
        "Akıllı Sütun Onarımı (POST /repair_column_anomalies)",
        res.status_code == 200 and d.get("success") is True,
    )

    res = client.post("/clean_data", json={"action": "drop"})
    d = j(res)
    assert_test(
        "Eksik Veri Temizleme (POST /clean_data)",
        res.status_code == 200 and d.get("success") is True,
    )

    # 17. Export Data (CSV)
    res = client.post("/export_data", json={"format": "csv"})
    assert_test(
        "Veri Dışa Aktarma CSV (POST /export_data)",
        res.status_code == 200 and "text/csv" in (res.content_type or ""),
    )

    # 18. Export Pivot Excel
    res = client.post(
        "/export_pivot_excel",
        json={
            "rows": ["Kategori"],
            "cols": ["Bölge"],
            "values": ["Satış_Tutarı"],
            "agg_func": "sum",
        },
    )
    assert_test(
        "Pivot Excel Dışa Aktarma (POST /export_pivot_excel)", res.status_code == 200
    )

    print("=" * 70)
    print(f"🎉 SONUÇ: {passed}/{total} TÜM MASTER ENTEGRASYON TESTLERİ KUSURSUZ GEÇTİ!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
