from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime, timedelta

reports_bp = Blueprint('reports', __name__)

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )

@reports_bp.route('/summary', methods=['GET'])
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@reports_bp.route('/daily', methods=['GET'])
def get_daily_report():
    """Get daily activity report"""
    try:
        date_str = request.args.get('date', datetime.now().strftime('%Y-%m-%d'))
        
        conn = get_db_connection()
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500