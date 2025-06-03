from flask import Blueprint, request, jsonify
import mysql.connector
import os
from datetime import datetime

jobs_bp = Blueprint('jobs', __name__)

def get_db_connection():
    """Get database connection"""
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST'),
        user=os.getenv('MYSQL_USER'),
        password=os.getenv('MYSQL_PASSWORD'),
        database=os.getenv('MYSQL_DATABASE')
    )

@jobs_bp.route('/', methods=['GET'])
def get_jobs():
    """Get all jobs"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs ORDER BY created_at DESC")
        jobs = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify(jobs)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get specific job"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM jobs WHERE id = %s", (job_id,))
        job = cursor.fetchone()
        cursor.close()
        conn.close()
        
        if job:
            return jsonify(job)
        else:
            return jsonify({'error': 'Job not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@jobs_bp.route('/', methods=['POST'])
def create_job():
    """Create new job"""
    try:
        data = request.get_json()
        conn = get_db_connection()
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
    except Exception as e:
        return jsonify({'error': str(e)}), 500