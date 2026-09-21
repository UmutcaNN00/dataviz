"""
Core Module - DataViz Platform
Configuration, session management, and in-memory store.
"""

from core.config import Config, UPLOAD_FOLDER, MAX_CONTENT_LENGTH, ALLOWED_EXTENSIONS
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
    'DATA_STORE',
    'get_user_id',
    'get_df',
    'set_df',
    'get_excel_data',
    'set_excel_data',
    'clear_user_data',
]
