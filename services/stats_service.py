"""
Statistical Analysis and Modeling Service
Handles descriptive statistics, correlations, polynomial/linear/logarithmic regressions,
hypothesis testing (T-Test, ANOVA), KPI generation, filtering, and pivot matrices.
"""

import logging

import numpy as np
import pandas as pd
from scipy import stats as sp_stats

logger = logging.getLogger(__name__)


def safe_float(val, default=None):
    """
    Converts a value to a JSON-safe float, replacing NaN, Infinity, and -Infinity with default.
    """
    try:
        if val is None or pd.isna(val):
            return default
        if not isinstance(val, (str, bytes)):
            if np.isinf(val):
                return default
        f = float(val)
        return f if np.isfinite(f) else default
    except Exception:  # noqa: BLE001
        return default


def interpret_bayes_factor(bf10: float | None) -> str:
    """
    Interprets Bayes Factor BF₁₀ using Harold Jeffreys' (1961) canonical evidence scale.
    """
    if bf10 is None or not np.isfinite(bf10):
        return "Belirsiz / Yetersiz Veri"
    if bf10 >= 100.0:
        return "Kesin / Çok Güçlü Kanıt (H₁)"
    if bf10 >= 30.0:
        return "Çok Güçlü Kanıt (H₁)"
    if bf10 >= 10.0:
        return "Güçlü Kanıt (H₁)"
    if bf10 >= 3.0:
        return "Orta Düzey Kanıt (H₁)"
    if bf10 >= 1.0:
        return "Zayıf / Anekdotsal Kanıt (H₁)"
    if bf10 >= 0.33:
        return "Zayıf Kanıt (H₀ Lehine)"
    if bf10 >= 0.1:
        return "Orta Düzey Kanıt (H₀ Lehine)"
    return "Güçlü Kanıt (H₀ Lehine)"


def compute_bayes_factor_ttest(t_stat: float | None, n1: int, n2: int) -> dict:
    """
    Computes Bayes Factor (BF₁₀) and posterior probability P(H₁|Data)
    for two-sample Welch / Student T-Test using the Wagenmakers (2007) / Masson (2011) BIC posterior odds model.
    """
    if t_stat is None or not np.isfinite(t_stat):
        return {"bf10": None, "p_h1": None, "evidence": "Hesaplanamadı"}
    n = n1 + n2
    if n < 4:
        return {"bf10": None, "p_h1": None, "evidence": "Yetersiz örneklem"}
    t2 = float(t_stat) ** 2
    delta_bic = t2 - np.log(n)
    delta_bic_clamped = min(max(delta_bic, -600.0), 600.0)
    bf10 = float(np.exp(delta_bic_clamped / 2.0))
    p_h1 = float(bf10 / (1.0 + bf10))
    ev = interpret_bayes_factor(bf10)
    return {
        "bf10": round(bf10, 4) if bf10 < 10000 else float(f"{bf10:.4e}"),
        "p_h1": round(p_h1, 4),
        "evidence": ev,
        "n1": n1,
        "n2": n2,
    }


def compute_bayes_factor_anova(
    f_stat: float | None, k_groups: int, n_total: int
) -> dict:
    """
    Computes Bayes Factor (BF₁₀), partial eta-squared (η²), and P(H₁|Data)
    for One-Way ANOVA using the Masson (2011) BIC model comparison formulation.
    """
    if f_stat is None or not np.isfinite(f_stat) or n_total <= k_groups or k_groups < 2:
        return {"bf10": None, "p_h1": None, "eta2": None, "evidence": "Hesaplanamadı"}
    df1 = k_groups - 1
    df2 = n_total - k_groups
    eta2 = float((df1 * f_stat) / (df1 * f_stat + df2))
    eta2 = min(max(eta2, 0.0), 0.999999)
    delta_bic = n_total * np.log(1.0 / (1.0 - eta2)) - df1 * np.log(n_total)
    delta_bic_clamped = min(max(delta_bic, -600.0), 600.0)
    bf10 = float(np.exp(delta_bic_clamped / 2.0))
    p_h1 = float(bf10 / (1.0 + bf10))
    ev = interpret_bayes_factor(bf10)
    return {
        "bf10": round(bf10, 4) if bf10 < 10000 else float(f"{bf10:.4e}"),
        "p_h1": round(p_h1, 4),
        "eta2": round(eta2, 4),
        "evidence": ev,
        "k_groups": k_groups,
        "n_total": n_total,
    }


def compute_bayes_factor_regression(
    r_squared: float | None, n_total: int, p_predictors: int = 1
) -> dict:
    """
    Computes Bayes Factor (BF₁₀) and P(H₁|Data) for linear/curve regression and correlation
    using the Wagenmakers (2007) BIC model comparison approximation.
    """
    if r_squared is None or not np.isfinite(r_squared) or n_total <= p_predictors + 1:
        return {"bf10": None, "p_h1": None, "evidence": "Hesaplanamadı"}
    r2 = min(max(float(r_squared), 0.0), 0.999999)
    delta_bic = n_total * np.log(1.0 / (1.0 - r2)) - p_predictors * np.log(n_total)
    delta_bic_clamped = min(max(delta_bic, -600.0), 600.0)
    bf10 = float(np.exp(delta_bic_clamped / 2.0))
    p_h1 = float(bf10 / (1.0 + bf10))
    ev = interpret_bayes_factor(bf10)
    return {
        "bf10": round(bf10, 4) if bf10 < 10000 else float(f"{bf10:.4e}"),
        "p_h1": round(p_h1, 4),
        "evidence": ev,
        "n_total": n_total,
        "p_predictors": p_predictors,
    }


def compute_naive_bayes_classification(
    df, feature_cols=None, target_col=None
) -> dict:
    """
    Fits Gaussian Naive Bayes classifier on numeric feature columns to predict categorical target_col.
    Handles NaN values and class distributions gracefully.
    """
    if df is None or df.empty or not target_col or target_col not in df.columns:
        return {"error": "Geçerli bir hedef (target) sütun seçilmelidir."}

    target_series = df[target_col].dropna().astype(str)
    if target_series.nunique() < 2:
        return {"error": "Hedef değişken en az 2 farklı sınıfa sahip olmalıdır."}

    if not feature_cols:
        feature_cols = [
            c for c in df.select_dtypes(include=["number"]).columns if c != target_col
        ][:8]
    else:
        feature_cols = [c for c in feature_cols if c in df.columns and c != target_col]

    if not feature_cols:
        return {
            "error": "Naive Bayes analizi için en az bir sayısal özellik sütunu seçilmelidir."
        }

    sub = df[feature_cols + [target_col]].dropna()
    if len(sub) < 8:
        return {
            "error": "Naive Bayes analizi için yeterli geçerli satır bulunamadı (en az 8 satır gereklidir)."
        }

    X_num = sub[feature_cols].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    valid_mask = X_num.notna().all(axis=1)
    X = X_num[valid_mask]
    y = sub.loc[X.index, target_col].astype(str)
    if len(X) < 8 or y.nunique() < 2:
        return {"error": "Geçerli sayısal dönüşüm sonrasında yeterli satır veya sınıf bulunamadı (en az 8 satır, 2 sınıf)." }

    try:
        from sklearn.model_selection import cross_val_score
        from sklearn.naive_bayes import GaussianNB

        gnb = GaussianNB()
        gnb.fit(X, y)
        preds = gnb.predict(X)
        acc = float(np.mean(preds == y))

        cv_score = None
        min_class_count = y.value_counts().min()
        if min_class_count >= 3 and len(X) >= 15:
            cv_folds = min(5, int(min_class_count))
            cv_scores = cross_val_score(gnb, X, y, cv=cv_folds)
            cv_score = round(float(np.mean(cv_scores)), 4)

        classes = [str(c) for c in gnb.classes_]
        priors = {
            classes[i]: round(float(p), 4) for i, p in enumerate(gnb.class_prior_)
        }
        means_dict = {}
        for c_idx, c_name in enumerate(classes):
            means_dict[c_name] = {
                feat: round(float(gnb.theta_[c_idx][f_idx]), 4)
                for f_idx, feat in enumerate(feature_cols)
            }

        return {
            "success": True,
            "target_col": target_col,
            "feature_cols": feature_cols,
            "classes": classes,
            "class_priors": priors,
            "accuracy": round(acc, 4),
            "cv_accuracy": cv_score,
            "feature_means": means_dict,
            "sample_size": len(X),
            "bayes_type": "GaussianNB",
        }
    except Exception as e:
        logger.exception("compute_naive_bayes_classification hatası")
        return {"error": f"Naive Bayes modeli eğitilirken hata: {e}"}


