"""
Main Routes Blueprint - Landing Page, Studio, Health, and Sample Data
"""

import logging
import os

import numpy as np
import pandas as pd
from flask import Blueprint, jsonify, render_template

# isort: split
from core.config import BASE_DIR
from core.store import (
    get_df,
    set_baseline_trust,
    set_df,
    set_excel_data,
    set_is_cleaned,
)
from services.file_service import clean_dataframe, read_csv_safely, read_excel_safely

logger = logging.getLogger(__name__)

main_bp = Blueprint("main", __name__)


@main_bp.route("/", methods=["GET"])
def index():
    """Renders the landing page."""
    return render_template("landing.html")


@main_bp.route("/analysis", methods=["GET"])
def analysis():
    """Renders the primary data analysis studio."""
    return render_template("analysis.html")


@main_bp.route("/health", methods=["GET"])
def health():
    """Health check endpoint indicating server and engine status."""
    return jsonify({"status": "ok", "service": "DataViz", "engine": "Polars"}), 200


@main_bp.route("/load_sample", methods=["GET", "POST"])
def load_sample():
    """Loads a demo sample dataset or generates a synthetic academic dataset."""
    try:
        sample_path = None
        candidates = [
            "ornek_veri_seti.xlsx",
            "1_Satis_Islemleri_Devasa.xlsx",
            "test_satislar.csv",
        ]

        for candidate in candidates:
            for p in [os.path.join(BASE_DIR, candidate), candidate]:
                if os.path.exists(p):
                    sample_path = p
                    break
            if sample_path:
                break

        sheet_names = []
        active_sheet = None
        loaded_file_name = "Akademik_Ornek_Veri_Seti.xlsx"

        if sample_path and sample_path.endswith(".xlsx"):
            with open(sample_path, "rb") as f:
                df, sheets_dict, sheet_names, active_sheet = read_excel_safely(f)
            loaded_file_name = os.path.basename(sample_path)
            set_df(df, 1)
            set_df(None, 2)
            set_excel_data(sheets_dict, sheet_names)
        elif sample_path and sample_path.endswith(".csv"):
            with open(sample_path, "rb") as f:
                df = read_csv_safely(f)
            loaded_file_name = os.path.basename(sample_path)
            set_df(df, 1)
            set_df(None, 2)
            set_excel_data(None, [])
        else:
            rng = np.random.default_rng(42)
            categories = [
                "Elektronik",
                "Mobilya",
                "Giyim",
                "Gıda",
                "Kırtasiye",
                "Kozmetik",
            ]
            regions = ["Marmara", "Ege", "İç Anadolu", "Akdeniz", "Karadeniz"]
            months = [
                "Ocak",
                "Şubat",
                "Mart",
                "Nisan",
                "Mayıs",
                "Haziran",
                "Temmuz",
                "Ağustos",
            ]
            n = 120
            kar_arr = rng.integers(200, 15000, n).astype(float)
            kar_arr[[5, 18, 42, 77, 103]] = np.nan
            mem_arr = rng.uniform(3.0, 5.0, n).round(2)
            mem_arr[[11, 29, 64, 91]] = np.nan
            indirim_list = [f"{rng.integers(100, 2500)} TL" for _ in range(n)]
            indirim_list[3] = "binikiyüz"
            indirim_list[14] = "yok"
            indirim_list[27] = "belirsiz"
            indirim_list[55] = "hatalı_giriş"
            indirim_list[88] = "üçbin"

            df = pd.DataFrame(
                {
                    "Kategori": rng.choice(categories, n),
                    "Bölge": rng.choice(regions, n),
                    "Dönem": rng.choice(months, n),
                    "Satış_Tutarı": rng.integers(1000, 50000, n),
                    "Kar": kar_arr,
                    "Maliyet": rng.integers(800, 35000, n),
                    "Müşteri_Memnuniyeti": mem_arr,
                    "İşlem_Adedi": rng.integers(1, 20, n),
                    "İndirim_Tutarı": indirim_list,
                }
            )
            # Add 3 duplicate rows and 2 statistical outliers for realistic quality demo
            df.loc[0, "Satış_Tutarı"] = 245000
            df.loc[1, "Satış_Tutarı"] = 260000
            df = pd.concat([df, df.iloc[:3]], ignore_index=True)
            df = clean_dataframe(df)
            set_df(df, 1)
            set_df(None, 2)
            set_excel_data(None, [])

        set_baseline_trust(None)
        set_is_cleaned(False)
        df = get_df(1)
        if df is None:
            return jsonify({"error": "Örnek veri oluşturulamadı."}), 500
        numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category", "bool", "string"]
        ).columns.tolist()

        return jsonify(
            {
                "success": True,
                "file_name": loaded_file_name,
                "total_rows": len(df),
                "total_cols": len(df.columns),
                "sheet_names": sheet_names,
                "active_sheet": active_sheet
                or (sheet_names[0] if sheet_names else None),
                "numeric_columns": numeric_cols,
                "categorical_columns": categorical_cols,
            }
        )
    except Exception:
        logger.exception("Örnek veri yükleme hatası")
        return jsonify({"error": "Örnek veri yüklenirken bir hata oluştu."}), 500
