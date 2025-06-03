from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime

devices_bp = Blueprint('devices', __name__)

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )

@devices_bp.route('/', methods=['GET'])
def get_devices():
    """Get all devices"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM devices ORDER BY name")
        devices = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(devices)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/<int:device_id>', methods=['GET'])
def get_device(device_id):
    """Get specific device"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM devices WHERE id = %s", (device_id,))
        device = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if device:
            return jsonify(device)
        else:
            return jsonify({'error': 'Device not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@devices_bp.route('/scan', methods=['POST'])
def scan_barcode():
    """Handle barcode scanning"""
    try:
        data = request.get_json()
        barcode = data.get('barcode')
        
        if not barcode:
            return jsonify({'error': 'No barcode provided'}), 400
        
        # Process barcode scan
        return jsonify({
            'barcode': barcode,
            'timestamp': str(datetime.now()),
            'status': 'scanned'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500