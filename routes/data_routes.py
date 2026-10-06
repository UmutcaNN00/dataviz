"""
Data Routes Blueprint - Data Health, Anomaly Healing, Cleaning, Dataset Joins, and Calculated Columns
"""

import logging
import re
from typing import Any, cast

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request

# isort: split
from core.store import (
    get_baseline_trust,
    get_df,
    get_is_cleaned,
    set_baseline_trust,
    set_df,
    set_is_cleaned,
)
from services.data_healer import (
    clean_missing_data,
    detect_column_anomalies,
    repair_column_data,
)
from services.file_service import (
    _deduplicate_columns,
    read_csv_safely,
    read_excel_safely,
    read_parquet_safely,
)

logger = logging.getLogger(__name__)

data_bp = Blueprint("data", __name__)


def _compute_health_dict(df: pd.DataFrame) -> dict[str, Any]:
    """Computes dataset health metrics with fast sampling for massive datasets (>500k rows)."""
    total_n = len(df)
    if total_n == 0:
        return {
            "success": True,
            "has_issues": False,
            "missing_cells": 0,
            "missing_rows": 0,
            "total_rows": 0,
            "anomalies": [],
            "has_anomalies": False,
        }

    if total_n > 500_000:
        sample_size = min(50_000, total_n)
        sample_check = df.iloc[:sample_size]
        sample_missing_cells = int(
            sum(int(sample_check[c].isna().sum()) for c in sample_check.columns)
        )
        if sample_missing_cells == 0:
            missing_count = 0
            missing_rows = 0
        else:
            scale = total_n / sample_size
            missing_count = max(1, round(sample_missing_cells * scale))
            sample_missing_ratio = float(sample_check.isna().any(axis=1).mean())
            missing_rows = max(1, round(sample_missing_ratio * total_n))
    else:
        missing_count = int(sum(int(df[c].isna().sum()) for c in df.columns))
        missing_rows = 0 if missing_count == 0 else int(df.isnull().any(axis=1).sum())

    anomalies = detect_column_anomalies(df)
    return {
        "success": True,
        "has_issues": missing_rows > 0 or len(anomalies) > 0,
        "missing_cells": missing_count,
        "missing_rows": missing_rows,
        "total_rows": total_n,
        "anomalies": anomalies,
        "has_anomalies": len(anomalies) > 0,
    }


@data_bp.route("/check_health", methods=["GET"])
def check_health():
    """Inspects dataset health: missing values, NaN count, and column type anomalies."""
    global_df = get_df(1)
    if global_df is None or len(global_df) == 0:
        return jsonify(
            {"error": "Aktif veri seti bulunamadı. Lütfen önce bir dosya yükleyin."}
        ), 400

    try:
        health_data = _compute_health_dict(global_df)
        resp = jsonify(health_data)
        resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
        return resp
    except Exception as e:
        logger.exception("check_health hatası")
        return jsonify(
            {"error": f"Veri sağlığı kontrol edilirken bir hata oluştu: {e}"}
        ), 500


