"""
DataViz - Core Application Server
Lightweight application factory registering modular Flask Blueprints.
"""

from datetime import date, datetime
import importlib
import json
import logging
import math

from flask import Flask
from flask.json.provider import DefaultJSONProvider
import numpy as np
import pandas as pd

from core.config import DEBUG, PORT, Config
from routes import register_blueprints

# Configure root logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def _sanitize_json_value(val):
    if val is None or val is pd.NA or val is pd.NaT:
        return None
    if isinstance(val, (float, np.floating)):
        fval = float(val)
        return None if (math.isnan(fval) or math.isinf(fval)) else fval
    if isinstance(val, (int, np.integer)) and not isinstance(val, bool):
        return int(val)
    if isinstance(val, (bool, np.bool_)):
        return bool(val)
    if isinstance(val, dict):
        return {str(k): _sanitize_json_value(v) for k, v in val.items()}
    if isinstance(val, (list, tuple, set)):
        return [_sanitize_json_value(v) for v in val]
    if isinstance(val, np.ndarray):
        return [_sanitize_json_value(v) for v in val.tolist()]
    if isinstance(val, (pd.Timestamp, datetime, date, np.datetime64)):
        return str(val)
    return val


class NumpyJSONProvider(DefaultJSONProvider):
    def default(self, obj):
        if obj is pd.NA or obj is pd.NaT:
            return None
        if isinstance(obj, (np.integer, int)) and not isinstance(obj, bool):
            return int(obj)
        if isinstance(obj, (np.floating, float)):
            fval = float(obj)
            return None if (math.isnan(fval) or math.isinf(fval)) else fval
        if isinstance(obj, np.ndarray):
            return [_sanitize_json_value(v) for v in obj.tolist()]
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, (pd.Timestamp, datetime, date, np.datetime64)):
            return str(obj)
        return super().default(obj)

    def dumps(self, obj, **kwargs):
        kwargs.setdefault("default", self.default)
        kwargs.setdefault("ensure_ascii", self.ensure_ascii)
        kwargs.setdefault("sort_keys", self.sort_keys)
        return json.dumps(_sanitize_json_value(obj), **kwargs)


def create_app(config_class=Config):
    """
    Application factory initializing Flask configuration, CORS, and Blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = config_class.SECRET_KEY
    app.config["UPLOAD_FOLDER"] = config_class.UPLOAD_FOLDER
    app.config["MAX_CONTENT_LENGTH"] = config_class.MAX_CONTENT_LENGTH

    # Custom JSON provider for NumPy / Pandas / SciPy types (prevents NaN/Inf JSON parse errors)
    app.json_provider_class = NumpyJSONProvider
    app.json = NumpyJSONProvider(app)

    # CORS support: enable flask_cors if available or use standard response headers
    try:
        flask_cors = importlib.import_module("flask_cors")
        flask_cors.CORS(app, supports_credentials=True)
    except ImportError:

        @app.after_request
        def add_cors_headers(response):
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = (
                "Content-Type,Authorization"
            )
            response.headers["Access-Control-Allow-Methods"] = (
                "GET,PUT,POST,DELETE,OPTIONS"
            )
            return response

    # Register modular Blueprints
    register_blueprints(app)
    logger.info("DataViz Blueprints successfully registered.")

    return app


# Create application instance for WSGI / Gunicorn / direct execution
app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting DataViz server on port {PORT} (debug={DEBUG})...")
    app.run(host="0.0.0.0", port=PORT, debug=DEBUG)