def apply_filters(df, filters):
    """
    Applies a list of categorical and numeric filters to a DataFrame.
    Supports both ('cat', 'values') and ('categorical', 'selected_values') as well as ('num', 'numeric_range').
    Uses a combined boolean mask to avoid unnecessary full-DataFrame copies and index alignment warnings.
    """
    if df is None or df.empty or not filters or not isinstance(filters, list):
        return df

    mask = pd.Series(True, index=df.index)
    mask_modified = False

    for f in filters:
        if not isinstance(f, dict):
            continue
        col = f.get("column")
        if not col or col not in df.columns:
            continue
        ftype = f.get("type") or f.get("filter_type")
        if ftype in ("cat", "categorical"):
            selected_vals = (
                f.get("values") if "values" in f else f.get("selected_values", [])
            )
            if (
                selected_vals is not None
                and isinstance(selected_vals, list)
                and len(selected_vals) > 0
            ):
                str_vals = [str(v) for v in selected_vals]
                mask &= df[col].astype(str).isin(str_vals)
                mask_modified = True
        elif ftype in ("num", "numeric_range"):
            min_val = f.get("min")
            max_val = f.get("max")
            col_num = pd.to_numeric(df[col], errors="coerce")
            if min_val is not None and str(min_val).strip() != "":
                try:
                    mask &= col_num >= float(min_val)
                    mask_modified = True
                except (ValueError, TypeError):
                    pass
            if max_val is not None and str(max_val).strip() != "":
                try:
                    mask &= col_num <= float(max_val)
                    mask_modified = True
                except (ValueError, TypeError):
                    pass

    if not mask_modified:
        return df
    return df.loc[mask]


def compute_robust_correlation(x_vals, y_vals, method="pearson"):
    """
    Computes Pearson, Spearman, or Kendall correlations with NaN safety and zero variance handling.
    """
    x_arr = pd.to_numeric(pd.Series(x_vals), errors="coerce").to_numpy(dtype=float)
    y_arr = pd.to_numeric(pd.Series(y_vals), errors="coerce").to_numpy(dtype=float)
    valid_mask = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_clean = x_arr[valid_mask]
    y_clean = y_arr[valid_mask]

    if (
        len(x_clean) < 3
        or len(y_clean) < 3
        or np.all(x_clean == x_clean[0])
        or np.all(y_clean == y_clean[0])
        or float(np.std(x_clean)) <= 1e-12
        or float(np.std(y_clean)) <= 1e-12
    ):
        return {
            "coef": 0.0,
            "p_value": None,
            "method": method,
            "interpretation": "Yetersiz veya sabit varyanslı veri",
            "sample_size": len(x_clean),
        }

    try:
        if method == "spearman":
            res = sp_stats.spearmanr(x_clean, y_clean)
            coef = safe_float(
                res.statistic if hasattr(res, "statistic") else res[0], 0.0
            )
            p_val = safe_float(res.pvalue if hasattr(res, "pvalue") else res[1], None)
        elif method == "kendall":
            res = sp_stats.kendalltau(x_clean, y_clean)
            coef = safe_float(
                res.statistic if hasattr(res, "statistic") else res[0], 0.0
            )
            p_val = safe_float(res.pvalue if hasattr(res, "pvalue") else res[1], None)
        else:  # pearson
            res = sp_stats.pearsonr(x_clean, y_clean)
            coef = safe_float(
                res.statistic if hasattr(res, "statistic") else res[0], 0.0
            )
            p_val = safe_float(res.pvalue if hasattr(res, "pvalue") else res[1], None)
    except Exception as e:  # noqa: BLE001
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

    r_val = float(coef) if coef is not None else 0.0
    bayes_corr = compute_bayes_factor_regression(
        r_val**2, len(x_clean), p_predictors=1
    )

    return {
        "coef": round(coef, 4) if coef is not None else 0.0,
        "p_value": p_val,
        "method": method,
        "interpretation": strength,
        "sample_size": len(x_clean),
        "bayes_factor": bayes_corr,
        "bayes_bf10": bayes_corr.get("bf10"),
        "bayes_evidence": bayes_corr.get("evidence"),
        "bayes_p_h1": bayes_corr.get("p_h1"),
    }