@data_bp.route("/repair_column_anomalies", methods=["POST"])
def repair_column_anomalies():
    """Executes smart repair or conversion on anomalous columns."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {}
    target_column = data.get("column", "__all__")
    repair_mode = data.get("repair_mode", "smart_heal")

    try:
        if get_baseline_trust() is None:
            set_baseline_trust(_compute_trust_snapshot(global_df))

        repaired_df, cols_to_repair = repair_column_data(
            global_df, target_column=target_column, repair_mode=repair_mode
        )
        set_df(repaired_df, 1)
        set_is_cleaned(True)

        numeric_cols = repaired_df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = repaired_df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()
        health_data = _compute_health_dict(repaired_df)

        return jsonify(
            {
                "success": True,
                "repaired_columns": cols_to_repair,
                "repair_mode": repair_mode,
                "total_rows": len(repaired_df),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
                "remaining_anomalies": health_data["anomalies"],
                "health": health_data,
            }
        )
    except ValueError as ve:
        logger.error(f"Sütun onarma hatası (Geçersiz istek): {ve}")
        return jsonify({"error": str(ve)}), 400
    except Exception as e:  # noqa: BLE001
        logger.error(f"Sütun onarma hatası: {e}")
        return jsonify({"error": f"Onarma işlemi sırasında hata: {e}"}), 500


@data_bp.route("/clean_data", methods=["POST"])
def clean_data():
    """Cleans missing data via dropping or mean/median/zero/mode imputation."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Veri yok"}), 400

    data = request.get_json(silent=True) or {}
    action = data.get("action", "drop")
    target_column = data.get("column")
    try:
        if get_baseline_trust() is None:
            set_baseline_trust(_compute_trust_snapshot(global_df))

        cleaned_df = clean_missing_data(
            global_df, action=action, target_column=target_column
        )
        is_global_clean = not target_column or target_column in ("__all__", "all")
        if is_global_clean:
            if len(cleaned_df) <= 500_000:
                cleaned_df = cleaned_df.drop_duplicates(ignore_index=True)
            elif (
                len(cleaned_df) <= 2_000_000
                and int(cleaned_df.iloc[:40_000].duplicated().sum()) > 0
            ):
                cleaned_df = cleaned_df.drop_duplicates(ignore_index=True)

        set_df(cleaned_df, 1)
        set_is_cleaned(True)

        numeric_cols = cleaned_df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = cleaned_df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()
        health_data = _compute_health_dict(cleaned_df)

        return jsonify(
            {
                "success": True,
                "total_rows": len(cleaned_df),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
                "health": health_data,
            }
        )
    except Exception as e:
        logger.exception("clean_data hatası")
        return jsonify({"error": str(e)}), 500


