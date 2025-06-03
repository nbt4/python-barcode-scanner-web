from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime, timedelta
import logging

jobs_bp = Blueprint('jobs', __name__)

# Mock data for development/testing when database is not available
MOCK_JOBS = [
    {
        'id': 1,
        'jobID': 'JOB001',
        'kunde': 'Tsunami Events GmbH',
        'title': 'Event Equipment Setup',
        'description': 'Setup audio and lighting equipment for corporate event',
        'status': 'active',
        'startDate': (datetime.now() - timedelta(days=2)).isoformat(),
        'endDate': (datetime.now() + timedelta(days=3)).isoformat(),
        'created_at': (datetime.now() - timedelta(days=5)).isoformat(),
        'device_count': 15
    },
    {
        'id': 2,
        'jobID': 'JOB002',
        'kunde': 'Tech Conference Ltd',
        'title': 'Conference AV Support',
        'description': 'Audio visual support for 3-day tech conference',
        'status': 'pending',
        'startDate': (datetime.now() + timedelta(days=7)).isoformat(),
        'endDate': (datetime.now() + timedelta(days=10)).isoformat(),
        'created_at': (datetime.now() - timedelta(days=3)).isoformat(),
        'device_count': 25
    },
    {
        'id': 3,
        'jobID': 'JOB003',
        'kunde': 'Wedding Planners Inc',
        'title': 'Wedding Reception',
        'description': 'Sound system and lighting for wedding reception',
        'status': 'completed',
        'startDate': (datetime.now() - timedelta(days=10)).isoformat(),
        'endDate': (datetime.now() - timedelta(days=9)).isoformat(),
        'created_at': (datetime.now() - timedelta(days=15)).isoformat(),
        'device_count': 8
    },
    {
        'id': 4,
        'jobID': 'JOB004',
        'kunde': 'Music Festival Org',
        'title': 'Summer Music Festival',
        'description': 'Full stage setup for 2-day music festival',
        'status': 'active',
        'startDate': (datetime.now() - timedelta(days=1)).isoformat(),
        'endDate': (datetime.now() + timedelta(days=1)).isoformat(),
        'created_at': (datetime.now() - timedelta(days=20)).isoformat(),
        'device_count': 50
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

@jobs_bp.route('/', methods=['GET'])
def get_jobs():
    """Get all jobs"""
    try:
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
            jobs = cursor.fetchall()
            cursor.close()
            conn.close()
            return jsonify(jobs)
        else:
            # Fallback to mock data
            logging.info("Using mock data for jobs")
            
            # Filter by status if provided
            status = request.args.get('status')
            limit = request.args.get('limit', type=int)
            
            filtered_jobs = MOCK_JOBS
            if status:
                filtered_jobs = [job for job in MOCK_JOBS if job['status'] == status]
            
            if limit:
                filtered_jobs = filtered_jobs[:limit]
                
            return jsonify(filtered_jobs)
            
    except Exception as e:
        logging.error(f"Error in get_jobs: {e}")
        return jsonify({'error': f'Failed to fetch jobs: {str(e)}'}), 500

@jobs_bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get specific job"""
    try:
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
            job = cursor.fetchone()
            cursor.close()
            conn.close()
            
            if job:
                return jsonify(job)
            else:
                return jsonify({'error': 'Job not found'}), 404
        else:
            # Fallback to mock data
            job = next((job for job in MOCK_JOBS if job['id'] == job_id), None)
            if job:
                return jsonify(job)
            else:
                return jsonify({'error': 'Job not found'}), 404
                
    except Exception as e:
        logging.error(f"Error in get_job: {e}")
        return jsonify({'error': f'Failed to fetch job: {str(e)}'}), 500

@jobs_bp.route('/', methods=['POST'])
def create_job():
    """Create new job"""
    try:
        data = request.get_json()
        
        # Try database first
        conn = get_db_connection()
        if conn:
            cursor = conn.cursor()
            
            query = """
            INSERT INTO jobs (title, description, status, created_at) 
            VALUES (%s, %s, %s, %s)
            """
            values = (
                data.get('title'),
                data.get('description'),
                data.get('status', 'pending'),
                datetime.now()
            )
            
            cursor.execute(query, values)
            conn.commit()
            job_id = cursor.lastrowid
            cursor.close()
            conn.close()
            
            return jsonify({'id': job_id, 'message': 'Job created successfully'}), 201
        else:
            # Fallback to mock creation (just return success)
            new_id = max([job['id'] for job in MOCK_JOBS]) + 1
            return jsonify({
                'id': new_id, 
                'message': 'Job created successfully (mock mode)',
                'note': 'Database not available, using mock mode'
            }), 201
            
    except Exception as e:
        logging.error(f"Error in create_job: {e}")
        return jsonify({'error': f'Failed to create job: {str(e)}'}), 500

@jobs_bp.route('/status', methods=['GET'])
def get_job_status():
    """Get job status information"""
    try:
        conn = get_db_connection()
        if conn:
            return jsonify({'database': 'connected', 'mode': 'production'})
        else:
            return jsonify({'database': 'disconnected', 'mode': 'mock'})
    except Exception as e:
        return jsonify({'database': 'error', 'mode': 'mock', 'error': str(e)})