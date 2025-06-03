# Database Setup Guide

## Current Status: Mock Mode

The application is currently running in **mock mode** with sample data because the database connection is not available. This allows you to test the application functionality without setting up a database.

## Mock Data Available

### Jobs
- 4 sample jobs with different statuses (active, pending, completed)
- Realistic event management scenarios
- Proper date ranges and customer information

### Devices
- 4 sample devices (audio, lighting, video equipment)
- Different statuses (available, in_use, maintenance)
- Barcode scanning simulation

### Reports
- Summary statistics
- Daily activity reports
- Device usage reports

## Setting Up Real Database

### Option 1: Use Existing Database (Recommended)

Your docker-compose.yml is already configured to connect to:
- Host: `tsunami-events.de`
- Database: `TS-Lager`
- User: `root`

**Required Tables:**

```sql
-- Jobs table
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    jobID VARCHAR(50) UNIQUE,
    kunde VARCHAR(255),
    title VARCHAR(255),
    description TEXT,
    status ENUM('pending', 'active', 'completed', 'cancelled') DEFAULT 'pending',
    startDate DATETIME,
    endDate DATETIME,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    device_count INT DEFAULT 0
);

-- Devices table
CREATE TABLE devices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    type VARCHAR(100),
    barcode VARCHAR(255) UNIQUE,
    status ENUM('available', 'in_use', 'maintenance', 'retired') DEFAULT 'available',
    location VARCHAR(255),
    last_scan TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- Scans table (for tracking barcode scans)
CREATE TABLE scans (
    id INT AUTO_INCREMENT PRIMARY KEY,
    device_id INT,
    job_id INT,
    barcode VARCHAR(255),
    scanned_by VARCHAR(255),
    scan_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    location VARCHAR(255),
    notes TEXT,
    FOREIGN KEY (device_id) REFERENCES devices(id),
    FOREIGN KEY (job_id) REFERENCES jobs(id)
);
```

### Option 2: Local MySQL with Docker

Add MySQL to your docker-compose.yml:

```yaml
services:
  mysql:
    image: mysql:8.0
    container_name: barcodescanner-mysql
    environment:
      MYSQL_ROOT_PASSWORD: rootpassword
      MYSQL_DATABASE: barcodescanner
      MYSQL_USER: app
      MYSQL_PASSWORD: apppassword
    ports:
      - "3306:3306"
    volumes:
      - mysql_data:/var/lib/mysql
      - ./database/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - app-network

volumes:
  mysql_data:
```

Then update backend environment:
```yaml
environment:
  - MYSQL_HOST=mysql
  - MYSQL_USER=app
  - MYSQL_PASSWORD=apppassword
  - MYSQL_DATABASE=barcodescanner
```

## Testing Database Connection

### Check Connection Status
```bash
# Check if app is using database or mock mode
curl http://localhost:5000/api/v1/jobs/status
```

Response will show:
- `"mode": "production"` - Database connected
- `"mode": "mock"` - Using mock data

### Backend Logs
```bash
docker-compose logs -f backend
```

Look for:
- `"Using mock data for jobs"` - Mock mode active
- `"Database connection failed"` - Connection issues

## Switching from Mock to Database

1. **Ensure database is accessible**
2. **Create required tables** (see SQL above)
3. **Restart containers**:
```bash
docker-compose down
docker-compose up -d
```

4. **Verify connection**:
```bash
curl http://localhost:5000/api/v1/jobs/status
```

## Populating Database with Sample Data

```sql
-- Insert sample jobs
INSERT INTO jobs (jobID, kunde, title, description, status, startDate, endDate, device_count) VALUES
('JOB001', 'Tsunami Events GmbH', 'Event Equipment Setup', 'Setup audio and lighting equipment for corporate event', 'active', '2024-01-15 09:00:00', '2024-01-18 18:00:00', 15),
('JOB002', 'Tech Conference Ltd', 'Conference AV Support', 'Audio visual support for 3-day tech conference', 'pending', '2024-01-25 08:00:00', '2024-01-28 20:00:00', 25),
('JOB003', 'Wedding Planners Inc', 'Wedding Reception', 'Sound system and lighting for wedding reception', 'completed', '2024-01-05 16:00:00', '2024-01-06 02:00:00', 8);

-- Insert sample devices
INSERT INTO devices (name, type, barcode, status, location) VALUES
('Audio Mixer XM-2000', 'audio', 'AUD001234567', 'available', 'Warehouse A'),
('LED Light Panel Pro', 'lighting', 'LED987654321', 'in_use', 'Event Site B'),
('Wireless Microphone Set', 'audio', 'MIC456789012', 'maintenance', 'Repair Shop'),
('Projector 4K Ultra', 'video', 'PROJ123456789', 'available', 'Warehouse A');
```

## Troubleshooting

### "Jobs couldn't be loaded" Error
1. **Check backend logs**: `docker-compose logs backend`
2. **Verify database connection**: Check if `tsunami-events.de` is accessible
3. **Test API directly**: `curl http://localhost:5000/api/v1/jobs`

### Database Connection Issues
- Verify host/credentials in docker-compose.yml
- Check if database server is running
- Ensure firewall allows connection
- Test connection from container:
```bash
docker exec -it barcodescanner-backend bash
mysql -h tsunami-events.de -u root -p TS-Lager
```

### Mock Mode Stuck
- Check backend logs for connection errors
- Restart containers: `docker-compose restart`
- Verify environment variables are set correctly

## Production Considerations

1. **Security**: Use environment variables for database credentials
2. **Backup**: Regular database backups
3. **Monitoring**: Database connection monitoring
4. **Performance**: Index frequently queried columns
5. **Scaling**: Consider connection pooling for high load