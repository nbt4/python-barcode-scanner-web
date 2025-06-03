-- Barcode Scanner Production Database Schema
-- This file creates the required tables for the barcode scanner application

-- Use the TS-Lager database
USE `TS-Lager`;

-- Jobs table for managing work orders/events
CREATE TABLE IF NOT EXISTS `jobs` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `jobID` VARCHAR(50) UNIQUE NOT NULL,
    `kunde` VARCHAR(255) NOT NULL DEFAULT '',
    `title` VARCHAR(255) NOT NULL,
    `description` TEXT,
    `status` ENUM('pending', 'active', 'completed', 'cancelled') DEFAULT 'pending',
    `startDate` DATETIME NULL,
    `endDate` DATETIME NULL,
    `device_count` INT DEFAULT 0,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_status` (`status`),
    INDEX `idx_kunde` (`kunde`),
    INDEX `idx_created_at` (`created_at`),
    INDEX `idx_dates` (`startDate`, `endDate`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Devices table for equipment/inventory management
CREATE TABLE IF NOT EXISTS `devices` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `name` VARCHAR(255) NOT NULL,
    `type` VARCHAR(100) DEFAULT 'equipment',
    `barcode` VARCHAR(255) UNIQUE NOT NULL,
    `status` ENUM('available', 'in_use', 'maintenance', 'retired') DEFAULT 'available',
    `location` VARCHAR(255) DEFAULT '',
    `last_scan` TIMESTAMP NULL,
    `created_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX `idx_barcode` (`barcode`),
    INDEX `idx_status` (`status`),
    INDEX `idx_type` (`type`),
    INDEX `idx_location` (`location`),
    INDEX `idx_last_scan` (`last_scan`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Scans table for tracking barcode scan history
CREATE TABLE IF NOT EXISTS `scans` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `device_id` INT NULL,
    `job_id` INT NULL,
    `barcode` VARCHAR(255) NOT NULL,
    `scanned_by` VARCHAR(255) DEFAULT '',
    `scan_timestamp` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `location` VARCHAR(255) DEFAULT '',
    `notes` TEXT,
    FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE SET NULL,
    FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE SET NULL,
    INDEX `idx_device_id` (`device_id`),
    INDEX `idx_job_id` (`job_id`),
    INDEX `idx_barcode` (`barcode`),
    INDEX `idx_scan_timestamp` (`scan_timestamp`),
    INDEX `idx_scanned_by` (`scanned_by`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Job-Device assignments (many-to-many relationship)
CREATE TABLE IF NOT EXISTS `job_devices` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `job_id` INT NOT NULL,
    `device_id` INT NOT NULL,
    `assigned_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `returned_at` TIMESTAMP NULL,
    `status` ENUM('assigned', 'returned', 'missing') DEFAULT 'assigned',
    `notes` TEXT,
    FOREIGN KEY (`job_id`) REFERENCES `jobs`(`id`) ON DELETE CASCADE,
    FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE CASCADE,
    UNIQUE KEY `unique_job_device` (`job_id`, `device_id`),
    INDEX `idx_job_id` (`job_id`),
    INDEX `idx_device_id` (`device_id`),
    INDEX `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Device maintenance log
CREATE TABLE IF NOT EXISTS `maintenance_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `device_id` INT NOT NULL,
    `maintenance_type` ENUM('repair', 'service', 'inspection', 'calibration') NOT NULL,
    `description` TEXT NOT NULL,
    `performed_by` VARCHAR(255) NOT NULL,
    `performed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    `cost` DECIMAL(10,2) DEFAULT 0.00,
    `status` ENUM('scheduled', 'in_progress', 'completed', 'cancelled') DEFAULT 'completed',
    `next_maintenance` DATE NULL,
    FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE CASCADE,
    INDEX `idx_device_id` (`device_id`),
    INDEX `idx_performed_at` (`performed_at`),
    INDEX `idx_status` (`status`),
    INDEX `idx_next_maintenance` (`next_maintenance`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- System settings/configuration
CREATE TABLE IF NOT EXISTS `settings` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `setting_key` VARCHAR(100) UNIQUE NOT NULL,
    `setting_value` TEXT,
    `description` TEXT,
    `updated_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `updated_by` VARCHAR(255),
    INDEX `idx_setting_key` (`setting_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Insert default settings
INSERT IGNORE INTO `settings` (`setting_key`, `setting_value`, `description`) VALUES
('app_name', 'Barcode Scanner System', 'Application name'),
('company_name', 'Tsunami Events', 'Company name'),
('default_job_status', 'pending', 'Default status for new jobs'),
('default_device_status', 'available', 'Default status for new devices'),
('session_timeout', '8', 'Session timeout in hours'),
('max_scan_history', '1000', 'Maximum number of scan records to keep per device');

-- Create views for common queries
CREATE OR REPLACE VIEW `active_jobs_view` AS
SELECT 
    j.*,
    COUNT(jd.device_id) as assigned_devices,
    GROUP_CONCAT(d.name SEPARATOR ', ') as device_names
FROM jobs j
LEFT JOIN job_devices jd ON j.id = jd.job_id AND jd.status = 'assigned'
LEFT JOIN devices d ON jd.device_id = d.id
WHERE j.status IN ('pending', 'active')
GROUP BY j.id;

CREATE OR REPLACE VIEW `device_status_view` AS
SELECT 
    d.*,
    COALESCE(j.jobID, '') as current_job,
    COALESCE(j.kunde, '') as current_customer,
    s.last_scan_time,
    s.scan_count_today
FROM devices d
LEFT JOIN job_devices jd ON d.id = jd.device_id AND jd.status = 'assigned'
LEFT JOIN jobs j ON jd.job_id = j.id
LEFT JOIN (
    SELECT 
        device_id,
        MAX(scan_timestamp) as last_scan_time,
        COUNT(CASE WHEN DATE(scan_timestamp) = CURDATE() THEN 1 END) as scan_count_today
    FROM scans 
    GROUP BY device_id
) s ON d.id = s.device_id;

-- Create stored procedures for common operations
DELIMITER //

CREATE PROCEDURE IF NOT EXISTS `AssignDeviceToJob`(
    IN p_job_id INT,
    IN p_device_id INT,
    IN p_assigned_by VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Check if device is available
    IF (SELECT status FROM devices WHERE id = p_device_id) != 'available' THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Device is not available for assignment';
    END IF;
    
    -- Assign device to job
    INSERT INTO job_devices (job_id, device_id, notes) 
    VALUES (p_job_id, p_device_id, CONCAT('Assigned by ', p_assigned_by));
    
    -- Update device status
    UPDATE devices SET status = 'in_use' WHERE id = p_device_id;
    
    -- Update job device count
    UPDATE jobs SET device_count = (
        SELECT COUNT(*) FROM job_devices WHERE job_id = p_job_id AND status = 'assigned'
    ) WHERE id = p_job_id;
    
    COMMIT;
END //

CREATE PROCEDURE IF NOT EXISTS `ReturnDeviceFromJob`(
    IN p_job_id INT,
    IN p_device_id INT,
    IN p_returned_by VARCHAR(255)
)
BEGIN
    DECLARE EXIT HANDLER FOR SQLEXCEPTION
    BEGIN
        ROLLBACK;
        RESIGNAL;
    END;
    
    START TRANSACTION;
    
    -- Mark device as returned
    UPDATE job_devices 
    SET status = 'returned', 
        returned_at = NOW(),
        notes = CONCAT(COALESCE(notes, ''), ' - Returned by ', p_returned_by)
    WHERE job_id = p_job_id AND device_id = p_device_id;
    
    -- Update device status
    UPDATE devices SET status = 'available' WHERE id = p_device_id;
    
    -- Update job device count
    UPDATE jobs SET device_count = (
        SELECT COUNT(*) FROM job_devices WHERE job_id = p_job_id AND status = 'assigned'
    ) WHERE id = p_job_id;
    
    COMMIT;
END //

DELIMITER ;

-- Create triggers for audit logging
CREATE TABLE IF NOT EXISTS `audit_log` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `table_name` VARCHAR(100) NOT NULL,
    `record_id` INT NOT NULL,
    `action` ENUM('INSERT', 'UPDATE', 'DELETE') NOT NULL,
    `old_values` JSON NULL,
    `new_values` JSON NULL,
    `changed_by` VARCHAR(255),
    `changed_at` TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX `idx_table_record` (`table_name`, `record_id`),
    INDEX `idx_changed_at` (`changed_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Sample data for testing (optional - remove in production)
-- Uncomment the following lines if you want sample data

/*
-- Sample jobs
INSERT IGNORE INTO jobs (jobID, kunde, title, description, status, startDate, endDate, device_count) VALUES
('JOB20240101001', 'Tsunami Events GmbH', 'Corporate Event Setup', 'Audio and lighting setup for annual company meeting', 'active', '2024-02-01 09:00:00', '2024-02-01 18:00:00', 0),
('JOB20240102001', 'Tech Conference Ltd', 'Conference AV Support', 'Full AV support for 3-day technology conference', 'pending', '2024-02-15 08:00:00', '2024-02-17 20:00:00', 0),
('JOB20240103001', 'Wedding Planners Inc', 'Wedding Reception', 'Sound system and lighting for wedding reception', 'completed', '2024-01-20 16:00:00', '2024-01-21 02:00:00', 0);

-- Sample devices
INSERT IGNORE INTO devices (name, type, barcode, status, location) VALUES
('Audio Mixer XM-2000', 'audio', 'AUD001234567', 'available', 'Warehouse A - Shelf 1'),
('LED Light Panel Pro', 'lighting', 'LED987654321', 'available', 'Warehouse A - Shelf 2'),
('Wireless Microphone Set', 'audio', 'MIC456789012', 'maintenance', 'Repair Shop'),
('Projector 4K Ultra', 'video', 'PROJ123456789', 'available', 'Warehouse B - Shelf 1'),
('Speaker System 5.1', 'audio', 'SPK111222333', 'available', 'Warehouse A - Shelf 3');
*/

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON TS-Lager.* TO 'your_app_user'@'%';
-- FLUSH PRIVILEGES;

-- Display table creation summary
SELECT 
    'Database schema created successfully' as Status,
    COUNT(*) as Tables_Created
FROM information_schema.tables 
WHERE table_schema = 'TS-Lager' 
AND table_name IN ('jobs', 'devices', 'scans', 'job_devices', 'maintenance_log', 'settings', 'audit_log');