"""
Data Healer Service - Smart anomaly detection, numeric string parsing, and automatic data healing.
"""

import re
import logging
import pandas as pd
import numpy as np
from core.config import ANOMALY_SAMPLE_THRESHOLD, ANOMALY_SAMPLE_SIZE

logger = logging.getLogger(__name__)


def robust_parse_numeric_string(v):
    """
    Parses textual representations of numbers, currencies, percentages, and written numbers into float.
    Returns None if value cannot be parsed or represents missing/null data ('yok', 'n/a', etc.).
    """
    if v is None or pd.isna(v):
        return None
    if isinstance(v, (int, float, np.number)) and not isinstance(v, bool):
        return float(v) if np.isfinite(v) else None

    s = str(v).strip().lower()
    if s in [
        'yok', 'n/a', 'nan', 'null', 'none', 'bilinmiyor', 'belirtilmedi',
        'tanımsız', 'tbd', '-', '', 'bilgi yok', 'kayıp', 'iptal', 'hata'
    ]:
        return None
    if s in ['sıfır', 'sifir', 'zero']:
        return 0.0
    if s in ['bir', 'one']:
        return 1.0

    # Date formats (2024-01-15, 15/01/2024, 15.01.2024 etc.) should not be treated as numbers
    if re.search(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}$', s) or re.search(r'^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$', s):
        return None

    # Strip currency symbols, percentages, and common unit suffixes (even when attached to digits like '100tl' or '50kg')
    s = re.sub(r'[₺$€£%]', '', s)
    s = re.sub(r'(?:^|(?<=[\d\s.,]))(tl|try|usd|eur|adet|kg|gr|km|m|cm|ay|yil|yıl|gün|gun|saat|dakika|dk)\b', '', s)
    s = s.strip()

    if not re.search(r'\d', s):
        return None

    # Comma and dot delimiter analysis
    if '.' in s and ',' in s:
        if s.rfind(',') > s.rfind('.'):  # European / Turkish: 1.250,50
            s = s.replace('.', '').replace(',', '.')
        else:  # US format: 1,250.50
            s = s.replace(',', '')
    elif '.' in s:
        if s.count('.') > 1:
            s = s.replace('.', '')
        else:
            parts = s.split('.')
            # In Turkish format, a dot followed by exactly 3 digits (e.g. 1.250 or 15.000) is a thousand separator
            if len(parts) == 2 and len(parts[1]) == 3 and parts[0].lstrip('-+').isdigit() and parts[0].lstrip('-+') != '0':
                s = s.replace('.', '')
    elif ',' in s:
        if s.count(',') > 1:
            s = s.replace(',', '')
        else:
            parts = s.split(',')
            if len(parts) == 2 and len(parts[1]) == 3 and parts[1] == '000':
                s = s.replace(',', '')
            else:
                s = s.replace(',', '.')

    s = re.sub(r'\s+', '', s)
    try:
        f = float(s)
        return f if np.isfinite(f) else None
    except Exception:
        return None


def detect_column_anomalies(df):
    """
    Scans columns in a DataFrame; detects columns that appear to be textual but contain
    underlying numeric data (type mismatch / anomalies).
    Uses smart sampling (>15,000 rows) for sub-second anomaly detection on massive datasets.
    """
    if df is None:
        return []
    if hasattr(df, 'empty') and df.empty:
        return []
    if hasattr(df, 'is_empty') and df.is_empty():
        return []
    if len(df) == 0:
        return []

    anomalies = []
    total_rows = len(df)

    # For datasets >ANOMALY_SAMPLE_THRESHOLD rows, sample ANOMALY_SAMPLE_SIZE rows for instant detection
    is_sampled = total_rows > ANOMALY_SAMPLE_THRESHOLD
    if is_sampled:
        sample_size = min(ANOMALY_SAMPLE_SIZE, total_rows)
        sample_df = df.sample(n=sample_size, random_state=42)
    else:
        sample_df = df
        sample_size = total_rows

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue

        series = sample_df[col]
        if isinstance(series.dtype, pd.CategoricalDtype):
            series = series.astype(object)
        parsed_vals = pd.to_numeric(series.apply(robust_parse_numeric_string), errors='coerce')
        sample_valid_numeric_count = int(parsed_vals.notna().sum())

        # If at least 2 numbers and >=15% parseable as numeric, but contains text anomalies
        if sample_valid_numeric_count >= 2 and (sample_valid_numeric_count / sample_size) >= 0.15:
            invalid_mask = parsed_vals.isna() & series.notna() & (series.astype(str).str.strip() != '')
            sample_invalid_count = int(invalid_mask.sum())
            if sample_invalid_count > 0:
                raw_invalid = series[invalid_mask].dropna().unique()
                sample_invalids = [str(x).strip() for x in raw_invalid if str(x).strip()][:8]

                if is_sampled:
                    scale = total_rows / sample_size
                    valid_numeric_count = int(sample_valid_numeric_count * scale)
                    invalid_count = int(sample_invalid_count * scale)
                else:
                    valid_numeric_count = sample_valid_numeric_count
                    invalid_count = sample_invalid_count

                anomalies.append({
                    'column': col,
                    'total_rows': total_rows,
                    'numeric_count': valid_numeric_count,
                    'invalid_count': invalid_count,
                    'invalid_pct': round((sample_invalid_count / sample_size) * 100, 1),
                    'sample_invalid_values': sample_invalids,
                    'suggested_action': 'smart_heal'
                })

    return anomalies


