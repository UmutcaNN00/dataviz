"""
Services Package - DataViz Platform
Clean modular architecture for file processing, data healing, statistics, AI, and exports.
"""

from services.file_service import (
    clean_dataframe,
    read_csv_safely,
    read_excel_safely,
    read_parquet_safely,
)

from services.data_healer import (
    robust_parse_numeric_string,
    detect_column_anomalies,
    repair_column_data,
    clean_missing_data,
)

from services.stats_service import (
    safe_float,
    apply_filters,
    compute_robust_correlation,
    compute_robust_regression,
    compute_column_statistics,
    compute_advanced_stats,
    generate_kpi_summary,
    compute_pivot_data,
)

from services.ai_service import (
    generate_academic_insight,
    generate_rule_based_insight,
)

from services.export_service import (
    export_dataframe,
    export_pivot_to_excel,
)

__all__ = [
    'clean_dataframe',
    'read_csv_safely',
    'read_excel_safely',
    'read_parquet_safely',
    'robust_parse_numeric_string',
    'detect_column_anomalies',
    'repair_column_data',
    'clean_missing_data',
    'safe_float',
    'apply_filters',
    'compute_robust_correlation',
    'compute_robust_regression',
    'compute_column_statistics',
    'compute_advanced_stats',
    'generate_kpi_summary',
    'compute_pivot_data',
    'generate_academic_insight',
    'generate_rule_based_insight',
    'export_dataframe',
    'export_pivot_to_excel',
]
