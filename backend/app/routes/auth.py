from flask import Blueprint, request, jsonify
import jwt
import datetime
from functools import wraps
import os

auth_bp = Blueprint('auth', __name__)

# Test user credentials (replace with database lookup in production)
TEST_USER = {
    'username': 'test',
    'password': 'test'
}

def create_token(user_data):
    """Create a JWT token for the authenticated user"""
    payload = {
        'user': user_data['username'],
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    return jwt.encode(payload, os.getenv('SECRET_KEY', 'dev-secret-key'), algorithm='HS256')

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
            jwt.decode(token, os.getenv('SECRET_KEY', 'dev-secret-key'), algorithms=['HS256'])
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token'}), 401

        return f(*args, **kwargs)
    return decorated

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint that returns a JWT token"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Missing username or password'}), 400

    # Simple test authentication (replace with database lookup in production)
    if username == TEST_USER['username'] and password == TEST_USER['password']:
        token = create_token(TEST_USER)
        return jsonify({'token': token, 'message': 'Login successful'}), 200

    return jsonify({'message': 'Invalid credentials'}), 401

@auth_bp.route('/verify', methods=['GET'])
@token_required
def verify_token():
    """Endpoint to verify if the JWT token is valid"""
    return jsonify({'message': 'Token is valid'}), 200
