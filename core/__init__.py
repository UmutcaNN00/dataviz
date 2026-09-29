"""
Core Module - DataViz Platform
Configuration, session management, and in-memory store.
"""

from core.config import (
    ALLOWED_EXTENSIONS,
    ANOMALY_SAMPLE_SIZE,
    ANOMALY_SAMPLE_THRESHOLD,
    CHART_SAMPLE_SIZE,
    DEBUG,
    MAX_ACTIVE_SESSIONS,
    MAX_CONTENT_LENGTH,
    PORT,
    SECRET_KEY,
    UPLOAD_FOLDER,
    Config,
)
from core.store import (
    DATA_STORE,
    get_baseline_trust,
    get_df,
    get_excel_data,
    get_is_cleaned,
    get_user_id,
    set_baseline_trust,
    set_df,
    set_excel_data,
    set_is_cleaned,
)

__all__ = [
    "ALLOWED_EXTENSIONS",
    "ANOMALY_SAMPLE_SIZE",
    "ANOMALY_SAMPLE_THRESHOLD",
    "CHART_SAMPLE_SIZE",
    "DATA_STORE",
    "DEBUG",
    "MAX_ACTIVE_SESSIONS",
    "MAX_CONTENT_LENGTH",
    "PORT",
    "SECRET_KEY",
    "UPLOAD_FOLDER",
    "Config",
    "get_baseline_trust",
    "get_df",
    "get_excel_data",
    "get_is_cleaned",
    "get_user_id",
    "set_baseline_trust",
    "set_df",
    "set_excel_data",
    "set_is_cleaned",
]
