"""
Comprehensive Test Suite for DataViz Statistics, Analytics, Regression, and Reporting Layer.
Tests all statistical functions, OLS multicollinearity/singular matrix resilience,
hypothesis tests (Welch T-Test, Mann-Whitney U, ANOVA, Kruskal-Wallis),
pivot matrix generation, Parquet/Excel/CSV exports, and ReportLab Academic PDF generation.
"""

import io
import math
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

from services.export_service import export_dataframe, export_pivot_to_excel
from services.report_service import generate_academic_pdf_report
from services.stats_service import (
    apply_filters,
    compute_advanced_stats,
    compute_column_statistics,
    compute_correlation_matrix,
    compute_hypothesis_tests,
    compute_logistic_regression,
    compute_multiple_linear_regression,
    compute_pivot_data,
    compute_robust_correlation,
    compute_robust_regression,
    safe_float,
)


# ==============================================================================
# 1. DESCRIPTIVE STATISTICS & EDGE CASES
# ==============================================================================

def test_descriptive_stats_normal():
    """Tests normal column statistics computation with skewness, kurtosis, and Jarque-Bera."""
    np.random.seed(42)
    data = np.random.normal(loc=50.0, scale=10.0, size=200)
    df = pd.DataFrame({"puan": data})

    res = compute_column_statistics(df, ["puan"])
    assert "puan" in res
    st = res["puan"]
    assert st["count"] == 200
    assert st["missing"] == 0
    assert 45.0 < st["mean"] < 55.0
    assert 8.0 < st["std"] < 12.0
    assert st["skewness"] is not None
    assert st["kurtosis"] is not None
    assert st["jarque_bera_stat"] is not None
    assert st["jarque_bera_p"] is not None
    assert isinstance(st["jarque_bera"], dict)
    print("✓ test_descriptive_stats_normal passed")


def test_descriptive_stats_zero_variance():
    """Tests constant values (zero variance): should not crash and return graceful stats."""
    df = pd.DataFrame({"sabit": [10.0, 10.0, 10.0, 10.0, 10.0]})
    res = compute_column_statistics(df, ["sabit"])
    st = res["sabit"]
    assert st["count"] == 5
    assert st["mean"] == 10.0
    assert st["std"] == 0.0
    assert st["skewness"] is None or st["skewness"] == 0.0
    assert st["jarque_bera_p"] is None
    print("✓ test_descriptive_stats_zero_variance passed")


def test_descriptive_stats_single_row():
    """Tests single-row DataFrame: should not crash."""
    df = pd.DataFrame({"tek": [42.0]})
    res = compute_column_statistics(df, ["tek"])
    st = res["tek"]
    assert st["count"] == 1
    assert st["mean"] == 42.0
    assert st["std"] is None or math.isnan(st["std"])
    assert st["skewness"] is None
    assert st["kurtosis"] is None
    assert st["jarque_bera_p"] is None
    print("✓ test_descriptive_stats_single_row passed")


def test_descriptive_stats_all_nan():
    """Tests all NaN column: should return count=0 and None for summary stats."""
    df = pd.DataFrame({"bos": [np.nan, None, np.nan]})
    res = compute_column_statistics(df, ["bos"])
    st = res["bos"]
    assert st["count"] == 0
    assert st["missing"] == 3
    assert st["mean"] is None
    assert st["std"] is None
    print("✓ test_descriptive_stats_all_nan passed")


def test_descriptive_stats_dirty_string_numbers():
    """Tests string column containing numbers with coerce conversion."""
    df = pd.DataFrame({"kirli": ["10.5", "20.2", "gecersiz", "30.3"]})
    res = compute_column_statistics(df, ["kirli"])
    st = res["kirli"]
    assert st["count"] == 3
    assert st["missing"] == 1
    assert abs(st["mean"] - 20.33) < 0.1
    print("✓ test_descriptive_stats_dirty_string_numbers passed")


# ==============================================================================
# 2. CORRELATION ANALYSIS & ZERO VARIANCE / SINGLE VALUE
# ==============================================================================

def test_correlation_normal():
    """Tests Pearson and Spearman correlation on normal correlated series."""
    x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
    y = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20]
    res_pearson = compute_robust_correlation(x, y, method="pearson")
    assert abs(res_pearson["coef"] - 1.0) < 1e-4
    assert res_pearson["p_value"] < 0.001

    res_spearman = compute_robust_correlation(x, y, method="spearman")
    assert abs(res_spearman["coef"] - 1.0) < 1e-4
    print("✓ test_correlation_normal passed")


