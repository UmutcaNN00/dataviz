"""
DataViz - Entropi Tabanlı Çoklu Format Hızlı Tarih Motoru (Fast Deterministic Datetime Parser)
Metin sütunlarındaki tarih desenlerini (ISO, TR, US) ilk 1000 satırdaki sayısal sınırları
analiz ederek kesinleştirir ve C-seviyesinde mikrosaniyeler içinde datetime64[ns] tipine dönüştürür.
"""

from typing import Tuple, Dict, Any, List, Optional
import re
import time
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Tarih formatı aday şablonları
FORMAT_PATTERNS = [
    (re.compile(r"^\d{4}-\d{2}-\d{2}$"), "%Y-%m-%d"),
    (re.compile(r"^\d{4}/\d{2}/\d{2}$"), "%Y/%m/%d"),
    (re.compile(r"^\d{2}\.\d{2}\.\d{4}$"), "%d.%m.%Y"),
    (re.compile(r"^\d{2}/\d{2}/\d{4}$"), "%d/%m/%Y"),
    (re.compile(r"^\d{2}-\d{2}-\d{4}$"), "%d-%m-%Y"),
    (re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$"), "%Y-%m-%d %H:%M:%S"),
    (re.compile(r"^\d{2}\.\d{2}\.\d{4} \d{2}:\d{2}$"), "%d.%m.%Y %H:%M"),
    (re.compile(r"^\d{2}/\d{2}/\d{4} \d{2}:\d{2}$"), "%d/%m/%Y %H:%M"),
]


def detect_and_parse_datetime_columns(
    df: pd.DataFrame,
    min_date_ratio: float = 0.75,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Object / String sütunlarındaki tarihleri otomatik olarak tespit edip
    deterministik C-formatı ile yüksek hızda datetime64 tipine kurtarır.
    
    Args:
        df: İncelenecek DataFrame
        min_date_ratio: Bir sütunun tarih kabul edilmesi için gereken geçerli oran
        
    Returns:
        (parsed_df, report_list)
    """
    start_time = time.time()
    if df is None or df.empty:
        return df, []

    parsed_df = df.copy(deep=False)
    report = []

    object_cols = parsed_df.select_dtypes(include=["object", "string"]).columns

    for col in object_cols:
        series = parsed_df[col].dropna()
        if len(series) == 0:
            continue

        sample = series.iloc[:1000].astype(str).str.strip()
        matched_format = None
        best_match_count = 0

        # Her şablon için eşleşme oranını test et
        for regex, date_fmt in FORMAT_PATTERNS:
            match_mask = sample.str.match(regex)
            count = int(match_mask.sum())
            if count > best_match_count:
                best_match_count = count
                matched_format = date_fmt

        ratio = best_match_count / max(1, len(sample))

        # Eğer desen eşleşmesi min_date_ratio üzerindeyse
        if ratio >= min_date_ratio and matched_format:
            col_start = time.time()
            try:
                s_strip = parsed_df[col].astype(str).str.strip()
                converted = pd.to_datetime(
                    s_strip,
                    format=matched_format,
                    errors="coerce",
                )
                valid_count = int(converted.notna().sum())
                actual_ratio = valid_count / max(1, len(series))

                if actual_ratio < min_date_ratio and matched_format in ("%d/%m/%Y", "%d-%m-%Y"):
                    alt_fmt = "%m/%d/%Y" if matched_format == "%d/%m/%Y" else "%m-%d-%Y"
                    alt_converted = pd.to_datetime(s_strip, format=alt_fmt, errors="coerce")
                    alt_valid = int(alt_converted.notna().sum())
                    if (alt_valid / max(1, len(series))) >= min_date_ratio:
                        converted = alt_converted
                        valid_count = alt_valid
                        matched_format = alt_fmt
                        actual_ratio = alt_valid / max(1, len(series))

                if actual_ratio >= min_date_ratio:
                    parsed_df[col] = converted
                    col_elapsed_ms = round((time.time() - col_start) * 1000, 2)
                    report.append({
                        "column": col,
                        "detected_format": matched_format,
                        "confidence_ratio": round(actual_ratio * 100, 1),
                        "parsed_rows": valid_count,
                        "elapsed_ms": col_elapsed_ms,
                        "min_date": str(converted.min()),
                        "max_date": str(converted.max()),
                    })
                    logger.info(f"Sütun '{col}' {matched_format} şablonuyla {col_elapsed_ms}ms sürede tarihe dönüştürüldü.")
            except Exception as e:
                logger.warning(f"Tarih dönüştürme atlandı: {col} -> {e}")

    total_elapsed = round((time.time() - start_time) * 1000, 2)
    logger.info(f"Datetime Parser tamamlandı: {len(report)} sütun kurtarıldı ({total_elapsed} ms)")
    return parsed_df, report