@data_bp.route("/preview_second_file", methods=["POST"])
def preview_second_file():
    """Parses a second dataset file for key discovery and merge preparation."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Önce 1. dosyayı yükleyin"}), 400
    if "file2" not in request.files:
        return jsonify({"error": "2. dosya bulunamadı"}), 400
    file2 = request.files["file2"]
    if not file2.filename:
        return jsonify({"error": "Dosya seçilmedi"}), 400

    try:
        filename2 = file2.filename.lower()
        if filename2.endswith(".parquet"):
            df2 = read_parquet_safely(file2)
        elif filename2.endswith(".csv"):
            df2 = read_csv_safely(file2)
        elif filename2.endswith((".xls", ".xlsx")):
            df2, _, _, _ = read_excel_safely(file2)
        else:
            return jsonify(
                {
                    "error": "Desteklenmeyen dosya formatı. Lütfen .parquet, .csv veya .xlsx dosyası yükleyin."
                }
            ), 400

        df2.columns = pd.Index(_deduplicate_columns(df2.columns))
        set_df(df2, 2)

        cols1 = [str(c) for c in global_df.columns.tolist()]
        cols2 = [str(c) for c in df2.columns.tolist()]

        auto_key1 = None
        auto_key2 = None

        # 1. Exact match (case insensitive)
        for c1 in cols1:
            for c2 in cols2:
                if c1.lower() == c2.lower():
                    auto_key1 = c1
                    auto_key2 = c2
                    break
            if auto_key1:
                break

        # 2. Semantic keyword group match (only pair columns belonging to the SAME keyword group)
        if not auto_key1:
            keyword_groups = [
                ("id", "no", "numara", "kod", "key", "tc"),
                ("sehir", "şehir", "il"),
                ("bolge", "bölge"),
                ("tarih", "date", "donem", "dönem", "ay", "yil", "yıl"),
                ("kategori", "urun", "ürün"),
            ]
            for kw_group in keyword_groups:
                pattern = r"(?:^|[_\s\-])(" + "|".join(kw_group) + r")(?:$|[_\s\-])"
                matched_c1 = next(
                    (c1 for c1 in cols1 if re.search(pattern, c1.lower())), None
                )
                matched_c2 = next(
                    (c2 for c2 in cols2 if re.search(pattern, c2.lower())), None
                )
                if matched_c1 and matched_c2:
                    auto_key1 = matched_c1
                    auto_key2 = matched_c2
                    break

        return jsonify(
            {
                "success": True,
                "file2_name": file2.filename,
                "file2_rows": len(df2),
                "cols1": cols1,
                "cols2": cols2,
                "auto_key1": auto_key1,
                "auto_key2": auto_key2,
            }
        )
    except Exception as e:
        logger.exception("preview_second_file hatası")
        return jsonify({"error": str(e)}), 500


@data_bp.route("/merge_datasets", methods=["POST"])
def merge_datasets():
    """Merges the active dataset with a second dataset using specified keys and join type."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Önce 1. dosyayı yükleyin"}), 400

    df2 = None
    if "file2" in request.files and request.files["file2"].filename:
        file2 = request.files["file2"]
        filename2 = (file2.filename or "").lower()
        try:
            if filename2.endswith(".parquet"):
                df2 = read_parquet_safely(file2)
            elif filename2.endswith(".csv"):
                df2 = read_csv_safely(file2)
            elif filename2.endswith((".xls", ".xlsx")):
                df2, _, _, _ = read_excel_safely(file2)
            else:
                return jsonify(
                    {
                        "error": "Desteklenmeyen dosya formatı. Lütfen .parquet, .csv veya .xlsx dosyası yükleyin."
                    }
                ), 400
            set_df(df2, 2)
        except Exception as e:  # noqa: BLE001
            return jsonify({"error": f"2. dosya okunamadı: {e}"}), 400
    else:
        df2 = get_df(2)

    if df2 is None or df2.empty:
        return jsonify({"error": "2. dosya bulunamadı veya boş"}), 400

    req_json = request.get_json(silent=True) or {}
    key1 = request.form.get("key1") or req_json.get("key1")
    key2 = request.form.get("key2") or req_json.get("key2")
    join_type = (
        str(request.form.get("join_type") or req_json.get("join_type") or "left")
        .lower()
        .strip()
    )
    if join_type not in ("left", "right", "inner", "outer"):
        join_type = "left"

    if not key1 or not key2:
        return jsonify(
            {"error": "Birleştirme anahtarları (ortak sütunlar) seçilmelidir."}
        ), 400

    df2.columns = pd.Index(_deduplicate_columns(df2.columns))

    if key1 not in global_df.columns:
        return jsonify({"error": f'1. tabloda "{key1}" sütunu bulunamadı'}), 400
    if key2 not in df2.columns:
        return jsonify({"error": f'2. tabloda "{key2}" sütunu bulunamadı'}), 400

    try:
        global_df_temp = global_df.copy()
        df2_temp = df2.copy()

        def normalize_merge_series(series: pd.Series, prefix: str) -> np.ndarray:
            s_str = series.astype(str).str.strip()
            # Remove trailing .0 from float-formatted integer keys without IEEE-754 precision loss on long IDs
            s_str = s_str.str.replace(r"^(-?\d+)\.0+$", r"\1", regex=True)
            null_mask = series.isna() | s_str.isin(
                ["", "nan", "NaN", "None", "none", "null", "NULL", "<NA>"]
            )
            null_keys = [f"__{prefix}_null_{i}__" for i in range(len(series))]
            return np.where(null_mask, null_keys, s_str)

        global_df_temp["_merge_key_"] = normalize_merge_series(
            global_df_temp[key1], "left"
        )
        df2_temp["_merge_key_"] = normalize_merge_series(df2_temp[key2], "right")

        used_col_names = set(str(c) for c in global_df_temp.columns) | set(
            str(c) for c in df2_temp.columns
        )
        right_rename_map: dict[str, str] = {}
        for c in df2_temp.columns:
            c_str = str(c)
            if c_str == "_merge_key_":
                continue
            if c_str == key2 and key1 == key2:
                right_rename_map[c_str] = "__right_join_key__"
                continue
            if c_str in global_df_temp.columns:
                suffix_idx = 2
                candidate = f"{c_str}_{suffix_idx}"
                while candidate in used_col_names:
                    suffix_idx += 1
                    candidate = f"{c_str}_{suffix_idx}"
                used_col_names.add(candidate)
                right_rename_map[c_str] = candidate

        if right_rename_map:
            df2_temp.rename(columns=right_rename_map, inplace=True)

        merged = pd.merge(
            global_df_temp,
            df2_temp,
            on="_merge_key_",
            how=cast(Any, join_type),
        )
        merged.drop(columns=["_merge_key_"], inplace=True)

        if "__right_join_key__" in merged.columns:
            if isinstance(merged[key1].dtype, pd.CategoricalDtype):
                merged[key1] = merged[key1].astype(object)
            right_key_col = merged["__right_join_key__"]
            if isinstance(right_key_col.dtype, pd.CategoricalDtype):
                right_key_col = right_key_col.astype(object)
            merged[key1] = merged[key1].where(merged[key1].notna(), right_key_col)
            merged.drop(columns=["__right_join_key__"], inplace=True)

        merged.columns = pd.Index(_deduplicate_columns(merged.columns))
        merged = merged.reset_index(drop=True)
        old_cols = set(global_df.columns)
        new_cols = [c for c in merged.columns if c not in old_cols]

        global_df = merged
        set_df(global_df, 1)
        set_baseline_trust(None)
        set_is_cleaned(False)

        numeric_cols = global_df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = global_df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        return jsonify(
            {
                "success": True,
                "total_rows": len(global_df),
                "total_cols": len(global_df.columns),
                "new_joined_columns": new_cols,
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
            }
        )
    except Exception as e:
        logger.exception("join_datasets hatası")
        return jsonify({"error": f"Birleştirme hatası: {e}"}), 500