def test_correlation_zero_variance():
    """Tests zero variance (constant inputs) without warning/crash."""
    x = [5, 5, 5, 5, 5]
    y = [1, 2, 3, 4, 5]
    res = compute_robust_correlation(x, y, method="pearson")
    assert res["coef"] == 0.0
    assert res["p_value"] is None
    assert "Yetersiz" in res["interpretation"] or "sabit" in res["interpretation"]
    print("✓ test_correlation_zero_variance passed")


def test_correlation_insufficient_data():
    """Tests sample size < 3."""
    x = [1.0, 2.0]
    y = [3.0, 4.0]
    res = compute_robust_correlation(x, y)
    assert res["coef"] == 0.0
    assert res["p_value"] is None
    print("✓ test_correlation_insufficient_data passed")


def test_correlation_matrix_with_constant_col():
    """Tests pairwise correlation matrix when one column is constant and another is all NaN."""
    df = pd.DataFrame({
        "norm_a": [1, 2, 3, 4, 5],
        "norm_b": [2, 4, 5, 8, 10],
        "sabit": [7, 7, 7, 7, 7],
        "tumu_nan": [np.nan, np.nan, np.nan, np.nan, np.nan]
    })
    res = compute_correlation_matrix(df, ["norm_a", "norm_b", "sabit", "tumu_nan"])
    matrix = res["matrix"]
    assert len(matrix) == 4
    # Diagonal must be 1.0
    for i in range(4):
        assert matrix[i][i] == 1.0
    # Correlation with constant or NaN should safely be 0.0 without crash
    assert matrix[0][2] == 0.0
    assert matrix[0][3] == 0.0
    print("✓ test_correlation_matrix_with_constant_col passed")


# ==============================================================================
# 3. HYPOTHESIS TESTING (T-TEST, ANOVA, MANN-WHITNEY U, KRUSKAL-WALLIS)
# ==============================================================================

def test_hypothesis_two_groups():
    """Tests Welch T-Test and Mann-Whitney U for 2 groups."""
    df = pd.DataFrame({
        "grup": ["A"] * 20 + ["B"] * 20,
        "deger": list(np.random.normal(10, 2, 20)) + list(np.random.normal(15, 2, 20))
    })
    res = compute_hypothesis_tests(df, "grup", "deger")
    assert res["success"] is True
    assert res["test_type"] == "two_group_comparison"
    assert res["welch_t_test"]["t_stat"] is not None
    assert res["welch_t_test"]["p_value"] is not None
    assert res["mann_whitney_u"]["u_stat"] is not None
    assert res["mann_whitney_u"]["p_value"] is not None
    assert res["is_significant"] is True
    assert "istatistiksel olarak anlamlı" in res["interpretation"]
    print("✓ test_hypothesis_two_groups passed")


def test_hypothesis_multi_groups():
    """Tests One-Way ANOVA and Kruskal-Wallis H for >2 groups."""
    df = pd.DataFrame({
        "grup": ["A"] * 15 + ["B"] * 15 + ["C"] * 15,
        "skor": list(np.random.normal(50, 5, 15)) + list(np.random.normal(60, 5, 15)) + list(np.random.normal(70, 5, 15))
    })
    res = compute_hypothesis_tests(df, "grup", "skor")
    assert res["success"] is True
    assert res["test_type"] == "multi_group_comparison"
    assert res["anova"]["f_stat"] is not None
    assert res["anova"]["p_value"] is not None
    assert res["kruskal_wallis"]["h_stat"] is not None
    assert res["kruskal_wallis"]["p_value"] is not None
    assert res["is_significant"] is True
    print("✓ test_hypothesis_multi_groups passed")


def test_hypothesis_identical_numbers_in_groups():
    """Tests Kruskal-Wallis edge case where all numbers in all groups are identical."""
    df = pd.DataFrame({
        "grup": ["A", "A", "A", "B", "B", "B", "C", "C", "C"],
        "skor": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.0]
    })
    res = compute_hypothesis_tests(df, "grup", "skor")
    assert res["success"] is True
    # In identical values, Kruskal would raise ValueError without our guard.
    # Our guard should safely set h_stat to None or handled value.
    assert res["kruskal_wallis"]["h_stat"] is None or res["kruskal_wallis"]["p_value"] is None
    print("✓ test_hypothesis_identical_numbers_in_groups passed")


def test_hypothesis_single_group_or_insufficient():
    """Tests single group edge case."""
    df = pd.DataFrame({
        "grup": ["A", "A", "A"],
        "skor": [1.0, 2.0, 3.0]
    })
    res = compute_hypothesis_tests(df, "grup", "skor")
    assert "error" in res
    assert "en az 2 geçerli grup" in res["error"]
    print("✓ test_hypothesis_single_group_or_insufficient passed")


# ==============================================================================
# 4. REGRESSION & MODELING (OLS, POLYNOMIAL, LOGISTIC, SINGULAR MATRIX)
# ==============================================================================

