"""
Data Healer Service - Smart anomaly detection, numeric string parsing, and automatic data healing.
"""

import logging
import re
from typing import Any

import numpy as np
import pandas as pd

# isort: split
from core.config import ANOMALY_SAMPLE_SIZE, ANOMALY_SAMPLE_THRESHOLD

logger = logging.getLogger(__name__)


def robust_parse_numeric_string(v: Any) -> float | None:
    """
    Parses textual representations of numbers, currencies, percentages, and written numbers into float.
    Returns None if value cannot be parsed or represents missing/null data ('yok', 'boş', 'n/a', etc.).
    """
    if v is None or pd.isna(v):
        return None
    if isinstance(v, (int, float, np.number)) and not isinstance(v, bool):
        return float(v) if np.isfinite(v) else None

    s = str(v).strip().lower()
    if s in [
        "yok",
        "boş",
        "bos",
        "eksik",
        "belirsiz",
        "n/a",
        "nan",
        "null",
        "none",
        "bilinmiyor",
        "belirtilmedi",
        "tanımsız",
        "tbd",
        "-",
        "",
        "bilgi yok",
        "kayıp",
        "iptal",
        "hata",
    ]:
        return None
    if s in ["sıfır", "sifir", "zero"]:
        return 0.0
    if s in ["bir", "one"]:
        return 1.0

    # Date formats (2024-01-15, 15/01/2024, 15.01.2024 etc.) should not be treated as numbers
    if re.search(r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}$", s) or re.search(
        r"^\d{1,2}[./-]\d{1,2}[./-]\d{2,4}$", s
    ):
        return None

    # Strip currency symbols, percentages, and common unit suffixes (including lt, ml, l, ton, paket, etc.)
    s = re.sub(r"[₺$€£%]", "", s)
    s = re.sub(
        r"(?:^|(?<=[\d\s.,]))(tl|try|usd|eur|adet|kg|gr|mg|ton|lt|ml|l|km|m|cm|mm|ay|yil|yıl|gün|gun|saat|dakika|dk|sn|saniye|puan|kisi|kişi|paket|koli|kutu|birim)\b",
        "",
        s,
    )
    s = s.strip()

    if not re.search(r"\d", s):
        return None

    # Comma and dot delimiter analysis
    if "." in s and "," in s:
        if s.rfind(",") > s.rfind("."):  # European / Turkish: 1.250,50
            s = s.replace(".", "").replace(",", ".")
        else:  # US format: 1,250.50
            s = s.replace(",", "")
    elif "." in s:
        if s.count(".") > 1:
            s = s.replace(".", "")
        else:
            parts = s.split(".")
            # In Turkish format, a dot followed by exactly 3 digits (e.g. 1.250 or 15.000) is a thousand separator
            if (
                len(parts) == 2
                and len(parts[1]) == 3
                and parts[0].lstrip("-+").isdigit()
                and parts[0].lstrip("-+") != "0"
            ):
                s = s.replace(".", "")
    elif "," in s:
        if s.count(",") > 1:
            s = s.replace(",", "")
        else:
            parts = s.split(",")
            if len(parts) == 2 and len(parts[1]) == 3 and parts[1] == "000":
                s = s.replace(",", "")
            else:
                s = s.replace(",", ".")

    s = re.sub(r"\s+", "", s)
    try:
        f = float(s)
        return f if np.isfinite(f) else None
    except ValueError:
        return None


