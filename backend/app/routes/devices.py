from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime
import logging

devices_bp = Blueprint('devices', __name__)

# Mock data for development/testing
MOCK_DEVICES = [
    {
        'id': 1,
        'name': 'Audio Mixer XM-2000',
        'type': 'audio',
        'barcode': 'AUD001234567',
        'status': 'available',
        'location': 'Warehouse A',
        'last_scan': datetime.now().isoformat()
    },
    {
        'id': 2,
        'name': 'LED Light Panel Pro',
        'type': 'lighting',
        'barcode': 'LED987654321',
        'status': 'in_use',
        'location': 'Event Site B',
        'last_scan': (datetime.now()).isoformat()
    },
    {
        'id': 3,
        'name': 'Wireless Microphone Set',
        'type': 'audio',
        'barcode': 'MIC456789012',
        'status': 'maintenance',
        'location': 'Repair Shop',
        'last_scan': datetime.now().isoformat()
    },
    {
        'id': 4,
        'name': 'Projector 4K Ultra',
        'type': 'video',
        'barcode': 'PROJ123456789',
        'status': 'available',
        'location': 'Warehouse A',
        'last_scan': datetime.now().isoformat()
    }
]

def get_db_connection():
    """Get database connection"""
    try:
        return mysql.connector.connect(
            host=os.getenv('MYSQL_HOST'),
            user=os.getenv('MYSQL_USER'),
            password=os.getenv('MYSQL_PASSWORD'),
            database=os.getenv('MYSQL_DATABASE'),
            connect_timeout=5
        )
    except Exception as e:
        logging.warning(f"Database connection failed: {e}")
        return None

@devices_bp.route('/', methods=['GET'])
def get_devices():
    """Get all devices"""
    try:
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM devices ORDER BY name")
            devices = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify(devices)
        else:
            # Fallback to mock data
            logging.info("Using mock data for devices")
            return jsonify(MOCK_DEVICES)
            
    except Exception as e:
        logging.error(f"Error in get_devices: {e}")
        return jsonify({'error': f'Failed to fetch devices: {str(e)}'}), 500

@devices_bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device"""
    try:
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
            device = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if device:
                return jsonify(device)
            else:
                return jsonify({'error': 'Device not found'}), 404
        else:
            # Fallback to mock data
            device = next((device for device in MOCK_DEVICES if device['id'] == device_id), None)
            if device:
                return jsonify(device)
            else:
                return jsonify({'error': 'Device not found'}), 404
                
    except Exception as e:
        logging.error(f"Error in get_device: {e}")
        return jsonify({'error': f'Failed to fetch device: {str(e)}'}), 500

@devices_bp.route('/scan', methods=['POST'])
def scan_barcode():
    """Handle barcode scanning"""
    try:
        data = request.get_json()
        barcode = data.get('barcode')
        
        if not barcode:
            return jsonify({'error': 'No barcode provided'}), 400
        
        # Try to find device by barcode in mock data
        device = next((d for d in MOCK_DEVICES if d['barcode'] == barcode), None)
        
        if device:
            # Update last scan time
            device['last_scan'] = datetime.now().isoformat()
            
            return jsonify({
                'success': True,
                'device': device,
                'message': f'Device {device["name"]} scanned successfully'
            })
        else:
            # Create new scan record for unknown barcode
            return jsonify({
                'success': True,
                'barcode': barcode,
                'timestamp': datetime.now().isoformat(),
                'status': 'unknown_device',
                'message': 'Barcode scanned but device not found in database'
            })
            
    except Exception as e:
        logging.error(f"Error in scan_barcode: {e}")
        return jsonify({'error': f'Scan failed: {str(e)}'}), 500

@devices_bp.route('/search', methods=['GET'])
def search_devices():
    """Search devices by barcode or name"""
    try:
        query = request.args.get('q', '').lower()
        
        if not query:
            return jsonify([])
        
        # Search in mock data
        results = []
        for device in MOCK_DEVICES:
            if (query in device['name'].lower() or 
                query in device['barcode'].lower() or
                query in device['type'].lower()):
                results.append(device)
        
        return jsonify(results)
        
    except Exception as e:
        logging.error(f"Error in search_devices: {e}")
        return jsonify({'error': f'Search failed: {str(e)}'}), 500