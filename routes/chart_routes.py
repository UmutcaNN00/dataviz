"""
Chart Routes Blueprint - Chart Data Aggregation, Column Value Discovery, and Regression Curves
"""

import logging
import numpy as np
import pandas as pd
from flask import Blueprint, request, jsonify

from core.config import CHART_SAMPLE_SIZE
from core.store import get_df
from services.data_healer import robust_parse_numeric_string
from services.stats_service import (
    safe_float,
    apply_filters,
    compute_robust_correlation,
    compute_robust_regression,
)

logger = logging.getLogger(__name__)

chart_bp = Blueprint("chart", __name__)


@chart_bp.route("/get_chart_data", methods=["POST"])
def get_chart_data():
    """Extracts, filters, and aggregates dataset records for Plotly visualizer using column projection."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Önce dosya yükleyin"}), 400

    data = request.get_json(silent=True) or {}
    x_col = data.get("x_col") or data.get("x")
    y_raw = data.get("y_cols") if "y_cols" in data else data.get("y", [])
    if isinstance(y_raw, str):
        y_cols = [y_raw] if y_raw else []
    elif isinstance(y_raw, list):
        y_cols = [c for c in y_raw if c]
    else:
        y_cols = []

    agg_func = data.get("agg_func", "sum")
    chart_type = data.get("chart_type", "bar")
    filters = data.get("filters", [])

    filtered_df = apply_filters(global_df, filters)
    if filtered_df.empty:
        return jsonify(
            {"error": "Uygulanan filtreler sonucunda görüntülenecek veri kalmadı."}
        ), 400

    available_cols = filtered_df.columns.tolist()
    if x_col and x_col not in available_cols:
        x_col = None
    y_cols = [y for y in y_cols if y in available_cols]

    raw_charts = [
        "histogram",
        "histogram2d",
        "box",
        "violin",
        "scatter",
        "bubble",
        "scatter3d",
        "line3d",
        "scattergeo",
        "scattermatrix",
        "density2d",
        "rug",
        "strip",
        "parcoords",
        "parcats",
        "candlestick",
        "ohlc",
        "dumbbell",
        "ternary",
    ]
    corr_charts = ["heatmap", "surface", "contour", "carpet", "contourcarpet"]

    # Column projection: only copy the columns needed for this chart (saves ~90% RAM on 10M-100M rows)
    if chart_type in corr_charts and len(y_cols) < 2:
        num_cols_all = filtered_df.select_dtypes(include=["number"]).columns.tolist()
        proj_cols = list(
            dict.fromkeys(([x_col] if x_col else []) + y_cols + num_cols_all[:6])
        )
    else:
        proj_cols = list(dict.fromkeys(([x_col] if x_col else []) + y_cols))

    active_df = filtered_df[proj_cols].copy() if proj_cols else filtered_df

    # Convert y_cols to numeric if needed for quantitative charts (using Turkish-aware parser)
    for y in y_cols:
        if y in active_df.columns and not pd.api.types.is_numeric_dtype(active_df[y]):
            try:
                if len(active_df) <= 200000:
                    converted = active_df[y].apply(robust_parse_numeric_string)
                else:
                    converted = pd.to_numeric(
                        active_df[y]
                        .astype(str)
                        .str.replace(".", "", regex=False)
                        .str.replace(",", ".", regex=False),
                        errors="coerce",
                    )
                if converted.notna().sum() > 0:
                    active_df[y] = converted.astype(float)
            except Exception:
                pass
        if y in active_df.columns and pd.api.types.is_numeric_dtype(active_df[y]):
            active_df[y] = active_df[y].replace([np.inf, -np.inf], np.nan)

    response_data = {
        "success": True,
        "chart_type": chart_type,
        "total_active_rows": len(active_df),
    }

    try:
        if chart_type in raw_charts:
            sample_n = min(CHART_SAMPLE_SIZE, len(active_df))
            df_sample = (
                active_df.sample(n=sample_n, random_state=42)
                if len(active_df) > sample_n
                else active_df
            )
            raw_dict = {}
            if x_col:
                if pd.api.types.is_numeric_dtype(df_sample[x_col]):
                    raw_dict["__x__"] = [
                        safe_float(v, None) for v in df_sample[x_col].tolist()
                    ]
                else:
                    raw_dict["__x__"] = (
                        df_sample[x_col]
                        .astype(object)
                        .where(pd.notnull(df_sample[x_col]), "Belirtilmemiş")
                        .astype(str)
                        .tolist()
                    )
            for y in y_cols:
                if pd.api.types.is_numeric_dtype(df_sample[y]):
                    raw_dict[y] = [safe_float(v, None) for v in df_sample[y].tolist()]
                else:
                    raw_dict[y] = (
                        df_sample[y]
                        .astype(object)
                        .where(pd.notnull(df_sample[y]), "Belirtilmemiş")
                        .tolist()
                    )
            if not y_cols and x_col:
                raw_dict[x_col] = raw_dict.get("__x__", [])
            response_data["raw"] = raw_dict

        elif chart_type in corr_charts:
            num_cols = active_df.select_dtypes(include=["number"]).columns.tolist()
            calc_cols = [y for y in y_cols if y in num_cols]
            if len(calc_cols) < 2:
                calc_cols = num_cols[:6] if len(num_cols) >= 2 else calc_cols
            if len(calc_cols) < 2:
                agg_dict = {"__x__": ["Tümü"]}
                for y in y_cols:
                    val = (
                        active_df[y].sum()
                        if pd.api.types.is_numeric_dtype(active_df[y])
                        else active_df[y].count()
                    )
                    agg_dict[y] = [safe_float(val, 0.0)]
                response_data["agg"] = agg_dict
            else:
                corr_matrix = active_df[calc_cols].corr(min_periods=2)
                response_data["corr"] = {
                    "labels": calc_cols,
                    "matrix": corr_matrix.fillna(0).values.tolist(),
                }

        else:
            if not x_col:
                agg_dict = {"__x__": ["Tümü"]}
                for y in y_cols:
                    is_num_y = pd.api.types.is_numeric_dtype(active_df[y])
                    if not is_num_y or agg_func == "count":
                        val = active_df[y].count()
                    elif agg_func == "sum":
                        val = active_df[y].sum()
                    elif agg_func == "mean":
                        val = active_df[y].mean()
                    elif agg_func == "median":
                        val = active_df[y].median()
                    elif agg_func == "min":
                        val = active_df[y].min()
                    elif agg_func == "max":
                        val = active_df[y].max()
                    else:
                        val = active_df[y].count()
                    agg_dict[y] = [safe_float(val, 0.0)]
                response_data["agg"] = agg_dict
            else:
                if not y_cols:
                    # Auto count frequencies if only X column is given
                    counts = active_df[x_col].dropna().value_counts().head(100)
                    response_data["agg"] = {
                        "__x__": [str(x) for x in counts.index.tolist()],
                        "Adet": [int(v) for v in counts.values.tolist()],
                    }
                else:
                    grouped = active_df.groupby(x_col, observed=False)
                    if agg_func == "sum":
                        grouped_df = grouped.sum(numeric_only=True)
                    elif agg_func == "mean":
                        grouped_df = grouped.mean(numeric_only=True)
                    elif agg_func == "median":
                        grouped_df = grouped.median(numeric_only=True)
                    elif agg_func == "min":
                        grouped_df = grouped.min(numeric_only=True)
                    elif agg_func == "max":
                        grouped_df = grouped.max(numeric_only=True)
                    else:
                        grouped_df = grouped.count()

                    if len(grouped_df) > 100:
                        if (
                            agg_func in ["sum", "mean"]
                            and y_cols
                            and y_cols[0] in grouped_df.columns
                        ):
                            grouped_df = grouped_df.sort_values(
                                by=y_cols[0], ascending=False
                            ).head(100)
                        else:
                            grouped_df = grouped_df.head(100)

                    agg_dict = {"__x__": [str(x) for x in grouped_df.index.tolist()]}
                    for y in y_cols:
                        if y in grouped_df.columns:
                            agg_dict[y] = [
                                safe_float(v, 0.0) for v in grouped_df[y].tolist()
                            ]
                        else:
                            try:
                                cnt_s = (
                                    active_df.groupby(x_col, observed=False)[y]
                                    .count()
                                    .reindex(grouped_df.index)
                                    .fillna(0)
                                )
                                agg_dict[y] = [int(v) for v in cnt_s.tolist()]
                            except Exception:
                                agg_dict[y] = [0] * len(grouped_df)
                    response_data["agg"] = agg_dict

        return jsonify(response_data)
    except Exception as e:
        logger.exception(f"get_chart_data hatası: {e}")
        return jsonify({"error": str(e)}), 500


@chart_bp.route("/get_column_unique_values", methods=["GET", "POST"])
@chart_bp.route("/get_column_details", methods=["GET", "POST"])
def get_column_unique_values():
    """Retrieves unique categories or numerical ranges for dynamic slicers and filters."""
    global_df = get_df(1)
    if global_df is None:
        return jsonify({"error": "Veri yok"}), 400

    col = request.args.get("column")
    if not col:
        data = request.get_json(silent=True) or {}
        col = data.get("column")
    if not col or col not in global_df.columns:
        return jsonify({"error": "Sütun bulunamadı"}), 400

    series = global_df[col]
    is_num = pd.api.types.is_numeric_dtype(series)

    if is_num:
        clean_s = series.replace([np.inf, -np.inf], np.nan).dropna()
        min_v = safe_float(clean_s.min(), 0.0) if not clean_s.empty else 0.0
        max_v = safe_float(clean_s.max(), 100.0) if not clean_s.empty else 100.0
        unique_sample = [safe_float(v, 0.0) for v in clean_s.unique()[:50]]
        return jsonify(
            {
                "column": col,
                "type": "num",
                "min": min_v,
                "max": max_v,
                "count": int(clean_s.count()),
                "unique_values": unique_sample,
            }
        )
    else:
        non_null = series.dropna()
        val_counts = non_null.astype(str).value_counts().head(100)
        categories = [{"value": str(k), "count": int(v)} for k, v in val_counts.items()]
        unique_vals = [c["value"] for c in categories]
        return jsonify(
            {
                "column": col,
                "type": "cat",
                "categories": categories,
                "values": unique_vals,
                "unique_values": unique_vals,
                "total_unique": int(non_null.nunique()),
            }
        )


@chart_bp.route("/get_regression_curve", methods=["POST"])
def get_regression_curve():
    """Calculates regression curve coefficients and correlation metrics for chart overlays."""
    global_df = get_df(1)
    if global_df is None or global_df.empty:
        return jsonify({"error": "Aktif veri seti bulunamadı."}), 400

    data = request.get_json(silent=True) or {}
    x_col = data.get("x_col") or data.get("x")
    y_raw = data.get("y_col") or data.get("y") or data.get("y_cols")
    if isinstance(y_raw, list):
        y_col = y_raw[0] if y_raw else None
    else:
        y_col = y_raw

    model_type = data.get("model_type", "linear")
    corr_method = data.get("corr_method", "pearson")
    filters = data.get("filters", [])

    if not x_col or not y_col:
        return jsonify({"error": "X ve Y sütunları seçilmelidir."}), 400

    active_df = apply_filters(global_df, filters)
    if x_col not in active_df.columns or y_col not in active_df.columns:
        return jsonify({"error": "Seçilen sütunlar veri setinde bulunamadı."}), 400

    x_series = pd.to_numeric(active_df[x_col], errors="coerce")
    y_series = pd.to_numeric(active_df[y_col], errors="coerce")

    valid_mask = (
        x_series.notna()
        & y_series.notna()
        & np.isfinite(x_series)
        & np.isfinite(y_series)
    )
    x_vals = x_series[valid_mask].values
    y_vals = y_series[valid_mask].values

    if len(x_vals) < 3:
        return jsonify(
            {
                "error": "Regresyon ve korelasyon için en az 3 geçerli sayısal değer gereklidir."
            }
        ), 400

    try:
        reg_result = compute_robust_regression(x_vals, y_vals, model_type=model_type)
        corr_result = compute_robust_correlation(x_vals, y_vals, method=corr_method)
        corr_result["r"] = corr_result.get("coef")

        return jsonify(
            {
                "success": True,
                "x_col": x_col,
                "y_col": y_col,
                "model_type": model_type,
                "corr_method": corr_method,
                "regression": reg_result,
                "correlation": corr_result,
            }
        )
    except Exception as e:
        logger.exception(f"get_regression_curve hatası: {e}")
        return jsonify({"error": f"Regresyon eğrisi hesaplanamadı: {str(e)}"}), 500
