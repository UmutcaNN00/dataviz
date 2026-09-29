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

    # 7. Add Calculated Column (Two-Column Operation: col1 - col2)
    res = client.post(
        "/add_calculated_column",
        json={
            "col1": "Satış_Tutarı",
            "operator": "-",
            "col2": "Maliyet",
            "new_column_name": "Brut_Kar",
        },
    )
    d = j(res)
    assert_test(
        "Hesaplanan Sütun - İki Sütunlu İşlem (POST /add_calculated_column)",
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

    # 13. Correlation Matrix & Regression Studio Data
    res_corr = client.post("/get_correlation_matrix", json={"method": "pearson"})
    d_corr = j(res_corr)
    res_reg = client.post(
        "/get_regression_studio_data",
        json={
            "x_col": "Satış_Tutarı",
            "y_col": "Kar",
            "model_type": "linear",
            "corr_method": "pearson",
        },
    )
    d_reg = j(res_reg)
    assert_test(
        "Korelasyon Matrisi & Regresyon Stüdyosu (POST /get_correlation_matrix & /get_regression_studio_data)",
        res_corr.status_code == 200
        and "matrix" in d_corr
        and res_reg.status_code == 200
        and d_reg.get("success") is True
        and "key_findings" in (d_reg.get("insight") or {}),
    )

    # 14. Academic Statistical Interpreter - /generate_insight
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
        "Akademik İstatistiksel Yorumlayıcı (POST /generate_insight)",
        res.status_code == 200 and "insight" in d and "key_findings" in d,
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

    # 19. Overlapping Pivot Rows/Cols Safety
    res_piv_overlap = client.post(
        "/get_pivot_data",
        json={
            "rows": ["Kategori", "Kategori"],
            "cols": ["Kategori", "Bölge"],
            "values": ["Satış_Tutarı", "Satış_Tutarı"],
            "agg_func": "sum",
        },
    )
    res_exp_overlap = client.post(
        "/export_pivot_excel",
        json={
            "rows": ["Kategori"],
            "cols": ["Kategori"],
            "values": ["Satış_Tutarı"],
            "agg_func": "sum",
        },
    )
    assert_test(
        "Çakışan Satır/Sütun Pivot Güvenliği (/get_pivot_data & /export_pivot_excel)",
        res_piv_overlap.status_code == 200 and res_exp_overlap.status_code == 200,
    )

    # 20. Single-Column Targeted Cleaning & Trust Studio Partial vs Full State
    import io

    csv_bytes = (
        "Isim,Puan,Maas\nAli,80,10000\nVeli,,12000\nAyse,90,\nFatma,85,11000\n"
    ).encode("utf-8")
    res_up = client.post(
        "/upload",
        data={"file": (io.BytesIO(csv_bytes), "test_partial.csv")},
        content_type="multipart/form-data",
    )
    res_clean_col = client.post(
        "/clean_data",
        json={"action": "fill_mean", "column": "Puan"},
    )
    d_clean_col = j(res_clean_col)
    res_trust_partial = client.get("/get_trust_report")
    d_trust_partial = j(res_trust_partial)
    assert_test(
        "Sütun Bazlı Eksik Veri Temizleme & Kısmi Güven Raporu (/clean_data & /get_trust_report)",
        res_up.status_code == 200
        and res_clean_col.status_code == 200
        and d_clean_col.get("health", {}).get("missing_cells") == 1
        and d_trust_partial.get("is_cleaned") is False
        and d_trust_partial.get("has_cleaning_history") is True,
        f"Kalan NaN: {d_clean_col.get('health', {}).get('missing_cells')}",
    )

    # 21. Full Cleaning Marks Trust Report as Cleaned, and Merge Resets Baseline
    res_clean_all = client.post("/clean_data", json={"action": "fill_zero"})
    d_trust_full = j(client.get("/get_trust_report"))
    csv2_bytes = "Isim,Departman\nAli,IT\nVeli,HR\n".encode("utf-8")
    res_merge = client.post(
        "/merge_datasets",
        data={
            "file2": (io.BytesIO(csv2_bytes), "dept.csv"),
            "key1": "Isim",
            "key2": "Isim",
            "join_type": "left",
        },
        content_type="multipart/form-data",
    )
    d_trust_after_merge = j(client.get("/get_trust_report"))
    assert_test(
        "Tam Temizleme Sonrası Güven Onayı & Birleştirme Sonrası Baseline Sıfırlama",
        res_clean_all.status_code == 200
        and d_trust_full.get("is_cleaned") is True
        and res_merge.status_code == 200
        and d_trust_after_merge.get("is_cleaned") is False,
    )

    # 22. Outer Join Key Coalescing & Duplicate Column Suffix Deduplication
    csv_left = "ID,Satis\n1,100\n2,200\n".encode("utf-8")
    csv_right = "ID,Satis,Satis_2\n2,250,999\n3,300,888\n".encode("utf-8")
    client.post(
        "/upload",
        data={"file": (io.BytesIO(csv_left), "left.csv")},
        content_type="multipart/form-data",
    )
    res_outer = client.post(
        "/merge_datasets",
        data={
            "file2": (io.BytesIO(csv_right), "right.csv"),
            "key1": "ID",
            "key2": "ID",
            "join_type": "outer",
        },
        content_type="multipart/form-data",
    )
    d_outer = j(res_outer)
    res_id_vals = j(client.get("/get_column_unique_values?column=ID"))
    all_merged_cols = d_outer.get("numeric_columns", []) + d_outer.get(
        "categorical_columns", []
    )
    assert_test(
        "Outer Join Anahtar Koruma & Çakışan Sütun Tekilleştirme (/merge_datasets)",
        res_outer.status_code == 200
        and len(all_merged_cols) == len(set(all_merged_cols))
        and res_id_vals.get("max") == 3.0,
        f"Sütunlar: {all_merged_cols}, ID Max: {res_id_vals.get('max')}",
    )

    # 23. Excel Multi-Sheet Reference Isolation on In-Place Mutation
    import pandas as pd

    excel_buf = io.BytesIO()
    with pd.ExcelWriter(excel_buf, engine="openpyxl") as writer:
        pd.DataFrame({"Kalem": ["A", "B"], "Tutar": [10, 20]}).to_excel(
            writer, sheet_name="Sayfa1", index=False
        )
        pd.DataFrame({"Kalem": ["X", "Y"], "Tutar": [30, 40]}).to_excel(
            writer, sheet_name="Sayfa2", index=False
        )
    excel_buf.seek(0)
    res_ex_up = client.post(
        "/upload",
        data={"file": (excel_buf, "coklu_sayfa.xlsx")},
        content_type="multipart/form-data",
    )
    client.post(
        "/add_calculated_column",
        json={"new_col_name": "Tutar_Kare", "col1": "Tutar", "op": "*", "col2": "Tutar"},
    )
    client.post("/switch_sheet", json={"sheet_name": "Sayfa2"})
    res_sw_back = client.post("/switch_sheet", json={"sheet_name": "Sayfa1"})
    d_sw_back = j(res_sw_back)
    assert_test(
        "Excel Çoklu Sayfa Bellek İzolasyonu (/upload & /switch_sheet)",
        res_ex_up.status_code == 200
        and res_sw_back.status_code == 200
        and "Tutar_Kare" not in d_sw_back.get("numeric_columns", []),
        f"Sayfa1 Sütunları: {d_sw_back.get('numeric_columns', [])}",
    )

    # 24. Global /clean_data Removes Duplicate Rows & Achieves 100% Cleaned Trust State
    client.post("/load_sample")
    client.post(
        "/repair_column_anomalies",
        json={"column": "__all__", "repair_mode": "smart_heal"},
    )
    client.post("/clean_data", json={"action": "fill_mean"})
    d_trust_sample_cleaned = j(client.get("/get_trust_report"))
    assert_test(
        "Global /clean_data Mükerrer Satır Temizliği & Tam Güven Onayı",
        d_trust_sample_cleaned.get("is_cleaned") is True
        and d_trust_sample_cleaned.get("has_cleaning_history") is True
        and d_trust_sample_cleaned.get("current_report", {}).get("duplicate_rows") == 0,
        f"Kalan Mükerrer: {d_trust_sample_cleaned.get('current_report', {}).get('duplicate_rows')}",
    )

    print("=" * 70)
    print(f"🎉 SONUÇ: {passed}/{total} TÜM MASTER ENTEGRASYON TESTLERİ KUSURSUZ GEÇTİ!")
    print("=" * 70)


if __name__ == "__main__":
    run_tests()
