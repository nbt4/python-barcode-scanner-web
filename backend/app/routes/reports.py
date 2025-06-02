from flask import Blueprint, request, jsonify, current_app, send_file
from app.routes.auth import token_required
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import datetime
import logging

reports_bp = Blueprint('reports', __name__)
logger = logging.getLogger(__name__)

@reports_bp.route('/jobs', methods=['GET'])
@token_required
def generate_jobs_report(current_user):
    try:
        # Get filter parameters
        search = request.args.get('search', '')
        status = request.args.get('status', '')
        date_from = request.args.get('date_from', '')
        date_to = request.args.get('date_to', '')
        
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Build query with filters
            query = """
                SELECT j.jobID, 
                       COALESCE(c.companyname, CONCAT_WS(', ', c.lastname, c.firstname)) as kunde,
                       j.startDate, j.endDate, 
                       COALESCE(s.status, 'N/A') as status,
                       COUNT(DISTINCT jd.deviceID) as device_count, 
                       j.final_revenue
                FROM jobs j
                LEFT JOIN customers c ON j.customerID = c.customerID
                LEFT JOIN status s ON j.statusID = s.statusID
                LEFT JOIN jobdevices jd ON j.jobID = jd.jobID
            """
            
            where_clauses = []
            params = []
            
            if search:
                search_param = f"%{search}%"
                where_clauses.append("""
                    (j.jobID LIKE %s OR 
                     c.companyname LIKE %s OR 
                     c.lastname LIKE %s OR 
                     c.firstname LIKE %s)
                """)
                params.extend([search_param] * 4)
            
            if status:
                where_clauses.append("s.status = %s")
                params.append(status)
            
            if date_from:
                where_clauses.append("j.startDate >= %s")
                params.append(date_from)
            
            if date_to:
                where_clauses.append("j.endDate <= %s")
                params.append(date_to)
            
            if where_clauses:
                query += " WHERE " + " AND ".join(where_clauses)
            
            query += """
                GROUP BY j.jobID, c.companyname, c.lastname, c.firstname, 
                         j.startDate, j.endDate, s.status, j.final_revenue
                ORDER BY j.jobID DESC
            """
            
            cursor.execute(query, params)
            jobs = cursor.fetchall()
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Title
            styles = getSampleStyleSheet()
            title = Paragraph(f"Jobs Report - {datetime.now().strftime('%d.%m.%Y')}", styles['Title'])
            elements.append(title)
            elements.append(Paragraph("<br/><br/>", styles['Normal']))
            
            # Filter Info
            if any([search, status, date_from, date_to]):
                elements.append(Paragraph("Applied Filters:", styles['Heading2']))
                filter_text = []
                if search:
                    filter_text.append(f"Search: {search}")
                if status:
                    filter_text.append(f"Status: {status}")
                if date_from:
                    filter_text.append(f"From: {date_from}")
                if date_to:
                    filter_text.append(f"To: {date_to}")
                for text in filter_text:
                    elements.append(Paragraph(f"• {text}", styles['Normal']))
                elements.append(Paragraph("<br/>", styles['Normal']))
            
            # Table
            if jobs:
                # Headers
                table_data = [['Job ID', 'Customer', 'Start Date', 'End Date', 'Status', 'Devices', 'Revenue']]
                
                # Data
                for job in jobs:
                    table_data.append([
                        str(job['jobID']),
                        str(job['kunde']),
                        job['startDate'].strftime('%Y-%m-%d') if job['startDate'] else 'N/A',
                        job['endDate'].strftime('%Y-%m-%d') if job['endDate'] else 'N/A',
                        str(job['status']),
                        str(job['device_count']),
                        f"€{job['final_revenue']:.2f}" if job['final_revenue'] else '€0.00'
                    ])
                
                # Create table
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(table)
                
                # Summary
                elements.append(Paragraph("<br/><br/>", styles['Normal']))
                elements.append(Paragraph("Summary:", styles['Heading2']))
                
                total_revenue = sum(job['final_revenue'] or 0 for job in jobs)
                total_devices = sum(job['device_count'] for job in jobs)
                
                summary = [
                    f"Total Jobs: {len(jobs)}",
                    f"Total Revenue: €{total_revenue:.2f}",
                    f"Total Devices: {total_devices}"
                ]
                
                for line in summary:
                    elements.append(Paragraph(f"• {line}", styles['Normal']))
            else:
                elements.append(Paragraph("No jobs found matching the criteria.", styles['Normal']))
            
            # Generate PDF
            doc.build(elements)
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'jobs_report_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error generating jobs report: {e}")
        return jsonify({'message': 'Failed to generate report'}), 500