@data_bp.route("/add_calculated_column", methods=["POST"])
def add_calculated_column():
    """Generates a calculated column based on arithmetic operations between columns/scalars."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Veri yok"}), 400

    data = request.get_json(silent=True) or {}
    new_col = (data.get("new_col_name") or data.get("new_column_name") or "").strip()
    col1 = data.get("col1")
    op = data.get("op") or data.get("operator")
    col2 = data.get("col2")
    scalar = data.get("scalar")

    if not new_col:
        return jsonify({"error": "Yeni sütun adı belirtilmelidir."}), 400
    if col1 not in global_df.columns:
        return jsonify({"error": "1. sütun bulunamadı."}), 400

    try:
        s1 = pd.to_numeric(global_df[col1], errors="coerce").fillna(0)

        if col2 and col2 in global_df.columns:
            s2 = pd.to_numeric(global_df[col2], errors="coerce").fillna(0)
        elif scalar is not None and str(scalar).strip() != "":
            try:
                s2 = float(scalar)
            except ValueError:
                return jsonify({"error": "Geçersiz sabit sayısal değer."}), 400
        else:
            return jsonify(
                {"error": "2. değişken veya sayısal değer belirtilmelidir."}
            ), 400

        if op == "+":
            res = s1 + s2
        elif op == "-":
            res = s1 - s2
        elif op == "*":
            res = s1 * s2
        elif op == "/":
            raw_div = np.where(s2 != 0, s1 / s2, 0.0)
            res = pd.Series(raw_div, index=global_df.index).replace(
                [np.inf, -np.inf, np.nan], 0.0
            )
        else:
            return jsonify({"error": "Geçersiz işlem operatörü."}), 400

        global_df[new_col] = res
        set_df(global_df, 1)

        numeric_cols = global_df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = global_df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        return jsonify(
            {
                "success": True,
                "new_column": new_col,
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
            }
        )
    except Exception as e:
        logger.exception("create_calculated_column hatası")
        return jsonify({"error": f"Hesaplama hatası: {e}"}), 500


from sklearn.ensemble import IsolationForest


@data_bp.route("/calculate_risk_score", methods=["POST"])
def calculate_risk_score():
    """Calculates an AI-based Trust/Risk Score using Isolation Forest."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Önce bir veri seti yükleyin."}), 400

    try:
        numeric_cols = [
            c
            for c in global_df.select_dtypes(include=["number"]).columns
            if c != "Guven_Skoru_AI"
        ]
        if len(numeric_cols) == 0:
            return jsonify(
                {"error": "Model eğitimi için en az bir sayısal sütun gereklidir."}
            ), 400

        n_rows = len(global_df)
        if n_rows <= 100_000:
            df_numeric = global_df[numeric_cols].copy()
            medians = df_numeric.median(numeric_only=True)
            df_numeric = df_numeric.fillna(medians).fillna(0)

            model = IsolationForest(
                n_estimators=100,
                max_samples=min(256, n_rows),
                contamination="auto",
                random_state=42,
                n_jobs=-1,
            )
            model.fit(df_numeric)
            anomaly_scores = model.decision_function(df_numeric)
        else:
            # Büyük veri setlerinde (>100K satır) örnekleme ile eğit ve vektörize skorla
            sample_df = global_df[numeric_cols].iloc[:50_000].copy()
            medians = sample_df.median(numeric_only=True).fillna(0)
            stds = sample_df.std(numeric_only=True).replace(0, 1.0).fillna(1.0)
            z_sum = np.zeros(n_rows, dtype=np.float32)
            for col in numeric_cols[:8]:
                col_arr = (
                    pd.to_numeric(global_df[col], errors="coerce")
                    .fillna(float(medians.get(col, 0.0)))
                    .to_numpy(dtype=np.float32, copy=False)
                )
                z_sum += np.abs(
                    (col_arr - float(medians.get(col, 0.0))) / float(stds.get(col, 1.0))
                )
            anomaly_scores = -z_sum / max(1, len(numeric_cols[:8]))

        min_score = float(np.nanmin(anomaly_scores))
        max_score = float(np.nanmax(anomaly_scores))

        if max_score > min_score:
            normalized_scores = (
                (anomaly_scores - min_score) / (max_score - min_score)
            ) * 100.0
        else:
            normalized_scores = np.full(n_rows, 100.0, dtype=np.float32)

        risk_scores = np.round(normalized_scores).astype(np.int16)

        global_df["Guven_Skoru_AI"] = risk_scores
        set_df(global_df, 1)

        new_numeric_cols = global_df.select_dtypes(include=["number"]).columns.tolist()
        new_categorical_cols = global_df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        return jsonify(
            {
                "success": True,
                "new_column": "Guven_Skoru_AI",
                "mean_score": round(float(np.mean(risk_scores)), 1),
                "message": "AI Güven Skoru (Isolation Forest) başarıyla hesaplandı ve sütun eklendi.",
                "numeric_columns": new_numeric_cols,
                "categorical_columns": new_categorical_cols,
            }
        )
    except Exception as e:
        logger.exception("AI Risk Skoru hatası")
        return jsonify({"error": f"Hesaplama hatası: {str(e)}"}), 500


