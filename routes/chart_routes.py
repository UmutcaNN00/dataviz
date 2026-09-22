"""
Chart Routes Blueprint - Chart Data Aggregation, Column Value Discovery, and Regression Curves
"""

import logging
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify

from core.store import get_df
from services.stats_service import (
    safe_float,
    apply_filters,
    compute_robust_correlation,
    compute_robust_regression,
)

logger = logging.getLogger(__name__)

chart_bp = Blueprint('chart', __name__)


@chart_bp.route('/get_chart_data', methods=['POST'])
def get_chart_data():
    """Extracts, filters, and aggregates dataset records for Plotly visualizer."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Önce dosya yükleyin'}), 400

    data = request.get_json(silent=True) or {}
    x_col = data.get('x_col') or data.get('x')
    y_raw = data.get('y_cols') if 'y_cols' in data else data.get('y', [])
    if isinstance(y_raw, str):
        y_cols = [y_raw] if y_raw else []
    elif isinstance(y_raw, list):
        y_cols = [c for c in y_raw if c]
    else:
        y_cols = []

    agg_func = data.get('agg_func', 'sum')
    chart_type = data.get('chart_type', 'bar')
    filters = data.get('filters', [])

    active_df = apply_filters(global_df, filters)
    active_df = active_df.replace([np.inf, -np.inf, np.nan], 0)
    if active_df.empty:
        return jsonify({'error': 'Uygulanan filtreler sonucunda görüntülenecek veri kalmadı.'}), 400

    available_cols = active_df.columns.tolist()
    if x_col and x_col not in available_cols:
        x_col = None
    y_cols = [y for y in y_cols if y in available_cols]

    # Convert y_cols to numeric if needed for quantitative charts
    for y in y_cols:
        if y in active_df.columns and not pd.api.types.is_numeric_dtype(active_df[y]):
            try:
                converted = pd.to_numeric(active_df[y].astype(str).str.replace(r'[^\d.-]', '', regex=True), errors='coerce')
                if converted.notna().sum() > 0:
                    active_df[y] = converted.fillna(0)
            except Exception:
                pass

    raw_charts = [
        'histogram', 'histogram2d', 'box', 'violin', 'scatter', 'bubble',
        'scatter3d', 'line3d', 'scattergeo', 'scattermatrix', 'density2d',
        'rug', 'strip', 'parcoords', 'parcats', 'candlestick', 'ohlc', 'dumbbell', 'ternary'
    ]
    corr_charts = ['heatmap', 'surface', 'contour', 'carpet', 'contourcarpet']
    response_data = {'success': True, 'chart_type': chart_type, 'total_active_rows': len(active_df)}

    try:
        if chart_type in raw_charts:
            df_sample = active_df.head(5000)
            raw_dict = {}
            if x_col:
                raw_dict['__x__'] = df_sample[x_col].fillna('N/A').tolist()
            for y in y_cols:
                raw_dict[y] = df_sample[y].astype(object).fillna(0).tolist()
            if not y_cols and x_col:
                raw_dict[x_col] = df_sample[x_col].fillna('N/A').tolist()
            response_data['raw'] = raw_dict
        elif chart_type in corr_charts:
            num_cols = active_df.select_dtypes(include=['number']).columns.tolist()
            calc_cols = y_cols if len(y_cols) >= 2 else (num_cols[:6] if len(num_cols) >= 2 else y_cols)
            if len(calc_cols) < 2:
                agg_dict = {'__x__': ['Tümü']}
                for y in y_cols:
                    agg_dict[y] = [float(active_df[y].sum()) if pd.notnull(active_df[y].sum()) else 0]
                response_data['agg'] = agg_dict
            else:
                corr_matrix = active_df[calc_cols].corr()
                response_data['corr'] = {'labels': calc_cols, 'matrix': corr_matrix.fillna(0).values.tolist()}
        else:
            if not x_col:
                agg_dict = {'__x__': ['Tümü']}
                for y in y_cols:
                    if agg_func == 'sum':
                        val = active_df[y].sum()
                    elif agg_func == 'mean':
                        val = active_df[y].mean()
                    elif agg_func == 'median':
                        val = active_df[y].median()
                    elif agg_func == 'min':
                        val = active_df[y].min()
                    elif agg_func == 'max':
                        val = active_df[y].max()
                    else:
                        val = active_df[y].count()
                    agg_dict[y] = [float(val) if pd.notnull(val) else 0]
                response_data['agg'] = agg_dict
            else:
                if not y_cols:
                    # Auto count frequencies if only X column is given
                    counts = active_df[x_col].value_counts().head(100)
                    response_data['agg'] = {
                        '__x__': [str(x) for x in counts.index.tolist()],
                        'Adet': counts.values.tolist()
                    }
                else:
                    grouped = active_df.groupby(x_col)
                    if agg_func == 'sum':
                        grouped = grouped.sum(numeric_only=True)
                    elif agg_func == 'mean':
                        grouped = grouped.mean(numeric_only=True)
                    elif agg_func == 'median':
                        grouped = grouped.median(numeric_only=True)
                    elif agg_func == 'min':
                        grouped = grouped.min(numeric_only=True)
                    elif agg_func == 'max':
                        grouped = grouped.max(numeric_only=True)
                    else:
                        grouped = grouped.count()

                    if len(grouped) > 100:
                        if agg_func in ['sum', 'mean'] and y_cols and y_cols[0] in grouped.columns:
                            grouped = grouped.sort_values(by=y_cols[0], ascending=False).head(100)
                        else:
                            grouped = grouped.head(100)

                    agg_dict = {'__x__': [str(x) for x in grouped.index.tolist()]}
                    for y in y_cols:
                        if y in grouped.columns:
                            agg_dict[y] = grouped[y].astype(object).fillna(0).tolist()
                        else:
                            try:
                                agg_dict[y] = active_df.groupby(x_col)[y].count().loc[grouped.index].fillna(0).tolist()
                            except Exception:
                                agg_dict[y] = [0] * len(grouped)
                    response_data['agg'] = agg_dict

        return jsonify(response_data)
    except Exception as e:
        logger.exception(f"get_chart_data hatası: {e}")
        return jsonify({'error': str(e)}), 500


@chart_bp.route('/get_column_unique_values', methods=['GET', 'POST'])
@chart_bp.route('/get_column_details', methods=['GET', 'POST'])
def get_column_unique_values():
    """Retrieves unique categories or numerical ranges for dynamic slicers and filters."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({'error': 'Veri yok'}), 400

    col = request.args.get('column')
    if not col:
        data = request.get_json(silent=True) or {}
        col = data.get('column')
    if not col or col not in global_df.columns:
        return jsonify({'error': 'Sütun bulunamadı'}), 400

    series = global_df[col]
    is_num = pd.api.types.is_numeric_dtype(series)

    if is_num:
        min_v = float(series.min()) if pd.notnull(series.min()) else 0.0
        max_v = float(series.max()) if pd.notnull(series.max()) else 100.0
        unique_sample = [safe_float(v) for v in series.dropna().unique()[:50]]
        return jsonify({
            'column': col,
            'type': 'num',
            'min': min_v,
            'max': max_v,
            'count': int(series.count()),
            'unique_values': unique_sample
        })
    else:
        val_counts = series.astype(str).value_counts().head(100)
        categories = [{'value': str(k), 'count': int(v)} for k, v in val_counts.items()]
        unique_vals = [c['value'] for c in categories]
        return jsonify({
            'column': col,
            'type': 'cat',
            'categories': categories,
            'values': unique_vals,
            'unique_values': unique_vals,
            'total_unique': int(series.nunique())
        })


