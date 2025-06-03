from flask import Blueprint, request, jsonify
from ..routes.auth import token_required
import pymysql
from datetime import datetime
import os
from dotenv import load_dotenv

# Reload environment variables
load_dotenv()

jobs_bp = Blueprint('jobs', __name__)

def get_db_connection():
    """Get a connection to the MySQL database"""
    try:
        from flask import current_app
        config = current_app.config
        print(f"Debug - Connection attempt with: host={config['MYSQL_HOST']}, db={config['MYSQL_DATABASE']}, user={config['MYSQL_USER']}")
        
        connection = pymysql.connect(
            host=config['MYSQL_HOST'],
            database=config['MYSQL_DATABASE'],
            user=config['MYSQL_USER'],
            password=config['MYSQL_PASSWORD'],
            cursorclass=pymysql.cursors.DictCursor,
            ssl={"ssl": False},
            port=3306,
            connect_timeout=10,
            read_timeout=30,
            write_timeout=30,
            charset='utf8mb4',
            ssl_verify_cert=False,
            ssl_verify_identity=False
        )
        print("Debug - Database connection successful")
        return connection
    except pymysql.Error as err:
        print(f"Error connecting to database: {err}")
        return None
    except Exception as e:
        print(f"Unexpected error connecting to database: {str(e)}")
        return None

