@echo off
echo 🚀 Deploying Barcode Scanner Production System
echo ==============================================

REM Check if database schema file exists
if not exist "database\schema.sql" (
    echo ❌ Error: database\schema.sql not found
    pause
    exit /b 1
)

REM Check if .env file exists
if not exist ".env" (
    echo ❌ Error: .env file not found
    pause
    exit /b 1
)

echo 📋 Pre-deployment checklist:
echo 1. Database schema file: ✅ Found
echo 2. Environment file: ✅ Found
echo.

REM Prompt for database setup
set /p db_setup="🗄️  Have you run the database schema on TS-Lager? (y/n): "
if not "%db_setup%"=="y" (
    echo.
    echo 📝 Please run the database schema first:
    echo    mysql -h tsunami-events.de -u root -p TS-Lager ^< database/schema.sql
    echo.
    echo    Or import database/schema.sql through phpMyAdmin
    echo.
    pause
)

echo.
echo 🐳 Starting Docker deployment...

REM Stop any existing containers
echo    Stopping existing containers...
docker-compose -f docker-compose.prod.yml down

REM Build and start production containers
echo    Building and starting production containers...
docker-compose -f docker-compose.prod.yml up --build -d

REM Wait for containers to start
echo    Waiting for containers to initialize...
timeout /t 15 /nobreak > nul

REM Check container status
echo.
echo 📊 Container Status:
docker-compose -f docker-compose.prod.yml ps

echo.
echo 🌐 Next Steps:
echo 1. Configure Nginx Proxy Manager:
echo    - Domain: job.tsunamievents.de
echo    - Forward to: barcodescanner-frontend-prod:80
echo    - Enable SSL certificate
echo.
echo 2. Test the application:
echo    - Access: https://job.tsunamievents.de
echo    - Login with your MySQL credentials
echo.
echo 3. Monitor logs:
echo    docker-compose -f docker-compose.prod.yml logs -f
echo.

REM Check if containers are running
docker-compose -f docker-compose.prod.yml ps | findstr "Up" > nul
if %errorlevel%==0 (
    echo ✅ Deployment completed successfully!
    echo.
    echo 📋 System Information:
    echo    - Frontend Container: barcodescanner-frontend-prod
    echo    - Backend Container: barcodescanner-backend-prod
    echo    - Database: tsunami-events.de/TS-Lager
    echo    - Authentication: MySQL credentials
    echo.
    echo 🔗 Access your application at: https://job.tsunamievents.de
) else (
    echo ❌ Deployment failed. Check logs:
    echo    docker-compose -f docker-compose.prod.yml logs
)

echo.
pause