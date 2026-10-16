"""
Anomaly Explainer Service - Explainable Isolation Forest & Feature Deviation Analysis
Calculates multivariable outlier scores and explains WHY a specific record is anomalous.
"""

import logging
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest

logger = logging.getLogger(__name__)


def explain_dataset_anomalies(
    df: pd.DataFrame,
    top_n: int = 50,
    contamination: float = 0.05,
    sample_limit: int = 50000,
) -> dict[str, Any]:
    """
    Fits an Isolation Forest model and extracts localized explanations for detected anomalies.
    Returns:
    - Global outlier count
    - Detailed list of top anomalous rows with feature deviations (+X sigma or out-of-range)
    """
    total_rows = 0 if df is None else len(df)
    if df is None or df.empty or total_rows < 2:
        return {
            "total_rows_analyzed": total_rows,
            "total_anomalies_found": 0,
            "anomaly_percentage": 0.0,
            "explained_rows": [],
            "message": "Anomali gerekçelendirme için en az 2 satır gereklidir.",
        }

    target_df = df.iloc[:sample_limit] if len(df) > sample_limit else df

    numeric_cols = target_df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return {
            "total_rows_analyzed": len(target_df),
            "total_anomalies_found": 0,
            "anomaly_percentage": 0.0,
            "explained_rows": [],
            "message": "Analiz edilecek sayısal sütun bulunamadı.",
        }

    contamination = min(max(float(contamination or 0.05), 0.001), 0.5)
    # Clean subset for model
    num_data = target_df[numeric_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    col_means = num_data.mean().fillna(0.0)
    col_stds = num_data.std().replace(0, 1e-6).fillna(1.0)
    col_mins = num_data.min().fillna(0.0)
    col_maxs = num_data.max().fillna(0.0)
    col_q25 = num_data.quantile(0.25).fillna(0.0)
    col_q75 = num_data.quantile(0.75).fillna(0.0)
    col_iqr = (col_q75 - col_q25).replace(0, 1e-6).fillna(1.0)

    # Impute missing for Isolation Forest
    num_clean = num_data.fillna(col_means).fillna(0.0)

    # Fit Isolation Forest
    iso = IsolationForest(
        n_estimators=100,
        max_samples=min(256, len(num_clean)),
        contamination=contamination,
        random_state=42,
        n_jobs=-1,
    )
    preds = iso.fit_predict(num_clean)  # -1 = anomaly, 1 = normal
    raw_scores = iso.decision_function(num_clean)  # lower = more abnormal

    # Normalize score to 0..100 Risk Score (where 100 = highest risk/anomaly)
    # raw_scores typically range from -0.3 (extreme) to +0.2 (normal)
    min_s = raw_scores.min()
    max_s = raw_scores.max()
    risk_scores = np.clip(100.0 * (1.0 - (raw_scores - min_s) / max(max_s - min_s, 1e-6)), 0, 100)

    anomaly_indices = np.where(preds == -1)[0]
    total_anomalies = len(anomaly_indices)

    # Rank anomalies by risk score descending
    sorted_anom_idx = anomaly_indices[np.argsort(-risk_scores[anomaly_indices])]
    top_anom_idx = sorted_anom_idx[:top_n]

    explained_rows = []
    for idx in top_anom_idx:
        row = num_clean.iloc[idx]
        risk = round(float(risk_scores[idx]), 1)

        # Calculate Z-score and IQR deviation for each feature
        feature_deviations = []
        for col in numeric_cols:
            val = float(row[col])
            mean = float(col_means[col])
            std = float(col_stds[col])
            z_score = (val - mean) / std

            q25 = float(col_q25[col])
            q75 = float(col_q75[col])
            iqr = float(col_iqr[col])

            # Check if this feature is a significant contributor to the anomaly
            if abs(z_score) >= 2.0 or val < (q25 - 1.5 * iqr) or val > (q75 + 1.5 * iqr):
                direction = "Yüksek" if z_score > 0 else "Düşük"
                feature_deviations.append({
                    "column": col,
                    "value": round(val, 2),
                    "mean": round(mean, 2),
                    "expected_range": f"{round(q25, 1)} - {round(q75, 1)}",
                    "z_score": round(z_score, 2),
                    "reason": f"Ortalamadan {abs(z_score):.1f}σ {direction} ({direction.lower()} sapma)",
                    "severity": "high" if abs(z_score) >= 3.0 else "medium",
                })

        # Sort reasons by highest absolute Z-score
        feature_deviations.sort(key=lambda x: abs(x["z_score"]), reverse=True)

        # Get a display preview of other columns in the original row
        preview_dict = {}
        for k in target_df.columns[:6]:
            pval = target_df.iloc[idx][k]
            if pd.isna(pval):
                preview_dict[str(k)] = None
            elif isinstance(pval, (float, np.floating)):
                fval = float(pval)
                preview_dict[str(k)] = None if (np.isnan(fval) or np.isinf(fval)) else round(fval, 2)
            elif isinstance(pval, (int, np.integer)) and not isinstance(pval, bool):
                preview_dict[str(k)] = int(pval)
            else:
                preview_dict[str(k)] = str(pval)

        explained_rows.append({
            "row_index": int(idx) + 1,  # 1-indexed for user display
            "risk_score": risk,
            "anomaly_level": "Yüksek Risk" if risk >= 75 else "Orta Risk",
            "top_reasons": feature_deviations[:3],  # top 3 reasons
            "total_deviant_columns": len(feature_deviations),
            "preview": preview_dict,
        })

    return {
        "total_rows_analyzed": len(target_df),
        "total_anomalies_found": total_anomalies,
        "anomaly_percentage": round((total_anomalies / max(len(target_df), 1)) * 100, 2),
        "explained_rows": explained_rows,
    }
