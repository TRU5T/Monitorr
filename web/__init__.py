"""
Flask web interface for Monitorr
"""

from flask import Flask, render_template_string
from flask_bootstrap import Bootstrap
from flask_wtf.csrf import CSRFProtect
import os
import traceback

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

    @app.errorhandler(500)
    def handle_500(e):
        """Show exception details when SHOW_ERRORS=1 so we can fix the cause."""
        if os.environ.get('SHOW_ERRORS', '').lower() in ('1', 'true', 'yes'):
            lines = traceback.format_exception(type(e), e, e.__traceback__) if e else [traceback.format_exc()]
            exc = ''.join(lines)
            return render_template_string(
                '<h1>Server Error</h1><pre style="white-space:pre-wrap;">{{ exc }}</pre>',
                exc=exc
            ), 500
        return render_template_string('<h1>Internal Server Error</h1><p>Set SHOW_ERRORS=1 and retry to see details.</p>'), 500

    return app 