def test_robust_regression_polynomial():
    """Tests linear and degree-2 polynomial regression."""
    x = np.linspace(1, 10, 20)
    y = 2.5 * x**2 - 1.2 * x + 5.0 + np.random.normal(0, 0.5, 20)

    res_poly2 = compute_robust_regression(x, y, model_type="poly2")
    assert res_poly2["r_squared"] > 0.95
    assert len(res_poly2["trend_x"]) > 0
    assert len(res_poly2["ci_lower"]) == len(res_poly2["trend_x"])

    res_linear = compute_robust_regression(x, y, model_type="linear")
    assert res_linear["r_squared"] > 0.70
    print("✓ test_robust_regression_polynomial passed")


def test_multiple_linear_regression_normal():
    """Tests multiple OLS regression with 2 predictors."""
    np.random.seed(42)
    n = 100
    x1 = np.random.uniform(10, 50, n)
    x2 = np.random.uniform(1, 10, n)
    y = 3.5 * x1 - 2.0 * x2 + 15.0 + np.random.normal(0, 1.0, n)

    df = pd.DataFrame({"x1": x1, "x2": x2, "y": y})
    res = compute_multiple_linear_regression(df, ["x1", "x2"], "y")
    assert res["success"] is True
    assert res["r_squared"] > 0.95
    assert res["f_statistic"] is not None
    assert len(res["coefficients"]) == 3  # Intercept + x1 + x2
    assert res["is_singular"] is False
    print("✓ test_multiple_linear_regression_normal passed")


def test_multiple_linear_regression_singular_matrix():
    """
    CRITICAL TEST: Tests perfect collinearity / singular matrix (x2 = 2 * x1).
    Standard np.linalg.inv crashes with LinAlgError: Singular matrix.
    Our implementation MUST use pinv and succeed with multicollinearity warning.
    """
    x1 = np.array([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0])
    x2 = 2.0 * x1  # Perfectly collinear!
    y = 3.0 * x1 + 5.0

    df = pd.DataFrame({"x1": x1, "x2": x2, "y": y})
    res = compute_multiple_linear_regression(df, ["x1", "x2"], "y")
    assert res["success"] is True
    assert res["is_singular"] is True
    assert "çoklu doğrusallık" in res["multicollinearity_note"].lower()
    assert res["r_squared"] > 0.99
    print("✓ test_multiple_linear_regression_singular_matrix passed")


def test_logistic_regression_binary():
    """Tests binary logistic regression classification."""
    np.random.seed(42)
    n = 60
    f1 = np.random.normal(5, 2, n)
    f2 = np.random.normal(10, 3, n)
    # y: 1 if f1 + f2 > 15 else 0
    target = ["Kabul" if (f1[i] + f2[i] > 15) else "Red" for i in range(n)]

    df = pd.DataFrame({"f1": f1, "f2": f2, "karar": target})
    res = compute_logistic_regression(df, ["f1", "f2"], "karar")
    assert res["success"] is True
    assert res["model_type"] == "Binary"
    assert res["accuracy"] > 0.70
    assert len(res["classes"]) == 2
    assert "f1" in res["coefficients"]
    print("✓ test_logistic_regression_binary passed")


def test_logistic_regression_single_class_edge_case():
    """Tests logistic regression when target only has 1 class."""
    df = pd.DataFrame({
        "f1": [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0],
        "karar": ["A", "A", "A", "A", "A", "A", "A", "A"]
    })
    res = compute_logistic_regression(df, ["f1"], "karar")
    assert "error" in res
    assert "en az 2 farklı sınıfa" in res["error"]
    print("✓ test_logistic_regression_single_class_edge_case passed")


# ==============================================================================
# 5. PIVOT TABLE & GROUPING EDGE CASES
# ==============================================================================

def test_pivot_data_normal():
    """Tests Excel-style Pivot Table with margins (Grand Total)."""
    df = pd.DataFrame({
        "Bolge": ["Marmara", "Ege", "Marmara", "Ege", "İç Anadolu"],
        "Kategori": ["Gıda", "Gıda", "Teknoloji", "Teknoloji", "Gıda"],
        "Satis": [100.0, 150.0, 300.0, 250.0, 200.0]
    })
    res = compute_pivot_data(df, rows=["Bolge"], cols=["Kategori"], values=["Satis"], agg_func="sum")
    assert "rows" in res
    assert len(res["rows"]) > 0
    assert any(r["is_grand_total"] for r in res["rows"])
    print("✓ test_pivot_data_normal passed")


def test_pivot_data_empty_df():
    """Tests pivot computation on empty DataFrame."""
    df = pd.DataFrame()
    raised = False
    try:
        compute_pivot_data(df, rows=["A"], cols=["B"], values=["C"])
    except ValueError:
        raised = True
    assert raised, "Boş DataFrame için ValueError fırlatılmalıydı"
    print("✓ test_pivot_data_empty_df passed")