@reports_bp.route('/job/<int:job_id>/devices', methods=['GET'])
@token_required
def generate_job_devices_report(current_user, job_id):
    try:
        conn = current_app.db_pool.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        try:
            # Get job info
            cursor.execute("""
                SELECT j.*, 
                       COALESCE(c.companyname, CONCAT_WS(', ', c.lastname, c.firstname)) as kunde,
                       s.status
                FROM jobs j
                LEFT JOIN customers c ON j.customerID = c.customerID
                LEFT JOIN status s ON j.statusID = s.statusID
                WHERE j.jobID = %s
            """, (job_id,))
            
            job = cursor.fetchone()
            if not job:
                return jsonify({'message': 'Job not found'}), 404
            
            # Get devices in job
            cursor.execute("""
                SELECT jd.deviceID, 
                       p.name AS product,
                       COALESCE(jd.custom_price, p.itemcostperday) AS price
                FROM jobdevices jd
                LEFT JOIN devices d ON jd.deviceID = d.deviceID
                LEFT JOIN products p ON d.productID = p.productID
                WHERE jd.jobID = %s
            """, (job_id,))
            
            devices = cursor.fetchall()
            
            # Create PDF
            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            elements = []
            
            # Title
            styles = getSampleStyleSheet()
            title = Paragraph(f"Devices Report - Job {job_id}", styles['Title'])
            elements.append(title)
            elements.append(Paragraph("<br/>", styles['Normal']))
            
            # Job Info
            elements.append(Paragraph("Job Information:", styles['Heading2']))
            job_info = [
                f"Customer: {job['kunde']}",
                f"Status: {job['status']}",
                f"Start Date: {job['startDate'].strftime('%Y-%m-%d') if job['startDate'] else 'N/A'}",
                f"End Date: {job['endDate'].strftime('%Y-%m-%d') if job['endDate'] else 'N/A'}"
            ]
            
            for line in job_info:
                elements.append(Paragraph(f"• {line}", styles['Normal']))
            elements.append(Paragraph("<br/>", styles['Normal']))
            
            # Devices Table
            if devices:
                elements.append(Paragraph("Devices:", styles['Heading2']))
                
                table_data = [['Device ID', 'Product', 'Price/Day']]
                for device in devices:
                    table_data.append([
                        str(device['deviceID']),
                        str(device['product']),
                        f"€{device['price']:.2f}" if device['price'] else '€0.00'
                    ])
                
                table = Table(table_data)
                table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 12),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                    ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                    ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 1), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]))
                elements.append(table)
                
                # Summary
                elements.append(Paragraph("<br/><br/>", styles['Normal']))
                elements.append(Paragraph("Summary:", styles['Heading2']))
                
                total_price = sum(device['price'] or 0 for device in devices)
                summary = [
                    f"Total Devices: {len(devices)}",
                    f"Total Daily Rate: €{total_price:.2f}"
                ]
                
                for line in summary:
                    elements.append(Paragraph(f"• {line}", styles['Normal']))
            else:
                elements.append(Paragraph("No devices found in this job.", styles['Normal']))
            
            # Generate PDF
            doc.build(elements)
            buffer.seek(0)
            
            return send_file(
                buffer,
                mimetype='application/pdf',
                as_attachment=True,
                download_name=f'job_{job_id}_devices_{datetime.now().strftime("%Y%m%d")}.pdf'
            )
            
        finally:
            cursor.close()
            conn.close()
            
    except Exception as e:
        logger.error(f"Error generating devices report for job {job_id}: {e}")
        return jsonify({'message': 'Failed to generate report'}), 500