def _compute_trust_snapshot(df: pd.DataFrame) -> dict[str, Any]:
    """
    Computes a comprehensive 4-factor Data Trust Score (0-100) and per-column scorecard:
      1. Eksiksizlik / Boş Veri Skoru (%35 ağırlık)
      2. Tip Doğruluğu / Yanlış & Sözel Veri Skoru (%30 ağırlık)
      3. İstatistiksel Tutarlılık / Aykırı Değer Skoru (%20 ağırlık)
      4. Tekillik / Mükerrer Satır Skoru (%15 ağırlık)
    """
    eval_cols = [c for c in df.columns if c != "Guven_Skoru_AI"]
    total_rows = len(df)
    total_cols = len(eval_cols)
    if total_rows == 0 or total_cols == 0:
        return {
            "overall_score": 100.0,
            "completeness_score": 100.0,
            "type_validity_score": 100.0,
            "outlier_score": 100.0,
            "uniqueness_score": 100.0,
            "total_rows": total_rows,
            "total_cols": total_cols,
            "total_cells": 0,
            "missing_cells": 0,
            "missing_rows": 0,
            "missing_pct": 0.0,
            "invalid_cells": 0,
            "invalid_pct": 0.0,
            "anomalous_cols_count": 0,
            "outlier_cells": 0,
            "outlier_pct": 0.0,
            "duplicate_rows": 0,
            "duplicate_pct": 0.0,
            "columns": [],
        }

    is_sampled = total_rows > 150_000
    sample_size = min(40_000, total_rows) if is_sampled else total_rows
    sample_df = df[eval_cols].iloc[:sample_size] if is_sampled else df[eval_cols]
    scale = total_rows / max(1, sample_size)

    anomalies = detect_column_anomalies(df[eval_cols])
    anomaly_map = {str(a["column"]): a for a in anomalies}

    total_cells = total_rows * total_cols
    total_missing_cells = 0
    total_invalid_cells = 0
    total_outlier_cells = 0
    total_numeric_eval_cells = 0

    col_cards: list[dict[str, Any]] = []

    for col in eval_cols:
        col_str = str(col)
        s_sample = sample_df[col]
        is_num = pd.api.types.is_numeric_dtype(df[col])

        sample_na = int(s_sample.isna().sum())
        col_missing = int(round(sample_na * scale)) if sample_na > 0 else 0
        col_missing_pct = round((sample_na / max(1, sample_size)) * 100.0, 2)
        total_missing_cells += col_missing

        anom = anomaly_map.get(col_str)
        has_anomaly = anom is not None
        col_invalid = int(anom["invalid_count"]) if anom else 0
        col_invalid_pct = float(anom["invalid_pct"]) if anom else 0.0
        sample_invalids = (
            list(anom.get("sample_invalid_values", []))[:5] if anom else []
        )
        total_invalid_cells += col_invalid

        # Outlier (IQR) calculation on numeric columns
        col_outliers = 0
        col_outlier_pct = 0.0
        if is_num:
            clean_num = pd.to_numeric(s_sample, errors="coerce").dropna()
            if len(clean_num) >= 8:
                q1 = float(clean_num.quantile(0.25))
                q3 = float(clean_num.quantile(0.75))
                iqr = q3 - q1
                if iqr > 0:
                    low_b = q1 - 1.5 * iqr
                    high_b = q3 + 1.5 * iqr
                    sample_out = int(((clean_num < low_b) | (clean_num > high_b)).sum())
                    col_outliers = (
                        int(round(sample_out * scale)) if sample_out > 0 else 0
                    )
                    col_outlier_pct = round(
                        (sample_out / max(1, len(clean_num))) * 100.0, 2
                    )
            total_outlier_cells += col_outliers
            total_numeric_eval_cells += total_rows

        # Per-column trust score (0-100)
        penalty_missing = (
            min(45.0, max(3.5, col_missing_pct * 1.8)) if col_missing > 0 else 0.0
        )
        penalty_invalid = (
            min(48.0, 18.0 + col_invalid_pct * 1.8) if has_anomaly else 0.0
        )
        penalty_outlier = min(18.0, col_outlier_pct * 1.2) if col_outliers > 0 else 0.0
        col_score = round(
            max(
                0.0,
                min(100.0, 100.0 - penalty_missing - penalty_invalid - penalty_outlier),
            ),
            1,
        )

        if has_anomaly:
            dtype_label = "Sayısal (Metin Bozulmalı)"
            status = "risky"
        elif is_num:
            dtype_label = "Sayısal"
            status = (
                "warning"
                if col_missing > 0
                else ("healthy" if col_score >= 85 else "warning")
            )
        else:
            dtype_label = "Kategorik / Metin"
            status = "warning" if col_missing > 0 else "healthy"

        col_cards.append(
            {
                "column": col_str,
                "dtype_label": dtype_label,
                "is_numeric": bool(is_num),
                "has_anomaly": has_anomaly,
                "trust_score": col_score,
                "status": status,
                "missing_count": col_missing,
                "missing_pct": col_missing_pct,
                "invalid_count": col_invalid,
                "invalid_pct": col_invalid_pct,
                "sample_invalid_values": sample_invalids,
                "outlier_count": col_outliers,
                "outlier_pct": col_outlier_pct,
                "needs_repair": bool(has_anomaly or col_missing > 0),
            }
        )

    # Sort column scorecard so problematic columns appear first
    col_cards.sort(
        key=lambda x: (x["trust_score"], -x["invalid_count"], -x["missing_count"])
    )

    sample_missing_rows = int(sample_df.isna().any(axis=1).sum())
    missing_rows = (
        int(round(sample_missing_rows * scale)) if sample_missing_rows > 0 else 0
    )
    missing_cell_pct = round((total_missing_cells / max(1, total_cells)) * 100.0, 2)
    missing_row_pct = (missing_rows / max(1, total_rows)) * 100.0
    cols_with_missing = sum(1 for c in col_cards if c["missing_count"] > 0)
    cols_missing_ratio = cols_with_missing / max(1, total_cols)

    # 1. Completeness Score (35%)
    if total_missing_cells == 0:
        completeness_score = 100.0
    else:
        completeness_score = round(
            max(
                0.0,
                min(
                    96.0,
                    100.0
                    - (
                        cols_missing_ratio * 35.0
                        + missing_row_pct * 0.9
                        + missing_cell_pct * 2.5
                    ),
                ),
            ),
            1,
        )

    # 2. Type Validity Score (30%)
    anomalous_cols_count = len(anomalies)
    invalid_cell_pct = round((total_invalid_cells / max(1, total_cells)) * 100.0, 2)
    if anomalous_cols_count == 0 and total_invalid_cells == 0:
        type_validity_score = 100.0
    else:
        col_anom_ratio = anomalous_cols_count / max(1, total_cols)
        type_validity_score = round(
            max(
                0.0,
                min(
                    92.0,
                    100.0 - (14.0 + col_anom_ratio * 75.0 + invalid_cell_pct * 4.5),
                ),
            ),
            1,
        )

    # 3. Outlier Score (20%)
    outlier_pct = round(
        (total_outlier_cells / max(1, total_numeric_eval_cells)) * 100.0, 2
    )
    if total_outlier_cells == 0:
        outlier_score = 100.0
    else:
        outlier_score = round(
            max(35.0, min(98.5, 100.0 - outlier_pct * 2.5)),
            1,
        )

    # 4. Uniqueness Score (15%)
    try:
        sample_dups = int(sample_df.duplicated().sum())
        duplicate_rows = int(round(sample_dups * scale)) if sample_dups > 0 else 0
    except Exception:
        duplicate_rows = 0
    duplicate_pct = round((duplicate_rows / max(1, total_rows)) * 100.0, 2)
    if duplicate_rows == 0:
        uniqueness_score = 100.0
    else:
        uniqueness_score = round(
            max(20.0, min(96.0, 100.0 - (4.0 + duplicate_pct * 3.0))),
            1,
        )

    overall_score = round(
        0.35 * completeness_score
        + 0.30 * type_validity_score
        + 0.20 * outlier_score
        + 0.15 * uniqueness_score,
        1,
    )

    return {
        "overall_score": overall_score,
        "completeness_score": completeness_score,
        "type_validity_score": type_validity_score,
        "outlier_score": outlier_score,
        "uniqueness_score": uniqueness_score,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "total_cells": total_cells,
        "missing_cells": total_missing_cells,
        "missing_rows": missing_rows,
        "missing_pct": missing_cell_pct,
        "invalid_cells": total_invalid_cells,
        "invalid_pct": invalid_cell_pct,
        "anomalous_cols_count": anomalous_cols_count,
        "outlier_cells": total_outlier_cells,
        "outlier_pct": outlier_pct,
        "duplicate_rows": duplicate_rows,
        "duplicate_pct": duplicate_pct,
        "columns": col_cards,
    }


