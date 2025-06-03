from flask import Blueprint, request, jsonify, current_app
import jwt
import datetime
from functools import wraps
import os
import pymysql

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    try:
        connection = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            user=current_app.config['MYSQL_USER'],
            password=current_app.config['MYSQL_PASSWORD'],
            database=current_app.config['MYSQL_DATABASE'],
            cursorclass=pymysql.cursors.DictCursor,
            ssl_disabled=True,
            charset='utf8mb4',
            connect_timeout=5
        )
        return connection
    except Exception as e:
        current_app.logger.error(f"Database connection error: {str(e)}")
        return None

def create_token(user_data):
    """Create a JWT token for the authenticated user"""
    payload = {
        'user': user_data['username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, os.getenv('JWT_SECRET_KEY', 'dev-secret-key'), algorithm='HS256')

def token_required(f):
    """Decorator to protect routes with JWT authentication"""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')

        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'dev-secret-key'), algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint that returns a JWT token"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Missing username or password'}), 400
        
        # Try to connect with the provided credentials
        connection = pymysql.connect(
            host=current_app.config['MYSQL_HOST'],
            user=username,
            password=password,
            database=current_app.config['MYSQL_DATABASE'],
            cursorclass=pymysql.cursors.DictCursor,
            ssl_disabled=True,
            charset='utf8mb4',
            connect_timeout=5
        )
        
        # Test the connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT 1')
            
        # If we get here, the credentials were valid
        connection.close()
        
        # Create JWT token
        token = create_token({'username': username})
        current_app.logger.info(f"Login successful for user: {username}")
        return jsonify({'token': token, 'message': 'Login successful'}), 200
        
    except pymysql.Error as e:
        current_app.logger.error(f"Database error during login: {str(e)}")
        return jsonify({'message': 'Invalid credentials'}), 401
    except Exception as e:
        current_app.logger.error(f"Unexpected error during login: {str(e)}")
        return jsonify({'message': 'Login failed'}), 500

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """Endpoint to verify if the JWT token is valid"""
    return jsonify({'message': 'Token is valid'}), 200
