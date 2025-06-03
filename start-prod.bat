@echo off
echo Starting Barcode Scanner Web Application in Production Mode...
echo.

echo Stopping any existing containers...
docker-compose -f docker-compose.prod.yml down

echo Building and starting containers for Nginx Proxy Manager...
docker-compose -f docker-compose.prod.yml up --build -d

echo.
echo Waiting for containers to start...
timeout /t 10 /nobreak > nul

echo.
echo Container status:
docker-compose -f docker-compose.prod.yml ps

echo.
echo Application should be available at:
echo Frontend: https://job.tsunamievents.de
echo Backend API: https://job.tsunamievents.de/api/v1
echo Health Check: https://job.tsunamievents.de/health
echo.
echo IMPORTANT: Configure Nginx Proxy Manager first!
echo See NGINX_PROXY_SETUP.md for detailed instructions.
echo.

echo To view logs, run: docker-compose -f docker-compose.prod.yml logs -f
echo To stop containers, run: docker-compose -f docker-compose.prod.yml down
pause