def compute_robust_regression(x_vals, y_vals, model_type="linear", num_points=100):
    """
    Computes Linear, Polynomial (degree 2, 3), Logarithmic, and Exponential regression models
    with R², standard error, p-value, 95% confidence interval, and curve prediction points.
    """
    x_arr = pd.to_numeric(pd.Series(x_vals), errors="coerce").to_numpy(dtype=float)
    y_arr = pd.to_numeric(pd.Series(y_vals), errors="coerce").to_numpy(dtype=float)
    valid_mask = np.isfinite(x_arr) & np.isfinite(y_arr)
    x_clean = x_arr[valid_mask]
    y_clean = y_arr[valid_mask]

    num_unique_x = len(np.unique(x_clean))
    min_points_required = 3
    if model_type == "poly3":
        min_points_required = 4
    elif model_type == "poly2":
        min_points_required = 3

    if (
        num_unique_x < min_points_required
        or np.all(y_clean == y_clean[0])
    ):
        return {
            "equation": "Yetersiz veya sabit varyanslı veri",
            "r_squared": 0.0,
            "se": None,
            "p_value": None,
            "model_type": model_type,
            "trend_x": [],
            "trend_y": [],
            "ci_lower": [],
            "ci_upper": [],
        }

    x_min, x_max = float(np.min(x_clean)), float(np.max(x_clean))
    x_curve = np.linspace(x_min, x_max, num_points)

    eq_str = ""
    r_squared = 0.0
    se = None
    p_val = None
    y_curve = np.zeros_like(x_curve)

    x_used = x_clean
    y_used = y_clean
    y_fit_used = None
    n_params = 2

    # Store design matrix for CI calculation if poly
    X_design = None
    X_curve_design = None

    try:
        if model_type in ("poly2", "poly3"):
            deg = 2 if model_type == "poly2" else 3
            n_params = deg + 1
            
            x_mean = np.mean(x_clean)
            x_std = np.std(x_clean) if np.std(x_clean) > 0 else 1.0
            
            x_scaled = (x_clean - x_mean) / x_std
            x_curve_scaled = (x_curve - x_mean) / x_std
            
            coeffs_scaled = np.polyfit(x_scaled, y_clean, deg)
            y_fit_used = np.polyval(coeffs_scaled, x_scaled)
            y_curve = np.polyval(coeffs_scaled, x_curve_scaled)
            
            # Equation string parameters from mathematically unscaling the scaled coefficients
            if deg == 2:
                A, B, C = coeffs_scaled
                a = A / (x_std**2)
                b = B / x_std - 2 * A * x_mean / (x_std**2)
                c = C - B * x_mean / x_std + A * (x_mean**2) / (x_std**2)
                
                sign_b = "+" if b >= 0 else "-"
                sign_c = "+" if c >= 0 else "-"
                eq_str = f"y = {a:.4f}x² {sign_b} {abs(b):.4f}x {sign_c} {abs(c):.4f}"
                X_design = np.column_stack([np.ones_like(x_scaled), x_scaled, x_scaled**2])
                X_curve_design = np.column_stack([np.ones_like(x_curve_scaled), x_curve_scaled, x_curve_scaled**2])
            else:
                A, B, C, D = coeffs_scaled
                a = A / (x_std**3)
                b = B / (x_std**2) - 3 * A * x_mean / (x_std**3)
                c = C / x_std - 2 * B * x_mean / (x_std**2) + 3 * A * (x_mean**2) / (x_std**3)
                d = D - C * x_mean / x_std + B * (x_mean**2) / (x_std**2) - A * (x_mean**3) / (x_std**3)
                
                sign_b = "+" if b >= 0 else "-"
                sign_c = "+" if c >= 0 else "-"
                sign_d = "+" if d >= 0 else "-"
                eq_str = f"y = {a:.4f}x³ {sign_b} {abs(b):.4f}x² {sign_c} {abs(c):.4f}x {sign_d} {abs(d):.4f}"
                X_design = np.column_stack([np.ones_like(x_scaled), x_scaled, x_scaled**2, x_scaled**3])
                X_curve_design = np.column_stack([np.ones_like(x_curve_scaled), x_curve_scaled, x_curve_scaled**2, x_curve_scaled**3])

            ss_res = float(np.sum((y_clean - y_fit_used) ** 2))
            ss_tot = float(np.sum((y_clean - np.mean(y_clean)) ** 2))
            r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
            dof_poly = max(len(x_clean) - n_params, 1)
            se = float(np.sqrt(ss_res / dof_poly))
            if ss_res > 0 and len(x_clean) > n_params:
                f_stat = ((ss_tot - ss_res) / float(deg)) / (ss_res / dof_poly)
                p_val = safe_float(1.0 - sp_stats.f.cdf(f_stat, deg, dof_poly), None)

        elif model_type == "log":
            pos_mask = x_clean > 0
            if np.sum(pos_mask) >= 3 and len(np.unique(x_clean[pos_mask])) >= 2:
                x_used = x_clean[pos_mask]
                y_used = y_clean[pos_mask]
                
                if np.var(x_used) == 0 or np.var(y_used) == 0:
                    eq_str = "Filtreleme sonrası yetersiz veya sabit varyanslı veri."
                else:
                    slope, intercept, r_val, p_val, std_err = sp_stats.linregress(
                        np.log(x_used), y_used
                    )
                    r_squared = safe_float(r_val**2, 0.0)
                    se = safe_float(std_err, None)
                    sign_int = "+" if intercept >= 0 else "-"
                    eq_str = f"y = {slope:.4f}·ln(x) {sign_int} {abs(intercept):.4f}"

                    x_curve_pos = np.linspace(
                        max(float(np.min(x_used)), 1e-4), float(np.max(x_used)), num_points
                    )
                    y_curve = slope * np.log(x_curve_pos) + intercept
                    x_curve = x_curve_pos
                    y_fit_used = slope * np.log(x_used) + intercept
            else:
                eq_str = "Logaritmik regresyon için yeterli pozitif X değeri bulunamadı."

        elif model_type == "exp":
            pos_mask = y_clean > 0
            if np.sum(pos_mask) >= 3 and len(np.unique(x_clean[pos_mask])) >= 2:
                x_used = x_clean[pos_mask]
                y_used = y_clean[pos_mask]
                
                if np.var(x_used) == 0 or np.var(y_used) == 0:
                    eq_str = "Filtreleme sonrası yetersiz veya sabit varyanslı veri."
                else:
                    slope, intercept, r_val, p_val, std_err = sp_stats.linregress(
                        x_used, np.log(y_used)
                    )
                    a = np.exp(intercept)
                    b = slope
                    eq_str = f"y = {a:.4f}·e^({b:.4f}x)"
                    
                    y_fit_used = a * np.exp(b * x_used)
                    y_curve = a * np.exp(b * x_curve)
                    
                    ss_res = float(np.sum((y_used - y_fit_used) ** 2))
                    ss_tot = float(np.sum((y_used - np.mean(y_used)) ** 2))
                    r_squared = min(max(1.0 - (ss_res / ss_tot), 0.0), 1.0) if ss_tot > 0 else 0.0
                    
                    se = safe_float(std_err, None)
            else:
                eq_str = "Üstel regresyon için yeterli pozitif Y değeri bulunamadı."

        else:  # linear
            slope, intercept, r_val, p_val, std_err = sp_stats.linregress(
                x_clean, y_clean
            )
            r_squared = safe_float(r_val**2, 0.0)
            se = safe_float(std_err, None)
            sign_int = "+" if intercept >= 0 else "-"
            eq_str = f"y = {slope:.4f}x {sign_int} {abs(intercept):.4f}"
            y_curve = slope * x_curve + intercept
            y_fit_used = slope * x_clean + intercept

    except Exception as e:  # noqa: BLE001
        logger.warning(f"Regresyon hesaplama hatası ({model_type}): {e}")
        eq_str = f"Hesaplama hatası: {e}"

    # 95% Confidence Interval band calculation
    ci_lower = []
    ci_upper = []
    try:
        n_used = len(x_used)
        if y_fit_used is not None and n_used > n_params:
            dof = max(n_used - n_params, 1)
            t_val = float(sp_stats.t.ppf(0.975, dof))
            
            if model_type in ("poly2", "poly3") and X_design is not None and X_curve_design is not None:
                residuals = y_used - y_fit_used
                s_err2 = np.sum(residuals**2) / dof
                
                inv_xtx = np.linalg.pinv(X_design.T @ X_design)
                
                var_fit = np.sum((X_curve_design @ inv_xtx) * X_curve_design, axis=1) * s_err2
                se_line = np.sqrt(np.maximum(var_fit, 0))
                
                ci_upper = [round(float(v), 4) for v in (y_curve + t_val * se_line)]
                ci_lower = [round(float(v), 4) for v in (y_curve - t_val * se_line)]
                
            elif model_type == "exp":
                log_y_used = np.log(y_used)
                log_y_fit = intercept + slope * x_used
                log_y_curve = intercept + slope * x_curve
                
                residuals_log = log_y_used - log_y_fit
                s_err_log = float(np.sqrt(np.sum(residuals_log**2) / dof))
                x_bar = float(np.mean(x_used))
                ss_x = float(np.sum((x_used - x_bar) ** 2))
                
                if ss_x > 0:
                    se_line_log = s_err_log * np.sqrt(
                        1.0 / n_used + ((x_curve - x_bar) ** 2) / ss_x
                    )
                    
                    exp_upper = np.clip(log_y_curve + t_val * se_line_log, -500, 500)
                    exp_lower = np.clip(log_y_curve - t_val * se_line_log, -500, 500)
                    ci_upper = [round(float(v), 4) for v in np.exp(exp_upper)]
                    ci_lower = [round(float(v), 4) for v in np.exp(exp_lower)]
                
            else: # linear and log
                x_for_ci = np.log(x_used) if model_type == "log" else x_used
                x_curve_for_ci = np.log(x_curve) if model_type == "log" else x_curve
                
                residuals = y_used - y_fit_used
                s_err = float(np.sqrt(np.sum(residuals**2) / dof))
                x_bar = float(np.mean(x_for_ci))
                ss_x = float(np.sum((x_for_ci - x_bar) ** 2))

                if ss_x > 0:
                    se_line = s_err * np.sqrt(
                        1.0 / n_used + ((x_curve_for_ci - x_bar) ** 2) / ss_x
                    )
                    ci_upper = [round(float(v), 4) for v in (y_curve + t_val * se_line)]
                    ci_lower = [round(float(v), 4) for v in (y_curve - t_val * se_line)]
    except Exception as e_ci:  # noqa: BLE001
        logger.debug(f"CI calculation error: {e_ci}")

    finite_mask = np.isfinite(x_curve) & np.isfinite(y_curve)
    trend_x = [round(float(v), 4) for v in x_curve[finite_mask]]
    trend_y = [round(float(v), 4) for v in y_curve[finite_mask]]
    if len(ci_lower) == len(x_curve):
        ci_lower = [ci_lower[i] for i, m in enumerate(finite_mask) if m]
        ci_upper = [ci_upper[i] for i, m in enumerate(finite_mask) if m]

    bayes_reg = compute_bayes_factor_regression(
        float(r_squared) if r_squared is not None and np.isfinite(r_squared) else 0.0,
        len(x_used),
        p_predictors=max(n_params - 1, 1),
    )

    return {
        "equation": eq_str,
        "r_squared": round(float(r_squared), 4)
        if r_squared is not None and np.isfinite(r_squared)
        else 0.0,
        "se": round(float(se), 4) if se is not None and np.isfinite(se) else None,
        "p_value": safe_float(p_val, None),
        "model_type": model_type,
        "trend_x": trend_x,
        "trend_y": trend_y,
        "ci_lower": ci_lower if len(ci_lower) == len(trend_x) else [],
        "ci_upper": ci_upper if len(ci_upper) == len(trend_x) else [],
        "bayes_factor": bayes_reg,
        "bayes_bf10": bayes_reg.get("bf10"),
        "bayes_evidence": bayes_reg.get("evidence"),
        "bayes_p_h1": bayes_reg.get("p_h1"),
    }


def compute_correlation_matrix(active_df, num_cols=None, method="pearson"):
    """
    Computes a full pairwise correlation matrix for numeric columns.
    Uses pairwise complete observations without fabricating zeros for missing values.
    """
    if active_df is None or active_df.empty:
        return {"columns": [], "matrix": [], "sample_size": 0}

    if not num_cols:
        num_cols = active_df.select_dtypes(include=["number"]).columns.tolist()
    else:
        num_cols = [
            c
            for c in num_cols
            if c in active_df.columns and pd.api.types.is_numeric_dtype(active_df[c])
        ]

    if len(num_cols) < 2:
        return {
            "columns": num_cols,
            "matrix": [[1.0]] if len(num_cols) == 1 else [],
            "sample_size": len(active_df),
            "method": method,
        }

    # Limit to max 12 numeric columns for clean layout; sample for rank correlations on massive datasets
    selected_cols = num_cols[:12]
    sub_df = active_df[selected_cols]
    if len(sub_df) > 100000 and method in ("spearman", "kendall"):
        sub_df = sub_df.sample(n=50000, random_state=42)
    clean_sub = sub_df.replace([np.inf, -np.inf], np.nan)

    try:
        corr_df = clean_sub.corr(method=method, min_periods=3)
        matrix = []
        for i, row in enumerate(corr_df.values):
            row_list = []
            for j, v in enumerate(row):
                if i == j:
                    row_list.append(1.0)
                else:
                    row_list.append(
                        round(float(v), 4) if pd.notnull(v) and np.isfinite(v) else 0.0
                    )
            matrix.append(row_list)
        return {
            "columns": selected_cols,
            "matrix": matrix,
            "sample_size": len(clean_sub),
            "method": method,
            "truncated": len(num_cols) > 12,
            "total_cols": len(num_cols),
        }
    except Exception as e:
        logger.exception("compute_correlation_matrix error")
        return {"columns": selected_cols, "matrix": [], "error": str(e)}


