from flask import Blueprint, request, jsonify
import jwt
import datetime
import os

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint"""
    data = request.get_json()
    
    # Simple authentication - replace with your actual auth logic
    if data and data.get('username') and data.get('password'):
        # Generate JWT token
        token = jwt.encode({
            'user': data['username'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, os.getenv('JWT_SECRET_KEY', 'default-secret'), algorithm='HS256')
        
        return jsonify({
            'token': token,
            'user': data['username']
        })
    
    return jsonify({'error': 'Invalid credentials'}), 401

@auth_bp.route('/verify', methods=['POST'])
def verify_token():
    """Verify JWT token"""
    token = request.headers.get('Authorization')
    if token:
        try:
            token = token.replace('Bearer ', '')
            decoded = jwt.decode(token, os.getenv('JWT_SECRET_KEY', 'default-secret'), algorithms=['HS256'])
            return jsonify({'valid': True, 'user': decoded['user']})
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'error': 'Invalid token'}), 401
    
    return jsonify({'error': 'No token provided'}), 401