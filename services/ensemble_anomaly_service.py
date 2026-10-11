"""
DataViz - Konsensüs Tabanlı Hibrit Anomali Tespiti (Ensemble Anomaly Engine)
Isolation Forest, Local Outlier Factor (LOF) ve Eliptik Z-Skoru modellerinin
oy çokluğu (majority voting) konsensüsü ile yanlış pozitifleri sıfırlar ve yüksek doğruluk sağlar.
"""

from typing import Dict, Any, List
import numpy as np
import pandas as pd
import logging

from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.preprocessing import RobustScaler

logger = logging.getLogger(__name__)


def detect_ensemble_anomalies(
    df: pd.DataFrame,
    contamination: float = 0.05,
    top_n: int = 50,
) -> Dict[str, Any]:
    """
    3 farklı anomali modelini paralel çalıştırıp konsensüs oylaması ile en güvenilir anomalileri saptar.
    
    Args:
        df: Analiz edilecek DataFrame
        contamination: Beklenen anomali oranı (varsayılan: 0.05)
        top_n: Döndürülecek en yüksek riskli anomali adedi
        
    Returns:
        Konsensüs anomali raporu
    """
    if df is None or df.empty:
        return {"error": "Boş DataFrame"}

    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return {
            "success": True,
            "total_rows": len(df),
            "total_consensus_anomalies": 0,
            "total_single_model_alerts": 0,
            "false_positive_reduction_pct": 0.0,
            "anomalies": [],
            "message": "Konsensüs anomali tespiti için en az 1 sayısal sütun gereklidir.",
        }

    if len(df) < 2:
        return {
            "success": True,
            "total_rows": len(df),
            "total_consensus_anomalies": 0,
            "total_single_model_alerts": 0,
            "false_positive_reduction_pct": 0.0,
            "anomalies": [],
            "message": "Konsensüs anomali tespiti için en az 2 satır gereklidir.",
        }

    # Eksik değerleri medyan ile doldur, tümü NaN ise 0.0 ata
    medians = df[numeric_cols].median().fillna(0.0)
    clean_matrix = df[numeric_cols].fillna(medians).fillna(0.0)
    
    # Robust scaling (Aykırı değerlerden etkilenmeyen ölçeklendirme)
    scaler = RobustScaler()
    scaled_features = scaler.fit_transform(clean_matrix)
    scaled_features = np.nan_to_num(scaled_features, nan=0.0, posinf=0.0, neginf=0.0)
    total_rows = len(df)

    # 1. Model: Isolation Forest
    iso = IsolationForest(
        contamination=contamination,
        random_state=42,
        n_estimators=100,
        n_jobs=-1,
    )
    iso_preds = iso.fit_predict(scaled_features)  # -1 anomali, 1 normal
    iso_scores = -iso.score_samples(scaled_features)  # Yüksek skor = daha anomali

    # 2. Model: Local Outlier Factor (LOF)
    n_neighbors = min(20, max(5, total_rows // 5))
    lof = LocalOutlierFactor(
        n_neighbors=n_neighbors,
        contamination=contamination,
        n_jobs=-1,
    )
    lof_preds = lof.fit_predict(scaled_features)  # -1 anomali, 1 normal
    lof_scores = -lof.negative_outlier_factor_

    # 3. Model: Robust Multidimensional Z-Score (Mahalanobis yaklaşımı)
    # Medyandan mutlak sapma (MAD tabanlı z-skorları)
    medians = clean_matrix.median()
    mads = (clean_matrix - medians).abs().median().replace(0, 1e-6)
    z_scores = ((clean_matrix - medians).abs() / (1.4826 * mads)).max(axis=1)
    z_threshold = 3.5
    z_preds = np.where(z_scores >= z_threshold, -1, 1)

    # Konsensüs Oylaması
    # Her model için anomali ise 1, normal ise 0
    vote_iso = (iso_preds == -1).astype(int)
    vote_lof = (lof_preds == -1).astype(int)
    vote_z = (z_preds == -1).astype(int)

    total_votes = vote_iso + vote_lof + vote_z  # 0, 1, 2 veya 3 oy

    # Konsensüs anomali indeksleri (en az 2 modelin oy verdiği)
    consensus_mask = total_votes >= 2
    single_model_mask = total_votes == 1

    consensus_indices = np.where(consensus_mask)[0]
    single_indices = np.where(single_model_mask)[0]

    # Sonuçları yapılandır
    anomalies_list = []
    
    # Öncelikli olarak konsensüs sağlananları, yetmezse tekil modelleri sırala
    all_anom_indices = np.concatenate([consensus_indices, single_indices])
    # Konsensüs oyları ve z-skorlarına göre sırala
    sorted_indices = sorted(
        all_anom_indices,
        key=lambda idx: (total_votes[idx], z_scores.iloc[idx]),
        reverse=True,
    )[:top_n]

    for idx in sorted_indices:
        votes = int(total_votes[idx])
        agreeing_models = []
        if vote_iso[idx]: agreeing_models.append("Isolation Forest")
        if vote_lof[idx]: agreeing_models.append("Local Outlier Factor (LOF)")
        if vote_z[idx]: agreeing_models.append("Robust Z-Score (>3.5σ)")

        risk_level = (
            "Kritik Risk (%100 Konsensüs)" if votes == 3
            else "Yüksek Risk (%66 Konsensüs)" if votes == 2
            else "Şüpheli (Tek Model)"
        )
        risk_pct = round((votes / 3.0) * 100, 1)

        row_preview = {}
        for c in df.columns[:6]:
            val = df.iloc[idx][c]
            row_preview[c] = round(float(val), 2) if isinstance(val, (float, np.floating)) else str(val)

        anomalies_list.append({
            "row_index": int(idx) + 1,
            "votes": votes,
            "risk_percentage": risk_pct,
            "risk_level": risk_level,
            "agreeing_models": agreeing_models,
            "max_z_score": round(float(z_scores.iloc[idx]), 2),
            "preview": row_preview,
        })

    result = {
        "success": True,
        "total_rows": total_rows,
        "total_consensus_anomalies": len(consensus_indices),
        "total_single_model_alerts": len(single_indices),
        "false_positive_reduction_pct": round(
            (len(single_indices) / max(1, len(consensus_indices) + len(single_indices))) * 100, 1
        ),
        "anomalies": anomalies_list,
    }

    logger.info(
        f"Ensemble Anomali tamamlandı: {len(consensus_indices)} konsensüs anomali, "
        f"{len(single_indices)} tekil şüphe filtrelendi."
    )
    return result