def compute_column_statistics(df, columns):
    """
    Computes summary descriptive statistics for the requested numerical columns.
    Includes count, missing, mean, median, min, max, std, skewness, kurtosis,
    and Jarque-Bera normality test statistics with graceful fallback for edge cases.
    """
    stats = {}
    if df is None or df.empty or not columns:
        return stats

    for col in columns:
        if col not in df.columns:
            continue

        raw_series = df[col]
        s = pd.to_numeric(raw_series, errors="coerce")
        clean = s.dropna().to_numpy(dtype=float)
        clean = clean[np.isfinite(clean)]
        n_valid = len(clean)

        mean_val = safe_float(s.mean(), None)
        median_val = safe_float(s.median(), None)
        min_val = safe_float(s.min(), None)
        max_val = safe_float(s.max(), None)
        std_val = safe_float(s.std(), None)

        # Skewness & Kurtosis
        skew_val = None
        kurt_val = None
        if n_valid >= 3 and std_val is not None and std_val > 0:
            try:
                skew_val = safe_float(sp_stats.skew(clean, bias=False), None)
            except Exception:
                skew_val = None

        if n_valid >= 4 and std_val is not None and std_val > 0:
            try:
                kurt_val = safe_float(sp_stats.kurtosis(clean, bias=False), None)
            except Exception:
                kurt_val = None

        # Jarque-Bera Normality Test
        jb_stat = None
        jb_p = None
        if n_valid >= 4 and std_val is not None and std_val > 0:
            try:
                jb_res = sp_stats.jarque_bera(clean)
                jb_stat = safe_float(
                    getattr(jb_res, "statistic", jb_res[0]), None
                )
                jb_p = safe_float(
                    getattr(jb_res, "pvalue", jb_res[1]), None
                )
            except Exception:
                jb_stat, jb_p = None, None

        stats[col] = {
            "count": int(s.count()),
            "missing": int(s.isna().sum()),
            "mean": mean_val,
            "median": median_val,
            "min": min_val,
            "max": max_val,
            "std": std_val,
            "skewness": skew_val,
            "kurtosis": kurt_val,
            "jarque_bera_stat": jb_stat,
            "jarque_bera_p": jb_p,
            "jarque_bera": {
                "statistic": jb_stat,
                "p_value": jb_p,
                "is_normal": bool(jb_p > 0.05) if jb_p is not None else None,
            },
        }
    return stats


