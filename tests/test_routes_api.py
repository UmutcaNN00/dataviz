"""
API Integration Tests for Flask Stats and Export Routes.
Tests endpoint behaviors, JSON responses, error handling, edge cases,
multiple regression, logistic regression, hypothesis tests, and ReportLab PDF streaming.
"""

import io
import os
import sys

# Force UTF-8 encoding on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure dataviz_prototype is on path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJ_DIR = os.path.dirname(CURRENT_DIR)
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

import numpy as np
import pandas as pd

from app import create_app
from core.store import set_df


def test_api_routes_suite():
    app = create_app()
    app.config["TESTING"] = True
    client = app.test_client()

    print("\n--- 1. Testing Endpoints Without Data (Should return 400 with Turkish error) ---")
    set_df(None, 1)

    r = client.post("/get_stats", json={"columns": ["a"]})
    assert r.status_code == 400
    assert "error" in r.get_json()

    r = client.post("/get_multiple_regression", json={"target_col": "y", "feature_cols": ["x"]})
    assert r.status_code == 400

    r = client.post("/get_logistic_regression", json={"target_col": "y", "feature_cols": ["x"]})
    assert r.status_code == 400

    r = client.post("/get_hypothesis_tests", json={"group_col": "grp", "value_col": "val"})
    assert r.status_code == 400

    r = client.post("/pivot_data", json={"rows": ["r"], "cols": ["c"], "values": ["v"]})
    assert r.status_code == 400

    r = client.post("/export_parquet", json={})
    assert r.status_code == 400

    r = client.post("/export_academic_pdf", json={})
    assert r.status_code == 400
    print("✓ All no-data 400 guard tests passed")

    print("\n--- 2. Setting Up Test Dataset in Memory Store ---")
    np.random.seed(42)
    n = 100
    x1 = np.random.uniform(10, 50, n)
    x2 = np.random.uniform(1, 10, n)
    y = 2.0 * x1 + 1.5 * x2 + np.random.normal(0, 2, n)
    grup = ["A" if val < 30 else ("B" if val < 40 else "C") for val in x1]
    sinif = ["Kabul" if y[i] > 70 else "Red" for i in range(n)]

    test_df = pd.DataFrame({
        "x1": x1,
        "x2": x2,
        "y": y,
        "grup": grup,
        "sinif": sinif,
        "sabit": [5.0] * n,
    })
    set_df(test_df, 1)

    print("\n--- 3. Testing POST /get_stats ---")
    r = client.post("/get_stats", json={"columns": ["y", "x1"], "x_col": "grup"})
    assert r.status_code == 200
    data = r.get_json()
    assert "stats" in data
    assert "y" in data["stats"]
    assert data["stats"]["y"]["mean"] is not None
    assert data["stats"]["y"]["skewness"] is not None
    assert data["stats"]["y"]["jarque_bera"] is not None
    assert "advanced" in data
    print("✓ /get_stats passed")

    print("\n--- 4. Testing POST /get_correlation_matrix ---")
    r = client.post("/get_correlation_matrix", json={"method": "pearson"})
    assert r.status_code == 200
    data = r.get_json()
    assert "columns" in data
    assert "matrix" in data
    assert len(data["matrix"]) == len(data["columns"])
    print("✓ /get_correlation_matrix passed")

    print("\n--- 5. Testing POST /get_regression_studio_data ---")
    r = client.post("/get_regression_studio_data", json={"x_col": "x1", "y_col": "y", "model_type": "linear"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert "regression" in data
    assert "correlation" in data
    assert "scatter_x" in data
    print("✓ /get_regression_studio_data passed")

    print("\n--- 6. Testing POST /get_multiple_regression ---")
    r = client.post("/get_multiple_regression", json={"target_col": "y", "feature_cols": ["x1", "x2"]})
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["r_squared"] > 0.8
    assert len(data["coefficients"]) == 3
    print("✓ /get_multiple_regression passed")

    print("\n--- 7. Testing POST /get_logistic_regression ---")
    r = client.post("/get_logistic_regression", json={"target_col": "sinif", "feature_cols": ["x1", "x2"]})
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["accuracy"] > 0.7
    assert "confusion_matrix" in data
    print("✓ /get_logistic_regression passed")

    print("\n--- 8. Testing POST /get_hypothesis_tests ---")
    r = client.post("/get_hypothesis_tests", json={"group_col": "grup", "value_col": "y"})
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["test_type"] == "multi_group_comparison"
    assert "anova" in data
    assert "kruskal_wallis" in data
    print("✓ /get_hypothesis_tests passed")

    print("\n--- 9. Testing POST /pivot_data and /get_pivot_data ---")
    r = client.post("/pivot_data", json={"rows": ["grup"], "cols": ["sinif"], "values": ["y"], "agg_func": "mean"})
    assert r.status_code == 200
    data = r.get_json()
    assert "rows" in data
    assert "column_headers" in data

    r2 = client.post("/get_pivot_data", json={"rows": ["grup"], "cols": ["sinif"], "values": ["y"], "agg_func": "sum"})
    assert r2.status_code == 200
    print("✓ /pivot_data and /get_pivot_data alias passed")

    print("\n--- 10. Testing POST /export_parquet ---")
    r = client.post("/export_parquet", json={})
    assert r.status_code == 200
    assert r.content_type == "application/octet-stream"
    assert r.data[:4] == b"PAR1"
    print("✓ /export_parquet passed")

    print("\n--- 11. Testing POST /export_academic_pdf ---")
    r = client.post("/export_academic_pdf", json={
        "title": "DataViz TÜBİTAK Test Raporu",
        "x_col": "grup",
        "y_cols": ["y", "x1"],
    })
    assert r.status_code == 200
    assert r.content_type == "application/pdf"
    assert r.data[:5] == b"%PDF-"
    print("✓ /export_academic_pdf passed")

    print("\n" + "=" * 60)
    print("TÜM FLASK API VE ENDPOINT ENTEGRASYON TESTLERİ GEÇTİ!")
    print("=" * 60)


if __name__ == "__main__":
    test_api_routes_suite()