def _parse_series_fast(series, use_float32=False):
    """
    Vectorized / Category-aware numeric string parser.
    For CategoricalDtype columns (e.g. 100M rows with dictionary encoding), parses only unique categories
    and maps codes in C/NumPy (~1000x faster and 10x less RAM).
    """
    target_dtype = np.float32 if use_float32 else np.float64
    if isinstance(series.dtype, pd.CategoricalDtype):
        cats = pd.Series(series.cat.categories, dtype=object)
        cat_parsed = pd.to_numeric(cats.apply(robust_parse_numeric_string), errors='coerce').to_numpy(dtype=target_dtype)
        codes = series.cat.codes.to_numpy()
        out = np.full(len(series), np.nan, dtype=target_dtype)
        valid_code_mask = codes >= 0
        out[valid_code_mask] = cat_parsed[codes[valid_code_mask]]
        return pd.Series(out, index=series.index, dtype=target_dtype)
    parsed = pd.to_numeric(series.apply(robust_parse_numeric_string), errors='coerce')
    return parsed.astype(target_dtype)


def repair_column_data(df, target_column='__all__', repair_mode='smart_heal'):
    """
    Repairs column anomalies in a DataFrame.
    
    Modes:
    - 'smart_heal' / 'fill_mean': replaces invalid values with column mean
    - 'fill_zero': replaces invalid values with 0.0
    - 'fill_median': replaces invalid values with column median
    - 'coerce_nan': coerces invalid values to NaN
    - 'drop_rows': removes rows with unparseable values
    
    Returns:
        tuple (repaired_df, list_of_repaired_columns)
    """
    if df is None or df.empty:
        return df, []

    is_massive = len(df) > 1_000_000
    df_copy = df.copy(deep=not is_massive)
    detected_anomalies = detect_column_anomalies(df_copy)

    if target_column == '__all__':
        cols_to_repair = [a['column'] for a in detected_anomalies]
    elif target_column in df_copy.columns:
        cols_to_repair = [target_column]
    else:
        raise ValueError(f"'{target_column}' sütunu veri setinde bulunamadı.")

    if not cols_to_repair:
        return df_copy, []

    target_float = np.float32 if is_massive else float

    for col in cols_to_repair:
        series = df_copy[col]
        parsed = _parse_series_fast(series, use_float32=is_massive)

        if repair_mode == 'drop_rows':
            valid_rows = parsed.notna()
            df_copy = df_copy[valid_rows].copy()
            df_copy[col] = parsed[valid_rows].astype(target_float)
            df_copy = df_copy.reset_index(drop=True)
        elif repair_mode == 'fill_zero':
            df_copy[col] = parsed.fillna(0.0).astype(target_float)
        elif repair_mode == 'fill_mean' or repair_mode == 'smart_heal':
            mean_val = float(parsed.mean()) if pd.notnull(parsed.mean()) else 0.0
            df_copy[col] = parsed.fillna(target_float(mean_val)).astype(target_float)
        elif repair_mode == 'fill_median':
            med_val = float(parsed.median()) if pd.notnull(parsed.median()) else 0.0
            df_copy[col] = parsed.fillna(target_float(med_val)).astype(target_float)
        elif repair_mode == 'coerce_nan':
            df_copy[col] = parsed.astype(target_float)
        else:
            mean_val = float(parsed.mean()) if pd.notnull(parsed.mean()) else 0.0
            df_copy[col] = parsed.fillna(target_float(mean_val)).astype(target_float)

    return df_copy, cols_to_repair


def _fill_categorical_columns(df_clean, fill_label='Bilinmiyor'):
    for c in df_clean.select_dtypes(include=['object', 'category', 'string']).columns:
        if df_clean[c].isna().any():
            if isinstance(df_clean[c].dtype, pd.CategoricalDtype):
                if fill_label not in df_clean[c].cat.categories:
                    df_clean[c] = df_clean[c].cat.add_categories([fill_label])
            df_clean[c] = df_clean[c].fillna(fill_label)


def clean_missing_data(df, action='drop'):
    """
    Cleans missing data across DataFrame based on action:
    - 'drop': drops rows with any missing values
    - 'fill_mean' / 'mean': fills numerical missing values with mean, categorical with 'Bilinmiyor'
    - 'fill_median' / 'median': fills numerical missing values with median, categorical with 'Bilinmiyor'
    - 'fill_zero' / 'zero': fills numerical missing values with 0, categorical with 'Bilinmiyor'
    """
    if df is None or df.empty:
        return df

    is_massive = len(df) > 1_000_000
    df_clean = df.copy(deep=not is_massive)
    if action == 'drop':
        df_clean = df_clean.dropna().reset_index(drop=True)
    elif action in ('fill_mean', 'mean'):
        num_cols = df_clean.select_dtypes(include=['number']).columns
        for c in num_cols:
            if df_clean[c].isna().any():
                m_val = df_clean[c].mean()
                fill_v = 0.0 if pd.isna(m_val) else m_val
                df_clean[c] = df_clean[c].fillna(fill_v)
        _fill_categorical_columns(df_clean)
    elif action in ('fill_median', 'median'):
        num_cols = df_clean.select_dtypes(include=['number']).columns
        for c in num_cols:
            if df_clean[c].isna().any():
                med_val = df_clean[c].iloc[:500_000].median() if is_massive else df_clean[c].median()
                fill_v = 0.0 if pd.isna(med_val) else med_val
                df_clean[c] = df_clean[c].fillna(fill_v)
        _fill_categorical_columns(df_clean)
    elif action in ('fill_zero', 'zero'):
        num_cols = df_clean.select_dtypes(include=['number']).columns
        for c in num_cols:
            if df_clean[c].isna().any():
                df_clean[c] = df_clean[c].fillna(0)
        _fill_categorical_columns(df_clean)

    return df_clean