def compute_advanced_stats(
    active_df, cols, x_col=None, corr_method="pearson", reg_model="linear"
):
    """
    Performs deep comparative analysis:
    - If X is numeric: Pearson/Spearman/Kendall correlation, curve regression, and Bayes Factor (BF₁₀).
    - If X is categorical with 2 groups: Independent two-sample Student/Welch's T-Test and Bayes Factor (BF₁₀).
    - If X is categorical with >2 groups: One-way ANOVA F-Test and Bayes Factor (BF₁₀).
    Robust against dirty datasets (auto-coerces numbers, ignores placeholder error categories).
    """
    advanced = {}
    if not x_col or x_col not in active_df.columns:
        return advanced

    # Check whether x_col is numeric or categorical, with dirty-data resilience
    is_x_num = pd.api.types.is_numeric_dtype(active_df[x_col])
    x_coerced = pd.to_numeric(active_df[x_col], errors="coerce")
    if not is_x_num:
        valid_num_ratio = (
            float(x_coerced.notna().sum() / len(active_df))
            if len(active_df) > 0
            else 0.0
        )
        if valid_num_ratio >= 0.55 and x_coerced.nunique() > 10:
            is_x_num = True

    for y_col in cols:
        if y_col not in active_df.columns:
            continue

        y_is_num = pd.api.types.is_numeric_dtype(active_df[y_col])
        y_coerced = pd.to_numeric(active_df[y_col], errors="coerce")
        if not y_is_num:
            valid_y_ratio = (
                float(y_coerced.notna().sum() / len(active_df))
                if len(active_df) > 0
                else 0.0
            )
            if valid_y_ratio < 0.3 or y_coerced.notna().sum() < 3:
                continue

        adv_info = {}

        if is_x_num:
            valid_mask = (
                x_coerced.notna()
                & y_coerced.notna()
                & np.isfinite(x_coerced)
                & np.isfinite(y_coerced)
            )
            x_vals = x_coerced[valid_mask].to_numpy(dtype=float)
            y_vals = y_coerced[valid_mask].to_numpy(dtype=float)

            if len(x_vals) > 2:
                corr_res = compute_robust_correlation(
                    x_vals, y_vals, method=corr_method
                )
                reg_res = compute_robust_regression(
                    x_vals, y_vals, model_type=reg_model
                )
                bayes_reg = reg_res.get(
                    "bayes_factor"
                ) or compute_bayes_factor_regression(
                    reg_res.get("r_squared"), len(x_vals)
                )

                adv_info["correlation"] = corr_res["coef"]
                adv_info["corr_method"] = corr_res["method"]
                adv_info["interpretation"] = corr_res["interpretation"]
                adv_info["p_value"] = corr_res["p_value"]
                adv_info["r_squared"] = reg_res["r_squared"]
                adv_info["regression"] = reg_res["equation"]
                adv_info["se"] = reg_res["se"]
                adv_info["reg_model"] = reg_res["model_type"]
                adv_info["sample_size"] = corr_res["sample_size"]
                adv_info["type"] = "numeric"
                adv_info["bayes_factor"] = bayes_reg
                adv_info["bayes_bf10"] = bayes_reg.get("bf10")
                adv_info["bayes_evidence"] = bayes_reg.get("evidence")
                adv_info["bayes_p_h1"] = bayes_reg.get("p_h1")
        else:
            # Categorical X vs Numeric Y
            x_raw = active_df[x_col]
            y_clean_series = y_coerced

            # Filter out missing, placeholder or dirty category labels
            ignored_placeholders = {
                "nan",
                "null",
                "none",
                "unknown",
                "error",
                "hata",
                "boş",
                "bos",
                "yok",
                "-",
                "",
            }

            valid_mask = (
                x_raw.notna() & y_clean_series.notna() & np.isfinite(y_clean_series)
            )
            x_valid = x_raw[valid_mask]
            y_valid = y_clean_series[valid_mask]

            group_dict = {}
            for g_name, g_indices in x_valid.groupby(
                x_valid, observed=False
            ).groups.items():
                g_str = str(g_name).strip()
                if not g_str or g_str.lower() in ignored_placeholders:
                    continue
                g_vals = y_valid.loc[g_indices].to_numpy(dtype=float)
                if len(g_vals) >= 2:
                    group_dict[g_str] = g_vals

            # If all valid groups were excluded or only 1, fallback to raw groupby
            if len(group_dict) < 2:
                group_dict = {}
                for g_name, g_indices in x_valid.groupby(
                    x_valid, observed=False
                ).groups.items():
                    g_str = str(g_name).strip()
                    if g_str and g_str.lower() not in ("nan", "null", ""):
                        g_vals = y_valid.loc[g_indices].to_numpy(dtype=float)
                        if len(g_vals) >= 2:
                            group_dict[g_str] = g_vals

            group_names = list(group_dict.keys())
            groups = list(group_dict.values())

            # Group means and rankings
            if group_names:
                grp_means = {
                    k: safe_float(np.mean(v), 0.0) for k, v in group_dict.items()
                }
                sorted_groups = sorted(
                    grp_means.items(),
                    key=lambda item: item[1] if item[1] is not None else -1e9,
                    reverse=True,
                )
                adv_info["best_group"] = sorted_groups[0][0]
                adv_info["best_val"] = sorted_groups[0][1]
                adv_info["worst_group"] = sorted_groups[-1][0]
                adv_info["worst_val"] = sorted_groups[-1][1]
                adv_info["group_means"] = grp_means

            if len(groups) == 2:
                # 1. Welch T-Test (Parametrik)
                try:
                    t_stat, p_val = sp_stats.ttest_ind(
                        groups[0], groups[1], equal_var=False
                    )
                    bayes_t = compute_bayes_factor_ttest(
                        t_stat, len(groups[0]), len(groups[1])
                    )
                    adv_info["t_test_stat"] = safe_float(t_stat, None)
                    adv_info["p_value"] = safe_float(p_val, None)
                    adv_info["type"] = "categorical_2"
                    adv_info["bayes_factor"] = bayes_t
                    adv_info["bayes_bf10"] = bayes_t.get("bf10")
                    adv_info["bayes_evidence"] = bayes_t.get("evidence")
                    adv_info["bayes_p_h1"] = bayes_t.get("p_h1")
                    adv_info["t_test"] = {
                        "t_stat": safe_float(t_stat, None),
                        "p_value": safe_float(p_val, None),
                        "group_means": adv_info.get("group_means", {}),
                        "groups": group_names,
                        "bayes_factor": bayes_t,
                        "bayes_bf10": bayes_t.get("bf10"),
                        "bayes_evidence": bayes_t.get("evidence"),
                    }
                except Exception as e_ttest:
                    logger.debug(f"T-Test error: {e_ttest}")
                    adv_info["t_test_stat"] = None
                    adv_info["p_value"] = None

                # 2. Mann-Whitney U Test (Parametrik Olmayan)
                try:
                    mw_res = sp_stats.mannwhitneyu(
                        groups[0], groups[1], alternative="two-sided"
                    )
                    mw_stat = safe_float(
                        getattr(mw_res, "statistic", mw_res[0]), None
                    )
                    mw_p = safe_float(getattr(mw_res, "pvalue", mw_res[1]), None)
                    adv_info["mann_whitney_u"] = mw_stat
                    adv_info["mann_whitney_p"] = mw_p
                    adv_info["mann_whitney"] = {
                        "u_stat": mw_stat,
                        "p_value": mw_p,
                    }
                except Exception as e_mw:
                    logger.debug(f"Mann-Whitney U error: {e_mw}")
                    adv_info["mann_whitney_u"] = None
                    adv_info["mann_whitney_p"] = None
                    adv_info["mann_whitney"] = {"u_stat": None, "p_value": None}

            elif len(groups) > 2:
                # 1. One-Way ANOVA (Parametrik)
                try:
                    f_stat, p_val = sp_stats.f_oneway(*groups)
                    n_tot = sum(len(g) for g in groups)
                    bayes_anova = compute_bayes_factor_anova(
                        f_stat, len(groups), n_tot
                    )
                    adv_info["anova_f"] = safe_float(f_stat, None)
                    adv_info["p_value"] = safe_float(p_val, None)
                    adv_info["type"] = "categorical_n"
                    adv_info["bayes_factor"] = bayes_anova
                    adv_info["bayes_bf10"] = bayes_anova.get("bf10")
                    adv_info["bayes_evidence"] = bayes_anova.get("evidence")
                    adv_info["bayes_p_h1"] = bayes_anova.get("p_h1")
                    adv_info["anova"] = {
                        "f_stat": safe_float(f_stat, None),
                        "p_value": safe_float(p_val, None),
                        "groups": group_names,
                        "bayes_factor": bayes_anova,
                        "bayes_bf10": bayes_anova.get("bf10"),
                        "bayes_evidence": bayes_anova.get("evidence"),
                    }
                except Exception as e_anova:
                    logger.debug(f"ANOVA error: {e_anova}")
                    adv_info["anova_f"] = None
                    adv_info["p_value"] = None

                # 2. Kruskal-Wallis H Test (Parametrik Olmayan)
                try:
                    all_vals = np.concatenate(groups)
                    if len(np.unique(all_vals)) > 1:
                        kw_res = sp_stats.kruskal(*groups)
                        kw_stat = safe_float(
                            getattr(kw_res, "statistic", kw_res[0]), None
                        )
                        kw_p = safe_float(
                            getattr(kw_res, "pvalue", kw_res[1]), None
                        )
                    else:
                        kw_stat, kw_p = None, None
                    adv_info["kruskal_h"] = kw_stat
                    adv_info["kruskal_p"] = kw_p
                    adv_info["kruskal_wallis"] = {
                        "h_stat": kw_stat,
                        "p_value": kw_p,
                    }
                except Exception as e_kw:
                    logger.debug(f"Kruskal-Wallis error: {e_kw}")
                    adv_info["kruskal_h"] = None
                    adv_info["kruskal_p"] = None
                    adv_info["kruskal_wallis"] = {"h_stat": None, "p_value": None}
            else:
                adv_info["type"] = "categorical_single"

            adv_info["anova_best_group"] = adv_info.get("best_group")
            adv_info["anova_low_group"] = adv_info.get("worst_group")

        advanced[y_col] = adv_info
        if adv_info.get("type") == "numeric":
            advanced["type"] = "numeric"
            advanced["regression"] = adv_info.get("regression")
            advanced["correlation"] = adv_info.get("correlation")
            advanced["r_squared"] = adv_info.get("r_squared")
            advanced["p_value"] = adv_info.get("p_value")
            advanced["bayes_factor"] = adv_info.get("bayes_factor")
            advanced["bayes_bf10"] = adv_info.get("bayes_bf10")
            advanced["bayes_evidence"] = adv_info.get("bayes_evidence")
        elif "anova" in adv_info:
            advanced["type"] = "categorical_n"
            advanced["anova"] = adv_info["anova"]
            advanced["kruskal_wallis"] = adv_info.get("kruskal_wallis", {})
            advanced["kruskal_h"] = adv_info.get("kruskal_h")
            advanced["kruskal_p"] = adv_info.get("kruskal_p")
            advanced["p_value"] = adv_info.get("p_value") or adv_info.get("anova", {}).get("p_value")
            advanced["anova_best_group"] = adv_info.get("best_group")
            advanced["anova_low_group"] = adv_info.get("worst_group")
            advanced["best_group"] = adv_info.get("best_group")
            advanced["best_val"] = adv_info.get("best_val")
            advanced["worst_group"] = adv_info.get("worst_group")
            advanced["worst_val"] = adv_info.get("worst_val")
            advanced["bayes_factor"] = adv_info.get("bayes_factor")
            advanced["bayes_bf10"] = adv_info.get("bayes_bf10")
            advanced["bayes_evidence"] = adv_info.get("bayes_evidence")
        elif "t_test" in adv_info:
            advanced["type"] = "categorical_2"
            advanced["t_test"] = adv_info["t_test"]
            advanced["t_test_stat"] = adv_info["t_test"]["t_stat"]
            advanced["mann_whitney"] = adv_info.get("mann_whitney", {})
            advanced["mann_whitney_u"] = adv_info.get("mann_whitney_u")
            advanced["mann_whitney_p"] = adv_info.get("mann_whitney_p")
            advanced["p_value"] = adv_info["t_test"]["p_value"]
            advanced["group_means"] = adv_info.get("group_means", {})
            advanced["best_group"] = adv_info.get("best_group")
            advanced["best_val"] = adv_info.get("best_val")
            advanced["worst_group"] = adv_info.get("worst_group")
            advanced["worst_val"] = adv_info.get("worst_val")
            advanced["bayes_factor"] = adv_info.get("bayes_factor")
            advanced["bayes_bf10"] = adv_info.get("bayes_bf10")
            advanced["bayes_evidence"] = adv_info.get("bayes_evidence")

    return advanced


def _format_tr_num(val, decimals=1):
    if val is None or not np.isfinite(val):
        return "0"
    fmt = f"{val:,.{decimals}f}"
    return fmt.replace(",", "X").replace(".", ",").replace("X", ".")


def _is_monetary_column(col_name):
    col_l = str(col_name).lower()
    monetary_keywords = (
        "tutar",
        "fiyat",
        "satış",
        "satis",
        "gelir",
        "gider",
        "maliyet",
        "maaş",
        "maas",
        "bütçe",
        "butce",
        "kar",
        "kâr",
        "ücret",
        "ucret",
        "tl",
        "usd",
        "eur",
        "ciro",
        "ödeme",
        "odeme",
        "harcama",
        "kazanç",
        "kazanc",
    )
    return any(k in col_l for k in monetary_keywords)


