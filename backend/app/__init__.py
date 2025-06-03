from flask import Flask
from flask_cors import CORS
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def create_app():
    """Initialize and configure the Flask application"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Load configuration from Config class
    import sys
    from os.path import dirname, join, abspath
    sys.path.insert(0, abspath(dirname(dirname(__file__))))
    from config import Config
    from .utils.encoders import CustomJSONEncoder
    
    # Set custom JSON encoder
    app.json_encoder = CustomJSONEncoder
    
    # Debug: Print environment variables
    print(f"Debug - ENV vars: MYSQL_USER={os.getenv('MYSQL_USER')}")
    
    app.config.from_object(Config)
    
    # Debug: Print loaded config
    print(f"Debug - Config: MYSQL_USER={app.config.get('MYSQL_USER')}")
    
    # Register blueprints
    from .routes.health import health_bp
    from .routes.auth import auth_bp
    from .routes.jobs import jobs_bp
    
    app.register_blueprint(health_bp)
    app.register_blueprint(auth_bp, url_prefix='/api/v1/auth')
    app.register_blueprint(jobs_bp, url_prefix='/api/v1/jobs')
    
    return app