def detect_column_anomalies(df: pd.DataFrame | None) -> list[dict[str, Any]]:
    """
    Scans columns in a DataFrame; detects columns that appear to be textual but contain
    underlying numeric data (type mismatch / anomalies).
    Uses smart sampling (>15,000 rows) for sub-second anomaly detection on massive datasets.
    """
    if df is None or df.empty or len(df) == 0:
        return []

    anomalies: list[dict[str, Any]] = []
    total_rows = len(df)

    # For datasets >ANOMALY_SAMPLE_THRESHOLD rows, sample ANOMALY_SAMPLE_SIZE rows for instant detection
    is_sampled = total_rows > ANOMALY_SAMPLE_THRESHOLD
    if is_sampled:
        sample_size = min(ANOMALY_SAMPLE_SIZE, total_rows)
        sample_df = df.iloc[:sample_size]
    else:
        sample_df = df
        sample_size = total_rows

    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df[col]):
            continue

        series = sample_df[col]
        if isinstance(series.dtype, pd.CategoricalDtype):
            series = series.astype(object)
        parsed_vals = pd.to_numeric(
            series.apply(robust_parse_numeric_string), errors="coerce"
        )
        sample_valid_numeric_count = int(parsed_vals.notna().sum())

        # If at least 2 numbers and >=15% parseable as numeric, but contains text anomalies
        if (
            sample_valid_numeric_count >= 2
            and (sample_valid_numeric_count / sample_size) >= 0.15
        ):
            invalid_mask = (
                parsed_vals.isna()
                & series.notna()
                & (series.astype(str).str.strip() != "")
            )
            sample_invalid_count = int(invalid_mask.sum())
            if sample_invalid_count > 0:
                raw_invalid = series[invalid_mask].dropna().unique()
                sample_invalids = [
                    str(x).strip() for x in raw_invalid if str(x).strip()
                ][:8]

                if is_sampled:
                    scale = total_rows / sample_size
                    valid_numeric_count = int(sample_valid_numeric_count * scale)
                    invalid_count = int(sample_invalid_count * scale)
                else:
                    valid_numeric_count = sample_valid_numeric_count
                    invalid_count = sample_invalid_count

                anomalies.append(
                    {
                        "column": col,
                        "total_rows": total_rows,
                        "numeric_count": valid_numeric_count,
                        "invalid_count": invalid_count,
                        "invalid_pct": round(
                            (sample_invalid_count / sample_size) * 100, 1
                        ),
                        "sample_invalid_values": sample_invalids,
                        "suggested_action": "smart_heal",
                    }
                )

    return anomalies


def _parse_series_fast(
    series: pd.Series,
    use_float32: bool = False,
    fill_mode: str | None = None,
) -> pd.Series:
    """
    Vectorized / Category-aware numeric string parser and optional in-place filler.
    For CategoricalDtype columns (e.g. 100M rows with dictionary encoding), parses only unique categories,
    computes the fill value on unique categories/sample, and maps codes in C/NumPy in a single pass.
    """
    target_dtype = np.float32 if use_float32 else np.float64
    if isinstance(series.dtype, pd.CategoricalDtype):
        cats = pd.Series(series.cat.categories, dtype=object)
        cat_parsed = pd.to_numeric(
            cats.apply(robust_parse_numeric_string), errors="coerce"
        ).to_numpy(dtype=target_dtype)

        fill_val = np.nan
        if fill_mode in ("fill_zero",):
            fill_val = target_dtype(0.0)
        elif fill_mode in ("fill_mean", "smart_heal"):
            valid_cats = cat_parsed[np.isfinite(cat_parsed)]
            fill_val = (
                target_dtype(np.mean(valid_cats))
                if len(valid_cats) > 0
                else target_dtype(0.0)
            )
        elif fill_mode in ("fill_median",):
            valid_cats = cat_parsed[np.isfinite(cat_parsed)]
            fill_val = (
                target_dtype(np.median(valid_cats))
                if len(valid_cats) > 0
                else target_dtype(0.0)
            )

        if not np.isnan(fill_val):
            cat_parsed = np.where(np.isfinite(cat_parsed), cat_parsed, fill_val)

        codes = series.cat.codes.to_numpy()
        if not np.isnan(fill_val):
            # Append fill_val at the end of lookup table so code -1 (missing) maps directly to fill_val
            lookup = np.empty(len(cat_parsed) + 1, dtype=target_dtype)
            lookup[:-1] = cat_parsed
            lookup[-1] = fill_val
            safe_codes = np.where(codes >= 0, codes, len(cat_parsed))
            out = lookup[safe_codes]
        else:
            out = np.full(len(series), np.nan, dtype=target_dtype)
            valid_code_mask = codes >= 0
            out[valid_code_mask] = cat_parsed[codes[valid_code_mask]]

        return pd.Series(out, index=series.index, dtype=target_dtype)

    parsed = pd.to_numeric(
        series.apply(robust_parse_numeric_string), errors="coerce"
    ).astype(target_dtype)
    if fill_mode == "fill_zero":
        return parsed.fillna(target_dtype(0.0))
    if fill_mode in ("fill_mean", "smart_heal"):
        m_val = parsed.mean()
        return parsed.fillna(target_dtype(float(m_val) if pd.notnull(m_val) else 0.0))
    if fill_mode == "fill_median":
        med_val = parsed.median()
        return parsed.fillna(
            target_dtype(float(med_val) if pd.notnull(med_val) else 0.0)
        )
    return parsed


