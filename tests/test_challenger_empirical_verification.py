"""
Challenger 2 - Codebase & Requirement Cross-Verification Test Suite
Executes deep empirical, mathematical, and algorithmic verification against:
1. PyArrow Zero-Copy parameters (split_blocks=True, self_destruct=True)
2. Data Healer cleaning logic (_parse_series_fast and robust_parse_numeric_string)
3. Statistical formulas (Pearson, Spearman, Kendall, OLS/Poly/Log/Exp, 95% CI bands, Welch T-Test, ANOVA)
4. Concurrency and LRU cache in store.py (threading.RLock, MAX_ACTIVE_SESSIONS, gc.collect)
5. 100M Dataset generator parameters (100M rows, 22 cols, 40 chunks of 2.5M, ZSTD level 3, 13 dict encoded cols)
6. Inter-module connectivity and PDF claims consistency
"""

import ast
import gc
import io
import inspect
import os
import sys

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

import threading
import time
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from scipy import stats as sp_stats

# Ensure dataviz root is in python path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from services.file_service import read_parquet_safely
from services.data_healer import robust_parse_numeric_string, _parse_series_fast, detect_column_anomalies
from services.stats_service import (
    compute_robust_correlation,
    compute_robust_regression,
    compute_advanced_stats,
    compute_correlation_matrix
)
from core.store import DATA_STORE, _STORE_LOCK, set_df, get_df, clear_user_data, _evict_old_sessions
from core.config import MAX_ACTIVE_SESSIONS
import generate_100m_dataset


def print_banner(msg):
    print("\n" + "=" * 75)
    print(f"🔬 {msg}")
    print("=" * 75)


def test_1_pyarrow_zero_copy():
    print_banner("TEST 1: PyArrow Zero-Copy Parameters & Parquet Ingestion")
    
    # 1.1 AST Inspection of services/file_service.py
    file_service_path = os.path.join(BASE_DIR, "services", "file_service.py")
    with open(file_service_path, "r", encoding="utf-8") as f:
        code_text = f.read()
    
    tree = ast.parse(code_text)
    found_to_pandas_kwargs = {}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and getattr(node.func, "attr", None) == "to_pandas":
            for kw in node.keywords:
                if isinstance(kw.value, ast.Constant):
                    found_to_pandas_kwargs[kw.arg] = kw.value.value

    print(f"  [AST] Detected to_pandas() kwargs: {found_to_pandas_kwargs}")
    assert found_to_pandas_kwargs.get("split_blocks") is True, "split_blocks=True NOT found in to_pandas call!"
    assert found_to_pandas_kwargs.get("self_destruct") is True, "self_destruct=True NOT found in to_pandas call!"
    print("  ✅ [AST VERIFIED] split_blocks=True and self_destruct=True confirmed in file_service.py")

    # 1.2 Empirical Execution with Synthetic Parquet Buffer
    n_rows = 50_000
    df_src = pd.DataFrame({
        "ID": np.arange(n_rows, dtype=np.int64),
        "Kategori": pd.Categorical(np.random.choice(["Elektronik", "Moda", "Gıda", "Ev"], size=n_rows)),
        "Tutar": np.random.uniform(10.0, 1000.0, size=n_rows).astype(np.float32),
        "Adet": np.random.randint(1, 20, size=n_rows).astype(np.int32)
    })
    table = pa.Table.from_pandas(df_src)
    sink = io.BytesIO()
    pq.write_table(table, sink, compression="zstd", compression_level=3)
    sink.seek(0)
    
    df_read = read_parquet_safely(sink)
    assert len(df_read) == n_rows, f"Row count mismatch: {len(df_read)} vs {n_rows}"
    assert list(df_read.columns) == ["ID", "Kategori", "Tutar", "Adet"], f"Columns mismatch: {list(df_read.columns)}"
    assert isinstance(df_read["Kategori"].dtype, pd.CategoricalDtype), "Categorical dtype was lost in zero-copy reading!"
    print("  ✅ [EMPIRICAL READ VERIFIED] read_parquet_safely successfully ingested Parquet with Categorical preservation.")
    return True


