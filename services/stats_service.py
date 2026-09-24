"""
Statistical Analysis and Modeling Service
Handles descriptive statistics, correlations, polynomial/linear/logarithmic regressions,
hypothesis testing (T-Test, ANOVA), KPI generation, filtering, and pivot matrices.
"""

import logging
import pandas as pd
import numpy as np
from scipy import stats as sp_stats

logger = logging.getLogger(__name__)


def safe_float(val, default=None):
    """
    Converts a value to a JSON-safe float, replacing NaN, Infinity, and -Infinity with default.
    """
    try:
        if val is None or pd.isna(val) or np.isinf(val):
            return default
        f = float(val)
        return f if np.isfinite(f) else default
    except Exception:
        return default


def apply_filters(df, filters):
    """
    Applies a list of categorical and numeric filters to a DataFrame.
    """
    if df is None or df.empty or not filters or not isinstance(filters, list):
        return df

    filtered_df = df.copy()
    for f in filters:
        col = f.get('column')
        if not col or col not in filtered_df.columns:
            continue
        ftype = f.get('type')
        if ftype == 'cat':
            selected_vals = f.get('values', [])
            if selected_vals and len(selected_vals) > 0:
                filtered_df = filtered_df[filtered_df[col].astype(str).isin([str(v) for v in selected_vals])]
        elif ftype == 'num':
            min_val = f.get('min')
            max_val = f.get('max')
            col_num = pd.to_numeric(filtered_df[col], errors='coerce')
            if min_val is not None and str(min_val).strip() != '':
                try:
                    filtered_df = filtered_df[col_num >= float(min_val)]
                except (ValueError, TypeError):
                    pass
            if max_val is not None and str(max_val).strip() != '':
                try:
                    filtered_df = filtered_df[col_num <= float(max_val)]
                except (ValueError, TypeError):
                    pass
    return filtered_df


def compute_robust_correlation(x_vals, y_vals, method='pearson'):
    """
    Computes Pearson, Spearman, or Kendall correlations with NaN safety and zero variance handling.
    """
    valid_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
    x_clean = np.asarray(x_vals)[valid_mask]
    y_clean = np.asarray(y_vals)[valid_mask]

    if len(x_clean) < 3 or np.all(x_clean == x_clean[0]) or np.all(y_clean == y_clean[0]):
        return {
            'coef': 0.0,
            'p_value': None,
            'method': method,
            'interpretation': 'Yetersiz veya sabit varyanslı veri',
            'sample_size': int(len(x_clean))
        }

    try:
        if method == 'spearman':
            res = sp_stats.spearmanr(x_clean, y_clean)
            coef = safe_float(res.statistic if hasattr(res, 'statistic') else res[0], 0.0)
            p_val = safe_float(res.pvalue if hasattr(res, 'pvalue') else res[1], None)
        elif method == 'kendall':
            res = sp_stats.kendalltau(x_clean, y_clean)
            coef = safe_float(res.statistic if hasattr(res, 'statistic') else res[0], 0.0)
            p_val = safe_float(res.pvalue if hasattr(res, 'pvalue') else res[1], None)
        else:  # pearson
            res = sp_stats.pearsonr(x_clean, y_clean)
            coef = safe_float(res.statistic if hasattr(res, 'statistic') else res[0], 0.0)
            p_val = safe_float(res.pvalue if hasattr(res, 'pvalue') else res[1], None)
    except Exception as e:
        logger.warning(f"Korelasyon hesaplama hatası ({method}): {e}")
        coef, p_val = 0.0, None

    abs_c = abs(coef) if coef is not None else 0
    sign = "Pozitif" if (coef or 0) >= 0 else "Negatif"
    if abs_c >= 0.8:
        strength = f"Çok Güçlü {sign} İlişki"
    elif abs_c >= 0.6:
        strength = f"Güçlü {sign} İlişki"
    elif abs_c >= 0.4:
        strength = f"Orta Düzey {sign} İlişki"
    elif abs_c >= 0.2:
        strength = f"Zayıf {sign} İlişki"
    else:
        strength = "İlişki Yok / İhmal Edilebilir"

    return {
        'coef': round(coef, 4) if coef is not None else 0.0,
        'p_value': p_val,
        'method': method,
        'interpretation': strength,
        'sample_size': int(len(x_clean))
    }