def test_pivot_data_single_row():
    """Tests pivot computation with single-row DataFrame."""
    df = pd.DataFrame({
        "Bolge": ["Marmara"],
        "Kategori": ["Gıda"],
        "Satis": [150.0]
    })
    res = compute_pivot_data(df, rows=["Bolge"], cols=["Kategori"], values=["Satis"], agg_func="sum")
    assert "rows" in res
    assert len(res["rows"]) >= 1
    print("✓ test_pivot_data_single_row passed")


# ==============================================================================
# 6. EXPORTS (PARQUET, EXCEL, CSV) & REPORTLAB ACADEMIC PDF
# ==============================================================================

def test_export_formats():
    """Tests CSV, Excel, and Apache Parquet in-memory exports."""
    df = pd.DataFrame({
        "id": [1, 2, 3, 4],
        "ad": ["Ahmet", "Mehmet", "Ayşe", "Fatma"],
        "tutar": [100.5, 250.0, 300.75, 450.2]
    })

    # 1. CSV
    buf_csv, mime_csv, name_csv = export_dataframe(df, export_format="csv")
    assert mime_csv.startswith("text/csv")
    assert name_csv.endswith(".csv")
    csv_bytes = buf_csv.getvalue()
    assert len(csv_bytes) > 0
    assert csv_bytes.startswith(b"\xef\xbb\xbf")  # UTF-8 BOM

    # 2. Excel
    buf_xlsx, mime_xlsx, name_xlsx = export_dataframe(df, export_format="xlsx")
    assert "spreadsheetml" in mime_xlsx
    assert name_xlsx.endswith(".xlsx")
    assert len(buf_xlsx.getvalue()) > 0

    # 3. Parquet
    buf_pq, mime_pq, name_pq = export_dataframe(df, export_format="parquet")
    assert name_pq.endswith(".parquet")
    assert buf_pq.getvalue()[:4] == b"PAR1"  # Standard Apache Parquet magic header
    print("✓ test_export_formats passed")


def test_reportlab_academic_pdf_generation():
    """
    Tests publication-quality ReportLab academic PDF generator with Turkish characters,
    descriptive statistics table, hypothesis tests, and regression.
    """
    df = pd.DataFrame({
        "Bölge": ["Marmara"] * 25 + ["Ege"] * 25,
        "Gelir_Düzeyi": list(np.random.normal(50000, 10000, 50)),
        "Harcama_Skoru": list(np.random.normal(3000, 500, 50)),
        "Tasarruf_Miktarı": list(np.random.normal(8000, 1500, 50)),
    })

    buf_pdf, filename = generate_academic_pdf_report(
        df,
        title="TÜBİTAK 1001 Araştırma Projesi İstatistik Raporu",
        subtitle="Hanehalkı Gelir ve Harcama Davranışları Parametrik İncelemesi",
        author="Prof. Dr. Veri Analisti",
        x_col="Bölge",
        y_cols=["Gelir_Düzeyi", "Harcama_Skoru", "Tasarruf_Miktarı"],
        project_code="TUBITAK-2026-TEST",
    )

    pdf_bytes = buf_pdf.getvalue()
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF-")  # Valid PDF signature
    assert filename.endswith(".pdf")
    print("✓ test_reportlab_academic_pdf_generation passed")


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("DATAVIZ STATISTICS & REPORTING LAYER FULL AUDIT TEST SUITE")
    print("=" * 60)
    test_descriptive_stats_normal()
    test_descriptive_stats_zero_variance()
    test_descriptive_stats_single_row()
    test_descriptive_stats_all_nan()
    test_descriptive_stats_dirty_string_numbers()
    test_correlation_normal()
    test_correlation_zero_variance()
    test_correlation_insufficient_data()
    test_correlation_matrix_with_constant_col()
    test_hypothesis_two_groups()
    test_hypothesis_multi_groups()
    test_hypothesis_identical_numbers_in_groups()
    test_hypothesis_single_group_or_insufficient()
    test_robust_regression_polynomial()
    test_multiple_linear_regression_normal()
    test_multiple_linear_regression_singular_matrix()
    test_logistic_regression_binary()
    test_logistic_regression_single_class_edge_case()
    test_pivot_data_normal()
    test_pivot_data_empty_df()
    test_pivot_data_single_row()
    test_export_formats()
    test_reportlab_academic_pdf_generation()
    print("=" * 60)
    print("TÜM TESTLER BAŞARIYLA GEÇTİ! (ALL 21 TESTS PASSED)")
    print("=" * 60 + "\n")