@chart_bp.route('/get_regression_curve', methods=['POST'])
def get_regression_curve():
    """Calculates regression curve coefficients and correlation metrics for chart overlays."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({'error': 'Aktif veri seti bulunamadı.'}), 400

    data = request.get_json(silent=True) or {}
    x_col = data.get('x_col') or data.get('x')
    y_raw = data.get('y_col') or data.get('y') or data.get('y_cols')
    if isinstance(y_raw, list):
        y_col = y_raw[0] if y_raw else None
    else:
        y_col = y_raw

    model_type = data.get('model_type', 'linear')
    corr_method = data.get('corr_method', 'pearson')
    filters = data.get('filters', [])

    if not x_col or not y_col:
        return jsonify({'error': 'X ve Y sütunları seçilmelidir.'}), 400

    active_df = apply_filters(global_df, filters)
    if x_col not in active_df.columns or y_col not in active_df.columns:
        return jsonify({'error': 'Seçilen sütunlar veri setinde bulunamadı.'}), 400

    x_series = pd.to_numeric(active_df[x_col], errors='coerce')
    y_series = pd.to_numeric(active_df[y_col], errors='coerce')

    valid_mask = x_series.notna() & y_series.notna() & np.isfinite(x_series) & np.isfinite(y_series)
    x_vals = x_series[valid_mask].values
    y_vals = y_series[valid_mask].values

    if len(x_vals) < 3:
        return jsonify({'error': 'Regresyon ve korelasyon için en az 3 geçerli sayısal değer gereklidir.'}), 400

    try:
        reg_result = compute_robust_regression(x_vals, y_vals, model_type=model_type)
        corr_result = compute_robust_correlation(x_vals, y_vals, method=corr_method)
        corr_result['r'] = corr_result.get('coef')

        return jsonify({
            'success': True,
            'x_col': x_col,
            'y_col': y_col,
            'model_type': model_type,
            'corr_method': corr_method,
            'regression': reg_result,
            'correlation': corr_result
        })
    except Exception as e:
        logger.exception(f"get_regression_curve hatası: {e}")
        return jsonify({'error': f"Regresyon eğrisi hesaplanamadı: {str(e)}"}), 500
