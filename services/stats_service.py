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

    X = sub[feature_cols].apply(pd.to_numeric, errors="coerce").dropna()
    y = sub.loc[X.index, target_col].astype(str)

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
        or np.all(x_clean == x_clean[0])
        or np.all(y_clean == y_clean[0])
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
                    r_squared = 1.0 - (ss_res / ss_tot) if ss_tot > 0 else 0.0
                    
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
                    
                    ci_upper = [round(float(v), 4) for v in np.exp(log_y_curve + t_val * se_line_log)]
                    ci_lower = [round(float(v), 4) for v in np.exp(log_y_curve - t_val * se_line_log)]
                
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
    """
    stats = {}
    for col in columns:
        if col in df.columns and pd.api.types.is_numeric_dtype(df[col]):
            s = df[col]
            stats[col] = {
                "count": int(s.count()),
                "missing": int(s.isna().sum()),
                "mean": safe_float(s.mean(), None),
                "median": safe_float(s.median(), None),
                "min": safe_float(s.min(), None),
                "max": safe_float(s.max(), None),
                "std": safe_float(s.std(), None),
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
            elif len(groups) > 2:
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
            advanced["anova_best_group"] = adv_info.get("best_group")
            advanced["anova_low_group"] = adv_info.get("worst_group")
            advanced["bayes_factor"] = adv_info.get("bayes_factor")
            advanced["bayes_bf10"] = adv_info.get("bayes_bf10")
            advanced["bayes_evidence"] = adv_info.get("bayes_evidence")
        elif "t_test" in adv_info:
            advanced["type"] = "categorical_2"
            advanced["t_test"] = adv_info["t_test"]
            advanced["t_test_stat"] = adv_info["t_test"]["t_stat"]
            advanced["p_value"] = adv_info["t_test"]["p_value"]
            advanced["group_means"] = adv_info.get("group_means", {})
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
    pt = pd.pivot_table(
        active_df[proj_cols],
        index=valid_rows if valid_rows else None,
        columns=valid_cols if valid_cols else None,
        values=valid_values,
        aggfunc=chosen_agg,
        fill_value=0,
        margins=True,
        margins_name="Genel Toplam",
        observed=True,
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
                raw_values_all.extend(
                    row_vals[:-1] if has_grand_total_col else row_vals
                )
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
                raw_values_all.extend(
                    row_vals[:-1] if has_grand_total_col else row_vals
                )
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
