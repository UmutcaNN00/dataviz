"""
Test Apple Pro Integration & Route Connectivity
Verifies that templates/landing.html and templates/analysis.html render cleanly,
and that all backend routes wire up properly with the new Apple Pro edition frontend.
"""

import sys
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

from app import app

def test_apple_pro():
    client = app.test_client()
    passed = 0
    total = 0

    def check(name, cond, extra=""):
        nonlocal passed, total
        total += 1
        if cond:
            passed += 1
            print(f"  ✅ [TEST {total:02d}] {name} - BAŞARILI {extra}")
        else:
            print(f"  ❌ [TEST {total:02d}] {name} - BAŞARISIZ! {extra}")
            sys.exit(1)

    print("=" * 70)
    print("🍎 APPLE PRO EDITIONS - ENTEGRASYON VE DOĞRULAMA TESTLERİ")
    print("=" * 70)

    # 1. Landing Page Template Render
    res = client.get('/')
    check("Landing Sayfası Render (GET /)", res.status_code == 200 and 'DataViz Pro' in res.text and 'Polars Motoru' in res.text)

    # 2. Analysis Studio Template Render
    res = client.get('/analysis')
    check("Analiz Stüdyosu Render (GET /analysis)", 
          res.status_code == 200 and 
          'screenUpload' in res.text and 
          'screenStudio' in res.text and
          'livePlotlyArea' in res.text and
          'modalHealer' in res.text and
          'modalMerge' in res.text and
          'modalFormula' in res.text and
          'modalFilter' in res.text and
          'modalA4' in res.text)

    # 3. Load Academic Sample Dataset
    res = client.post('/load_sample')
    check("Örnek Veri Yükleme (POST /load_sample)", res.status_code == 200 and res.json.get('success') is True,
          f"Satır: {res.json.get('total_rows')}, Sütun: {res.json.get('total_cols')}")

    # 4. Check Health Endpoint
    res = client.get('/check_health')
    check("Veri Sağlık Denetimi (GET /check_health)", res.status_code == 200 and 'has_issues' in res.json)

    # 5. Get Sheet Preview (In-Memory Table Mode 5)
    res = client.get('/get_sheet_preview?limit=10')
    check("Canlı Veri Tablosu Önizleme (GET /get_sheet_preview)",
          res.status_code == 200 and len(res.json.get('preview', [])) > 0)

    # 6. Scatter Chart Data (Mode 1)
    res = client.post('/get_chart_data', json={
        'chart_type': 'scatter',
        'x_col': 'Maliyet',
        'y_cols': ['Kar'],
        'filters': []
    })
    check("Scatter Grafik Verisi (POST /get_chart_data)", res.status_code == 200 and res.json.get('success') is True)

    # 7. Regression & Correlation Curve with Equation
    res = client.post('/get_regression_curve', json={
        'x_col': 'Maliyet',
        'y_col': 'Kar',
        'model_type': 'linear',
        'corr_method': 'pearson'
    })
    check("Canlı OLS Regresyon Denklemi & R² (POST /get_regression_curve)",
          res.status_code == 200 and 'regression' in res.json and 'correlation' in res.json)

    # 8. ANOVA & Hypothesis Testing (Mode 2)
    res = client.post('/get_stats', json={
        'columns': ['Satış_Tutarı'],
        'x_col': 'Bölge',
        'filters': []
    })
    check("ANOVA Varyans Analizi (POST /get_stats)",
          res.status_code == 200 and 'advanced' in res.json and 'anova' in res.json.get('advanced', {}))

    # 9. Academic AI / LLM Insight
    res = client.post('/get_ai_insight', json={
        'chart_type': 'scatter',
        'x': 'Maliyet',
        'y': ['Kar'],
        'stats': {'Kar': {'mean': 5000, 'median': 4500, 'min': 200, 'max': 15000}}
    })
    check("Akademik Yorumlayıcı (POST /get_ai_insight)", res.status_code == 200 and 'insight' in res.json)

    # 10. Dynamic Pivot Table Matrix (Mode 3)
    res = client.post('/get_pivot_data', json={
        'rows': ['Bölge'],
        'cols': ['Dönem'],
        'values': ['Satış_Tutarı'],
        'agg_func': 'sum'
    })
    check("Dinamik Pivot Tablo Matrisi (POST /get_pivot_data)",
          res.status_code == 200 and len(res.json.get('rows', [])) > 0)

    # 11. Pivot Table Excel Export
    res = client.post('/export_pivot_excel', json={
        'rows': ['Bölge'],
        'cols': ['Dönem'],
        'values': ['Satış_Tutarı'],
        'agg_func': 'sum'
    })
    check("Pivot Excel İndirme (POST /export_pivot_excel)",
          res.status_code == 200 and 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' in res.content_type)

    # 12. Executive KPI Summary (Mode 4)
    res = client.post('/get_kpi_summary', json={})
    check("Yönetici KPI Özeti (POST /get_kpi_summary)", res.status_code == 200 and 'kpis' in res.json)

    # 13. Dynamic Column Slicer Unique Values
    res = client.get('/get_column_unique_values?column=B%C3%B6lge')
    check("Dinamik Dilimleyici Sütun Değerleri (GET /get_column_unique_values)",
          res.status_code == 200 and res.json.get('type') == 'cat' and len(res.json.get('categories', [])) > 0)

    # 14. Formula Wizard Calculated Column
    res = client.post('/create_calculated_column', json={
        'new_col_name': 'Net_Kar_Marji',
        'col1': 'Kar',
        'op': '/',
        'col2': 'Satış_Tutarı'
    })
    check("Formül Sihirbazı Yeni Sütun (POST /create_calculated_column)",
          res.status_code == 200 and res.json.get('new_column') == 'Net_Kar_Marji')

    # 15. Smart Anomaly Repair
    res = client.post('/repair_column_anomalies', json={'column': '__all__', 'repair_mode': 'smart_heal'})
    check("Tip Onarıcı (POST /repair_column_anomalies)", res.status_code == 200 and res.json.get('success') is True)

    # 16. Missing Data Cleaner
    res = client.post('/clean_data', json={'action': 'mean'})
    check("Eksik Veri Temizleme (POST /clean_data)", res.status_code == 200 and res.json.get('success') is True)

    # 17. Parquet Streaming Export
    res = client.post('/export_data', json={'format': 'parquet'})
    check("Parquet Dışa Aktarma (POST /export_data)",
          res.status_code == 200 and ('parquet' in res.content_type or 'octet-stream' in res.content_type))

    print("=" * 70)
    print(f"🎉 SONUÇ: {passed}/{total} TÜM APPLE PRO ENTEGRASYON TESTLERİ KUSURSUZ GEÇTİ!")
    print("=" * 70)

if __name__ == '__main__':
    test_apple_pro()