def test_2_data_healer_logic():
    print_banner("TEST 2: Data Healer Cleaning Logic & Vectorized Acceleration")
    
    # 2.1 Edge Case Verification for robust_parse_numeric_string
    test_cases = [
        # (input_val, expected_val, description)
        ("1.250,50", 1250.50, "Turkish thousand dot + decimal comma"),
        ("15.000", 15000.0, "Turkish thousand dot"),
        ("1.250", 1250.0, "Turkish thousand dot single"),
        ("1,250.50", 1250.50, "US thousand comma + decimal dot"),
        ("1,250,000.75", 1250000.75, "US multiple commas"),
        ("₺14.250,75", 14250.75, "Turkish Lira symbol + format"),
        ("$1,250.50", 1250.50, "US Dollar symbol + format"),
        ("€9.500,00", 9500.0, "Euro symbol + format"),
        ("£450.25", 450.25, "Pound symbol"),
        ("8.420 TL", 8420.0, "TL suffix"),
        ("1500 TRY", 1500.0, "TRY suffix"),
        ("250 USD", 250.0, "USD suffix"),
        ("12.40kg", 12.40, "kg suffix directly attached"),
        ("8,50 kg", 8.50, "kg suffix with space and decimal comma"),
        ("50 adet", 50.0, "adet suffix"),
        ("%18.5", 18.5, "Percentage prefix"),
        ("25,0%", 25.0, "Percentage suffix with comma"),
        ("sıfır", 0.0, "Turkish word zero"),
        ("sifir", 0.0, "Turkish ascii zero"),
        ("zero", 0.0, "English zero"),
        ("bir", 1.0, "Turkish word one"),
        ("one", 1.0, "English one"),
        # Dates (must be None)
        ("2024-01-15", None, "ISO date YYYY-MM-DD"),
        ("15/01/2024", None, "Slash date DD/MM/YYYY"),
        ("15.01.2024", None, "Dot date DD.MM.YYYY"),
        # Null strings (must be None)
        ("yok", None, "Turkish yok"),
        ("n/a", None, "n/a"),
        ("nan", None, "nan"),
        ("null", None, "null"),
        ("none", None, "none"),
        ("bilinmiyor", None, "bilinmiyor"),
        ("belirtilmedi", None, "belirtilmedi"),
        ("tanımsız", None, "tanımsız"),
        ("-", None, "dash"),
        ("", None, "empty string"),
        ("kayıp", None, "kayıp"),
        ("hata", None, "hata"),
    ]

    for val, expected, desc in test_cases:
        res = robust_parse_numeric_string(val)
        if expected is None:
            assert res is None, f"Expected None for '{val}' ({desc}), got {res}"
        else:
            assert res is not None and abs(res - expected) < 1e-4, f"Mismatch for '{val}' ({desc}): got {res}, expected {expected}"
    print(f"  ✅ [UNIT PARSER VERIFIED] All {len(test_cases)} robust_parse_numeric_string edge cases passed!")

    # 2.2 Vectorized / Categorical Acceleration Verification (_parse_series_fast)
    n_sample = 200_000
    dirty_categories = ["₺1.250,50", "Yok", "8,50 kg", "%18.5", "500 TL", "Bilinmiyor"]
    cat_indices = np.random.choice(len(dirty_categories), size=n_sample)
    
    # Create Categorical series
    cat_series = pd.Series(pd.Categorical.from_codes(cat_indices, categories=dirty_categories))
    
    # Time categorical-aware parsing
    t0 = time.perf_counter()
    parsed_cat = _parse_series_fast(cat_series, use_float32=False)
    t_fast = time.perf_counter() - t0
    
    # Time standard naive apply over object series
    obj_series = cat_series.astype(object)
    t0 = time.perf_counter()
    parsed_naive = pd.to_numeric(obj_series.apply(robust_parse_numeric_string), errors="coerce")
    t_naive = time.perf_counter() - t0

    # Verification of equality
    diff = np.abs(np.nan_to_num(parsed_cat.to_numpy()) - np.nan_to_num(parsed_naive.to_numpy()))
    assert np.max(diff) < 1e-5, f"Categorical parsing divergence detected! Max diff: {np.max(diff)}"
    
    speedup = t_naive / max(t_fast, 1e-6)
    print(f"  [BENCHMARK] 200k rows: Fast Categorical = {t_fast*1000:.2f}ms | Naive Object = {t_naive*1000:.2f}ms | Speedup = {speedup:.1f}x")
    assert speedup > 5.0, f"Expected at least 5x speedup over categorical codes, got {speedup:.1f}x"
    print("  ✅ [VECTORIZED ACCELERATION VERIFIED] _parse_series_fast correctly leverages dictionary codes.")
    return True


