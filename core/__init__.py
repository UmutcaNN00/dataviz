"""
Core Module - DataViz Platform
Configuration, session management, and in-memory store.
"""

from core.config import (
    Config,
    UPLOAD_FOLDER,
    MAX_CONTENT_LENGTH,
    ALLOWED_EXTENSIONS,
    SECRET_KEY,
    PORT,
    DEBUG,
    ANOMALY_SAMPLE_THRESHOLD,
    ANOMALY_SAMPLE_SIZE,
    CHART_SAMPLE_SIZE,
    MAX_ACTIVE_SESSIONS,
)
from core.store import (
    DATA_STORE,
    get_user_id,
    get_df,
    set_df,
    get_excel_data,
    set_excel_data,
    clear_user_data,
)

__all__ = [
    'Config',
    'UPLOAD_FOLDER',
    'MAX_CONTENT_LENGTH',
    'ALLOWED_EXTENSIONS',
    'SECRET_KEY',
    'PORT',
    'DEBUG',
    'ANOMALY_SAMPLE_THRESHOLD',
    'ANOMALY_SAMPLE_SIZE',
    'CHART_SAMPLE_SIZE',
    'MAX_ACTIVE_SESSIONS',
    'DATA_STORE',
    'get_user_id',
    'get_df',
    'set_df',
    'get_excel_data',
    'set_excel_data',
    'clear_user_data',
]
