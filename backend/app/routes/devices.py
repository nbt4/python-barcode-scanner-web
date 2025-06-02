from flask import Blueprint, request, jsonify, current_app, send_file
import qrcode
from barcode import Code128
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from app.routes.auth import token_required
import logging

devices_bp = Blueprint('devices', __name__)
logger = logging.getLogger(__name__)

@devices_bp.route('/job/<int:job_id>', methods=['GET'])
@token_required
def get_devices_in_job(current_user, job_id):
    try:
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            query = """
                SELECT jd.deviceID, 
                       p.name AS product, 
                       jd.custom_price,
                       p.itemcostperday,
                       COALESCE(jd.custom_price, p.itemcostperday) AS price
                FROM jobdevices jd
                LEFT JOIN devices d ON jd.deviceID = d.deviceID
                LEFT JOIN products p ON d.productID = p.productID
                WHERE jd.jobID = %s
            """
            cursor.execute(query, (job_id,))
            devices = cursor.fetchall()
            
            return jsonify(devices)
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error fetching devices for job {job_id}: {e}")
        return jsonify({'message': 'Failed to fetch devices'}), 500

@devices_bp.route('/job/<int:job_id>/device', methods=['POST'])
@token_required
def add_device_to_job(current_user, job_id):
    try:
        data = request.get_json()
        device_id = data.get('deviceID')
        custom_price = data.get('customPrice')
        
        if not device_id:
            return jsonify({'message': 'Device ID is required'}), 400
        
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Check if device exists
            cursor.execute("""
                SELECT d.deviceID, p.itemcostperday 
                FROM devices d
                LEFT JOIN products p ON d.productID = p.productID
                WHERE d.deviceID = %s
            """, (device_id,))
            device = cursor.fetchone()
            
            if not device:
                return jsonify({'message': 'Device not found'}), 404
            
            # Check if device is already in job
            cursor.execute("""
                SELECT 1 FROM jobdevices 
                WHERE jobID = %s AND deviceID = %s
            """, (job_id, device_id))
            
            if cursor.fetchone():
                return jsonify({'message': 'Device already in job'}), 400
            
            # Add device to job
            cursor.execute("""
                INSERT INTO jobdevices (jobID, deviceID, custom_price)
                VALUES (%s, %s, %s)
            """, (job_id, device_id, custom_price or device['itemcostperday']))
            
            conn.commit()
            
            return jsonify({'message': 'Device added successfully'})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error adding device to job {job_id}: {e}")
        return jsonify({'message': 'Failed to add device'}), 500

@devices_bp.route('/job/<int:job_id>/device/<device_id>', methods=['DELETE'])
@token_required
def remove_device_from_job(current_user, job_id, device_id):
    try:
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                DELETE FROM jobdevices 
                WHERE jobID = %s AND deviceID = %s
            """, (job_id, device_id))
            
            conn.commit()
            
            if cursor.rowcount == 0:
                return jsonify({'message': 'Device not found in job'}), 404
            
            return jsonify({'message': 'Device removed successfully'})
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error removing device {device_id} from job {job_id}: {e}")
        return jsonify({'message': 'Failed to remove device'}), 500

@devices_bp.route('/job/<int:job_id>/bulk', methods=['POST'])
@token_required
def bulk_add_devices(current_user, job_id):
    try:
        data = request.get_json()
        devices = data.get('devices', [])
        
        if not devices:
            return jsonify({'message': 'No devices provided'}), 400
        
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            results = {
                'success': [],
                'errors': []
            }
            
            for device in devices:
                device_id = device.get('deviceID')
                custom_price = device.get('customPrice')
                
                try:
                    # Check if device exists
                    cursor.execute("""
                        SELECT d.deviceID, p.itemcostperday 
                        FROM devices d
                        LEFT JOIN products p ON d.productID = p.productID
                        WHERE d.deviceID = %s
                    """, (device_id,))
                    device_info = cursor.fetchone()
                    
                    if not device_info:
                        results['errors'].append({
                            'deviceID': device_id,
                            'error': 'Device not found'
                        })
                        continue
                    
                    # Check if already in job
                    cursor.execute("""
                        SELECT 1 FROM jobdevices 
                        WHERE jobID = %s AND deviceID = %s
                    """, (job_id, device_id))
                    
                    if cursor.fetchone():
                        results['errors'].append({
                            'deviceID': device_id,
                            'error': 'Already in job'
                        })
                        continue
                    
                    # Add to job
                    cursor.execute("""
                        INSERT INTO jobdevices (jobID, deviceID, custom_price)
                        VALUES (%s, %s, %s)
                    """, (job_id, device_id, custom_price or device_info['itemcostperday']))
                    
                    results['success'].append(device_id)
                    
                except Exception as e:
                    results['errors'].append({
                        'deviceID': device_id,
                        'error': str(e)
                    })
            
            conn.commit()
            
            return jsonify(results)
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error in bulk device add for job {job_id}: {e}")
        return jsonify({'message': 'Failed to process bulk device add'}), 500

@devices_bp.route('/qrcode/<device_id>', methods=['GET'])
@token_required
def generate_qr_code(current_user, device_id):
    try:
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(f"DEVICE:{device_id}")
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to bytes
        img_byte_arr = BytesIO()
        img.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        return send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'qr_device_{device_id}.png'
        )
        
    except Exception as e:
        logger.error(f"Error generating QR code for device {device_id}: {e}")
        return jsonify({'message': 'Failed to generate QR code'}), 500

@devices_bp.route('/barcode/<device_id>', methods=['GET'])
@token_required
def generate_barcode(current_user, device_id):
    try:
        # Generate barcode
        code = Code128(device_id, writer=ImageWriter())
        
        # Save to bytes
        img_byte_arr = BytesIO()
        code.write(img_byte_arr)
        img_byte_arr.seek(0)
        
        return send_file(
            img_byte_arr,
            mimetype='image/png',
            as_attachment=True,
            download_name=f'barcode_device_{device_id}.png'
        )
        
    except Exception as e:
        logger.error(f"Error generating barcode for device {device_id}: {e}")
        return jsonify({'message': 'Failed to generate barcode'}), 500

@devices_bp.route('/verify/<device_id>', methods=['GET'])
@token_required
def verify_device(current_user, device_id):
    try:
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            cursor.execute("""
                SELECT d.deviceID, p.name, p.itemcostperday
                FROM devices d
                LEFT JOIN products p ON d.productID = p.productID
                WHERE d.deviceID = %s
            """, (device_id,))
            
            device = cursor.fetchone()
            
            if not device:
                return jsonify({'valid': False, 'message': 'Device not found'}), 404
            
            return jsonify({
                'valid': True,
                'device': device
            })
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error verifying device {device_id}: {e}")
        return jsonify({'message': 'Failed to verify device'}), 500