def generate_kpi_summary(active_df, total_original_rows=None):
    """
    Generates executive KPI tiles based on the active filtered DataFrame.
    """
    if active_df is None or active_df.empty:
        return {"kpis": [], "total_active_rows": 0}

    total_rows = total_original_rows or len(active_df)
    num_cols = active_df.select_dtypes(include=["number"]).columns.tolist()
    cat_cols = active_df.select_dtypes(
        include=["object", "category", "string"]
    ).columns.tolist()

    kpis = []

    # 1. Total records
    sub_records = f"Toplam {total_rows:,} satırdan".replace(",", ".")
    kpis.append(
        {
            "title": "Toplam Kayıt",
            "value": f"{len(active_df):,}".replace(",", "."),
            "sub": sub_records,
            "subtext": sub_records,
            "icon": "📋",
            "color": "blue",
        }
    )

    # 2. Main numeric metric
    if num_cols:
        main_num = num_cols[0]
        total_val = safe_float(active_df[main_num].sum(), 0.0)
        mean_val = safe_float(active_df[main_num].mean(), 0.0)
        prefix = "₺" if _is_monetary_column(main_num) else ""

        if abs(total_val) >= 1_000_000:
            val_str = f"{prefix}{total_val / 1_000_000:.2f}M"
        elif abs(total_val) >= 1_000:
            val_str = f"{prefix}{total_val / 1_000:.1f}K"
        else:
            val_str = f"{prefix}{_format_tr_num(total_val, 1)}"

        sub_main = f"Ort: {_format_tr_num(mean_val, 1)}"
        kpis.append(
            {
                "title": f"Toplam {main_num}",
                "value": val_str,
                "sub": sub_main,
                "subtext": sub_main,
                "icon": "💰" if prefix else "📊",
                "color": "green",
            }
        )

        # 3. Secondary numeric metric
        if len(num_cols) > 1:
            sec_num = num_cols[1]
            sec_total = safe_float(active_df[sec_num].sum(), 0.0)
            sec_max = safe_float(active_df[sec_num].max(), 0.0)
            sub_sec = f"Maks: {_format_tr_num(sec_max, 1)}"
            kpis.append(
                {
                    "title": f"Toplam {sec_num}",
                    "value": _format_tr_num(sec_total, 1),
                    "sub": sub_sec,
                    "subtext": sub_sec,
                    "icon": "📈",
                    "color": "purple",
                }
            )

    # 4. Leading category
    if cat_cols:
        main_cat = cat_cols[0]
        vc = active_df[main_cat].dropna().value_counts()
        if not vc.empty:
            top_cat_name = str(vc.index[0])
            top_cat_count = int(vc.iloc[0])
            pct = (top_cat_count / len(active_df)) * 100 if len(active_df) > 0 else 0
            sub_cat = f"%{pct:.1f} pay ({top_cat_count} adet)"
            kpis.append(
                {
                    "title": f"Lider {main_cat}",
                    "value": top_cat_name[:15],
                    "sub": sub_cat,
                    "subtext": sub_cat,
                    "icon": "🏆",
                    "color": "orange",
                }
            )

    return {"kpis": kpis, "total_active_rows": len(active_df), "total_rows": total_rows}


def compute_pivot_data(active_df, rows, cols, values, agg_func="sum"):
    """
    Computes live Excel-style Pivot Table Matrix with multi-level indices and grand totals.
    """
    if active_df is None or active_df.empty:
        raise ValueError("Uygulanan filtreler sonucunda veri kalmadı.")

    if isinstance(rows, str):
        rows = [rows] if rows else []
    if isinstance(cols, str):
        cols = [cols] if cols else []
    if isinstance(values, str):
        values = [values] if values else []

    valid_rows = list(
        dict.fromkeys(r for r in (rows or []) if r in active_df.columns)
    )
    valid_cols = list(
        dict.fromkeys(
            c
            for c in (cols or [])
            if c in active_df.columns and c not in valid_rows
        )
    )
    valid_values = list(
        dict.fromkeys(
            v
            for v in (values or [])
            if v in active_df.columns
            and pd.api.types.is_numeric_dtype(active_df[v])
            and v not in valid_rows
            and v not in valid_cols
        )
    )

    if len(valid_rows) == 0 and len(valid_cols) == 0:
        raise ValueError("En az bir Satır veya Sütun boyutu seçmelisiniz.")

    if not valid_values:
        raise ValueError(
            "Lütfen satır/sütun boyutlarından farklı en az bir sayısal Değer (Metrik) seçin."
        )

    agg_map = {
        "sum": "sum",
        "mean": "mean",
        "count": "count",
        "min": "min",
        "max": "max",
        "median": "median",
    }
    chosen_agg = agg_map.get(agg_func, "sum")

    proj_cols = list(dict.fromkeys(valid_rows + valid_cols + valid_values))
    try:
        pt = pd.pivot_table(
            active_df[proj_cols],
            index=valid_rows if valid_rows else None,
            columns=valid_cols if valid_cols else None,
            values=valid_values,
            aggfunc=chosen_agg,
            fill_value=0,
            margins=True,
            margins_name="Genel Toplam",
            observed=False,
        )
    except Exception as e_pt:
        logger.warning(
            f"Margins=True ile pivot table hatası, margins=False deneniyor: {e_pt}"
        )
        pt = pd.pivot_table(
            active_df[proj_cols],
            index=valid_rows if valid_rows else None,
            columns=valid_cols if valid_cols else None,
            values=valid_values,
            aggfunc=chosen_agg,
            fill_value=0,
            margins=False,
            observed=False,
        )

    if isinstance(pt.columns, pd.MultiIndex):
        raw_headers = pt.columns.tolist()
        table_headers = [
            " | ".join([str(x) for x in item if str(x) != ""]) for item in raw_headers
        ]
    else:
        table_headers = [str(c) for c in pt.columns.tolist()]

    has_grand_total_col = any("Genel Toplam" in h for h in table_headers)
    table_rows = []
    raw_values_all = []

    if isinstance(pt.index, pd.MultiIndex):
        index_names = [
            str(n) if n else f"Seviye {i + 1}" for i, n in enumerate(pt.index.names)
        ]
        for idx_val, row_series in pt.iterrows():
            row_labels = [str(x) for x in idx_val]
            row_vals = [safe_float(v, 0.0) for v in row_series.tolist()]
            is_gt_row = any("Genel Toplam" in lbl for lbl in row_labels)
            if not is_gt_row:
                non_gt_idx = [i for i, h in enumerate(table_headers) if "Genel Toplam" not in str(h)]
                raw_values_all.extend([row_vals[i] for i in non_gt_idx if i < len(row_vals)])
            table_rows.append(
                {
                    "row_labels": row_labels,
                    "cells": row_vals,
                    "is_grand_total": is_gt_row,
                }
            )
    else:
        index_names = [
            str(pt.index.name)
            if pt.index.name
            else (valid_rows[0] if valid_rows else "Boyut")
        ]
        for idx_val, row_series in pt.iterrows():
            row_labels = [str(idx_val)]
            row_vals = [safe_float(v, 0.0) for v in row_series.tolist()]
            is_gt_row = str(idx_val) == "Genel Toplam"
            if not is_gt_row:
                non_gt_idx = [i for i, h in enumerate(table_headers) if "Genel Toplam" not in str(h)]
                raw_values_all.extend([row_vals[i] for i in non_gt_idx if i < len(row_vals)])
            table_rows.append(
                {
                    "row_labels": row_labels,
                    "cells": row_vals,
                    "is_grand_total": is_gt_row,
                }
            )

    min_val = float(min(raw_values_all)) if raw_values_all else 0.0
    max_val = float(max(raw_values_all)) if raw_values_all else 0.0

    return {
        "index_names": index_names,
        "column_headers": table_headers,
        "rows": table_rows,
        "min_value": min_val,
        "max_value": max_val,
        "total_data_rows": len(active_df),
        "row_dimensions": valid_rows,
        "col_dimensions": valid_cols,
        "value_metrics": valid_values,
        "agg_func": agg_func,
    }


