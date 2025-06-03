from flask import Blueprint, request, jsonify
import jwt
import datetime
import os
import mysql.connector
import hashlib
import logging

auth_bp = Blueprint('auth', __name__)

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            connect_timeout=10,
            autocommit=True
        )
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        raise

def verify_mysql_credentials(username, password):
    """Verify credentials against MySQL user table"""
    try:
        # Try to connect to MySQL with provided credentials
        test_conn = mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=username,
            password=password,
            database=os.getenv('MYSQL_DATABASE'),
            connect_timeout=5
        )
        test_conn.close()
        return True
    except mysql.connector.Error:
        return False

def get_user_permissions(username):
    """Get user permissions from MySQL"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Check if user exists in mysql.user table
        cursor.execute("""
            SELECT User, Host, 
                   CASE 
                       WHEN Super_priv = 'Y' THEN 'admin'
                       WHEN Select_priv = 'Y' AND Insert_priv = 'Y' AND Update_priv = 'Y' AND Delete_priv = 'Y' THEN 'manager'
                       WHEN Select_priv = 'Y' THEN 'viewer'
                       ELSE 'limited'
                   END as role
            FROM mysql.user 
            WHERE User = %s
            LIMIT 1
        """, (username,))
        
        user_info = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if user_info:
            return {
                'username': user_info['User'],
                'host': user_info['Host'],
                'role': user_info['role']
            }
        return None
        
    except Exception as e:
        logging.error(f"Error getting user permissions: {e}")
        return None

@auth_bp.route('/login', methods=['POST'])
def login():
    """Login endpoint using MySQL credentials"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'error': 'Username and password required'}), 400
        
        # Verify credentials against MySQL
        if not verify_mysql_credentials(username, password):
            return jsonify({'error': 'Invalid MySQL credentials'}), 401
        
        # Get user permissions
        user_info = get_user_permissions(username)
        if not user_info:
            return jsonify({'error': 'Unable to determine user permissions'}), 401
        
        # Generate JWT token
        token_payload = {
            'user': username,
            'role': user_info['role'],
            'host': user_info['host'],
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=8)  # 8 hour sessions
        }
        
        token = jwt.encode(
            token_payload,
            os.getenv('JWT_SECRET_KEY', 'change-this-in-production'),
            algorithm='HS256'
        )
        
        # Log successful login
        logging.info(f"Successful login: {username} from {user_info['host']} with role {user_info['role']}")
        
        return jsonify({
            'token': token,
            'user': username,
            'role': user_info['role'],
            'message': 'Login successful'
        })
        
    except mysql.connector.Error as e:
        logging.error(f"MySQL error during login: {e}")
        return jsonify({'error': 'Database connection failed'}), 500
    except Exception as e:
        logging.error(f"Login error: {e}")
        return jsonify({'error': 'Login failed'}), 500

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
        decoded = jwt.decode(
            token, 
            os.getenv('JWT_SECRET_KEY', 'change-this-in-production'), 
            algorithms=['HS256']
        )
        
        return jsonify({
            'valid': True, 
            'user': decoded['user'],
            'role': decoded.get('role', 'limited'),
            'exp': decoded['exp']
        })
        
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logging.error(f"Token verification error: {e}")
        return jsonify({'error': 'Token verification failed'}), 401

@auth_bp.route('/logout', methods=['POST'])
def logout():
    """Logout endpoint"""
    try:
        # Get user from token for logging
        token = request.headers.get('Authorization')
        if token and token.startswith('Bearer '):
            token = token[7:]
            try:
                decoded = jwt.decode(
                    token, 
                    os.getenv('JWT_SECRET_KEY', 'change-this-in-production'), 
                    algorithms=['HS256']
                )
                logging.info(f"User logout: {decoded['user']}")
            except:
                pass
        
        return jsonify({'message': 'Logout successful'})
    except Exception as e:
        logging.error(f"Logout error: {e}")
        return jsonify({'message': 'Logout completed'})

@auth_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get user profile information"""
    try:
        token = request.headers.get('Authorization')
        
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'No valid token provided'}), 401
            
        token = token[7:]
        decoded = jwt.decode(
            token, 
            os.getenv('JWT_SECRET_KEY', 'change-this-in-production'), 
            algorithms=['HS256']
        )
        
        # Get fresh user info from database
        user_info = get_user_permissions(decoded['user'])
        
        if user_info:
            return jsonify({
                'username': user_info['username'],
                'role': user_info['role'],
                'host': user_info['host'],
                'login_time': datetime.datetime.fromtimestamp(decoded['exp'] - 28800).isoformat()  # 8 hours ago
            })
        else:
            return jsonify({'error': 'User not found'}), 404
            
    except jwt.ExpiredSignatureError:
        return jsonify({'error': 'Token expired'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'error': 'Invalid token'}), 401
    except Exception as e:
        logging.error(f"Profile error: {e}")
        return jsonify({'error': 'Failed to get profile'}), 500