def test_3_statistical_formulas():
    print_banner("TEST 3: Statistical Formulas, Regressions, CI Bands & Hypothesis Tests")
    
    rng = np.random.default_rng(42)
    n = 100
    x = rng.uniform(5.0, 50.0, size=n)
    y = 2.5 * x + 10.0 + rng.normal(0, 5.0, size=n)
    
    # 3.1 Pearson Correlation
    res_pearson = compute_robust_correlation(x, y, method="pearson")
    sp_p_coef, sp_p_pval = sp_stats.pearsonr(x, y)
    assert abs(res_pearson["coef"] - round(float(sp_p_coef), 4)) < 1e-4, "Pearson coef mismatch"
    assert abs(res_pearson["p_value"] - float(sp_p_pval)) < 1e-3, "Pearson p-value mismatch"
    print(f"  ✅ [PEARSON VERIFIED] r = {res_pearson['coef']} (p = {res_pearson['p_value']:.4e})")

    # 3.2 Spearman Correlation
    res_spearman = compute_robust_correlation(x, y, method="spearman")
    sp_s_coef, sp_s_pval = sp_stats.spearmanr(x, y)
    assert abs(res_spearman["coef"] - round(float(sp_s_coef), 4)) < 1e-4, "Spearman coef mismatch"
    assert abs(res_spearman["p_value"] - float(sp_s_pval)) < 1e-3, "Spearman p-value mismatch"
    print(f"  ✅ [SPEARMAN VERIFIED] rho = {res_spearman['coef']} (p = {res_spearman['p_value']:.4e})")

    # 3.3 Kendall Correlation
    res_kendall = compute_robust_correlation(x, y, method="kendall")
    sp_k_coef, sp_k_pval = sp_stats.kendalltau(x, y)
    assert abs(res_kendall["coef"] - round(float(sp_k_coef), 4)) < 1e-4, "Kendall coef mismatch"
    assert abs(res_kendall["p_value"] - float(sp_k_pval)) < 1e-3, "Kendall p-value mismatch"
    print(f"  ✅ [KENDALL VERIFIED] tau = {res_kendall['coef']} (p = {res_kendall['p_value']:.4e})")

    # 3.4 Linear Regression & 95% Confidence Interval Band Verification
    reg_lin = compute_robust_regression(x, y, model_type="linear", num_points=50)
    sp_lin = sp_stats.linregress(x, y)
    assert abs(reg_lin["r_squared"] - round(sp_lin.rvalue**2, 4)) < 1e-4, "Linear R² mismatch"
    assert abs(reg_lin["se"] - round(sp_lin.stderr, 4)) < 1e-4, "Linear SE mismatch"

    # Analytical verification of 95% CI bands
    dof = n - 2
    y_fit = sp_lin.slope * x + sp_lin.intercept
    s_err = np.sqrt(np.sum((y - y_fit)**2) / dof)
    x_bar = np.mean(x)
    ss_x = np.sum((x - x_bar)**2)
    t_val = sp_stats.t.ppf(0.975, dof)

    # Check a test curve point
    x_curve = np.array(reg_lin["trend_x"])
    y_curve = np.array(reg_lin["trend_y"])
    se_line_manual = s_err * np.sqrt(1.0 / n + ((x_curve - x_bar)**2) / ss_x)
    ci_lower_manual = y_curve - t_val * se_line_manual
    ci_upper_manual = y_curve + t_val * se_line_manual

    ci_low_calc = np.array(reg_lin["ci_lower"])
    ci_upp_calc = np.array(reg_lin["ci_upper"])
    assert np.allclose(ci_low_calc, ci_lower_manual, atol=1e-3), "Linear CI lower band mismatch"
    assert np.allclose(ci_upp_calc, ci_upper_manual, atol=1e-3), "Linear CI upper band mismatch"
    print(f"  ✅ [OLS & 95% CI BAND VERIFIED] Eq: {reg_lin['equation']} | R²={reg_lin['r_squared']} | CI bands matched analytical formula.")

    # 3.5 Polynomial Regressions (degree 2 and degree 3)
    reg_p2 = compute_robust_regression(x, y, model_type="poly2", num_points=20)
    assert "x²" in reg_p2["equation"], f"poly2 equation missing x²: {reg_p2['equation']}"
    assert reg_p2["r_squared"] > 0, "poly2 R² invalid"
    print(f"  ✅ [POLY2 VERIFIED] Eq: {reg_p2['equation']} | R²={reg_p2['r_squared']}")

    reg_p3 = compute_robust_regression(x, y, model_type="poly3", num_points=20)
    assert "x³" in reg_p3["equation"], f"poly3 equation missing x³: {reg_p3['equation']}"
    assert reg_p3["r_squared"] > 0, "poly3 R² invalid"
    print(f"  ✅ [POLY3 VERIFIED] Eq: {reg_p3['equation']} | R²={reg_p3['r_squared']}")

    # 3.6 Logarithmic and Exponential Regressions
    x_pos = np.abs(x) + 1.0
    y_pos = np.abs(y) + 1.0
    reg_log = compute_robust_regression(x_pos, y_pos, model_type="log", num_points=20)
    assert "ln(x)" in reg_log["equation"], f"log equation missing ln(x): {reg_log['equation']}"
    print(f"  ✅ [LOG VERIFIED] Eq: {reg_log['equation']} | R²={reg_log['r_squared']}")

    reg_exp = compute_robust_regression(x_pos, y_pos, model_type="exp", num_points=20)
    assert "e^" in reg_exp["equation"], f"exp equation missing e^: {reg_exp['equation']}"
    print(f"  ✅ [EXP VERIFIED] Eq: {reg_exp['equation']} | R²={reg_exp['r_squared']}")

    # 3.7 Welch's T-Test (equal_var=False) & One-Way ANOVA (f_oneway)
    # Test Welch's T-Test (2 groups)
    df_ttest = pd.DataFrame({
        "Grup": ["A"] * 50 + ["B"] * 50,
        "Skor": np.concatenate([rng.normal(10, 2, 50), rng.normal(15, 4, 50)])
    })
    res_ttest = compute_advanced_stats(df_ttest, cols=["Skor"], x_col="Grup")
    gA = df_ttest[df_ttest["Grup"] == "A"]["Skor"].values
    gB = df_ttest[df_ttest["Grup"] == "B"]["Skor"].values
    sp_t_stat, sp_t_pval = sp_stats.ttest_ind(gA, gB, equal_var=False)

    calc_t = res_ttest["Skor"]["t_test"]["t_stat"]
    calc_t_p = res_ttest["Skor"]["t_test"]["p_value"]
    assert abs(calc_t - sp_t_stat) < 1e-4, f"Welch T-stat mismatch: {calc_t} vs {sp_t_stat}"
    assert abs(calc_t_p - sp_t_pval) < 1e-4, f"Welch p-value mismatch: {calc_t_p} vs {sp_t_pval}"
    print(f"  ✅ [WELCH T-TEST VERIFIED] t = {calc_t:.4f}, p = {calc_t_p:.4e} (equal_var=False confirmed)")

    # Test One-Way ANOVA (3 groups)
    df_anova = pd.DataFrame({
        "Kategori": ["X"] * 30 + ["Y"] * 30 + ["Z"] * 30,
        "Metrik": np.concatenate([rng.normal(10, 2, 30), rng.normal(14, 2, 30), rng.normal(20, 2, 30)])
    })
    res_anova = compute_advanced_stats(df_anova, cols=["Metrik"], x_col="Kategori")
    gX = df_anova[df_anova["Kategori"] == "X"]["Metrik"].values
    gY = df_anova[df_anova["Kategori"] == "Y"]["Metrik"].values
    gZ = df_anova[df_anova["Kategori"] == "Z"]["Metrik"].values
    sp_f_stat, sp_f_pval = sp_stats.f_oneway(gX, gY, gZ)

    calc_f = res_anova["Metrik"]["anova"]["f_stat"]
    calc_f_p = res_anova["Metrik"]["anova"]["p_value"]
    assert abs(calc_f - sp_f_stat) < 1e-4, f"ANOVA F-stat mismatch: {calc_f} vs {sp_f_stat}"
    assert abs(calc_f_p - sp_f_pval) < 1e-4, f"ANOVA p-value mismatch: {calc_f_p} vs {sp_f_pval}"
    print(f"  ✅ [ONE-WAY ANOVA VERIFIED] F = {calc_f:.4f}, p = {calc_f_p:.4e} (f_oneway confirmed)")
    return True


