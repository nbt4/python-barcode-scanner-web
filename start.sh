#!/bin/bash

echo "Starting Barcode Scanner Web Application..."
echo

echo "Stopping any existing containers..."
docker-compose down

echo "Building and starting containers..."
docker-compose up --build -d

echo
echo "Waiting for containers to start..."
sleep 10

echo
echo "Container status:"
docker-compose ps

echo
echo "Application should be available at:"
echo "Frontend: http://localhost:3000"
echo "Backend API: http://localhost:5000"
echo "Health Check: http://localhost:5000/health"
echo

echo "To view logs, run: docker-compose logs -f"
echo "To stop containers, run: docker-compose down"