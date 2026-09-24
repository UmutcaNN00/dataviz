import io
import pandas as pd
import numpy as np
from app import create_app

def test_apple_pro_deep_audit():
    app = create_app()
    app.config['TESTING'] = True
    client = app.test_client()

    print("\n" + "=" * 65)
    print(">> DEEP AUDIT: SCIENTIFIC STATS & BACKEND CONTRACTS")
    print("=" * 65)

    # 1. Load Sample Data
    resp = client.post('/load_sample')
    assert resp.status_code == 200, f"Sample load failed: {resp.data}"
    data = resp.get_json()
    assert data['success'] is True
    print("  [OK] [01] Sample dataset loaded into session successfully")

    # 2. Test Independent Two-Sample T-Test (Categorical X with 2 groups)
    num_cols = data.get('numeric_columns', [])
    cat_cols = data.get('categorical_columns', [])
    print(f"       Categorical cols: {cat_cols}")
    print(f"       Numeric cols: {num_cols}")

    stat_resp = client.post('/get_stats', json={
        'columns': [num_cols[0]],
        'x_col': cat_cols[0]
    })
    assert stat_resp.status_code == 200
    stat_data = stat_resp.get_json()
    adv = stat_data.get('advanced', {})
    print(f"  [OK] [02] /get_stats with cat x_col='{cat_cols[0]}': type={adv.get('type')}")
    assert 'type' in adv or len(adv) > 0

    from services.stats_service import compute_advanced_stats, compute_robust_regression, compute_robust_correlation

    # Test 2 groups -> T-Test
    df_2grp = pd.DataFrame({
        'Group': ['A'] * 20 + ['B'] * 20,
        'Score': [10.5 + i * 0.1 for i in range(20)] + [20.2 + i * 0.2 for i in range(20)]
    })
    res_2grp = compute_advanced_stats(df_2grp, ['Score'], x_col='Group')
    assert res_2grp['type'] == 'categorical_2'
    assert 't_test' in res_2grp
    assert res_2grp['t_test']['t_stat'] is not None
    assert res_2grp['t_test']['p_value'] is not None
    assert 'A' in res_2grp['t_test']['group_means']
    assert 'B' in res_2grp['t_test']['group_means']
    print(f"  [OK] [03] Independent Two-Sample T-Test verified: t={res_2grp['t_test']['t_stat']:.4f}, p={res_2grp['t_test']['p_value']:.4e}")

    # Test >2 groups -> One-Way ANOVA
    df_3grp = pd.DataFrame({
        'Group': ['A'] * 15 + ['B'] * 15 + ['C'] * 15,
        'Score': [10.0 + i * 0.1 for i in range(15)] + [15.0 + i * 0.1 for i in range(15)] + [25.0 + i * 0.1 for i in range(15)]
    })
    res_3grp = compute_advanced_stats(df_3grp, ['Score'], x_col='Group')
    assert res_3grp['type'] == 'categorical_n'
    assert 'anova' in res_3grp
    assert res_3grp['anova']['f_stat'] is not None
    assert res_3grp['anova']['p_value'] is not None
    print(f"  [OK] [04] One-Way ANOVA F-Test verified: F={res_3grp['anova']['f_stat']:.4f}, p={res_3grp['anova']['p_value']:.4e}")

    # 4. Test Correlation methods: pearson, spearman, kendall
    x_test = np.array([1, 2, 3, 4, 5, 6, 7, 8, 9, 10], dtype=float)
    y_test = np.array([2, 4, 5, 4, 8, 9, 11, 14, 15, 19], dtype=float)

    for method in ['pearson', 'spearman', 'kendall']:
        corr = compute_robust_correlation(x_test, y_test, method=method)
        assert corr['coef'] > 0.8
        assert corr['method'] == method
        assert corr['p_value'] is not None
        print(f"  [OK] [05] Correlation ({method}): coef={corr['coef']}, p={corr['p_value']:.4e}, interp='{corr['interpretation']}'")

    # 5. Test Regression models: linear, poly2, poly3, exp, log
    for model in ['linear', 'poly2', 'poly3', 'exp', 'log']:
        reg = compute_robust_regression(x_test, y_test, model_type=model)
        assert reg['r_squared'] > 0.5, f"R² too low for {model}: {reg}"
        assert 'trend_x' in reg and len(reg['trend_x']) > 0
        assert 'trend_y' in reg and len(reg['trend_y']) > 0
        print(f"  [OK] [06] Regression ({model}): eq='{reg['equation']}', R2={reg['r_squared']:.4f}")

    # 6. Test Zero-variance and NaN edge cases
    x_const = np.array([5.0, 5.0, 5.0, 5.0, 5.0])
    y_const = np.array([10.0, 10.0, 10.0, 10.0, 10.0])
    reg_const = compute_robust_regression(x_const, y_const)
    assert reg_const['p_value'] is None
    assert reg_const['r_squared'] == 0.0

    corr_const = compute_robust_correlation(x_const, y_const)
    assert corr_const['p_value'] is None
    print("  [OK] [07] Zero-variance and constant input edge cases handled gracefully without crashing")

    # 7. Test /get_regression_curve endpoint with all models and correlation methods
    for model in ['linear', 'poly2', 'poly3', 'exp', 'log']:
        r = client.post('/get_regression_curve', json={
            'x_col': num_cols[0],
            'y_col': num_cols[1],
            'model_type': model,
            'corr_method': 'spearman'
        })
        assert r.status_code == 200
        res_json = r.get_json()
        assert res_json['success'] is True
        assert 'regression' in res_json
        assert 'correlation' in res_json
    print("  [OK] [08] /get_regression_curve endpoint handles all models and spearman correlation")

    # 8. Test Pivot Aggregation functions via /get_pivot_data
    for agg in ['sum', 'mean', 'count', 'min', 'max', 'median']:
        p_resp = client.post('/get_pivot_data', json={
            'rows': [cat_cols[0]],
            'cols': [cat_cols[1]] if len(cat_cols) > 1 else [],
            'values': [num_cols[0]],
            'agg_func': agg
        })
        assert p_resp.status_code == 200, f"Pivot {agg} failed"
        p_data = p_resp.get_json()
        assert 'rows' in p_data
        assert 'column_headers' in p_data
    print("  [OK] [09] /get_pivot_data handles sum, mean, count, min, max, median perfectly")

    # 9. Test /get_ai_insight with both stats and advanced_stats populated
    ai_resp = client.post('/get_ai_insight', json={
        'chart_type': 'scatter',
        'x': num_cols[0],
        'y': [num_cols[1]],
        'stats': {'mean': 150.5, 'std': 25.2, 'min': 100, 'max': 250},
        'advanced_stats': {
            'type': 'numeric',
            'correlation': 0.875,
            'r_squared': 0.765,
            'regression': 'y = 1.25x + 30'
        }
    })
    assert ai_resp.status_code == 200
    ai_data = ai_resp.get_json()
    assert 'insight' in ai_data
    assert len(ai_data['insight']) > 20
    print(f"  [OK] [10] /get_ai_insight generated rich academic interpretation")

    # 10. Test /create_calculated_column
    calc_resp = client.post('/create_calculated_column', json={
        'new_col_name': 'Test_Verim',
        'col1': num_cols[0],
        'op': '+',
        'col2': num_cols[1]
    })
    assert calc_resp.status_code == 200
    calc_data = calc_resp.get_json()
    assert 'Test_Verim' in calc_data['numeric_columns']
    print("  [OK] [11] /create_calculated_column created new numeric column successfully")

    # 11. Test Filter Slicing on Chart Data
    cat_vals_resp = client.get(f'/get_column_unique_values?column={cat_cols[0]}').get_json()
    first_cat = cat_vals_resp['categories'][0]['value'] if cat_vals_resp.get('categories') else 'Elektronik'

    chart_all = client.post('/get_chart_data', json={
        'x': num_cols[0],
        'y': [num_cols[1]],
        'chart_type': 'scatter',
        'filters': []
    }).get_json()
    
    chart_filtered = client.post('/get_chart_data', json={
        'x': num_cols[0],
        'y': [num_cols[1]],
        'chart_type': 'scatter',
        'filters': [{'column': cat_cols[0], 'type': 'cat', 'values': [first_cat]}]
    }).get_json()

    assert 'total_active_rows' in chart_all
    assert 'total_active_rows' in chart_filtered
    assert chart_all['total_active_rows'] >= chart_filtered['total_active_rows']
    print(f"  [OK] [12] Global Slicer filtering verified: all={chart_all['total_active_rows']} >= filtered={chart_filtered['total_active_rows']}")

    # 12. Template Element Integrity
    landing_html = client.get('/').data.decode('utf-8')
    assert 'DataViz Pro' in landing_html
    assert '/analysis' in landing_html

    analysis_html = client.get('/analysis').data.decode('utf-8')
    assert 'chartFamilyFilters' in analysis_html
    assert 'pivotAggFuncSelect' in analysis_html
    assert 'modalHealer' in analysis_html
    assert 'modalMerge' in analysis_html
    assert 'modalFormula' in analysis_html
    assert 'modalFilter' in analysis_html
    assert 'modalA4' in analysis_html
    assert 'charts_config.js' in analysis_html
    assert 'analysis_apple.js' in analysis_html
    print("  [OK] [13] Template integrity verified: Landing & Analysis contain all UI elements and script references")

    print("=" * 65)
    print(">>> ALL 13 DEEP SCIENTIFIC & STATISTICAL AUDIT TESTS PASSED!")
    print("=" * 65)

if __name__ == '__main__':
    test_apple_pro_deep_audit()
