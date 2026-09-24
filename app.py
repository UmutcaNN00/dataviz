"""
DataViz - Core Application Server
Lightweight application factory registering modular Flask Blueprints.
"""

import logging
from flask import Flask
from core.config import Config, PORT, DEBUG
from routes import register_blueprints

# Configure root logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)


def create_app(config_class=Config):
    """
    Application factory initializing Flask configuration, CORS, and Blueprints.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    app.secret_key = config_class.SECRET_KEY
    app.config['UPLOAD_FOLDER'] = config_class.UPLOAD_FOLDER
    app.config['MAX_CONTENT_LENGTH'] = config_class.MAX_CONTENT_LENGTH

    # Custom JSON provider for NumPy / SciPy types
    try:
        import numpy as np
        from flask.json.provider import DefaultJSONProvider

        class NumpyJSONProvider(DefaultJSONProvider):
            def default(self, obj):
                if isinstance(obj, (np.integer, int)):
                    return int(obj)
                elif isinstance(obj, (np.floating, float)):
                    return float(obj)
                elif isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, np.bool_):
                    return bool(obj)
                return super().default(obj)

        app.json_provider_class = NumpyJSONProvider
        app.json = NumpyJSONProvider(app)
    except Exception as e_json:
        logger.warning(f"Could not configure NumpyJSONProvider: {e_json}")

    # CORS support: enable flask_cors if available or use standard response headers
    try:
        from flask_cors import CORS
        CORS(app)
    except ImportError:
        @app.after_request
        def add_cors_headers(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
            response.headers['Access-Control-Allow-Methods'] = 'GET,PUT,POST,DELETE,OPTIONS'
            return response

    # Register modular Blueprints
    register_blueprints(app)
    logger.info("DataViz Blueprints successfully registered.")

    return app


# Create application instance for WSGI / Gunicorn / direct execution
app = create_app()

if __name__ == '__main__':
    logger.info(f"Starting DataViz server on port {PORT} (debug={DEBUG})...")
    app.run(host='0.0.0.0', port=PORT, debug=DEBUG)
