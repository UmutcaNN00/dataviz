"""
Upload Routes Blueprint - File Ingestion, Sheet Switching, and Sheet Previews
Supports CSV, Excel (.xlsx, .xls), and Apache Parquet formats.
"""

import logging

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, request

# isort: split
from core.store import get_df, get_excel_data, set_df, set_excel_data
from services.file_service import (
    clean_dataframe,
    read_csv_safely,
    read_excel_safely,
    read_parquet_safely,
)

logger = logging.getLogger(__name__)

upload_bp = Blueprint("upload", __name__)


@upload_bp.route("/upload", methods=["POST"])
def upload():
    """Handles dataset file uploads across CSV, Parquet, and Excel formats."""
    if "file" not in request.files:
        return jsonify(
            {"error": "İstekte dosya bulunamadı. Lütfen bir dosya seçin."}
        ), 400
    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Herhangi bir dosya seçilmedi."}), 400

    filename = file.filename.lower()
    logger.info(f"Dosya yükleme isteği alındı: {file.filename}")

    try:
        sheet_names = []
        active_sheet = None

        if filename.endswith(".parquet"):
            df = read_parquet_safely(file)
            set_excel_data(None, [])
        elif filename.endswith(".csv"):
            df = read_csv_safely(file)
            set_excel_data(None, [])
        elif filename.endswith((".xls", ".xlsx")):
            df, sheets_dict, sheet_names, active_sheet = read_excel_safely(file)
            set_excel_data(sheets_dict, sheet_names)
        else:
            return jsonify(
                {
                    "error": "Desteklenmeyen dosya formatı. Lütfen sadece .parquet, .csv, .xlsx veya .xls uzantılı dosyalar yükleyin."
                }
            ), 400

        if df is None or df.empty or len(df.columns) == 0:
            return jsonify(
                {"error": "Yüklenen dosyada geçerli veri veya sütun bulunamadı."}
            ), 400

        df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
        set_df(df, 1)
        set_df(None, 2)

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        logger.info(
            f"Yükleme başarılı: {file.filename} -> {len(df)} satır, {len(df.columns)} sütun"
        )

        return jsonify(
            {
                "success": True,
                "total_rows": len(df),
                "total_cols": len(df.columns),
                "sheet_names": sheet_names,
                "active_sheet": active_sheet
                or (sheet_names[0] if sheet_names else None),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
            }
        )
    except pd.errors.EmptyDataError:
        logger.warning(f"Boş dosya yüklendi: {file.filename}")
        return jsonify(
            {"error": "Yüklenen dosya tamamen boş veya veri içermiyor."}
        ), 400
    except UnicodeDecodeError as e:
        logger.error(f"Kodlama hatası ({file.filename}): {e}")
        return jsonify(
            {
                "error": "Dosya karakter kodlaması çözülemedi. Lütfen dosyanın UTF-8 veya Windows-1254 (Türkçe) formatında olduğundan emin olun."
            }
        ), 400
    except ValueError as e:
        logger.error(f"Doğrulama hatası ({file.filename}): {e}")
        return jsonify({"error": str(e)}), 400
    except Exception as e:
        logger.exception(f"Dosya yükleme hatası ({file.filename})")
        return jsonify({"error": f"Dosya işlenirken bir hata oluştu: {e}"}), 400


@upload_bp.route("/select_sheet", methods=["POST"])
@upload_bp.route("/switch_sheet", methods=["POST"])
def select_sheet():
    """Switches the active DataFrame to a selected Excel sheet."""
    excel_file, sheet_names = get_excel_data()

    if not excel_file:
        return jsonify({"error": "Yüklü bir Excel dosyası bulunamadı."}), 400

    req_json = request.get_json(silent=True) or {}
    sheet_name = req_json.get("sheet_name") or request.form.get("sheet_name")
    if not sheet_name or sheet_name not in sheet_names:
        return jsonify(
            {
                "error": f"Geçersiz sayfa adı: '{sheet_name}'. Mevcut sayfalar: {', '.join(sheet_names)}"
            }
        ), 400

    try:
        if isinstance(excel_file, dict):
            df = excel_file.get(sheet_name)
            if df is not None:
                df = df.copy()
        elif hasattr(excel_file, "parse"):
            df = clean_dataframe(excel_file.parse(sheet_name))
        else:
            return jsonify({"error": "Excel sayfa verisi okunamadı."}), 400

        if df is None or df.empty:
            return jsonify(
                {"error": f"'{sheet_name}' sayfası boş veya veri içermiyor."}
            ), 400

        df.columns = [str(c).replace("\ufeff", "").strip() for c in df.columns]
        set_df(df, 1)

        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        logger.info(
            f"Excel sayfası değiştirildi: {sheet_name} ({len(df)} satır, {len(df.columns)} sütun)"
        )

        return jsonify(
            {
                "success": True,
                "active_sheet": sheet_name,
                "total_rows": len(df),
                "total_cols": len(df.columns),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
            }
        )
    except Exception as e:
        logger.exception("Sayfa değiştirme hatası")
        return jsonify({"error": f"Sayfa değiştirilirken bir hata oluştu: {e}"}), 400


@upload_bp.route("/get_sheet_preview", methods=["GET"])
def get_sheet_preview():
    """Returns preview records and schema metadata for a specified or active sheet."""
    excel_file, sheet_names = get_excel_data()
    sheet_name = request.args.get("sheet_name")
    try:
        limit = max(1, min(int(request.args.get("limit", 10)), 500))
    except (ValueError, TypeError):
        limit = 10

    target_df = None
    resolved_sheet_name = sheet_name

    if excel_file:
        if sheet_name and sheet_name in sheet_names:
            target_df = (
                excel_file.get(sheet_name)
                if isinstance(excel_file, dict)
                else excel_file.parse(sheet_name)
            )
        elif sheet_names:
            resolved_sheet_name = sheet_names[0]
            target_df = (
                excel_file.get(resolved_sheet_name)
                if isinstance(excel_file, dict)
                else excel_file.parse(resolved_sheet_name)
            )

    if target_df is None:
        target_df = get_df(1)
        resolved_sheet_name = resolved_sheet_name or "active_dataset"

    if target_df is None or target_df.empty:
        return jsonify({"error": "Önizleme yapılacak sayfa veya veri bulunamadı."}), 400

    head_df = target_df.head(limit).replace([np.inf, -np.inf], np.nan)
    preview_df = head_df.astype(object).where(pd.notnull(head_df), None)
    preview_rows = preview_df.to_dict(orient="records")

    return jsonify(
        {
            "success": True,
            "sheet_name": resolved_sheet_name,
            "total_rows": len(target_df),
            "total_cols": len(target_df.columns),
            "columns": target_df.columns.tolist(),
            "preview": preview_rows,
        }
    )
