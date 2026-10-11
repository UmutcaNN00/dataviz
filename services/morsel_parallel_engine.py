"""
DataViz - Morsel-Driven Çok Çekirdekli Paralel Sorgu Motoru (DuckDB & Tableau Hyper Mimarisi)
Büyük veri setlerini dinamik lokmalara (morsels) bölerek CPU'nun tüm çekirdeklerinde
(multi-threading) paralel filtreleme, agregasyon ve istatistik hesaplama sağlar.
"""

from typing import Dict, Any, List, Callable
import time
import os
import concurrent.futures
import numpy as np
import pandas as pd
import logging

logger = logging.getLogger(__name__)

DEFAULT_MORSEL_SIZE = 40_000


def _compute_chunk_stats(chunk: pd.DataFrame, numeric_cols: List[str]) -> Dict[str, Dict[str, float]]:
    """Tek bir morsel lokması için yerel özet istatistikleri hesaplar."""
    stats = {}
    for col in numeric_cols:
        series = chunk[col].dropna()
        if len(series) == 0:
            continue
        stats[col] = {
            "count": int(len(series)),
            "sum": float(series.sum()),
            "min": float(series.min()),
            "max": float(series.max()),
            "sum_sq": float((series ** 2).sum()),
        }
    return stats


def parallel_morsel_stats(
    df: pd.DataFrame,
    morsel_size: int = DEFAULT_MORSEL_SIZE,
    max_workers: int = None,
) -> Dict[str, Any]:
    """
    DuckDB Morsel-Driven mimarisiyle, DataFrame'i parçalara bölüp tüm CPU çekirdeklerinde
    paralel olarak istatistiksel özet çıkarır.
    
    Args:
        df: Hesaplanacak DataFrame
        morsel_size: Her bir lokmadaki satır sayısı (varsayılan: 40.000)
        max_workers: Thread havuzu iş parçacığı sayısı (None ise os.cpu_count())
        
    Returns:
        Paralel hesaplama sonuçları ve benchmark metrikleri
    """
    if df is None or df.empty:
        return {"error": "Boş DataFrame"}

    start_time = time.time()
    num_cpus = os.cpu_count() or 4
    workers = max_workers or min(num_cpus, 16)

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    total_rows = len(df)

    if not numeric_cols:
        return {"error": "Sayısal sütun bulunamadı"}

    # Morsel lokmalarını oluştur
    chunks = [
        df.iloc[i : i + morsel_size]
        for i in range(0, total_rows, morsel_size)
    ]
    num_morsels = len(chunks)

    # Çok çekirdekli paralel yürütme
    chunk_results = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = [
            executor.submit(_compute_chunk_stats, chunk, numeric_cols)
            for chunk in chunks
        ]
        for f in concurrent.futures.as_completed(futures):
            chunk_results.append(f.result())

    # Paralel sonuçları birleştir (Merge / Reduction)
    merged_stats = {}
    for col in numeric_cols:
        col_count = sum(r[col]["count"] for r in chunk_results if col in r)
        if col_count == 0:
            continue
        col_sum = sum(r[col]["sum"] for r in chunk_results if col in r)
        col_min = min(r[col]["min"] for r in chunk_results if col in r)
        col_max = max(r[col]["max"] for r in chunk_results if col in r)
        col_sum_sq = sum(r[col]["sum_sq"] for r in chunk_results if col in r)

        mean_val = col_sum / col_count
        # Varyans = E[X^2] - (E[X])^2
        variance = max(0.0, (col_sum_sq / col_count) - (mean_val ** 2))
        std_val = float(np.sqrt(variance))

        merged_stats[col] = {
            "count": col_count,
            "mean": round(mean_val, 3),
            "std": round(std_val, 3),
            "min": round(col_min, 3),
            "max": round(col_max, 3),
        }

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    return {
        "success": True,
        "total_rows": total_rows,
        "num_cpus": num_cpus,
        "workers_used": workers,
        "morsel_size": morsel_size,
        "num_morsels": num_morsels,
        "elapsed_ms": elapsed_ms,
        "column_stats": merged_stats,
    }