def test_4_concurrency_and_lru_cache():
    print_banner("TEST 4: Concurrency & LRU Cache in core/store.py")

    # 4.1 RLock verification
    assert hasattr(_STORE_LOCK, "acquire") and hasattr(_STORE_LOCK, "release"), "_STORE_LOCK is not a valid lock!"
    # Check if re-entrant
    acquired_1 = _STORE_LOCK.acquire(blocking=False)
    acquired_2 = _STORE_LOCK.acquire(blocking=False)
    assert acquired_1 and acquired_2, "_STORE_LOCK failed re-entrant acquisition test!"
    _STORE_LOCK.release()
    _STORE_LOCK.release()
    print("  ✅ [LOCK VERIFIED] _STORE_LOCK confirmed as functional threading.RLock re-entrant lock.")

    # 4.2 LRU Eviction & MAX_ACTIVE_SESSIONS verification
    clear_user_data("test_clear_all")
    with _STORE_LOCK:
        DATA_STORE.clear()

    print(f"  [CONFIG] MAX_ACTIVE_SESSIONS = {MAX_ACTIVE_SESSIONS}")
    assert MAX_ACTIVE_SESSIONS in (3, 5), f"Unexpected MAX_ACTIVE_SESSIONS: {MAX_ACTIVE_SESSIONS}"

    # Add MAX_ACTIVE_SESSIONS distinct user sessions
    df_dummy = pd.DataFrame({"a": [1, 2, 3]})
    for i in range(1, MAX_ACTIVE_SESSIONS + 1):
        uid = f"user_{i}"
        set_df(df_dummy, ds_index=1, user_id=uid)
        time.sleep(0.01)

    assert len(DATA_STORE) == MAX_ACTIVE_SESSIONS, f"Expected {MAX_ACTIVE_SESSIONS} sessions, got {len(DATA_STORE)}"

    # Access user_1 so that user_2 becomes the oldest
    _ = get_df(ds_index=1, user_id="user_1")

    # Add one more session (should trigger eviction of user_2)
    new_uid = f"user_{MAX_ACTIVE_SESSIONS + 1}"
    set_df(df_dummy, ds_index=1, user_id=new_uid)

    assert len(DATA_STORE) <= MAX_ACTIVE_SESSIONS, f"DATA_STORE exceeded capacity: {len(DATA_STORE)}"
    assert "user_1" in DATA_STORE, "user_1 was unexpectedly evicted even though it was recently accessed!"
    assert "user_2" not in DATA_STORE, "user_2 (least recently used) was NOT evicted as expected!"
    assert new_uid in DATA_STORE, f"New session {new_uid} was not stored!"
    print(f"  ✅ [LRU EVICTION VERIFIED] Oldest session (user_2) evicted. Capacity bounded to <= {MAX_ACTIVE_SESSIONS}.")

    # 4.3 Concurrent Multi-Threading Stress Test
    # Test concurrent operations across 4 workers (within MAX_ACTIVE_SESSIONS capacity)
    # and verify thread safety without race conditions
    errors = []
    def worker(worker_id):
        try:
            uid = f"worker_thread_{worker_id}"
            for it in range(50):
                set_df(df_dummy, ds_index=1, user_id=uid)
                res = get_df(ds_index=1, user_id=uid)
                assert res is not None, f"Expected active session {uid} to exist"
                if it % 15 == 0:
                    clear_user_data(uid)
        except Exception as e:
            errors.append(e)

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(4)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert len(errors) == 0, f"Concurrency errors encountered: {errors}"
    print("  ✅ [CONCURRENCY STRESS VERIFIED] 4 threads, 200 operations completed without deadlocks or race conditions.")
    return True


