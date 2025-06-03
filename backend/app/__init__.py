from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    """Initialize and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS with proper configuration
    CORS(app, resources={
        r"/api/v1/*": {
            "origins": "*",
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Load configuration from Config class
    import sys
    from os.path import dirname, join, abspath
    sys.path.insert(0, abspath(dirname(dirname(__file__))))
    from config import Config
    
    # Configure the app
    app.config.from_object(Config)
    
    # Configure logging
    import logging
    logging.basicConfig(
        level=logging.INFO if not app.debug else logging.DEBUG,
        format='%(asctime)s [%(levelname)s] %(message)s'
    )
    
    # Initialize extensions
    from .utils.encoders import CustomJSONEncoder
    
    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    # Load and register blueprints
    from .routes.auth import auth_bp
    from .routes.jobs import jobs_bp
    from .routes.devices import devices_bp
    from .routes.reports import reports_bp
    from .routes.health import health_bp
    
    # Register blueprints without prefix for health check
    app.register_blueprint(health_bp)
    
    # Register all other blueprints with API prefix
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(jobs_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(devices_bp, url_prefix='/api/v1/devices')
    app.register_blueprint(reports_bp, url_prefix='/api/v1/reports')
    
    return app
