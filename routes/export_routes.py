"""
Export Routes Blueprint - Dataset Exporting (CSV, Excel, Parquet) and Pivot Matrix Computing / Exporting
"""

import logging

from flask import Blueprint, jsonify, request, send_file

# isort: split
from core.store import get_df
from services.export_service import export_dataframe, export_pivot_to_excel
from services.stats_service import apply_filters, compute_pivot_data

logger = logging.getLogger(__name__)

export_bp = Blueprint("export", __name__)


@export_bp.route("/get_pivot_data", methods=["POST"])
def get_pivot_data():
    """Computes an interactive pivot matrix for cross-tabulation."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Lütfen önce bir veri seti yükleyin."}), 400

    data = request.get_json(silent=True) or {}
    rows = data.get("rows", [])
    cols = data.get("cols", [])
    values = data.get("values", [])
    agg_func = data.get("agg_func", "sum")
    filters = data.get("filters", [])

    try:
        active_df = apply_filters(global_df, filters)
        pivot_data = compute_pivot_data(
            active_df, rows=rows, cols=cols, values=values, agg_func=agg_func
        )
        return jsonify(pivot_data)
    except ValueError as e_val:
        return jsonify({"error": str(e_val)}), 400
    except Exception as e:
        logger.exception("Pivot tablosu hesaplanırken hata")
        return jsonify({"error": f"Pivot tablosu hesaplanırken hata oluştu: {e}"}), 500


@export_bp.route("/export_pivot", methods=["POST"])
@export_bp.route("/export_pivot_excel", methods=["POST"])
def export_pivot():
    """Exports the generated pivot table matrix to an formatted Excel (.xlsx) file."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Veri yok"}), 400

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