def compute_multiple_linear_regression(
    df, feature_cols, target_col, fit_intercept=True
) -> dict:
    """
    Fits an Ordinary Least Squares (OLS) Multiple Linear Regression model
    with strict singular matrix (multicollinearity) resilience using Moore-Penrose pseudo-inverse.
    Returns R², Adjusted R², F-statistic, p-value, standard errors, t-statistics,
    p-values for each coefficient, and Variance Inflation Factor (VIF) / Multicollinearity warning.
    """
    if df is None or df.empty or not target_col or not feature_cols:
        return {"error": "Geçerli bağımlı ve bağımsız değişkenler seçilmelidir."}

    if target_col not in df.columns:
        return {"error": f"Hedef sütun ({target_col}) veri setinde bulunamadı."}

    valid_feats = [
        c for c in feature_cols if c in df.columns and c != target_col
    ]
    if not valid_feats:
        return {"error": "En az bir geçerli bağımsız (özellik) değişken seçilmelidir."}

    sub = df[valid_feats + [target_col]].dropna()
    if sub.empty:
        return {"error": "Seçilen sütunlarda geçerli (boş olmayan) veri satırı bulunamadı."}

    X_df = sub[valid_feats].apply(pd.to_numeric, errors="coerce")
    y_ser = pd.to_numeric(sub[target_col], errors="coerce")
    valid_mask = X_df.notna().all(axis=1) & y_ser.notna() & np.isfinite(y_ser)
    for c in valid_feats:
        valid_mask &= np.isfinite(X_df[c])

    X_clean = X_df.loc[valid_mask].to_numpy(dtype=float)
    y_clean = y_ser.loc[valid_mask].to_numpy(dtype=float)

    n_samples, n_features = X_clean.shape
    if n_samples <= n_features + (1 if fit_intercept else 0):
        return {
            "error": f"Gözlem sayısı ({n_samples}), serbestlik derecesi için yetersiz (en az {n_features + 2} geçerli satır gereklidir)."
        }

    if np.isclose(float(np.std(y_clean)), 0.0):
        return {"error": "Hedef değişken sabit değerlidir (sıfır varyans), regresyon kurulamaz."}

    try:
        if fit_intercept:
            X_design = np.column_stack([np.ones(n_samples), X_clean])
            feature_names = ["(Sabit Terim / Intercept)"] + valid_feats
        else:
            X_design = X_clean
            feature_names = list(valid_feats)

        p_params = X_design.shape[1]
        df_resid = max(n_samples - p_params, 1)

        # Singülerlik ve Çoklu Doğrusallık Denetimi
        rank = int(np.linalg.matrix_rank(X_design))
        cond_number = safe_float(np.linalg.cond(X_design), 1e15)
        is_singular = rank < p_params or (cond_number is not None and cond_number > 1e10)

        # OLS Çözümü: pinv (Moore-Penrose) ile singüler matris çökmesi engellenir
        XtX = X_design.T @ X_design
        XtX_inv = np.linalg.pinv(XtX)
        beta = XtX_inv @ (X_design.T @ y_clean)

        y_pred = X_design @ beta
        residuals = y_clean - y_pred
        ss_res = float(np.sum(residuals**2))
        ss_tot = float(np.sum((y_clean - np.mean(y_clean)) ** 2))

        r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
        r_squared = min(max(r_squared, 0.0), 1.0)

        adj_r2 = 1.0 - ((1.0 - r_squared) * (n_samples - 1) / max(df_resid, 1))
        adj_r2 = min(max(adj_r2, 0.0), 1.0)

        s2 = ss_res / df_resid
        se_est = float(np.sqrt(max(s2, 0.0)))

        cov_beta = s2 * XtX_inv
        se_beta = np.sqrt(np.maximum(np.diag(cov_beta), 1e-15))
        t_stats = beta / se_beta
        p_values = [
            safe_float(2.0 * (1.0 - sp_stats.t.cdf(abs(t), df=df_resid)), 1.0)
            for t in t_stats
        ]

        k_predictors = p_params - 1 if fit_intercept else p_params
        if ss_res > 0 and k_predictors > 0:
            f_stat = ((ss_tot - ss_res) / k_predictors) / (ss_res / df_resid)
            f_pval = safe_float(1.0 - sp_stats.f.cdf(f_stat, k_predictors, df_resid), None)
            f_stat_val = safe_float(f_stat, None)
        else:
            f_stat_val = None
            f_pval = None

        # VIF (Variance Inflation Factor)
        vif_dict = {}
        for idx, feat in enumerate(valid_feats):
            if n_features == 1:
                vif_dict[feat] = 1.0
            else:
                try:
                    other_idx = [i for i in range(n_features) if i != idx]
                    X_other = np.column_stack([np.ones(n_samples), X_clean[:, other_idx]])
                    beta_other = np.linalg.pinv(X_other.T @ X_other) @ (X_other.T @ X_clean[:, idx])
                    ss_feat_res = np.sum((X_clean[:, idx] - X_other @ beta_other)**2)
                    ss_feat_tot = max(np.sum((X_clean[:, idx] - np.mean(X_clean[:, idx]))**2), 1e-12)
                    r2_other = 1.0 - (ss_feat_res / ss_feat_tot)
                    vif_val = 1.0 / max(1.0 - min(max(r2_other, 0.0), 0.9999), 1e-6)
                    vif_dict[feat] = round(float(vif_val), 2)
                except Exception:
                    vif_dict[feat] = None

        coefficients_list = []
        for idx, name in enumerate(feature_names):
            coefficients_list.append({
                "feature": name,
                "coef": round(float(beta[idx]), 4),
                "std_err": round(float(se_beta[idx]), 4),
                "t_stat": round(float(t_stats[idx]), 4),
                "p_value": p_values[idx],
                "vif": vif_dict.get(name),
                "is_significant": bool(p_values[idx] < 0.05) if p_values[idx] is not None else False
            })

        terms = []
        for item in coefficients_list:
            feat_name = item["feature"]
            c_val = item["coef"]
            sign = "+" if c_val >= 0 else "-"
            if "(Sabit Terim" in feat_name:
                terms.append(f"{c_val:.4f}")
            else:
                terms.append(f"{sign} {abs(c_val):.4f}·{feat_name}")
        equation_str = f"{target_col} = " + " ".join(terms)

        multicollinearity_msg = (
            "Yüksek çoklu doğrusallık veya singüler matris tespit edildi; Moore-Penrose genelleştirilmiş ters matris ile stabil çözüm üretildi."
            if is_singular
            else "Çoklu doğrusallık riski bulunmamaktadır (matris tam mertebedir)."
        )

        return {
            "success": True,
            "target_col": target_col,
            "feature_cols": valid_feats,
            "sample_size": n_samples,
            "r_squared": round(float(r_squared), 4),
            "adj_r_squared": round(float(adj_r2), 4),
            "std_error": round(float(se_est), 4),
            "f_statistic": round(float(f_stat_val), 4) if f_stat_val is not None else None,
            "p_value": f_pval,
            "equation": equation_str,
            "coefficients": coefficients_list,
            "vif": vif_dict,
            "is_singular": is_singular,
            "condition_number": round(float(cond_number), 2) if cond_number is not None else None,
            "multicollinearity_note": multicollinearity_msg,
        }
    except Exception as e:
        logger.exception("compute_multiple_linear_regression hatası")
        return {"error": f"Çoklu regresyon hesaplanırken hata oluştu: {e}"}


def compute_logistic_regression(
    df, feature_cols, target_col, max_iter=1000
) -> dict:
    """
    Fits a Logistic Regression classifier (Binary or Multinomial) on numeric feature columns.
    Returns accuracy, confusion matrix, class distribution, odds ratios, and coefficients.
    """
    if df is None or df.empty or not target_col or not feature_cols:
        return {"error": "Geçerli bağımlı ve bağımsız değişkenler seçilmelidir."}

    if target_col not in df.columns:
        return {"error": f"Hedef sütun ({target_col}) veri setinde bulunamadı."}

    valid_feats = [
        c for c in feature_cols if c in df.columns and c != target_col
    ]
    if not valid_feats:
        return {"error": "En az bir geçerli sayısal özellik sütunu seçilmelidir."}

    sub = df[valid_feats + [target_col]].dropna()
    if len(sub) < 8:
        return {"error": "Lojistik regresyon için yeterli geçerli satır bulunamadı (en az 8 satır gereklidir)."}

    X_df = sub[valid_feats].apply(pd.to_numeric, errors="coerce").replace([np.inf, -np.inf], np.nan)
    y_ser = sub[target_col].astype(str)
    valid_mask = X_df.notna().all(axis=1) & y_ser.notna() & (y_ser != "nan")
    if valid_mask.sum() < 8:
        return {"error": "Lojistik regresyon için yeterli geçerli satır bulunamadı (en az 8 satır gereklidir)." }

    X_clean = X_df.loc[valid_mask].to_numpy(dtype=float)
    y_clean = y_ser.loc[valid_mask].to_numpy()

    unique_classes, class_counts = np.unique(y_clean, return_counts=True)
    if len(unique_classes) < 2:
        return {"error": "Lojistik regresyon için hedef değişken en az 2 farklı sınıfa sahip olmalıdır."}

    if min(class_counts) < 2:
        return {"error": "Hedef değişkendeki her bir sınıf en az 2 gözlem içermelidir."}

    try:
        from sklearn.linear_model import LogisticRegression
        from sklearn.metrics import accuracy_score, confusion_matrix

        model = LogisticRegression(max_iter=max_iter, solver="lbfgs")
        model.fit(X_clean, y_clean)
        preds = model.predict(X_clean)
        acc = float(accuracy_score(y_clean, preds))
        cm = confusion_matrix(y_clean, preds, labels=unique_classes).tolist()

        classes_list = [str(c) for c in unique_classes]
        coef_dict = {}
        odds_ratios = {}

        if len(unique_classes) == 2:
            raw_coef = model.coef_[0]
            for idx, feat in enumerate(valid_feats):
                c_val = float(raw_coef[idx])
                coef_dict[feat] = round(c_val, 4)
                odds_ratios[feat] = round(float(np.exp(c_val)), 4) if abs(c_val) < 20 else None
            intercept_val = round(float(model.intercept_[0]), 4)
        else:
            for c_idx, c_name in enumerate(classes_list):
                coef_dict[c_name] = {
                    feat: round(float(model.coef_[c_idx][f_idx]), 4)
                    for f_idx, feat in enumerate(valid_feats)
                }
            intercept_val = [round(float(b), 4) for b in model.intercept_]

        return {
            "success": True,
            "model_type": "Binary" if len(unique_classes) == 2 else "Multinomial",
            "target_col": target_col,
            "feature_cols": valid_feats,
            "classes": classes_list,
            "class_counts": {str(k): int(v) for k, v in zip(unique_classes, class_counts)},
            "sample_size": len(X_clean),
            "accuracy": round(acc, 4),
            "confusion_matrix": cm,
            "coefficients": coef_dict,
            "odds_ratios": odds_ratios if len(unique_classes) == 2 else None,
            "intercept": intercept_val,
        }
    except Exception as e:
        logger.exception("compute_logistic_regression hatası")
        return {"error": f"Lojistik regresyon modeli eğitilirken hata: {e}"}


