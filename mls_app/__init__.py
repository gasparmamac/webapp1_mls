import os
from flask import Flask
from flask_bootstrap import Bootstrap5
from flask_wtf.csrf import CSRFProtect

from .auth import login_manager
from .db import db

from .auth import auth_bp
from .landing_pages import landing_bp
from .admin_tool import admin_tool_bp
from .encoder_tool import encoder_tool_bp
from .invoice import invoicing_bp
from .kpi import kpi_bp

bootstrap = Bootstrap5()
csrf = CSRFProtect()


def initialize_extensions(app):
    bootstrap.init_app(app)
    csrf.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)


def register_blueprints(app):
    app.register_blueprint(auth_bp)
    app.register_blueprint(landing_bp)
    app.add_url_rule('/', endpoint='index')
    app.register_blueprint(admin_tool_bp)
    app.register_blueprint(encoder_tool_bp)
    app.register_blueprint(invoicing_bp)
    app.register_blueprint(kpi_bp)


def create_app():
    # create and config the app
    app = Flask(__name__, instance_relative_config=False)
    app.config.from_object('config.ProductionConfig')

    """initialize extensions and register blueprints"""
    initialize_extensions(app)
    register_blueprints(app)
    with app.app_context():
        db.create_all()

    return app