def compute_robust_regression(x_vals, y_vals, model_type='linear', num_points=100):
    """
    Computes Linear, Polynomial (degree 2, 3), Logarithmic, and Exponential regression models
    with R², standard error, and curve prediction points.
    """
    valid_mask = np.isfinite(x_vals) & np.isfinite(y_vals)
    x_clean = np.asarray(x_vals)[valid_mask]
    y_clean = np.asarray(y_vals)[valid_mask]

    if len(x_clean) < 3 or np.all(x_clean == x_clean[0]) or np.all(y_clean == y_clean[0]):
        return {
            'equation': 'Yetersiz veya sabit varyanslı veri',
            'r_squared': 0.0,
            'se': None,
            'p_value': None,
            'model_type': model_type,
            'trend_x': [],
            'trend_y': []
        }

    x_min, x_max = float(np.min(x_clean)), float(np.max(x_clean))
    x_curve = np.linspace(x_min, x_max, num_points)

    eq_str = ""
    r_squared = 0.0
    se = None
    p_val = None
    y_curve = np.zeros_like(x_curve)

    try:
        if model_type == 'poly2':
            coeffs = np.polyfit(x_clean, y_clean, 2)
            y_pred = np.polyval(coeffs, x_clean)
            y_curve = np.polyval(coeffs, x_curve)
            a, b, c = coeffs
            sign_b = "+" if b >= 0 else "-"
            sign_c = "+" if c >= 0 else "-"
            eq_str = f"y = {a:.4f}x² {sign_b} {abs(b):.4f}x {sign_c} {abs(c):.4f}"

            ss_res = np.sum((y_clean - y_pred) ** 2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        elif model_type == 'poly3':
            coeffs = np.polyfit(x_clean, y_clean, 3)
            y_pred = np.polyval(coeffs, x_clean)
            y_curve = np.polyval(coeffs, x_curve)
            a, b, c, d = coeffs
            sign_b = "+" if b >= 0 else "-"
            sign_c = "+" if c >= 0 else "-"
            sign_d = "+" if d >= 0 else "-"
            eq_str = f"y = {a:.4f}x³ {sign_b} {abs(b):.4f}x² {sign_c} {abs(c):.4f}x {sign_d} {abs(d):.4f}"

            ss_res = np.sum((y_clean - y_pred) ** 2)
            ss_tot = np.sum((y_clean - np.mean(y_clean)) ** 2)
            r_squared = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0.0

        elif model_type == 'log':
            pos_mask = x_clean > 0
            if np.sum(pos_mask) >= 3:
                x_pos = x_clean[pos_mask]
                y_pos = y_clean[pos_mask]
                slope, intercept, r_val, p_val, std_err = sp_stats.linregress(np.log(x_pos), y_pos)
                r_squared = safe_float(r_val ** 2, 0.0)
                se = safe_float(std_err, None)
                sign_int = "+" if intercept >= 0 else "-"
                eq_str = f"y = {slope:.4f}·ln(x) {sign_int} {abs(intercept):.4f}"

                x_curve_pos = np.linspace(max(x_min, 1e-4), x_max, num_points)
                y_curve = slope * np.log(x_curve_pos) + intercept
                x_curve = x_curve_pos
            else:
                eq_str = "Logaritmik regresyon için X değerleri pozitif (>0) olmalıdır."

        elif model_type == 'exp':
            pos_mask = y_clean > 0
            if np.sum(pos_mask) >= 3:
                x_pos = x_clean[pos_mask]
                y_pos = y_clean[pos_mask]
                slope, intercept, r_val, p_val, std_err = sp_stats.linregress(x_pos, np.log(y_pos))
                a = np.exp(intercept)
                b = slope
                sign_b = "+" if b >= 0 else "-"
                eq_str = f"y = {a:.4f}·e^({b:.4f}x)"
                r_squared = safe_float(r_val ** 2, 0.0)
                se = safe_float(std_err, None)
                y_curve = a * np.exp(b * x_curve)
            else:
                eq_str = "Üstel regresyon için Y değerleri pozitif (>0) olmalıdır."

        else:  # linear
            slope, intercept, r_val, p_val, std_err = sp_stats.linregress(x_clean, y_clean)
            r_squared = safe_float(r_val ** 2, 0.0)
            se = safe_float(std_err, None)
            sign_int = "+" if intercept >= 0 else "-"
            eq_str = f"y = {slope:.4f}x {sign_int} {abs(intercept):.4f}"
            y_curve = slope * x_curve + intercept

    except Exception as e:
        logger.warning(f"Regresyon hesaplama hatası ({model_type}): {e}")
        eq_str = f"Hesaplama hatası: {str(e)}"

    finite_mask = np.isfinite(x_curve) & np.isfinite(y_curve)
    trend_x = [round(float(v), 4) for v in x_curve[finite_mask]]
    trend_y = [round(float(v), 4) for v in y_curve[finite_mask]]

    return {
        'equation': eq_str,
        'r_squared': round(float(r_squared), 4) if r_squared is not None and np.isfinite(r_squared) else 0.0,
        'se': round(float(se), 4) if se is not None and np.isfinite(se) else None,
        'p_value': p_val,
        'model_type': model_type,
        'trend_x': trend_x,
        'trend_y': trend_y
    }


def compute_column_statistics(df, columns):
    """
    Computes summary descriptive statistics for the requested numerical columns.
    """
    stats = {}
    for col in columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            s = df[col]
            stats[col] = {
                'count': int(s.count()),
                'missing': int(s.isna().sum()),
                'mean': float(s.mean()) if pd.notnull(s.mean()) else None,
                'median': float(s.median()) if pd.notnull(s.median()) else None,
                'min': float(s.min()) if pd.notnull(s.min()) else None,
                'max': float(s.max()) if pd.notnull(s.max()) else None,
                'std': float(s.std()) if pd.notnull(s.std()) else None
            }
    return stats


def compute_advanced_stats(active_df, cols, x_col=None, corr_method='pearson', reg_model='linear'):
    """
    Performs deep comparative analysis:
    - If X is numeric: Pearson/Spearman/Kendall correlation and curve regression.
    - If X is categorical with 2 groups: Independent two-sample Student's T-Test.
    - If X is categorical with >2 groups: One-way ANOVA F-Test.
    """
    advanced = {}
    if not x_col or x_col not in active_df.columns:
        return advanced

    is_x_num = pd.api.types.is_numeric_dtype(active_df[x_col])

    for y_col in cols:
        if y_col not in active_df.columns or not pd.api.types.is_numeric_dtype(active_df[y_col]):
            continue

        adv_info = {}
        valid_df = active_df[[x_col, y_col]].dropna()

        if len(valid_df) > 2:
            if is_x_num:
                x_vals = valid_df[x_col].values
                y_vals = valid_df[y_col].values

                corr_res = compute_robust_correlation(x_vals, y_vals, method=corr_method)
                reg_res = compute_robust_regression(x_vals, y_vals, model_type=reg_model)

                adv_info['correlation'] = corr_res['coef']
                adv_info['corr_method'] = corr_res['method']
                adv_info['interpretation'] = corr_res['interpretation']
                adv_info['p_value'] = corr_res['p_value']
                adv_info['r_squared'] = reg_res['r_squared']
                adv_info['regression'] = reg_res['equation']
                adv_info['se'] = reg_res['se']
                adv_info['reg_model'] = reg_res['model_type']
                adv_info['sample_size'] = corr_res['sample_size']
                adv_info['type'] = 'numeric'
            else:
                groups = [group[y_col].values for _, group in valid_df.groupby(x_col) if len(group) > 0]
                
                # Compute best and worst groups for AI business templates
                try:
                    grouped_sum = valid_df.groupby(x_col)[y_col].sum()
                    adv_info['best_group'] = str(grouped_sum.idxmax())
                    adv_info['best_val'] = float(grouped_sum.max())
                    adv_info['worst_group'] = str(grouped_sum.idxmin())
                    adv_info['worst_val'] = float(grouped_sum.min())
                except Exception as e_grp:
                    logger.debug(f"Group aggregation error: {e_grp}")

                if len(groups) == 2:
                    try:
                        t_stat, p_val = sp_stats.ttest_ind(groups[0], groups[1], equal_var=False)
                        adv_info['t_test_stat'] = safe_float(t_stat, None)
                        adv_info['p_value'] = safe_float(p_val, None)
                        adv_info['type'] = 'categorical_2'
                    except Exception as e_ttest:
                        logger.debug(f"T-Test error: {e_ttest}")
                elif len(groups) > 2:
                    try:
                        f_stat, p_val = sp_stats.f_oneway(*groups)
                        adv_info['anova_f'] = safe_float(f_stat, None)
                        adv_info['p_value'] = safe_float(p_val, None)
                        adv_info['type'] = 'categorical_n'
                    except Exception as e_anova:
                        logger.debug(f"ANOVA error: {e_anova}")

        advanced[y_col] = adv_info

    return advanced


def generate_kpi_summary(active_df, total_original_rows=None):
    """
    Generates executive KPI tiles based on the active filtered DataFrame.
    """
    if active_df is None or active_df.empty:
        return {'kpis': [], 'total_active_rows': 0}

    total_rows = total_original_rows or len(active_df)
    num_cols = active_df.select_dtypes(include=['number']).columns.tolist()
    cat_cols = active_df.select_dtypes(include=['object', 'category']).columns.tolist()

    kpis = []

    # 1. Total records
    kpis.append({
        'title': 'Toplam Kayıt',
        'value': f"{len(active_df):,}".replace(',', '.'),
        'sub': f"Toplam {total_rows:,} satırdan",
        'icon': '📋',
        'color': 'blue'
    })

    # 2. Main numeric metric
    if num_cols:
        main_num = num_cols[0]
        total_val = float(active_df[main_num].sum())
        mean_val = float(active_df[main_num].mean())

        val_str = f"{total_val:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.')
        if total_val >= 1_000_000:
            val_str = f"₺{total_val / 1_000_000:.2f}M"
        elif total_val >= 1_000:
            val_str = f"₺{total_val / 1_000:.1f}K"

        kpis.append({
            'title': f'Toplam {main_num}',
            'value': val_str,
            'sub': f"Ort: {mean_val:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
            'icon': '💰',
            'color': 'green'
        })

        # 3. Secondary numeric metric
        if len(num_cols) > 1:
            sec_num = num_cols[1]
            sec_total = float(active_df[sec_num].sum())
            kpis.append({
                'title': f'Toplam {sec_num}',
                'value': f"{sec_total:,.1f}".replace(',', 'X').replace('.', ',').replace('X', '.'),
                'sub': f"Maks: {active_df[sec_num].max():,.1f}",
                'icon': '📈',
                'color': 'purple'
            })

    # 4. Leading category
    if cat_cols:
        main_cat = cat_cols[0]
        vc = active_df[main_cat].dropna().value_counts()
        if not vc.empty:
            top_cat_name = str(vc.index[0])
            top_cat_count = int(vc.iloc[0])
            pct = (top_cat_count / len(active_df)) * 100 if len(active_df) > 0 else 0
            kpis.append({
                'title': f'Lider {main_cat}',
                'value': top_cat_name[:15],
                'sub': f"%{pct:.1f} pay ({top_cat_count} adet)",
                'icon': '🏆',
                'color': 'orange'
            })

    return {'kpis': kpis, 'total_active_rows': len(active_df), 'total_rows': total_rows}


def compute_pivot_data(active_df, rows, cols, values, agg_func='sum'):
    """
    Computes live Excel-style Pivot Table Matrix with multi-level indices and grand totals.
    """
    if active_df is None or active_df.empty:
        raise ValueError("Uygulanan filtreler sonucunda veri kalmadı.")

    valid_rows = [r for r in rows if r in active_df.columns]
    valid_cols = [c for c in cols if c in active_df.columns]
    valid_values = [v for v in values if v in active_df.columns and pd.api.types.is_numeric_dtype(active_df[v])]

    if len(valid_rows) == 0 and len(valid_cols) == 0:
        raise ValueError("En az bir Satır veya Sütun boyutu seçmelisiniz.")

    if not valid_values:
        raise ValueError("Lütfen hesaplanacak en az bir sayısal Değer (Metrik) seçin.")

    agg_map = {
        'sum': 'sum',
        'mean': 'mean',
        'count': 'count',
        'min': 'min',
        'max': 'max',
        'median': 'median'
    }
    chosen_agg = agg_map.get(agg_func, 'sum')

    pt = pd.pivot_table(
        active_df,
        index=valid_rows if valid_rows else None,
        columns=valid_cols if valid_cols else None,
        values=valid_values,
        aggfunc=chosen_agg,
        fill_value=0,
        margins=True,
        margins_name='Genel Toplam'
    )

    if isinstance(pt.columns, pd.MultiIndex):
        raw_headers = pt.columns.tolist()
        table_headers = [" | ".join([str(x) for x in item if str(x) != '']) for item in raw_headers]
    else:
        table_headers = [str(c) for c in pt.columns.tolist()]

    table_rows = []
    raw_values_all = []

    if isinstance(pt.index, pd.MultiIndex):
        index_names = [str(n) if n else f"Seviye {i+1}" for i, n in enumerate(pt.index.names)]
        for idx_val, row_series in pt.iterrows():
            row_labels = [str(x) for x in idx_val]
            row_vals = [float(v) if pd.notnull(v) else 0 for v in row_series.tolist()]
            if 'Genel Toplam' not in row_labels:
                raw_values_all.extend(row_vals[:-1] if 'Genel Toplam' in table_headers else row_vals)
            table_rows.append({
                'row_labels': row_labels,
                'cells': row_vals,
                'is_grand_total': 'Genel Toplam' in row_labels
            })
    else:
        index_names = [str(pt.index.name) if pt.index.name else (valid_rows[0] if valid_rows else 'Boyut')]
        for idx_val, row_series in pt.iterrows():
            row_labels = [str(idx_val)]
            row_vals = [float(v) if pd.notnull(v) else 0 for v in row_series.tolist()]
            if str(idx_val) != 'Genel Toplam':
                raw_values_all.extend(row_vals[:-1] if 'Genel Toplam' in table_headers else row_vals)
            table_rows.append({
                'row_labels': row_labels,
                'cells': row_vals,
                'is_grand_total': str(idx_val) == 'Genel Toplam'
            })

    min_val = float(min(raw_values_all)) if raw_values_all else 0
    max_val = float(max(raw_values_all)) if raw_values_all else 0

    return {
        'index_names': index_names,
        'column_headers': table_headers,
        'rows': table_rows,
        'min_value': min_val,
        'max_value': max_val,
        'total_data_rows': len(active_df),
        'row_dimensions': valid_rows,
        'col_dimensions': valid_cols,
        'value_metrics': valid_values,
        'agg_func': agg_func
    }
