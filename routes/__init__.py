"""
Routes Package - Flask Blueprint Registration
Exports blueprints and register_blueprints helper.
"""

from routes.chart_routes import chart_bp
from routes.data_routes import data_bp
from routes.export_routes import export_bp
from routes.main_routes import main_bp
from routes.stats_routes import stats_bp
from routes.upload_routes import upload_bp


def register_blueprints(app):
    """
    Registers all application blueprints with the Flask app.
    Maintains clean modular separation across platform capabilities.
    """
    app.register_blueprint(main_bp)
    app.register_blueprint(upload_bp)
    app.register_blueprint(data_bp)
    app.register_blueprint(chart_bp)
    app.register_blueprint(stats_bp)
    app.register_blueprint(export_bp)


__all__ = [
    "chart_bp",
    "data_bp",
    "export_bp",
    "main_bp",
    "register_blueprints",
    "stats_bp",
    "upload_bp",
]
