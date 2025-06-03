from flask import Blueprint, request, jsonify
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__)

# Simple user database - replace with your actual user management
USERS = {
    'admin': 'password123',
    'user': 'user123',
    'scanner': 'scanner123'
}

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Validate credentials
        if username in USERS and USERS[username] == password:
            # Generate JWT token
            token = jwt.encode({
                'user': username,
                'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
            }, os.getenv('JWT_SECRET_KEY', 'default-secret'), algorithm='HS256')
            
            return jsonify({
                'token': token,
                'user': username,
                'message': 'Login successful'
            })
        else:
            return jsonify({'error': 'Invalid credentials'}), 401
            
    except Exception as e:
        return jsonify({'error': f'Login failed: {str(e)}'}), 500

@auth_bp.route('/verify', methods=['GET', 'POST'])
def verify_token():
    """Verify JWT token"""
    try:
        token = request.headers.get('Authorization')
        
        if not token:
            return jsonify({'error': 'No token provided'}), 401
            
        # Remove Bearer prefix if present
        if token.startswith('Bearer '):
            token = token[7:]
            
        # Decode and verify token
        decoded = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'default-secret'), algorithms=['HS256'])
        
        return jsonify({
            'valid': True, 
            'user': decoded['user'],
            'exp': decoded['exp']
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        return jsonify({'error': f'Token verification failed: {str(e)}'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    return jsonify({'message': 'Logout successful'})