def _simulate_cleaned_snapshot(raw_snap: dict[str, Any]) -> dict[str, Any]:
    """Projects the post-cleaning trust score snapshot when the dataset has not been cleaned yet."""
    completeness_score = 100.0
    type_validity_score = 100.0
    uniqueness_score = 100.0
    outlier_score = float(raw_snap.get("outlier_score", 100.0))
    overall_score = round(
        0.35 * completeness_score
        + 0.30 * type_validity_score
        + 0.20 * outlier_score
        + 0.15 * uniqueness_score,
        1,
    )
    total_rows = max(
        0,
        int(raw_snap.get("total_rows", 0)) - int(raw_snap.get("duplicate_rows", 0)),
    )
    total_cols = int(raw_snap.get("total_cols", 0))
    return {
        "overall_score": overall_score,
        "completeness_score": completeness_score,
        "type_validity_score": type_validity_score,
        "outlier_score": outlier_score,
        "uniqueness_score": uniqueness_score,
        "total_rows": total_rows,
        "total_cols": total_cols,
        "total_cells": total_rows * total_cols,
        "missing_cells": 0,
        "missing_rows": 0,
        "missing_pct": 0.0,
        "invalid_cells": 0,
        "invalid_pct": 0.0,
        "anomalous_cols_count": 0,
        "outlier_cells": int(raw_snap.get("outlier_cells", 0)),
        "outlier_pct": float(raw_snap.get("outlier_pct", 0.0)),
        "duplicate_rows": 0,
        "duplicate_pct": 0.0,
    }


