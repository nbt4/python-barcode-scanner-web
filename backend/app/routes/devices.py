from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime
import logging

devices_bp = Blueprint('devices', __name__)

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

def require_auth(f):
    """Decorator to require authentication"""
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token or not token.startswith('Bearer '):
            return jsonify({'error': 'Authentication required'}), 401
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

@devices_bp.route('/', methods=['GET'])
@require_auth
def get_devices():
    """Get all devices"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get query parameters
        device_type = request.args.get('type')
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = "SELECT * FROM devices"
        params = []
        conditions = []
        
        if device_type:
            conditions.append("type = %s")
            params.append(device_type)
            
        if status:
            conditions.append("status = %s")
            params.append(status)
        
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " ORDER BY name"
        
        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        devices = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for device in devices:
            for key, value in device.items():
                if isinstance(value, datetime):
                    device[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(devices)
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_devices: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_devices: {e}")
        return jsonify({'error': 'Failed to fetch devices'}), 500

@devices_bp.route('/<int:device_id>', methods=['GET'])
@require_auth
def get_device(device_id):
    """Get specific device"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
        device = cursor.fetchone()
        
        if device:
            # Convert datetime objects to ISO format
            for key, value in device.items():
                if isinstance(value, datetime):
                    device[key] = value.isoformat()
            
            cursor.close()
            conn.close()
            return jsonify(device)
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Device not found'}), 404
            
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_device: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_device: {e}")
        return jsonify({'error': 'Failed to fetch device'}), 500

@devices_bp.route('/', methods=['POST'])
@require_auth
def create_device():
    """Create new device"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['name', 'barcode']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if barcode already exists
        cursor.execute("SELECT id FROM devices WHERE barcode = %s", (data['barcode'],))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Barcode already exists'}), 400
        
        query = """
        INSERT INTO devices (name, type, barcode, status, location, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s)
        """
        
        values = (
            data.get('name'),
            data.get('type', 'equipment'),
            data.get('barcode'),
            data.get('status', 'available'),
            data.get('location', ''),
            datetime.now()
        )
        
        cursor.execute(query, values)
        device_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        logging.info(f"Device created: {data['name']} (ID: {device_id})")
        
        return jsonify({
            'id': device_id,
            'message': 'Device created successfully'
        }), 201
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in create_device: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in create_device: {e}")
        return jsonify({'error': 'Failed to create device'}), 500

@devices_bp.route('/scan', methods=['POST'])
@require_auth
def scan_barcode():
    """Handle barcode scanning"""
    try:
        data = request.get_json()
        barcode = data.get('barcode')
        job_id = data.get('job_id')
        location = data.get('location', '')
        notes = data.get('notes', '')
        
        if not barcode:
            return jsonify({'error': 'No barcode provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Find device by barcode
        cursor.execute("SELECT * FROM devices WHERE barcode = %s", (barcode,))
        device = cursor.fetchone()
        
        if device:
            # Update device last scan time
            cursor.execute(
                "UPDATE devices SET last_scan = %s WHERE id = %s",
                (datetime.now(), device['id'])
            )
            
            # Record the scan
            scan_query = """
            INSERT INTO scans (device_id, job_id, barcode, scan_timestamp, location, notes)
            VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(scan_query, (
                device['id'],
                job_id,
                barcode,
                datetime.now(),
                location,
                notes
            ))
            
            cursor.close()
            conn.close()
            
            # Convert datetime objects to ISO format
            for key, value in device.items():
                if isinstance(value, datetime):
                    device[key] = value.isoformat()
            
            logging.info(f"Device scanned: {device['name']} ({barcode})")
            
            return jsonify({
                'success': True,
                'device': device,
                'message': f'Device {device["name"]} scanned successfully'
            })
        else:
            # Record unknown barcode scan
            scan_query = """
            INSERT INTO scans (barcode, scan_timestamp, location, notes)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(scan_query, (
                barcode,
                datetime.now(),
                location,
                f"Unknown device - {notes}"
            ))
            
            cursor.close()
            conn.close()
            
            logging.warning(f"Unknown barcode scanned: {barcode}")
            
            return jsonify({
                'success': False,
                'barcode': barcode,
                'timestamp': datetime.now().isoformat(),
                'message': 'Barcode scanned but device not found in database'
            }), 404
            
    except mysql.connector.Error as e:
        logging.error(f"Database error in scan_barcode: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in scan_barcode: {e}")
        return jsonify({'error': 'Scan failed'}), 500

@devices_bp.route('/search', methods=['GET'])
@require_auth
def search_devices():
    """Search devices by barcode, name, or type"""
    try:
        query = request.args.get('q', '').strip()
        
        if not query:
            return jsonify([])
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        search_query = """
        SELECT * FROM devices 
        WHERE name LIKE %s 
           OR barcode LIKE %s 
           OR type LIKE %s 
           OR location LIKE %s
        ORDER BY name
        LIMIT 20
        """
        
        search_term = f"%{query}%"
        cursor.execute(search_query, (search_term, search_term, search_term, search_term))
        results = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for device in results:
            for key, value in device.items():
                if isinstance(value, datetime):
                    device[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(results)
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in search_devices: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in search_devices: {e}")
        return jsonify({'error': 'Search failed'}), 500

@devices_bp.route('/stats', methods=['GET'])
@require_auth
def get_device_stats():
    """Get device statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get status counts
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM devices 
            GROUP BY status
        """)
        status_stats = cursor.fetchall()
        
        # Get type counts
        cursor.execute("""
            SELECT type, COUNT(*) as count 
            FROM devices 
            GROUP BY type
        """)
        type_stats = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM devices")
        total_count = cursor.fetchone()['total']
        
        # Get recent scans
        cursor.execute("""
            SELECT d.name, d.barcode, s.scan_timestamp
            FROM scans s
            JOIN devices d ON s.device_id = d.id
            ORDER BY s.scan_timestamp DESC
            LIMIT 10
        """)
        recent_scans = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for scan in recent_scans:
            for key, value in scan.items():
                if isinstance(value, datetime):
                    scan[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_devices': total_count,
            'status_breakdown': status_stats,
            'type_breakdown': type_stats,
            'recent_scans': recent_scans,
            'generated_at': datetime.now().isoformat()
        })
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_device_stats: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_device_stats: {e}")
        return jsonify({'error': 'Failed to fetch device statistics'}), 500