def compute_hypothesis_tests(df, group_col, value_col) -> dict:
    """
    Performs comprehensive hypothesis testing between a categorical grouping variable
    and a numeric continuous variable:
    - 2 groups: Independent Student & Welch T-Tests, Mann-Whitney U, Levene's variance homogeneity.
    - >2 groups: One-Way ANOVA, Kruskal-Wallis H, Levene's test.
    Includes normality checks (Shapiro-Wilk) and Turkish APA interpretation.
    """
    if df is None or df.empty or not group_col or not value_col:
        return {"error": "Geçerli bir grup sütunu ve sayısal değer sütunu seçilmelidir."}

    if group_col not in df.columns or value_col not in df.columns:
        return {"error": f"Sütunlar bulunamadı: {group_col}, {value_col}"}

    sub = df[[group_col, value_col]].dropna()
    sub_val = pd.to_numeric(sub[value_col], errors="coerce")
    valid_mask = sub_val.notna() & np.isfinite(sub_val) & sub[group_col].notna()

    clean_df = sub.loc[valid_mask].copy()
    clean_df["_val"] = sub_val.loc[valid_mask]
    clean_df["_grp"] = clean_df[group_col].astype(str).str.strip()
    clean_df = clean_df[~clean_df["_grp"].str.lower().isin(["nan", "null", "none", ""])]

    grouped = {
        name: grp["_val"].to_numpy(dtype=float)
        for name, grp in clean_df.groupby("_grp")
        if len(grp) >= 2
    }

    group_names = list(grouped.keys())
    if len(group_names) < 2:
        return {"error": "Hipotez testi için en az 2 geçerli grup bulunmalıdır (her grupta en az 2 gözlem olmalıdır)."}

    group_arrays = [grouped[name] for name in group_names]
    n_total = sum(len(a) for a in group_arrays)

    group_summaries = {}
    for name in group_names:
        arr = grouped[name]
        sw_stat, sw_p = None, None
        if len(arr) >= 3 and np.std(arr) > 0:
            try:
                sw_res = sp_stats.shapiro(arr)
                sw_stat = safe_float(getattr(sw_res, "statistic", sw_res[0]), None)
                sw_p = safe_float(getattr(sw_res, "pvalue", sw_res[1]), None)
            except Exception:
                sw_stat, sw_p = None, None

        group_summaries[name] = {
            "n": len(arr),
            "mean": safe_float(np.mean(arr), 0.0),
            "std": safe_float(np.std(arr, ddof=1), 0.0) if len(arr) > 1 else 0.0,
            "median": safe_float(np.median(arr), 0.0),
            "shapiro_p": sw_p,
            "is_normal": bool(sw_p > 0.05) if sw_p is not None else None,
        }

    levene_stat, levene_p = None, None
    try:
        lev_res = sp_stats.levene(*group_arrays)
        levene_stat = safe_float(getattr(lev_res, "statistic", lev_res[0]), None)
        levene_p = safe_float(getattr(lev_res, "pvalue", lev_res[1]), None)
    except Exception as e_lev:
        logger.debug(f"Levene test hatası: {e_lev}")

    results = {
        "success": True,
        "group_col": group_col,
        "value_col": value_col,
        "group_names": group_names,
        "n_groups": len(group_names),
        "total_sample_size": n_total,
        "group_summaries": group_summaries,
        "levene_test": {
            "statistic": levene_stat,
            "p_value": levene_p,
            "equal_variance": bool(levene_p > 0.05) if levene_p is not None else None,
        },
    }

    if len(group_names) == 2:
        g1, g2 = group_arrays[0], group_arrays[1]
        n1, n2 = len(g1), len(g2)
        try:
            t_welch_res = sp_stats.ttest_ind(g1, g2, equal_var=False)
            t_welch_stat = safe_float(getattr(t_welch_res, "statistic", t_welch_res[0]), None)
            t_welch_p = safe_float(getattr(t_welch_res, "pvalue", t_welch_res[1]), None)
        except Exception:
            t_welch_stat, t_welch_p = None, None

        try:
            t_stud_res = sp_stats.ttest_ind(g1, g2, equal_var=True)
            t_stud_stat = safe_float(getattr(t_stud_res, "statistic", t_stud_res[0]), None)
            t_stud_p = safe_float(getattr(t_stud_res, "pvalue", t_stud_res[1]), None)
        except Exception:
            t_stud_stat, t_stud_p = None, None

        try:
            mw_res = sp_stats.mannwhitneyu(g1, g2, alternative="two-sided")
            mw_stat = safe_float(getattr(mw_res, "statistic", mw_res[0]), None)
            mw_p = safe_float(getattr(mw_res, "pvalue", mw_res[1]), None)
        except Exception:
            mw_stat, mw_p = None, None

        bf_t = compute_bayes_factor_ttest(t_welch_stat, n1, n2)

        results["test_type"] = "two_group_comparison"
        results["welch_t_test"] = {"t_stat": t_welch_stat, "p_value": t_welch_p}
        results["student_t_test"] = {"t_stat": t_stud_stat, "p_value": t_stud_p}
        results["mann_whitney_u"] = {"u_stat": mw_stat, "p_value": mw_p}
        results["bayes_factor"] = bf_t

        sig = (t_welch_p is not None and t_welch_p < 0.05) or (mw_p is not None and mw_p < 0.05)
        results["is_significant"] = sig
        results["interpretation"] = (
            f"{group_names[0]} ve {group_names[1]} grupları arasında {value_col} açısından "
            f"istatistiksel olarak anlamlı bir fark saptanmıştır (Welch t = {t_welch_stat}, p = {t_welch_p}; Mann-Whitney U = {mw_stat}, p = {mw_p})."
            if sig
            else f"{group_names[0]} ve {group_names[1]} grupları arasında {value_col} açısından "
            f"istatistiksel olarak anlamlı bir fark bulunamamıştır (p ≥ 0.05)."
        )

    else:
        try:
            f_res = sp_stats.f_oneway(*group_arrays)
            f_stat = safe_float(getattr(f_res, "statistic", f_res[0]), None)
            f_p = safe_float(getattr(f_res, "pvalue", f_res[1]), None)
        except Exception:
            f_stat, f_p = None, None

        try:
            all_vals = np.concatenate(group_arrays)
            if len(np.unique(all_vals)) > 1:
                kw_res = sp_stats.kruskal(*group_arrays)
                kw_stat = safe_float(getattr(kw_res, "statistic", kw_res[0]), None)
                kw_p = safe_float(getattr(kw_res, "pvalue", kw_res[1]), None)
            else:
                kw_stat, kw_p = None, None
        except Exception:
            kw_stat, kw_p = None, None

        bf_anova = compute_bayes_factor_anova(f_stat, len(group_names), n_total)

        results["test_type"] = "multi_group_comparison"
        results["anova"] = {"f_stat": f_stat, "p_value": f_p}
        results["kruskal_wallis"] = {"h_stat": kw_stat, "p_value": kw_p}
        results["bayes_factor"] = bf_anova

        sig = (f_p is not None and f_p < 0.05) or (kw_p is not None and kw_p < 0.05)
        results["is_significant"] = sig
        results["interpretation"] = (
            f"{len(group_names)} grup arasında {value_col} değişkeni bakımından "
            f"istatistiksel olarak anlamlı bir fark bulunmaktadır (ANOVA F = {f_stat}, p = {f_p}; Kruskal-Wallis H = {kw_stat}, p = {kw_p})."
            if sig
            else f"{len(group_names)} grup arasında {value_col} değişkeni bakımından "
            f"istatistiksel olarak anlamlı bir fark saptanmamıştır (p ≥ 0.05)."
        )

    return results
