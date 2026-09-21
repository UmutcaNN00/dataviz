"""
Data Healer Service - Smart anomaly detection, numeric string parsing, and automatic data healing.
"""

import re
import logging
import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


def robust_parse_numeric_string(v):
    """
    Parses textual representations of numbers, currencies, percentages, and written numbers into float.
    Returns None if value cannot be parsed or represents missing/null data ('yok', 'n/a', etc.).
    """
    if v is None or pd.isna(v):
        return None
    if isinstance(v, (int, float, np.number)):
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

    # Strip currency symbols, percentages, and common unit suffixes
    s = re.sub(r'[₺$€£%]', '', s)
    s = re.sub(r'\b(tl|try|usd|eur|adet|kg|gr|km|m|cm|ay|yil|yıl|gün|gun|saat|dakika|dk)\b', '', s)
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
            if len(parts) == 2 and len(parts[1]) == 3 and parts[1] == '000':
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

    # For datasets >15,000 rows, sample 10,000 rows for instant detection
    is_sampled = total_rows > 15000
    if is_sampled:
        sample_size = 10000
        sample_df = df.sample(n=sample_size, random_state=42)
    else:
        sample_df = df
        sample_size = total_rows

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue

        series = sample_df[col]
        parsed_vals = series.apply(robust_parse_numeric_string)
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

    df_copy = df.copy()
    detected_anomalies = detect_column_anomalies(df_copy)

    if target_column == '__all__':
        cols_to_repair = [a['column'] for a in detected_anomalies]
    elif target_column in df_copy.columns:
        cols_to_repair = [target_column]
    else:
        raise ValueError(f"'{target_column}' sütunu veri setinde bulunamadı.")

    if not cols_to_repair:
        return df_copy, []

    for col in cols_to_repair:
        series = df_copy[col]
        parsed = series.apply(robust_parse_numeric_string)

        if repair_mode == 'drop_rows':
            valid_rows = parsed.notna()
            df_copy = df_copy[valid_rows].copy()
            df_copy[col] = parsed[valid_rows].astype(float)
        elif repair_mode == 'fill_zero':
            df_copy[col] = parsed.fillna(0.0).astype(float)
        elif repair_mode == 'fill_mean' or repair_mode == 'smart_heal':
            mean_val = float(parsed.mean()) if pd.notnull(parsed.mean()) else 0.0
            df_copy[col] = parsed.fillna(mean_val).astype(float)
        elif repair_mode == 'fill_median':
            med_val = float(parsed.median()) if pd.notnull(parsed.median()) else 0.0
            df_copy[col] = parsed.fillna(med_val).astype(float)
        elif repair_mode == 'coerce_nan':
            df_copy[col] = parsed.astype(float)
        else:
            mean_val = float(parsed.mean()) if pd.notnull(parsed.mean()) else 0.0
            df_copy[col] = parsed.fillna(mean_val).astype(float)

    return df_copy, cols_to_repair


def clean_missing_data(df, action='drop'):
    """
    Cleans missing data across DataFrame based on action:
    - 'drop': drops rows with any missing values
    - 'fill_mean': fills numerical missing values with mean, categorical with 'Bilinmiyor'
    - 'fill_zero': fills numerical missing values with 0, categorical with 'Bilinmiyor'
    """
    if df is None or df.empty:
        return df

    df_clean = df.copy()
    if action == 'drop':
        df_clean = df_clean.dropna()
    elif action == 'fill_mean':
        num_cols = df_clean.select_dtypes(include=['number']).columns
        means = df_clean[num_cols].mean()
        df_clean[num_cols] = df_clean[num_cols].fillna(means).fillna(0)
        for c in df_clean.select_dtypes(include=['object', 'category']).columns:
            if pd.api.types.is_categorical_dtype(df_clean[c]):
                if 'Bilinmiyor' not in df_clean[c].cat.categories:
                    df_clean[c] = df_clean[c].cat.add_categories(['Bilinmiyor'])
            df_clean[c] = df_clean[c].fillna('Bilinmiyor')
    elif action == 'fill_zero':
        num_cols = df_clean.select_dtypes(include=['number']).columns
        df_clean[num_cols] = df_clean[num_cols].fillna(0)
        for c in df_clean.select_dtypes(include=['object', 'category']).columns:
            if pd.api.types.is_categorical_dtype(df_clean[c]):
                if 'Bilinmiyor' not in df_clean[c].cat.categories:
                    df_clean[c] = df_clean[c].cat.add_categories(['Bilinmiyor'])
            df_clean[c] = df_clean[c].fillna('Bilinmiyor')

    return df_clean
