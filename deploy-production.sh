#!/bin/bash

echo "🚀 Deploying Barcode Scanner Production System"
echo "=============================================="

# Check if database schema file exists
if [ ! -f "database/schema.sql" ]; then
    echo "❌ Error: database/schema.sql not found"
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found"
    exit 1
fi

echo "📋 Pre-deployment checklist:"
echo "1. Database schema file: ✅ Found"
echo "2. Environment file: ✅ Found"
echo ""

# Prompt for database setup
read -p "🗄️  Have you run the database schema on TS-Lager? (y/n): " db_setup
if [ "$db_setup" != "y" ]; then
    echo ""
    echo "📝 Please run the database schema first:"
    echo "   mysql -h tsunami-events.de -u root -p TS-Lager < database/schema.sql"
    echo ""
    echo "   Or import database/schema.sql through phpMyAdmin"
    echo ""
    read -p "Press Enter when database setup is complete..."
fi

# Prompt for JWT secret
echo ""
echo "🔐 Security Check:"
grep -q "change-this-in-production" .env
if [ $? -eq 0 ]; then
    echo "⚠️  WARNING: Default JWT secret detected in .env file"
    read -p "   Do you want to generate a new secure JWT secret? (y/n): " gen_secret
    if [ "$gen_secret" = "y" ]; then
        new_secret="TsunamiEvents2024-$(openssl rand -hex 32)"
        sed -i "s/JWT_SECRET_KEY=.*/JWT_SECRET_KEY=$new_secret/" .env
        echo "   ✅ New JWT secret generated"
    fi
fi

echo ""
echo "🐳 Starting Docker deployment..."

# Stop any existing containers
echo "   Stopping existing containers..."
docker-compose -f docker-compose.prod.yml down

# Build and start production containers
echo "   Building and starting production containers..."
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for containers to start
echo "   Waiting for containers to initialize..."
sleep 15

# Check container status
echo ""
echo "📊 Container Status:"
docker-compose -f docker-compose.prod.yml ps

# Test health endpoints
echo ""
echo "🏥 Health Checks:"

# Test backend health
if curl -s -f http://localhost:5000/health > /dev/null 2>&1; then
    echo "   Backend: ✅ Healthy"
else
    echo "   Backend: ❌ Not responding"
fi

# Test database connection
if curl -s -f http://localhost:5000/api/v1/jobs/stats > /dev/null 2>&1; then
    echo "   Database: ✅ Connected"
else
    echo "   Database: ❌ Connection failed"
fi

echo ""
echo "🌐 Next Steps:"
echo "1. Configure Nginx Proxy Manager:"
echo "   - Domain: job.tsunamievents.de"
echo "   - Forward to: barcodescanner-frontend-prod:80"
echo "   - Enable SSL certificate"
echo ""
echo "2. Test the application:"
echo "   - Access: https://job.tsunamievents.de"
echo "   - Login with your MySQL credentials"
echo ""
echo "3. Monitor logs:"
echo "   docker-compose -f docker-compose.prod.yml logs -f"
echo ""

# Show final status
if docker-compose -f docker-compose.prod.yml ps | grep -q "Up"; then
    echo "✅ Deployment completed successfully!"
    echo ""
    echo "📋 System Information:"
    echo "   - Frontend Container: barcodescanner-frontend-prod"
    echo "   - Backend Container: barcodescanner-backend-prod"
    echo "   - Database: tsunami-events.de/TS-Lager"
    echo "   - Authentication: MySQL credentials"
    echo ""
    echo "🔗 Access your application at: https://job.tsunamievents.de"
else
    echo "❌ Deployment failed. Check logs:"
    echo "   docker-compose -f docker-compose.prod.yml logs"
fi