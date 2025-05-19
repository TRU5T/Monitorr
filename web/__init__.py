"""
Flask web interface for Monitorr
"""

from flask import Flask
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
import os

def create_app(monitorr_instance=None):
    """Create and configure Flask application"""
    app = Flask(__name__)
    app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-key-change-in-production')
    app.config['MONITORR_INSTANCE'] = monitorr_instance
    
    # Initialize Bootstrap
    Bootstrap(app)
    
    # Set up CSRF protection
    csrf = CSRFProtect()
    csrf.init_app(app)
    
    # Register blueprints
    from web import dashboard, logs, settings, containers
    app.register_blueprint(dashboard.bp, url_prefix='/')
    app.register_blueprint(logs.bp, url_prefix='/logs')
    app.register_blueprint(settings.bp, url_prefix='/settings')
    app.register_blueprint(containers.bp, url_prefix='/containers')
    
    return app 