@jobs_bp.route('', methods=['GET'])
@token_required
def get_jobs():
    """Get all jobs"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
          # Base query with all joins
        query = """
            SELECT 
                j.jobID,
                j.customerID,
                j.statusID,
                j.startDate,
                j.endDate,
                j.description,
                j.created_at,
                j.updated_at,
                c.companyname,
                COALESCE(c.firstname, '') as firstname,
                COALESCE(c.lastname, '') as lastname,
                COALESCE(s.status, 'Unknown') as status,
                COUNT(DISTINCT jd.deviceID) as device_count,
                CAST(COALESCE(SUM(CASE 
                    WHEN jd.customPrice IS NOT NULL THEN jd.customPrice 
                    WHEN d.price IS NOT NULL THEN d.price
                    ELSE 0 
                END), 0) AS DECIMAL(10,2)) as total_price
            FROM jobs j
            LEFT JOIN customers c ON j.customerID = c.customerID
            LEFT JOIN status s ON j.statusID = s.statusID
            LEFT JOIN jobdevices jd ON j.jobID = jd.jobID 
            LEFT JOIN devices d ON jd.deviceID = d.deviceID
        """
        
        # Add search conditions if provided
        conditions = []
        params = []
        
        if request.args.get('search'):
            search = f"%{request.args.get('search')}%"
            conditions.append("(c.companyname LIKE %s OR c.firstname LIKE %s OR c.lastname LIKE %s)")
            params.extend([search, search, search])
            
        if request.args.get('status'):
            conditions.append("s.status = %s")
            params.append(request.args.get('status'))
            
        if conditions:
            query += " WHERE " + " AND ".join(conditions)
            
        query += " GROUP BY j.jobID ORDER BY j.startDate DESC"
        
        cursor.execute(query, params)        jobs = cursor.fetchall()
        
        # Format customer name and ensure all dates are strings
        formatted_jobs = []
        for job in jobs:
            formatted_job = dict(job)
            
            # Format customer name
            if job.get('companyname'):
                formatted_job['customer_name'] = job['companyname']
            else:
                name_parts = [job.get('lastname', ''), job.get('firstname', '')]
                formatted_job['customer_name'] = ', '.join(filter(None, name_parts))
            
            # Convert dates to strings
            if formatted_job.get('startDate'):
                formatted_job['startDate'] = formatted_job['startDate'].strftime('%Y-%m-%d')
            if formatted_job.get('endDate'):
                formatted_job['endDate'] = formatted_job['endDate'].strftime('%Y-%m-%d')
            if formatted_job.get('created_at'):
                formatted_job['created_at'] = formatted_job['created_at'].strftime('%Y-%m-%d %H:%M:%S')
            if formatted_job.get('updated_at'):
                formatted_job['updated_at'] = formatted_job['updated_at'].strftime('%Y-%m-%d %H:%M:%S')
                
            # Ensure numeric values are properly formatted
            formatted_job['device_count'] = int(formatted_job.get('device_count', 0))
            formatted_job['total_price'] = float(formatted_job.get('total_price', 0))
            
            formatted_jobs.append(formatted_job)
        
        return jsonify(formatted_jobs)
    except pymysql.Error as err:
        print(f"Database error: {err}")
        return jsonify({'message': 'Database error occurred'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@jobs_bp.route('/<int:job_id>', methods=['GET'])
@token_required
def get_job(job_id):
    """Get a specific job by ID"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        
        # Get job details
        cursor.execute("""
            SELECT j.*, c.companyname, c.firstname, c.lastname, s.status,
                   COUNT(jd.deviceID) as device_count 
            FROM jobs j 
            LEFT JOIN customers c ON j.customerID = c.customerID
            LEFT JOIN status s ON j.statusID = s.statusID
            LEFT JOIN jobdevices jd ON j.jobID = jd.jobID 
            WHERE j.jobID = %s 
            GROUP BY j.jobID
        """, (job_id,))
        job = cursor.fetchone()
        
        if not job:
            return jsonify({'message': 'Job not found'}), 404
        
        # Format customer name
        if job.get('companyname'):
            job['customer_name'] = job['companyname']
        else:
            job['customer_name'] = f"{job.get('lastname', '')}, {job.get('firstname', '')}".strip(', ')
        
        # Get devices for this job
        cursor.execute("""
            SELECT d.*, p.name as product_name, p.itemcostperday,
                   jd.custom_price
            FROM jobdevices jd
            JOIN devices d ON jd.deviceID = d.deviceID
            JOIN products p ON d.productID = p.productID
            WHERE jd.jobID = %s
        """, (job_id,))
        devices = cursor.fetchall()
        
        job['devices'] = devices
        return jsonify(job)
    except pymysql.Error as err:
        print(f"Database error: {err}")
        return jsonify({'message': 'Database error occurred'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@jobs_bp.route('/', methods=['POST'])
@token_required
def create_job():
    """Create a new job"""
    data = request.get_json()
    
    if not data or not data.get('customerID'):
        return jsonify({'message': 'Customer ID is required'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        now = datetime.utcnow()
        
        cursor.execute("""
            INSERT INTO jobs (customerID, statusID, description, startDate, endDate) 
            VALUES (%s, %s, %s, %s, %s)
        """, (
            data['customerID'],
            data.get('statusID', 1),  # Default to first status if not specified
            data.get('description', ''),
            data.get('startDate', now.strftime('%Y-%m-%d')),
            data.get('endDate', now.strftime('%Y-%m-%d'))
        ))
        
        conn.commit()
        job_id = cursor.lastrowid
        
        # Fetch the created job
        cursor.execute("""
            SELECT j.*, c.companyname, c.firstname, c.lastname, s.status
            FROM jobs j 
            LEFT JOIN customers c ON j.customerID = c.customerID
            LEFT JOIN status s ON j.statusID = s.statusID
            WHERE j.jobID = %s
        """, (job_id,))
        job = cursor.fetchone()
        
        # Format customer name
        if job.get('companyname'):
            job['customer_name'] = job['companyname']
        else:
            job['customer_name'] = f"{job.get('lastname', '')}, {job.get('firstname', '')}".strip(', ')
        
        return jsonify(job), 201
    except pymysql.Error as err:
        print(f"Database error: {err}")
        return jsonify({'message': 'Database error occurred'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@jobs_bp.route('/<int:job_id>', methods=['PUT'])
@token_required
def update_job(job_id):
    """Update a job"""
    data = request.get_json()
    
    if not data:
        return jsonify({'message': 'No update data provided'}), 400
    
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        
        # Check if job exists
        cursor.execute("SELECT * FROM jobs WHERE jobID = %s", (job_id,))
        if not cursor.fetchone():
            return jsonify({'message': 'Job not found'}), 404
        
        # Update job
        update_fields = []
        update_values = []
        
        if 'customerID' in data:
            update_fields.append("customerID = %s")
            update_values.append(data['customerID'])
        if 'statusID' in data:
            update_fields.append("statusID = %s")
            update_values.append(data['statusID'])
        if 'description' in data:
            update_fields.append("description = %s")
            update_values.append(data['description'])
        if 'startDate' in data:
            update_fields.append("startDate = %s")
            update_values.append(data['startDate'])
        if 'endDate' in data:
            update_fields.append("endDate = %s")
            update_values.append(data['endDate'])
        
        update_values.append(job_id)
        
        query = f"""
            UPDATE jobs 
            SET {', '.join(update_fields)}
            WHERE jobID = %s
        """
        
        cursor.execute(query, tuple(update_values))
        conn.commit()
        
        # Fetch updated job
        cursor.execute("""
            SELECT j.*, c.companyname, c.firstname, c.lastname, s.status
            FROM jobs j 
            LEFT JOIN customers c ON j.customerID = c.customerID
            LEFT JOIN status s ON j.statusID = s.statusID
            WHERE j.jobID = %s
        """, (job_id,))
        job = cursor.fetchone()
        
        # Format customer name
        if job.get('companyname'):
            job['customer_name'] = job['companyname']
        else:
            job['customer_name'] = f"{job.get('lastname', '')}, {job.get('firstname', '')}".strip(', ')
        
        return jsonify(job)
    except pymysql.Error as err:
        print(f"Database error: {err}")
        return jsonify({'message': 'Database error occurred'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()

@jobs_bp.route('/<int:job_id>', methods=['DELETE'])
@token_required
def delete_job(job_id):
    """Delete a job"""
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Database connection failed'}), 500

    try:
        cursor = conn.cursor()
        
        # Check if job exists
        cursor.execute("SELECT * FROM jobs WHERE jobID = %s", (job_id,))
        if not cursor.fetchone():
            return jsonify({'message': 'Job not found'}), 404
        
        # Delete job devices first
        cursor.execute("DELETE FROM jobdevices WHERE jobID = %s", (job_id,))
        
        # Then delete job
        cursor.execute("DELETE FROM jobs WHERE jobID = %s", (job_id,))
        conn.commit()
        
        return jsonify({'message': 'Job deleted successfully'})
    except pymysql.Error as err:
        print(f"Database error: {err}")
        return jsonify({'message': 'Database error occurred'}), 500
    finally:
        if conn:
            cursor.close()
            conn.close()