@data_bp.route("/get_trust_report", methods=["GET"])
def get_trust_report():
    """Returns side-by-side Raw (Uncleaned) vs Cleaned dataset trust scores and column scorecard."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Önce bir veri seti yükleyin."}), 400

    try:
        current_snap = _compute_trust_snapshot(global_df)
        baseline = get_baseline_trust()
        if baseline is None:
            set_baseline_trust(current_snap)
            baseline = current_snap

        is_cleaned = get_is_cleaned()
        has_remaining_issues = (
            current_snap["missing_cells"] > 0
            or current_snap["invalid_cells"] > 0
            or current_snap["duplicate_rows"] > 0
        )
        if is_cleaned and not has_remaining_issues:
            cleaned_snap = current_snap
        else:
            cleaned_snap = _simulate_cleaned_snapshot(current_snap)

        score_delta = round(
            float(cleaned_snap["overall_score"]) - float(baseline["overall_score"]),
            1,
        )

        return jsonify(
            {
                "success": True,
                "is_cleaned": bool(is_cleaned and not has_remaining_issues),
                "has_cleaning_history": bool(is_cleaned),
                "score_delta": score_delta,
                "raw_report": baseline,
                "cleaned_report": cleaned_snap,
                "current_report": current_snap,
                "has_Guven_Skoru_AI": "Guven_Skoru_AI" in global_df.columns,
            }
        )
    except Exception as e:
        logger.exception("get_trust_report hatası")
        return jsonify({"error": f"Güven raporu oluşturulamadı: {e}"}), 500


@data_bp.route("/auto_heal_all_trust", methods=["POST"])
def auto_heal_all_trust():
    """
    One-click full dataset healing from the Trust Studio:
    1. Captures raw baseline trust snapshot if not yet captured.
    2. Repairs all anomalous numeric-text columns using smart_heal.
    3. Imputes remaining missing values (median/mean for numeric, mode/'Bilinmiyor' for categorical).
    4. Removes duplicate rows (for datasets <= 500k rows).
    5. Returns updated raw vs cleaned trust reports.
    """
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Aktif veri seti bulunamadı."}), 400

    try:
        if get_baseline_trust() is None:
            set_baseline_trust(_compute_trust_snapshot(global_df))

        # 1. Smart heal all anomalous columns
        healed_df, repaired_cols = repair_column_data(
            global_df, target_column="__all__", repair_mode="smart_heal"
        )

        # 2. Fill missing numeric and categorical values (massive-dataset optimized)
        healed_df = clean_missing_data(healed_df, action="fill_mean")

        # 3. Drop full-row duplicates safely without single-column subset corruption
        if len(healed_df) <= 500_000:
            healed_df = healed_df.drop_duplicates(ignore_index=True)
        elif (
            len(healed_df) <= 2_000_000
            and int(healed_df.iloc[:40_000].duplicated().sum()) > 0
        ):
            healed_df = healed_df.drop_duplicates(ignore_index=True)

        set_df(healed_df, 1)
        set_is_cleaned(True)

        current_snap = _compute_trust_snapshot(healed_df)
        baseline = get_baseline_trust() or current_snap
        score_delta = round(
            float(current_snap["overall_score"]) - float(baseline["overall_score"]),
            1,
        )

        numeric_cols = healed_df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = healed_df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()
        health_data = _compute_health_dict(healed_df)

        return jsonify(
            {
                "success": True,
                "is_cleaned": True,
                "has_cleaning_history": True,
                "repaired_columns": repaired_cols,
                "score_delta": score_delta,
                "raw_report": baseline,
                "cleaned_report": current_snap,
                "current_report": current_snap,
                "total_rows": len(healed_df),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
                "health": health_data,
                "has_Guven_Skoru_AI": "Guven_Skoru_AI" in healed_df.columns,
            }
        )
    except Exception as e:
        logger.exception("auto_heal_all_trust hatası")
        return jsonify({"error": f"Otomatik veri onarma hatası: {e}"}), 500
