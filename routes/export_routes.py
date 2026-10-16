"""
Export Routes Blueprint - Dataset Exporting (CSV, Excel, Parquet), Pivot Matrix, and Academic PDF Reports
"""

import logging

from flask import Blueprint, jsonify, request, send_file

# isort: split
from core.store import get_df
from services.export_service import export_dataframe, export_pivot_to_excel
from services.report_service import generate_academic_pdf_report
from services.stats_service import apply_filters

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)


@export_bp.route("/export_pivot_excel", methods=["POST"])
def export_pivot_excel():
    """Exports the generated pivot table matrix to an formatted Excel (.xlsx) file."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Dışa aktarılacak veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    cols = data.get("cols", [])
    values = data.get("values", [])
    agg_func = data.get("agg_func", "sum")
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        buffer, mimetype, download_name = export_pivot_to_excel(
            active_df, rows=rows, cols=cols, values=values, agg_func=agg_func
        )
        return send_file(
            buffer, mimetype=mimetype, as_attachment=True, download_name=download_name
        )
    except ValueError as e_val:
        return jsonify({"error": str(e_val)}), 400
    except Exception as e:
        logger.exception("export_pivot hatası")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_data", methods=["POST"])
def export_data():
    """Streams the active filtered dataset as a CSV, Excel (.xlsx), or Apache Parquet file."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Dışa aktarılacak aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {}
    export_format = str(data.get("format") or "csv").lower().strip()
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        buffer, mimetype, download_name = export_dataframe(
            active_df, export_format=export_format
        )
        return send_file(
            buffer, mimetype=mimetype, as_attachment=True, download_name=download_name
        )
    except ValueError as e_val:
        return jsonify({"error": str(e_val)}), 400
    except Exception as e:
        logger.exception("export_data hatası")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_parquet", methods=["POST", "GET"])
def export_parquet():
    """Explicit endpoint to stream the dataset directly as an Apache Parquet file."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Dışa aktarılacak aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {} if request.method == "POST" else {}
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        buffer, mimetype, download_name = export_dataframe(
            active_df, export_format="parquet"
        )
        return send_file(
            buffer, mimetype=mimetype, as_attachment=True, download_name=download_name
        )
    except ValueError as e_val:
        return jsonify({"error": str(e_val)}), 400
    except Exception as e:
        logger.exception("export_parquet hatası")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_csv", methods=["POST", "GET"])
def export_csv():
    """Explicit endpoint to stream the dataset directly as a CSV file."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Dışa aktarılacak aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {} if request.method == "POST" else {}
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        buffer, mimetype, download_name = export_dataframe(
            active_df, export_format="csv"
        )
        return send_file(
            buffer, mimetype=mimetype, as_attachment=True, download_name=download_name
        )
    except ValueError as e_val:
        return jsonify({"error": str(e_val)}), 400
    except Exception as e:
        logger.exception("export_csv hatası")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_excel", methods=["POST", "GET"])
def export_excel():
    """Explicit endpoint to stream the dataset directly as an Excel (.xlsx) file."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Dışa aktarılacak aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {} if request.method == "POST" else {}
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        buffer, mimetype, download_name = export_dataframe(
            active_df, export_format="xlsx"
        )
        return send_file(
            buffer, mimetype=mimetype, as_attachment=True, download_name=download_name
        )
    except ValueError as e_val:
        return jsonify({"error": str(e_val)}), 400
    except Exception as e:
        logger.exception("export_excel hatası")
        return jsonify({"error": str(e)}), 500


@export_bp.route("/export_academic_pdf", methods=["POST", "GET"])
@export_bp.route("/export_pdf_report", methods=["POST", "GET"])
def export_academic_pdf():
    """
    Generates and streams an Academic / TÜBİTAK publication-standard PDF report
    with full descriptive statistics, hypothesis tests, OLS multiple regression, and APA commentary.
    """
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Rapor oluşturulacak aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {}
    title = data.get("title") or "TÜBİTAK & Akademik Veri Analiz Raporu"
    subtitle = data.get("subtitle") or "Betimsel İstatistikler, Hipotez Testleri ve Regresyon Modellemesi"
    author = data.get("author") or "DataViz Analitik Laboratuvarı"
    x_col = data.get("x_col") or data.get("x")
    y_cols = data.get("y_cols") or data.get("columns") or []
    if isinstance(y_cols, str):
        y_cols = [y_cols]
    project_code = data.get("project_code") or "TUBITAK-DV-2026"
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        if active_df is None or active_df.empty:
            return jsonify({"error": "Uygulanan filtreler sonucunda raporlanacak veri kalmadı."}), 400
        buffer, download_name = generate_academic_pdf_report(
            active_df,
            title=title,
            subtitle=subtitle,
            author=author,
            x_col=x_col,
            y_cols=y_cols,
            project_code=project_code,
        )
        return send_file(
            buffer,
            mimetype="application/pdf",
            as_attachment=True,
            download_name=download_name,
        )
    except Exception as e:
        logger.exception("export_academic_pdf hatası")
        return jsonify({"error": f"Akademik PDF raporu oluşturulurken hata: {e}"}), 500