def repair_column_data(
    df: pd.DataFrame | None,
    target_column: str = "__all__",
    repair_mode: str = "smart_heal",
) -> tuple[pd.DataFrame, list[str]]:
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
    if df is None:
        return pd.DataFrame(), []
    if df.empty:
        return df, []

    is_massive = len(df) > 1_000_000
    df_copy = df.copy(deep=not is_massive)

    if target_column == "__all__":
        detected_anomalies = detect_column_anomalies(df_copy)
        cols_to_repair = [str(a["column"]) for a in detected_anomalies]
    elif target_column in df_copy.columns:
        cols_to_repair = [target_column]
    else:
        raise ValueError(f"'{target_column}' sütunu veri setinde bulunamadı.")

    if not cols_to_repair:
        return df_copy, []

    target_float = np.float32 if is_massive else float

    for col in cols_to_repair:
        series = df_copy[col]
        if repair_mode == "drop_rows":
            parsed = _parse_series_fast(series, use_float32=is_massive, fill_mode=None)
            valid_rows = parsed.notna()
            df_copy = df_copy[valid_rows].copy(deep=not is_massive)
            df_copy[col] = parsed[valid_rows].astype(target_float)
            df_copy = df_copy.reset_index(drop=True)
        elif repair_mode == "coerce_nan":
            df_copy[col] = _parse_series_fast(
                series, use_float32=is_massive, fill_mode=None
            )
        else:
            effective_mode = (
                repair_mode
                if repair_mode
                in ("fill_zero", "fill_mean", "smart_heal", "fill_median")
                else "smart_heal"
            )
            df_copy[col] = _parse_series_fast(
                series, use_float32=is_massive, fill_mode=effective_mode
            )

    return df_copy, cols_to_repair


def _fill_categorical_columns(
    df_clean: pd.DataFrame, fill_label: str = "Bilinmiyor", is_massive: bool = False
) -> None:
    for c in df_clean.select_dtypes(include=["object", "category", "string"]).columns:
        col_s = df_clean[c]
        has_na = (
            bool(col_s.iloc[:100_000].isna().any() or col_s.isna().any())
            if not is_massive
            else bool(col_s.isna().any())
        )
        if has_na:
            if (
                isinstance(col_s.dtype, pd.CategoricalDtype)
                and fill_label not in col_s.cat.categories
            ):
                col_s = col_s.cat.add_categories([fill_label])
            df_clean[c] = col_s.fillna(fill_label)


def clean_missing_data(df: pd.DataFrame | None, action: str = "drop") -> pd.DataFrame:
    """
    Cleans missing data across DataFrame based on action:
    - 'drop': drops rows with any missing values
    - 'fill_mean' / 'mean': fills numerical missing values with mean, categorical with 'Bilinmiyor'
    - 'fill_median' / 'median': fills numerical missing values with median, categorical with 'Bilinmiyor'
    - 'fill_zero' / 'zero': fills numerical missing values with 0, categorical with 'Bilinmiyor'
    """
    if df is None:
        return pd.DataFrame()
    if df.empty:
        return df

    is_massive = len(df) > 1_000_000
    df_clean = df.copy(deep=not is_massive)
    if action == "drop":
        df_clean = df_clean.dropna().reset_index(drop=True)
    elif action in ("fill_mean", "mean"):
        num_cols = df_clean.select_dtypes(include=["number"]).columns
        for c in num_cols:
            col_s = df_clean[c]
            if col_s.isna().any():
                m_val = col_s.iloc[:250_000].mean() if is_massive else col_s.mean()
                fill_v = 0.0 if pd.isna(m_val) else float(m_val)
                df_clean[c] = col_s.fillna(
                    np.float32(fill_v) if col_s.dtype == np.float32 else fill_v
                )
        _fill_categorical_columns(df_clean, is_massive=is_massive)
    elif action in ("fill_median", "median"):
        num_cols = df_clean.select_dtypes(include=["number"]).columns
        for c in num_cols:
            col_s = df_clean[c]
            if col_s.isna().any():
                med_val = (
                    col_s.iloc[:250_000].median() if is_massive else col_s.median()
                )
                fill_v = 0.0 if pd.isna(med_val) else float(med_val)
                df_clean[c] = col_s.fillna(
                    np.float32(fill_v) if col_s.dtype == np.float32 else fill_v
                )
        _fill_categorical_columns(df_clean, is_massive=is_massive)
    elif action in ("fill_zero", "zero"):
        num_cols = df_clean.select_dtypes(include=["number"]).columns
        for c in num_cols:
            col_s = df_clean[c]
            if col_s.isna().any():
                df_clean[c] = col_s.fillna(
                    np.float32(0.0) if col_s.dtype == np.float32 else 0
                )
        _fill_categorical_columns(df_clean, is_massive=is_massive)

    return df_clean
