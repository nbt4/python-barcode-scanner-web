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
            connect_timeout=5
        )
    except Exception as e:
        logging.warning(f"Database connection failed: {e}")
        return None

@reports_bp.route('/summary', methods=['GET'])
def get_summary():
    """Get summary report"""
    try:
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            # Get job counts by status
            cursor.execute("""
                SELECT status, COUNT(*) as count 
                FROM jobs 
                GROUP BY status
            """)
            job_stats = cursor.fetchall()
            
            # Get recent activity
            cursor.execute("""
                SELECT * FROM jobs 
                ORDER BY created_at DESC 
                LIMIT 10
            """)
            recent_jobs = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return jsonify({
                'job_stats': job_stats,
                'recent_jobs': recent_jobs,
                'generated_at': datetime.now().isoformat()
            })
        else:
            # Fallback to mock data
            logging.info("Using mock data for reports")
            
            mock_job_stats = [
                {'status': 'active', 'count': 2},
                {'status': 'pending', 'count': 1},
                {'status': 'completed', 'count': 1}
            ]
            
            mock_recent_jobs = [
                {
                    'id': 1,
                    'jobID': 'JOB001',
                    'kunde': 'Tsunami Events GmbH',
                    'title': 'Event Equipment Setup',
                    'status': 'active',
                    'created_at': (datetime.now() - timedelta(days=1)).isoformat()
                },
                {
                    'id': 2,
                    'jobID': 'JOB002',
                    'kunde': 'Tech Conference Ltd',
                    'title': 'Conference AV Support',
                    'status': 'pending',
                    'created_at': (datetime.now() - timedelta(days=2)).isoformat()
                }
            ]
            
            return jsonify({
                'job_stats': mock_job_stats,
                'recent_jobs': mock_recent_jobs,
                'generated_at': datetime.now().isoformat(),
                'mode': 'mock'
            })
            
    except Exception as e:
        logging.error(f"Error in get_summary: {e}")
        return jsonify({'error': f'Failed to generate summary: {str(e)}'}), 500

@reports_bp.route('/daily', methods=['GET'])
def get_daily_report():
    """Get daily activity report"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT * FROM jobs 
                WHERE DATE(created_at) = %s
                ORDER BY created_at DESC
            """, (date_str,))
            
            jobs = cursor.fetchall()
            cursor.close()
            conn.close()
            
            return jsonify({
                'date': date_str,
                'jobs': jobs,
                'total_count': len(jobs)
            })
        else:
            # Fallback to mock data
            mock_jobs = [
                {
                    'id': 1,
                    'jobID': 'JOB001',
                    'kunde': 'Tsunami Events GmbH',
                    'title': 'Event Equipment Setup',
                    'status': 'active',
                    'created_at': datetime.now().isoformat()
                }
            ]
            
            return jsonify({
                'date': date_str,
                'jobs': mock_jobs,
                'total_count': len(mock_jobs),
                'mode': 'mock'
            })
            
    except Exception as e:
        logging.error(f"Error in get_daily_report: {e}")
        return jsonify({'error': f'Failed to generate daily report: {str(e)}'}), 500

@reports_bp.route('/devices', methods=['GET'])
def get_device_report():
    """Get device usage report"""
    try:
        # Mock device report data
        mock_device_stats = [
            {'status': 'available', 'count': 15},
            {'status': 'in_use', 'count': 8},
            {'status': 'maintenance', 'count': 2}
        ]
        
        mock_device_usage = [
            {
                'device_name': 'Audio Mixer XM-2000',
                'usage_count': 25,
                'last_used': (datetime.now() - timedelta(days=1)).isoformat()
            },
            {
                'device_name': 'LED Light Panel Pro',
                'usage_count': 18,
                'last_used': datetime.now().isoformat()
            }
        ]
        
        return jsonify({
            'device_stats': mock_device_stats,
            'device_usage': mock_device_usage,
            'generated_at': datetime.now().isoformat(),
            'mode': 'mock'
        })
        
    except Exception as e:
        logging.error(f"Error in get_device_report: {e}")
        return jsonify({'error': f'Failed to generate device report: {str(e)}'}), 500