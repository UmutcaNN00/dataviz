"""
Stats Routes Blueprint - Statistical Calculations, Executive KPI Tiles, and Academic AI Interpretation
"""

import logging
import numpy as np
from flask import Blueprint, request, jsonify

from core.store import get_df
from services.stats_service import (
    apply_filters,
    compute_column_statistics,
    compute_advanced_stats,
    generate_kpi_summary,
)
from services.ai_service import generate_academic_insight

logger = logging.getLogger(__name__)

stats_bp = Blueprint('stats', __name__)


@stats_bp.route('/get_stats', methods=['POST'])
def get_stats():
    """Computes descriptive and inferential statistics (ANOVA, t-test, correlation, regression)."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Veri yok'}), 400

    data = request.get_json(silent=True) or {}
    cols = data.get('columns') or data.get('y_cols') or data.get('y') or []
    if isinstance(cols, str):
        cols = [cols] if cols else []
    filters = data.get('filters', [])
    x_col = data.get('x_col') or data.get('x')
    corr_method = data.get('corr_method', 'pearson')
    reg_model = data.get('reg_model', 'linear')

    active_df = apply_filters(global_df, filters)
    active_df = active_df.replace([np.inf, -np.inf], np.nan)
    if not cols:
        num_cols = active_df.select_dtypes(include=['number']).columns.tolist()
        cols = num_cols[:6]

    if not cols or active_df.empty:
        return jsonify({'stats': {}, 'advanced': {}, 'total_active_rows': len(active_df)})

    try:
        stats = compute_column_statistics(active_df, cols)
        advanced = compute_advanced_stats(
            active_df,
            cols,
            x_col=x_col,
            corr_method=corr_method,
            reg_model=reg_model
        )

        return jsonify({
            'stats': stats,
            'advanced': advanced,
            'total_active_rows': len(active_df)
        })
    except Exception as e:
        logger.exception(f"get_stats hatası: {e}")
        return jsonify({'error': f"İstatistik hesaplanırken hata: {str(e)}"}), 500


@stats_bp.route('/get_kpi_summary', methods=['POST'])
@stats_bp.route('/get_kpis', methods=['POST'])
def get_kpi_summary():
    """Generates high-level KPI tiles for the active filtered dataset."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Veri yok'}), 400

    data = request.get_json(silent=True) or {}
    filters = data.get('filters', [])

    try:
        active_df = apply_filters(global_df, filters)
        kpis_data = generate_kpi_summary(active_df, total_original_rows=len(global_df))
        return jsonify(kpis_data)
    except Exception as e:
        logger.exception(f"get_kpi_summary hatası: {e}")
        return jsonify({'error': f"KPI özeti hesaplanırken hata: {str(e)}"}), 500


@stats_bp.route('/generate_interpretation', methods=['POST'])
@stats_bp.route('/generate_insight', methods=['POST'])
def generate_interpretation():
    """Generates academic, APA-style statistical commentary and business insights."""
    data = request.get_json(silent=True) or {}
    stats = data.get('stats', {})
    chart = data.get('chart_type', 'Grafik')
    x_col = data.get('x_col', 'Bilinmiyor')
    y_cols = data.get('y_cols', [])

    try:
        result = generate_academic_insight(stats, chart_type=chart, x_col=x_col, y_cols=y_cols)
        return jsonify(result)
    except Exception as e:
        logger.exception(f"generate_interpretation hatası: {e}")
        return jsonify({'error': f"Yorum üretilirken hata: {str(e)}"}), 500
