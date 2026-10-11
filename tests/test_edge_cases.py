import sys
sys.stdout.reconfigure(encoding='utf-8')
import pandas as pd
import numpy as np

print("--- Testing _compute_trust_snapshot ---")
from routes.data_routes import _compute_trust_snapshot
test_dfs = [
    ("single_value", pd.DataFrame({'a': [1]})),
    ("single_nan", pd.DataFrame({'a': [np.nan]})),
    ("strings", pd.DataFrame({'a': ['xyz', '123']})),
    ("infinities", pd.DataFrame({'a': [np.inf, -np.inf, np.nan, 10.0]})),
    ("empty", pd.DataFrame()),
    ("no_cols", pd.DataFrame(index=range(5))),
]
for name, df in test_dfs:
    try:
        snap = _compute_trust_snapshot(df)
        print(f"  {name}: OK (overall={snap.get('overall_score')})")
    except Exception as e:
        print(f"  {name}: FAILED with {type(e)}: {e}")

print("\n--- Testing evaluate_data_contracts ---")
from services.data_contracts_service import evaluate_data_contracts
contracts_dfs = [
    ("empty", pd.DataFrame(), None),
    ("single_row", pd.DataFrame({'fiyat': [100], 'adet': [5]}), None),
    ("string_cols", pd.DataFrame({'fiyat_kodu': ['A1', 'B2']}), [{'column': 'fiyat_kodu', 'type': 'non_negative'}]),
    ("range_on_string", pd.DataFrame({'oran_adi': ['x', 'y']}), [{'column': 'oran_adi', 'type': 'range', 'min': 0, 'max': 100}]),
    ("all_nans", pd.DataFrame({'sayi': [np.nan, np.nan]}), None),
    ("dirty_numeric", pd.DataFrame({'sayi': ['10', '20', 'invalid']}), [{'column': 'sayi', 'type': 'non_negative'}]),
]
for name, df, custom in contracts_dfs:
    try:
        res = evaluate_data_contracts(df, custom_contracts=custom)
        print(f"  {name}: OK (grade={res.get('grade')}, score={res.get('compliance_score')})")
    except Exception as e:
        print(f"  {name}: FAILED with {type(e)}: {e}")

print("\n--- Testing detect_ensemble_anomalies ---")
from services.ensemble_anomaly_service import detect_ensemble_anomalies
anom_dfs = [
    ("empty", pd.DataFrame()),
    ("1_row_2_cols", pd.DataFrame({'a': [1.0], 'b': [2.0]})),
    ("1_row_1_col", pd.DataFrame({'a': [1.0]})),
    ("5_rows_1_col", pd.DataFrame({'a': [1.0, 2.0, 3.0, 100.0, 2.0]})),
    ("no_numeric", pd.DataFrame({'a': ['x', 'y', 'z'], 'b': ['u', 'v', 'w']})),
    ("all_nan", pd.DataFrame({'a': [np.nan, np.nan], 'b': [np.nan, np.nan]})),
]
for name, df in anom_dfs:
    try:
        res = detect_ensemble_anomalies(df)
        print(f"  {name}: OK (consensus={res.get('total_consensus_anomalies')}, err={res.get('error')})")
    except Exception as e:
        print(f"  {name}: FAILED with {type(e)}: {e}")

print("\n--- Testing explain_dataset_anomalies ---")
from services.anomaly_explainer import explain_dataset_anomalies
expl_dfs = [
    ("empty", pd.DataFrame()),
    ("1_row", pd.DataFrame({'a': [1.0], 'b': [2.0]})),
    ("3_rows", pd.DataFrame({'a': [1.0, 2.0, 3.0], 'b': [2.0, 3.0, 4.0]})),
    ("1_col", pd.DataFrame({'a': [1.0, 2.0, 3.0, 4.0, 50.0]})),
    ("no_numeric", pd.DataFrame({'a': ['x', 'y', 'z']})),
]
for name, df in expl_dfs:
    try:
        res = explain_dataset_anomalies(df)
        print(f"  {name}: OK (rows_count={len(res.get('explained_rows', []))}, has_explained_rows={'explained_rows' in res})")
    except Exception as e:
        print(f"  {name}: FAILED with {type(e)}: {e}")

print("\n--- Testing execute_predicate_pushdown ---")
from services.predicate_pushdown_engine import execute_predicate_pushdown
push_dfs = [
    ("empty", pd.DataFrame(), []),
    ("invalid_col", pd.DataFrame({'a': [1, 2]}), [{'column': 'nonexistent', 'op': '==', 'value': 1}]),
    ("invalid_op", pd.DataFrame({'a': [1, 2]}), [{'column': 'a', 'op': 'UNKNOWN_OP', 'value': 1}]),
    ("type_mismatch_str_greater", pd.DataFrame({'a': ['x', 'y']}), [{'column': 'a', 'op': '>', 'value': 5}]),
    ("type_mismatch_num_contains", pd.DataFrame({'a': [10, 20]}), [{'column': 'a', 'op': 'contains', 'value': '1'}]),
    ("invalid_float_val", pd.DataFrame({'a': [10, 20]}), [{'column': 'a', 'op': '>', 'value': 'not_a_number'}]),
    ("none_val", pd.DataFrame({'a': [10, 20]}), [{'column': 'a', 'op': '>', 'value': None}]),
]
for name, df, preds in push_dfs:
    try:
        res = execute_predicate_pushdown(df, preds)
        print(f"  {name}: OK (matched={res.get('matched_rows')}, err={res.get('error')})")
    except Exception as e:
        print(f"  {name}: FAILED with {type(e)}: {e}")
