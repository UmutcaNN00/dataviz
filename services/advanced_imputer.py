"""
DataViz - Çok Değişkenli Akıllı Veri Doldurucu (Advanced Imputation)
MICE (Iterative Imputer / Chained Equations) ve KNN Imputer ile
sütunlar arası korelasyonu ve gerçekçiliği koruyarak eksik verileri doldurur.
"""

from typing import Tuple, Dict, Any, List, Optional
import numpy as np
import pandas as pd
import logging

# Scikit-learn IterativeImputer etkinleştirme
from sklearn.experimental import enable_iterative_imputer  # noqa: F401
from sklearn.impute import IterativeImputer, KNNImputer

logger = logging.getLogger(__name__)


def impute_missing_advanced(
    df: pd.DataFrame,
    method: str = "mice",
    max_iter: int = 10,
    n_neighbors: int = 5,
    target_columns: Optional[List[str]] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Eksik verileri çok değişkenli istatistiksel modellerle doldurur.
    
    Args:
        df: Eksik değer içeren DataFrame
        method: 'mice' (Iterative Chained Equations) veya 'knn' (K-En Yakın Komşu)
        max_iter: MICE için maksimum iterasyon
        n_neighbors: KNN için komşu sayısı
        target_columns: Sadece seçili sütunları doldur (None ise tüm sayısal ve eksik içeren sütunlar)
        
    Returns:
        (imputed_df, report)
    """
    if df is None or df.empty:
        return df, {"error": "Boş DataFrame"}

    imputed_df = df.copy(deep=True)
    all_numeric_cols = imputed_df.select_dtypes(include=[np.number]).columns.tolist()
    all_cat_cols = imputed_df.select_dtypes(include=["object", "category", "string"]).columns.tolist()

    if target_columns:
        numeric_cols = [c for c in all_numeric_cols if c in target_columns]
        cat_cols = [c for c in all_cat_cols if c in target_columns]
    else:
        numeric_cols = all_numeric_cols
        cat_cols = all_cat_cols

    if not numeric_cols and not cat_cols:
        return imputed_df, {"error": "Doldurulacak sayısal veya kategorik sütun bulunamadı."}

    # Eksik değer içeren sayısal sütunlar
    cols_with_missing_num = [c for c in numeric_cols if imputed_df[c].isna().sum() > 0]
    num_missing_before = int(imputed_df[cols_with_missing_num].isna().sum().sum()) if cols_with_missing_num else 0

    # Eksik değer içeren kategorik sütunlar
    cols_with_missing_cat = [c for c in cat_cols if imputed_df[c].isna().sum() > 0]
    cat_missing_before = int(imputed_df[cols_with_missing_cat].isna().sum().sum()) if cols_with_missing_cat else 0

    if num_missing_before == 0 and cat_missing_before == 0:
        return imputed_df, {
            "success": True,
            "message": "Seçili sütunlarda eksik değer bulunamadı.",
            "total_imputed": 0,
            "total_numeric_imputed": 0,
            "total_categorical_imputed": 0,
            "method": method.upper(),
        }

    try:
        # 1. Sayısal sütunların çok değişkenli (MICE / KNN) doldurulması
        if numeric_cols and num_missing_before > 0:
            # Sayısal sütunları float64 formatına güvenle çekip sonsuz değerleri temizle
            imputed_df[numeric_cols] = imputed_df[numeric_cols].replace([np.inf, -np.inf], np.nan).astype(np.float64)
            all_nan_cols = [c for c in numeric_cols if imputed_df[c].isna().all()]
            for c in all_nan_cols:
                imputed_df[c] = 0.0

            remaining_missing = [c for c in numeric_cols if imputed_df[c].isna().sum() > 0]
            if remaining_missing:
                safe_n_samples = len(imputed_df)
                safe_k = max(1, min(n_neighbors, safe_n_samples))

                if method.lower() == "knn":
                    imputer = KNNImputer(n_neighbors=safe_k, keep_empty_features=True)
                else:
                    imputer = IterativeImputer(
                        max_iter=max_iter,
                        random_state=42,
                        initial_strategy="median",
                        skip_complete=False,
                        keep_empty_features=True,
                    )

                if safe_n_samples > 20000:
                    sample_size = min(10000, safe_n_samples)
                    sample_df = imputed_df[numeric_cols].sample(n=sample_size, random_state=42)
                    imputer.fit(sample_df)
                    filled_array = imputer.transform(imputed_df[numeric_cols])
                else:
                    filled_array = imputer.fit_transform(imputed_df[numeric_cols])

                if filled_array.shape[1] == len(numeric_cols):
                    imputed_df[numeric_cols] = filled_array
                else:
                    # Sütun boyutu uyuşmazlığı durumunda güvenli tek tek atama
                    for idx, c in enumerate(numeric_cols[: filled_array.shape[1]]):
                        imputed_df[c] = filled_array[:, idx]

        # 2. Kategorik sütunların doldurulması (Mod veya 'Bilinmiyor')
        cat_imputed_count = 0
        for cc in cat_cols:
            cat_missing = int(imputed_df[cc].isna().sum())
            if cat_missing > 0:
                if isinstance(imputed_df[cc].dtype, pd.CategoricalDtype):
                    if "Bilinmiyor" not in imputed_df[cc].cat.categories:
                        imputed_df[cc] = imputed_df[cc].cat.add_categories(["Bilinmiyor"])
                    imputed_df[cc] = imputed_df[cc].fillna("Bilinmiyor")
                else:
                    mode_series = imputed_df[cc].dropna().mode()
                    fill_val = str(mode_series.iloc[0]) if len(mode_series) > 0 else "Bilinmiyor"
                    imputed_df[cc] = imputed_df[cc].fillna(fill_val)
                cat_imputed_count += cat_missing

        total_imputed = num_missing_before + cat_imputed_count
        affected_cols = list(set(cols_with_missing_num + cols_with_missing_cat))

        report = {
            "success": True,
            "method": method.upper(),
            "total_numeric_imputed": num_missing_before,
            "total_categorical_imputed": cat_imputed_count,
            "total_imputed": total_imputed,
            "affected_columns": affected_cols,
            "message": f"{total_imputed} eksik hücre {method.upper()} algoritmasıyla başarıyla onarıldı.",
        }
        return imputed_df, report

    except Exception as e:
        logger.exception("Çok değişkenli veri doldurma hatası")
        return df, {"error": f"Doldurma işlemi başarısız: {str(e)}"}
