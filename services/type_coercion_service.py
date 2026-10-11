"""
DataViz - Olasılıksal Tip Kurtarma ve Vektörize Sayı Ayrıştırıcı
Kirli stringler, para birimleri ve semboller içeren sütunları tespit edip gerçek sayısal tipe kurtarır.
"""

from typing import Tuple, List, Dict, Any
import re
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# Yaygın para birimleri, semboller ve geçersiz göstergeler
CLEAN_REGEX = re.compile(r"(?i)[₺$€£¥% ]|\btl\b|\busd\b|\beur\b|\btry\b")
INVALID_TOKENS = {"-", "--", "n/a", "na", "null", "none", "yok", "belirsiz", "nan", "?"}


def recover_dirty_numeric_columns(
    df: pd.DataFrame,
    min_numeric_ratio: float = 0.80,
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Object / String tipinde kalmış ancak çoğunluğu sayısal olan sütunları
    otomatik tespit edip güvenli şekilde sayısal tipe dönüştürür.
    
    Args:
        df: İncelenecek DataFrame
        min_numeric_ratio: Bir sütunun sayısal kabul edilmesi için gereken geçerli sayı oranı (örn: %80)
        
    Returns:
        (recovered_df, recovery_report)
    """
    if df is None or df.empty:
        return df, []

    recovered_df = df.copy(deep=False)
    report = []
    total_rows = len(recovered_df)
    if total_rows == 0:
        return recovered_df, []

    object_cols = recovered_df.select_dtypes(include=["object", "string", "category"]).columns

    for col in object_cols:
        series = recovered_df[col].dropna()
        if len(series) == 0:
            continue

        # 1. Örnekleme veya tam seri analizi (10.000 satırdan büyükse ilk 10.000 satırı incele)
        sample = series.iloc[:10000].astype(str).str.strip().str.lower()

        # Geçersiz boşluk benzeri tokenları temizle
        sample_cleaned = sample.replace(list(INVALID_TOKENS), np.nan).dropna()
        if len(sample_cleaned) == 0:
            continue

        # Para birimi ve sembolleri temizle
        cleaned_str = sample_cleaned.str.replace(CLEAN_REGEX, "", regex=True)

        # Türkiye formatı (1.250,50 -> 1250.50) veya US formatı (1,250.50 -> 1250.50) normalizasyonu
        # Eğer hem nokta hem virgül varsa:
        def _normalize_separators(s: pd.Series) -> pd.Series:
            has_comma = s.str.contains(",", regex=False)
            has_dot = s.str.contains(".", regex=False)

            # Durum A: 1.250,50 (TR/AB formatı) -> noktayı kaldır, virgülü nokta yap
            tr_format = has_comma & has_dot & (s.str.rfind(",") > s.str.rfind("."))
            # Durum B: 1,250.50 (US formatı) -> virgülü kaldır
            us_format = has_comma & has_dot & (s.str.rfind(".") > s.str.rfind(","))
            # Durum C: Sadece virgül var (1250,50) -> virgülü nokta yap
            only_comma = has_comma & ~has_dot

            res = s.copy()
            res.loc[tr_format] = res.loc[tr_format].str.replace(".", "", regex=False).str.replace(",", ".", regex=False)
            res.loc[us_format] = res.loc[us_format].str.replace(",", "", regex=False)
            res.loc[only_comma] = res.loc[only_comma].str.replace(",", ".", regex=False)
            return res

        normalized = _normalize_separators(cleaned_str)

        # Sayıya dönüştürmeyi dene
        parsed_numeric = pd.to_numeric(normalized, errors="coerce")
        valid_numeric_count = int(parsed_numeric.notna().sum())
        ratio = valid_numeric_count / max(1, len(sample_cleaned))

        # Eğer örneklenen verinin %80'den fazlası sayısal ise tüm sütunu kurtar!
        if ratio >= min_numeric_ratio:
            full_series = recovered_df[col].astype(str).str.strip().str.lower()
            full_series_cleaned = full_series.replace(list(INVALID_TOKENS), np.nan)
            full_cleaned_str = full_series_cleaned.str.replace(CLEAN_REGEX, "", regex=True)
            full_normalized = _normalize_separators(full_cleaned_str)

            converted_series = pd.to_numeric(full_normalized, errors="coerce")
            
            # Tam sayı olup olmadığını kontrol et
            is_pure_int = False
            valid_vals = converted_series.dropna()
            if len(valid_vals) > 0 and (valid_vals % 1 == 0).all():
                is_pure_int = True

            if is_pure_int and converted_series.isna().sum() == 0:
                recovered_df[col] = converted_series.astype(np.int64)
                target_type = "int64"
            else:
                recovered_df[col] = converted_series.astype(np.float32)
                target_type = "float32"

            coerced_count = int(converted_series.notna().sum())
            null_count = int(converted_series.isna().sum())

            report.append({
                "column": col,
                "previous_type": "object",
                "recovered_type": target_type,
                "confidence_ratio": round(ratio * 100, 1),
                "recovered_values_count": coerced_count,
                "unparseable_null_count": null_count,
            })

            logger.info(
                f"Sütun '{col}' başarıyla {target_type} tipine kurtarıldı (Güven: %{round(ratio * 100, 1)})"
            )

    return recovered_df, report
