"""
Configuration Constants for DataViz Platform
"""

import os

# Base directory
BASE_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))

# File uploads and memory limits (5 GB for 100M+ row Big Data / Polars engine)
UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER", os.path.join(BASE_DIR, "uploads"))
MAX_CONTENT_LENGTH = int(
    os.environ.get("MAX_CONTENT_LENGTH", str(5 * 1024 * 1024 * 1024))
)  # 5 GB
ALLOWED_EXTENSIONS = {"csv", "xlsx", "xls", "parquet"}

# Security and session
SECRET_KEY = os.environ.get("SECRET_KEY", "dataviz_secret_super_key")

# Server settings
PORT = int(os.environ.get("PORT", "5000"))
DEBUG = os.environ.get("FLASK_DEBUG", "False").lower() in ["true", "1"]

# Sampling parameters for performance
ANOMALY_SAMPLE_THRESHOLD = 15000
ANOMALY_SAMPLE_SIZE = 10000
CHART_SAMPLE_SIZE = 5000
MAX_ACTIVE_SESSIONS = 5

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


class Config:
    """Flask configuration container."""

    SECRET_KEY = SECRET_KEY
    UPLOAD_FOLDER = UPLOAD_FOLDER
    MAX_CONTENT_LENGTH = MAX_CONTENT_LENGTH
    ALLOWED_EXTENSIONS = ALLOWED_EXTENSIONS
    TEMPLATES_AUTO_RELOAD = True
    SEND_FILE_MAX_AGE_DEFAULT = 0
