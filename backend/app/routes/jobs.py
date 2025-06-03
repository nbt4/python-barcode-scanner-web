from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime
import logging

jobs_bp = Blueprint('jobs', __name__)

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

@jobs_bp.route('/', methods=['GET'])
@require_auth
def get_jobs():
    """Get all jobs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get query parameters
        status = request.args.get('status')
        limit = request.args.get('limit', type=int)
        offset = request.args.get('offset', 0, type=int)
        
        # Build query
        query = "SELECT * FROM jobs"
        params = []
        
        if status:
            query += " WHERE status = %s"
            params.append(status)
            
        query += " ORDER BY created_at DESC"
        
        if limit:
            query += " LIMIT %s OFFSET %s"
            params.extend([limit, offset])
        
        cursor.execute(query, params)
        jobs = cursor.fetchall()
        
        # Convert datetime objects to ISO format
        for job in jobs:
            for key, value in job.items():
                if isinstance(value, datetime):
                    job[key] = value.isoformat()
        
        cursor.close()
        conn.close()
        
        return jsonify(jobs)
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_jobs: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_jobs: {e}")
        return jsonify({'error': 'Failed to fetch jobs'}), 500

@jobs_bp.route('/<int:job_id>', methods=['GET'])
@require_auth
def get_job(job_id):
    """Get specific job"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if job:
            # Convert datetime objects to ISO format
            for key, value in job.items():
                if isinstance(value, datetime):
                    job[key] = value.isoformat()
            
            cursor.close()
            conn.close()
            return jsonify(job)
        else:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
            
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_job: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_job: {e}")
        return jsonify({'error': 'Failed to fetch job'}), 500

@jobs_bp.route('/', methods=['POST'])
@require_auth
def create_job():
    """Create new job"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        required_fields = ['title']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Generate job ID if not provided
        job_id = data.get('jobID')
        if not job_id:
            # Generate job ID based on current date and sequence
            cursor.execute("SELECT COUNT(*) as count FROM jobs WHERE DATE(created_at) = CURDATE()")
            result = cursor.fetchone()
            daily_count = result[0] + 1
            job_id = f"JOB{datetime.now().strftime('%Y%m%d')}{daily_count:03d}"
        
        query = """
        INSERT INTO jobs (jobID, kunde, title, description, status, startDate, endDate, device_count, created_at) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            job_id,
            data.get('kunde', ''),
            data.get('title'),
            data.get('description', ''),
            data.get('status', 'pending'),
            data.get('startDate'),
            data.get('endDate'),
            data.get('device_count', 0),
            datetime.now()
        )
        
        cursor.execute(query, values)
        new_job_id = cursor.lastrowid
        
        cursor.close()
        conn.close()
        
        logging.info(f"Job created: {job_id} (ID: {new_job_id})")
        
        return jsonify({
            'id': new_job_id,
            'jobID': job_id,
            'message': 'Job created successfully'
        }), 201
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in create_job: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in create_job: {e}")
        return jsonify({'error': 'Failed to create job'}), 500

@jobs_bp.route('/<int:job_id>', methods=['PUT'])
@require_auth
def update_job(job_id):
    """Update existing job"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if job exists
        cursor.execute("SELECT id FROM jobs WHERE id = %s", (job_id,))
        if not cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        # Build update query dynamically
        update_fields = []
        values = []
        
        allowed_fields = ['kunde', 'title', 'description', 'status', 'startDate', 'endDate', 'device_count']
        
        for field in allowed_fields:
            if field in data:
                update_fields.append(f"{field} = %s")
                values.append(data[field])
        
        if not update_fields:
            cursor.close()
            conn.close()
            return jsonify({'error': 'No valid fields to update'}), 400
        
        # Add updated_at timestamp
        update_fields.append("updated_at = %s")
        values.append(datetime.now())
        values.append(job_id)
        
        query = f"UPDATE jobs SET {', '.join(update_fields)} WHERE id = %s"
        cursor.execute(query, values)
        
        cursor.close()
        conn.close()
        
        logging.info(f"Job updated: {job_id}")
        
        return jsonify({'message': 'Job updated successfully'})
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in update_job: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in update_job: {e}")
        return jsonify({'error': 'Failed to update job'}), 500

@jobs_bp.route('/<int:job_id>', methods=['DELETE'])
@require_auth
def delete_job(job_id):
    """Delete job"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Check if job exists
        cursor.execute("SELECT jobID FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        
        if not job:
            cursor.close()
            conn.close()
            return jsonify({'error': 'Job not found'}), 404
        
        # Delete the job
        cursor.execute("DELETE FROM jobs WHERE id = %s", (job_id,))
        
        cursor.close()
        conn.close()
        
        logging.info(f"Job deleted: {job[0]} (ID: {job_id})")
        
        return jsonify({'message': 'Job deleted successfully'})
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in delete_job: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in delete_job: {e}")
        return jsonify({'error': 'Failed to delete job'}), 500

@jobs_bp.route('/stats', methods=['GET'])
@require_auth
def get_job_stats():
    """Get job statistics"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get status counts
        cursor.execute("""
            SELECT status, COUNT(*) as count 
            FROM jobs 
            GROUP BY status
        """)
        status_stats = cursor.fetchall()
        
        # Get total count
        cursor.execute("SELECT COUNT(*) as total FROM jobs")
        total_count = cursor.fetchone()['total']
        
        # Get recent activity (last 7 days)
        cursor.execute("""
            SELECT DATE(created_at) as date, COUNT(*) as count
            FROM jobs 
            WHERE created_at >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            GROUP BY DATE(created_at)
            ORDER BY date DESC
        """)
        recent_activity = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'total_jobs': total_count,
            'status_breakdown': status_stats,
            'recent_activity': recent_activity,
            'generated_at': datetime.now().isoformat()
        })
        
    except mysql.connector.Error as e:
        logging.error(f"Database error in get_job_stats: {e}")
        return jsonify({'error': 'Database error occurred'}), 500
    except Exception as e:
        logging.error(f"Error in get_job_stats: {e}")
        return jsonify({'error': 'Failed to fetch job statistics'}), 500