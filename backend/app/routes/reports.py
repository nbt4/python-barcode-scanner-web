from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime, timedelta
import logging

reports_bp = Blueprint('reports', __name__)

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

@reports_bp.route('/summary', methods=['GET'])
@require_auth
def get_summary():
    """Get summary report"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get job counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM jobs 
            GROUP BY status
        """)
        job_stats = cursor.fetchall()
        
        # Get device counts by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM devices 
            GROUP BY status
        """)
        device_stats = cursor.fetchall()
        
        # Get recent jobs (last 10)
        cursor.execute("""
            SELECT id, jobID, kunde, title, status, created_at
            FROM jobs 
            ORDER BY created_at DESC 
            LIMIT 10
        """)
        recent_jobs = cursor.fetchall()
        
        # Get scan activity (last 7 days)
        cursor.execute("""
            SELECT DATE(scan_timestamp) as date, COUNT(*) as scan_count
            FROM scans 
            WHERE scan_timestamp >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(scan_timestamp)
            ORDER BY date DESC
        """)
        scan_activity = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for job in recent_jobs:
            for key, value in job.items():
                if isinstance(value, datetime):
                    job[key] = value.isoformat()
        
        for activity in scan_activity:
            for key, value in activity.items():
                if isinstance(value, datetime):
                    activity[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'job_stats': job_stats,
            'device_stats': device_stats,
            'recent_jobs': recent_jobs,
            'scan_activity': scan_activity,
            'generated_at': datetime.now().isoformat()
        })
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_summary: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_summary: {e}")
        return jsonify({'error': 'Failed to generate summary'}), 500

@reports_bp.route('/daily', methods=['GET'])
def get_daily_report():
    """Get daily activity report"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get jobs created on this date
        cursor.execute("""
            SELECT * FROM jobs 
            WHERE DATE(created_at) = %s
            ORDER BY created_at DESC
        """, (date_str,))
        jobs = cursor.fetchall()
        
        # Get scans on this date
        cursor.execute("""
            SELECT s.*, d.name as device_name, d.type as device_type
            FROM scans s
            LEFT JOIN devices d ON s.device_id = d.id
            WHERE DATE(s.scan_timestamp) = %s
            ORDER BY s.scan_timestamp DESC
        """, (date_str,))
        scans = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for job in jobs:
            for key, value in job.items():
                if isinstance(value, datetime):
                    job[key] = value.isoformat()
        
        for scan in scans:
            for key, value in scan.items():
                if isinstance(value, datetime):
                    scan[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'date': date_str,
            'jobs': jobs,
            'scans': scans,
            'job_count': len(jobs),
            'scan_count': len(scans)
        })
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_daily_report: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_daily_report: {e}")
        return jsonify({'error': 'Failed to generate daily report'}), 500

@reports_bp.route('/devices', methods=['GET'])
@require_auth
def get_device_report():
    """Get device usage report"""
    try:
        # Get date range parameters
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get device usage statistics
        cursor.execute("""
            SELECT 
                d.id,
                d.name,
                d.type,
                d.status,
                d.location,
                COUNT(s.id) as scan_count,
                MAX(s.scan_timestamp) as last_scan
            FROM devices d
            LEFT JOIN scans s ON d.id = s.device_id 
                AND s.scan_timestamp BETWEEN %s AND %s
            GROUP BY d.id, d.name, d.type, d.status, d.location
            ORDER BY scan_count DESC, d.name
        """, (start_date, end_date))
        device_usage = cursor.fetchall()
        
        # Get most active devices
        cursor.execute("""
            SELECT 
                d.name,
                d.type,
                COUNT(s.id) as scan_count
            FROM devices d
            JOIN scans s ON d.id = s.device_id
            WHERE s.scan_timestamp BETWEEN %s AND %s
            GROUP BY d.id, d.name, d.type
            ORDER BY scan_count DESC
            LIMIT 10
        """, (start_date, end_date))
        most_active = cursor.fetchall()
        
        # Get devices by status
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM devices 
            GROUP BY status
        """)
        status_breakdown = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for device in device_usage:
            for key, value in device.items():
                if isinstance(value, datetime):
                    device[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'start_date': start_date,
            'end_date': end_date,
            'device_usage': device_usage,
            'most_active_devices': most_active,
            'status_breakdown': status_breakdown,
            'generated_at': datetime.now().isoformat()
        })
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_device_report: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_device_report: {e}")
        return jsonify({'error': 'Failed to generate device report'}), 500

@reports_bp.route('/jobs', methods=['GET'])
@require_auth
def get_job_report():
    """Get job performance report"""
    try:
        # Get date range parameters
        start_date = request.args.get('start_date', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        end_date = request.args.get('end_date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get jobs in date range
        cursor.execute("""
            SELECT 
                jobID,
                kunde,
                title,
                status,
                startDate,
                endDate,
                device_count,
                created_at,
                DATEDIFF(endDate, startDate) as duration_days
            FROM jobs 
            WHERE created_at BETWEEN %s AND %s
            ORDER BY created_at DESC
        """, (start_date, end_date))
        jobs = cursor.fetchall()
        
        # Get job statistics
        cursor.execute("""
            SELECT 
                status,
                COUNT(*) as count,
                AVG(device_count) as avg_devices,
                AVG(DATEDIFF(endDate, startDate)) as avg_duration
            FROM jobs 
            WHERE created_at BETWEEN %s AND %s
            GROUP BY status
        """, (start_date, end_date))
        job_stats = cursor.fetchall()
        
        # Get customer statistics
        cursor.execute("""
            SELECT 
                kunde,
                COUNT(*) as job_count,
                SUM(device_count) as total_devices
            FROM jobs 
            WHERE created_at BETWEEN %s AND %s
            GROUP BY kunde
            ORDER BY job_count DESC
            LIMIT 10
        """, (start_date, end_date))
        customer_stats = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for job in jobs:
            for key, value in job.items():
                if isinstance(value, datetime):
                    job[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'start_date': start_date,
            'end_date': end_date,
            'jobs': jobs,
            'job_statistics': job_stats,
            'customer_statistics': customer_stats,
            'total_jobs': len(jobs),
            'generated_at': datetime.now().isoformat()
        })
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_job_report: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_job_report: {e}")
        return jsonify({'error': 'Failed to generate job report'}), 500

@reports_bp.route('/export/<report_type>', methods=['GET'])
@require_auth
def export_report(report_type):
    """Export report as CSV"""
    try:
        # This would implement CSV export functionality
        # For now, return JSON with export info
        return jsonify({
            'message': f'Export functionality for {report_type} reports will be implemented',
            'report_type': report_type,
            'format': 'CSV',
            'status': 'pending_implementation'
        })
        
    except Exception as e:
        logging.error(f"Error in export_report: {e}")
        return jsonify({'error': 'Export failed'}), 500