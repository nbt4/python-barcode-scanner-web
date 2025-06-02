import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Database settings (using external MySQL database)
    MYSQL_HOST = 'tsunami-events.de'
    MYSQL_DATABASE = 'TS-Lager'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', '')  # Get password from environment variable
    MYSQL_POOL_SIZE = int(os.getenv('MYSQL_POOL_SIZE', '5'))

    # JWT Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'your-secret-key-here')
    JWT_EXPIRATION = int(os.getenv('JWT_EXPIRATION', '3600'))  # 1 hour

    # CORS Settings
    CORS_ORIGINS = os.getenv('CORS_ORIGINS', '*')

    # File Upload Settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    UPLOAD_FOLDER = 'uploads'

    # API Settings
    API_TITLE = 'Barcode Scanner API'
    API_VERSION = 'v1'
    API_PREFIX = '/api/v1'
