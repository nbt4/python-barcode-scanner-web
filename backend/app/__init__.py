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
    from .utils.encoders import CustomJSONEncoder
    
    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    app.config.from_object(Config)
    
    # Register blueprints with URL prefix
    from .routes import auth, jobs, devices, health, reports
    app.register_blueprint(auth.auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(jobs.jobs_bp, url_prefix='/api/v1/jobs')
    app.register_blueprint(devices.devices_bp, url_prefix='/api/v1/devices')
    app.register_blueprint(health.health_bp, url_prefix='/api/v1/health')
    app.register_blueprint(reports.reports_bp, url_prefix='/api/v1/reports')
    
    return app