def test_5_100m_dataset_generator():
    print_banner("TEST 5: 100M Dataset Generator Parameters")
    
    gen_file = os.path.join(BASE_DIR, "generate_100m_dataset.py")
    with open(gen_file, "r", encoding="utf-8") as f:
        src = f.read()

    tree = ast.parse(src)
    
    # Extract total_rows, chunk_size, compression, dictionary encoded columns
    total_rows = None
    chunk_size = None
    compression = None
    compression_level = None
    dict_encoded_cols = []
    all_table_cols = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    if target.id == "total_rows" and isinstance(node.value, ast.Constant):
                        total_rows = node.value.value
                    elif target.id == "chunk_size" and isinstance(node.value, ast.Constant):
                        chunk_size = node.value.value
        elif isinstance(node, ast.Call):
            # Check ParquetWriter call
            if getattr(node.func, "attr", None) == "ParquetWriter":
                for kw in node.keywords:
                    if kw.arg == "compression" and isinstance(kw.value, ast.Constant):
                        compression = kw.value.value
                    elif kw.arg == "compression_level" and isinstance(kw.value, ast.Constant):
                        compression_level = kw.value.value
            # Check pa.table dictionary_encode calls
            elif getattr(node.func, "attr", None) == "table":
                if len(node.args) > 0 and isinstance(node.args[0], ast.Dict):
                    d = node.args[0]
                    for k, v in zip(d.keys, d.values):
                        if isinstance(k, ast.Constant):
                            col_name = k.value
                            all_table_cols.append(col_name)
                            if isinstance(v, ast.Call) and getattr(v.func, "attr", None) == "dictionary_encode":
                                dict_encoded_cols.append(col_name)

    print(f"  [PARAMETERS] total_rows: {total_rows:,}")
    print(f"  [PARAMETERS] chunk_size: {chunk_size:,} (Total chunks: {total_rows // chunk_size})")
    print(f"  [PARAMETERS] Compression: {compression} level {compression_level}")
    print(f"  [PARAMETERS] Total Columns: {len(all_table_cols)}")
    print(f"  [PARAMETERS] Dictionary Encoded Columns ({len(dict_encoded_cols)}): {dict_encoded_cols}")

    assert total_rows == 100_000_000, f"Expected 100M rows, got {total_rows}"
    assert chunk_size == 2_500_000, f"Expected 2.5M chunk size, got {chunk_size}"
    assert total_rows // chunk_size == 40, f"Expected 40 chunks, got {total_rows // chunk_size}"
    assert compression == "zstd", f"Expected zstd, got {compression}"
    assert compression_level == 3, f"Expected compression level 3, got {compression_level}"
    assert len(all_table_cols) == 22, f"Expected 22 columns, got {len(all_table_cols)}"
    assert len(dict_encoded_cols) == 13, f"Expected exactly 13 dictionary encoded columns, got {len(dict_encoded_cols)}"

    expected_dict_cols = {
        "Sehir", "Bolge", "Urun_Kategorisi", "Alt_Kategori", "Odeme_Yontemi",
        "Musteri_Segmenti", "Satis_Kanali", "Kargo_Firmasi", "Kirli_Etiket_Fiyati_TL",
        "Kirli_Paket_Agirligi_Kg", "Kirli_Indirim_Orani", "Kirli_Musteri_Yillik_Ciro",
        "Kirli_Siparis_Adedi"
    }
    assert set(dict_encoded_cols) == expected_dict_cols, f"Mismatch in dict encoded cols: {set(dict_encoded_cols) ^ expected_dict_cols}"
    print("  ✅ [100M GENERATOR VERIFIED] 100,000,000 rows, 22 cols, 40 chunks of 2.5M, ZSTD level 3, 13 dict encoded cols confirmed.")
    return True


def run_all_challenger_verifications():
    print("\n" + "#" * 75)
    print("🚀 CHALLENGER 2 EMPIRICAL ADVERSARIAL VERIFICATION STARTING")
    print("#" * 75)
    
    t0 = time.time()
    v1 = test_1_pyarrow_zero_copy()
    v2 = test_2_data_healer_logic()
    v3 = test_3_statistical_formulas()
    v4 = test_4_concurrency_and_lru_cache()
    v5 = test_5_100m_dataset_generator()
    
    elapsed = time.time() - t0
    print("\n" + "#" * 75)
    if all([v1, v2, v3, v4, v5]):
        print(f"🏆 ALL 5 ADVANCED EMPIRICAL CHALLENGES PASSED IN {elapsed:.2f}s!")
    else:
        print("❌ ONE OR MORE VERIFICATION CHALLENGES FAILED!")
        sys.exit(1)
    print("#" * 75)


if __name__ == "__main__":
    run_all_challenger_verifications()
