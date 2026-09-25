"""
Services Package - DataViz Platform
Clean modular architecture for file processing, data healing, statistics, AI, and exports.
"""

from services.ai_service import (
    generate_academic_insight,
    generate_rule_based_insight,
)
from services.data_healer import (
    clean_missing_data,
    detect_column_anomalies,
    repair_column_data,
    robust_parse_numeric_string,
)
from services.export_service import (
    export_dataframe,
    export_pivot_to_excel,
)
from services.file_service import (
    clean_dataframe,
    read_csv_safely,
    read_excel_safely,
    read_parquet_safely,
)
from services.stats_service import (
    apply_filters,
    compute_advanced_stats,
    compute_column_statistics,
    compute_correlation_matrix,
    compute_pivot_data,
    compute_robust_correlation,
    compute_robust_regression,
    generate_kpi_summary,
    safe_float,
)

__all__ = [
    "apply_filters",
    "clean_dataframe",
    "clean_missing_data",
    "compute_advanced_stats",
    "compute_column_statistics",
    "compute_correlation_matrix",
    "compute_pivot_data",
    "compute_robust_correlation",
    "compute_robust_regression",
    "detect_column_anomalies",
    "export_dataframe",
    "export_pivot_to_excel",
    "generate_academic_insight",
    "generate_kpi_summary",
    "generate_rule_based_insight",
    "read_csv_safely",
    "read_excel_safely",
    "read_parquet_safely",
    "repair_column_data",
    "robust_parse_numeric_string",
    "safe_float",
]
