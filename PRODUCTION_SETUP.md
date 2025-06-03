# Production Setup Guide

## Overview

This is a production-ready barcode scanner webapp that uses MySQL authentication and your existing `TS-Lager` database.

## Key Features

✅ **MySQL Authentication**: Uses your existing MySQL/phpMyAdmin credentials
✅ **Production Database**: Connects to your `tsunami-events.de` MySQL server
✅ **Role-Based Access**: Automatic role assignment based on MySQL privileges
✅ **No Mock Data**: All data comes from your database
✅ **Audit Logging**: Tracks all changes and scans
✅ **Professional UI**: Clean, production-ready interface

## Database Setup

### 1. Create Required Tables

Run the SQL schema on your `TS-Lager` database:

```bash
mysql -h tsunami-events.de -u root -p TS-Lager < database/schema.sql
```

Or execute the SQL file through phpMyAdmin:
1. Login to phpMyAdmin
2. Select `TS-Lager` database
3. Go to Import tab
4. Upload `database/schema.sql`
5. Execute

### 2. Verify Tables Created

The following tables will be created:
- `jobs` - Work orders/events
- `devices` - Equipment inventory
- `scans` - Barcode scan history
- `job_devices` - Job-device assignments
- `maintenance_log` - Device maintenance records
- `settings` - System configuration
- `audit_log` - Change tracking

## Authentication System

### How It Works

1. **Login**: Users enter their MySQL username/password
2. **Verification**: System connects to MySQL to verify credentials
3. **Role Assignment**: Automatic role based on MySQL privileges:
   - `admin` - Users with SUPER privilege
   - `manager` - Users with full CRUD privileges
   - `viewer` - Users with SELECT privilege only
   - `limited` - Users with minimal access

### Supported MySQL Users

Any MySQL user that can connect to `tsunami-events.de` and access `TS-Lager` database can login.

## Deployment Steps

### 1. Update Environment Variables

Edit `.env` file:
```bash
# Change this to a secure secret for production
JWT_SECRET_KEY=your-very-secure-production-secret-key-here
```

### 2. Deploy with Docker

For production deployment:
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up --build -d
```

### 3. Configure Nginx Proxy Manager

Follow the setup in `NGINX_PROXY_SETUP.md` to configure:
- Domain: `job.tsunamievents.de`
- SSL certificate
- Proxy configuration

### 4. Test the System

1. **Access**: https://job.tsunamievents.de
2. **Login**: Use your MySQL credentials (same as phpMyAdmin)
3. **Verify**: Check that you can see the dashboard

## User Roles & Permissions

### Admin Role (MySQL SUPER privilege)
- Full access to all features
- Can create/edit/delete jobs and devices
- Access to all reports
- System configuration

### Manager Role (Full CRUD privileges)
- Create/edit/delete jobs and devices
- Access to reports
- Cannot modify system settings

### Viewer Role (SELECT privilege)
- View-only access to jobs and devices
- Can scan barcodes
- Limited report access

### Limited Role (Minimal access)
- Basic scanning functionality only

## Security Features

### Database Security
- Uses existing MySQL user authentication
- No additional user management required
- Leverages your existing security policies

### Application Security
- JWT tokens with 8-hour expiration
- HTTPS enforcement (with Nginx Proxy Manager)
- SQL injection protection
- Input validation and sanitization

### Audit Trail
- All database changes logged
- Scan history tracking
- User action logging

## Monitoring & Maintenance

### Health Checks

Check application status:
```bash
curl https://job.tsunamievents.de/health
```

### Database Connection

Verify database connectivity:
```bash
curl https://job.tsunamievents.de/api/v1/jobs/stats
```

### Logs

View application logs:
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Backup

Regular database backups are recommended:
```bash
mysqldump -h tsunami-events.de -u root -p TS-Lager > backup_$(date +%Y%m%d).sql
```

## Troubleshooting

### Login Issues

1. **"Invalid MySQL credentials"**
   - Verify username/password work in phpMyAdmin
   - Check if user has access to `TS-Lager` database

2. **"Database connection failed"**
   - Verify `tsunami-events.de` is accessible from Docker containers
   - Check firewall settings
   - Verify MySQL server is running

3. **"Unable to determine user permissions"**
   - User might not have sufficient privileges
   - Check MySQL user grants

### Application Issues

1. **"Jobs couldn't be loaded"**
   - Verify database tables exist
   - Check user has SELECT privilege on jobs table

2. **500 Internal Server Error**
   - Check backend logs: `docker-compose logs backend`
   - Verify database connection

### Performance Issues

1. **Slow queries**
   - Database indexes are created automatically
   - Consider MySQL query optimization

2. **High memory usage**
   - Adjust Docker memory limits if needed
   - Monitor with `docker stats`

## Customization

### Company Branding

Update company information in database:
```sql
UPDATE settings SET setting_value = 'Your Company Name' WHERE setting_key = 'company_name';
```

### Default Settings

Modify default values in `settings` table:
```sql
UPDATE settings SET setting_value = '12' WHERE setting_key = 'session_timeout';
```

### Additional Fields

Add custom fields to jobs or devices tables as needed for your business requirements.

## Support

For technical support:
1. Check logs first: `docker-compose logs`
2. Verify database connectivity
3. Check Nginx Proxy Manager configuration
4. Review this documentation

## Backup Strategy

Recommended backup approach:
1. **Database**: Daily automated MySQL dumps
2. **Application**: Docker image versioning
3. **Configuration**: Version control for docker-compose files
4. **Logs**: Log rotation and archival

## Scaling Considerations

For high-volume usage:
1. **Database**: Consider MySQL replication
2. **Application**: Multiple container instances
3. **Load Balancing**: Nginx upstream configuration
4. **Caching**: Redis for session management