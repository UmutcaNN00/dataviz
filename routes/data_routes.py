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
from core.store import get_df, set_df
from services.data_healer import (
    clean_missing_data,
    detect_column_anomalies,
    repair_column_data,
)
from services.file_service import (
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
        repaired_df, cols_to_repair = repair_column_data(
            global_df, target_column=target_column, repair_mode=repair_mode
        )
        set_df(repaired_df, 1)

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
    try:
        cleaned_df = clean_missing_data(global_df, action=action)
        set_df(cleaned_df, 1)

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

        df2.columns = [str(c).replace("\ufeff", "").strip() for c in df2.columns]
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

    df2.columns = [str(c).replace("\ufeff", "").strip() for c in df2.columns]

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

        merged = pd.merge(
            global_df_temp,
            df2_temp,
            on="_merge_key_",
            how=cast(Any, join_type),
            suffixes=("", "_2"),
        )
        merged.drop(columns=["_merge_key_"], inplace=True)

        if key2 + "_2" in merged.columns:
            merged.drop(columns=[key2 + "_2"], inplace=True)

        merged = merged.reset_index(drop=True)
        old_cols = set(global_df.columns)
        new_cols = [c for c in merged.columns if c not in old_cols]

        global_df = merged
        set_df(global_df, 1)

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
