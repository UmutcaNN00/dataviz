"""
Stats Routes Blueprint - Statistical Calculations, Executive KPI Tiles, and Academic AI Interpretation
"""

import logging
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify

from core.store import get_df
from services.stats_service import (
    apply_filters,
    compute_column_statistics,
    compute_advanced_stats,
    generate_kpi_summary,
    compute_correlation_matrix,
    compute_robust_regression,
    compute_robust_correlation,
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
@stats_bp.route('/get_ai_insight', methods=['POST'])
def generate_interpretation():
    """Generates academic, APA-style statistical commentary and business insights."""
    data = request.get_json(silent=True) or {}
    stats = data.get('stats', {})
    advanced = data.get('advanced_stats', {})
    chart = data.get('chart_type', 'Grafik')
    x_col = data.get('x_col') or data.get('x') or 'Bilinmiyor'
    
    y_raw = data.get('y_cols') if data.get('y_cols') is not None else data.get('y')
    if isinstance(y_raw, list):
        y_cols = y_raw
    elif y_raw:
        y_cols = [str(y_raw)]
    else:
        y_cols = []

    try:
        result = generate_academic_insight(stats, advanced=advanced, chart_type=chart, x_col=x_col, y_cols=y_cols)
        return jsonify(result)
    except Exception as e:
        logger.exception(f"generate_interpretation hatası: {e}")
        return jsonify({'error': f"Yorum üretilirken hata: {str(e)}"}), 500


@stats_bp.route('/get_correlation_matrix', methods=['POST'])
def get_correlation_matrix_route():
    """Returns pairwise correlation matrix for all numeric columns."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({'error': 'Veri yok'}), 400

    data = request.get_json(silent=True) or {}
    filters = data.get('filters', [])
    method = data.get('method', 'pearson')
    cols = data.get('columns', [])

    active_df = apply_filters(global_df, filters)
    matrix_data = compute_correlation_matrix(active_df, num_cols=cols, method=method)
    return jsonify(matrix_data)


@stats_bp.route('/get_regression_studio_data', methods=['POST'])
def get_regression_studio_data_route():
    """
    Returns full regression curve, scatter points sample, correlation,
    and academic insights in a single round trip for the Regression Studio.
    """
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({'error': 'Önce dosya yükleyin'}), 400

    data = request.get_json(silent=True) or {}
    x_col = data.get('x_col') or data.get('x')
    y_col = data.get('y_col') or data.get('y')
    model_type = data.get('model_type', 'linear')
    corr_method = data.get('corr_method', 'pearson')
    filters = data.get('filters', [])
    max_scatter = int(data.get('max_scatter', 2500))

    num_cols = global_df.select_dtypes(include=['number']).columns.tolist()
    if not x_col or not y_col:
        if len(num_cols) >= 2:
            x_col = x_col or num_cols[0]
            y_col = y_col or num_cols[1]
        else:
            return jsonify({'error': 'Regresyon için en az 2 sayısal değişken gereklidir.'}), 400

    active_df = apply_filters(global_df, filters)
    if x_col not in active_df.columns or y_col not in active_df.columns:
        return jsonify({'error': f'Sütunlar bulunamadı: {x_col}, {y_col}'}), 400

    x_series = pd.to_numeric(active_df[x_col], errors='coerce')
    y_series = pd.to_numeric(active_df[y_col], errors='coerce')
    valid_mask = x_series.notna() & y_series.notna() & np.isfinite(x_series) & np.isfinite(y_series)

    total_valid = int(valid_mask.sum())
    if total_valid < 3:
        return jsonify({'error': 'Regresyon ve korelasyon için en az 3 geçerli sayısal değer gereklidir.'}), 400

    x_clean = x_series[valid_mask].values
    y_clean = y_series[valid_mask].values

    # Compute regression and correlation
    reg_result = compute_robust_regression(x_clean, y_clean, model_type=model_type)
    corr_result = compute_robust_correlation(x_clean, y_clean, method=corr_method)
    corr_result['r'] = corr_result.get('coef')

    # Scatter points sample
    if total_valid > max_scatter:
        sample_indices = np.random.RandomState(42).choice(total_valid, size=max_scatter, replace=False)
        scatter_x = [round(float(v), 4) for v in x_clean[sample_indices]]
        scatter_y = [round(float(v), 4) for v in y_clean[sample_indices]]
    else:
        scatter_x = [round(float(v), 4) for v in x_clean]
        scatter_y = [round(float(v), 4) for v in y_clean]

    # Generate academic interpretation text
    stats_mock = {
        y_col: {
            'mean': float(np.mean(y_clean)),
            'std': float(np.std(y_clean)),
            'count': total_valid
        }
    }
    adv_mock = {
        y_col: {
            'type': 'numeric',
            'correlation': corr_result.get('coef'),
            'corr_method': corr_method,
            'regression': reg_result.get('equation'),
            'r_squared': reg_result.get('r_squared'),
            'p_value': reg_result.get('p_value') or corr_result.get('p_value'),
            'se': reg_result.get('se'),
            'interpretation': corr_result.get('interpretation')
        }
    }
    try:
        insight = generate_academic_insight(stats_mock, advanced=adv_mock, chart_type='Scatter & Regresyon', x_col=x_col, y_cols=[y_col])
    except Exception as e_in:
        logger.debug(f"Insight generation error: {e_in}")
        insight = {'text': f"{x_col} ve {y_col} arasında {corr_method.upper()} korelasyonu {corr_result.get('coef', 0):.4f} olarak saptanmıştır.", 'key_findings': []}

    return jsonify({
        'success': True,
        'x_col': x_col,
        'y_col': y_col,
        'all_numeric_cols': num_cols,
        'model_type': model_type,
        'corr_method': corr_method,
        'total_valid': total_valid,
        'scatter_sample_count': len(scatter_x),
        'scatter_x': scatter_x,
        'scatter_y': scatter_y,
        'regression': reg_result,
        'correlation': corr_result,
        'insight': insight
    })

