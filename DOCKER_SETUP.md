# Docker Setup Instructions

## Issues Fixed

1. **Port Mapping**: Changed from `expose` to `ports` in docker-compose.yml to make services accessible from host
2. **Nginx Configuration**: Fixed syntax error in nginx.conf (missing closing brace)
3. **Missing Routes**: Created all required Flask route files (auth, jobs, devices, reports, health)
4. **Port Conflicts**: Changed frontend port from 80 to 3000 to avoid conflicts
5. **Environment Variables**: Added .env file for JWT secret
6. **Build Optimization**: Optimized Dockerfiles and added .dockerignore files

## Build Time Information

**First Build**: 200+ seconds is normal due to:
- React frontend with many dependencies (Material-UI, etc.)
- Node.js package installation
- Python package compilation

**Subsequent Builds**: Much faster (~30-60 seconds) due to Docker layer caching

## Quick Start

### Production Build (Optimized)
```bash
cd webapp
docker-compose up --build -d
```

### Development Build (Faster, with hot reload)
```bash
cd webapp
docker-compose -f docker-compose.dev.yml up --build -d
```

### Windows
```cmd
cd webapp
start.bat
```

### Linux/Mac
```bash
cd webapp
chmod +x start.sh
./start.sh
```

## Build Optimization Tips

1. **Use Docker BuildKit** (faster builds):
```bash
export DOCKER_BUILDKIT=1
docker-compose up --build -d
```

2. **Parallel builds**:
```bash
docker-compose up --build -d --parallel
```

3. **Clean build cache** (if builds are failing):
```bash
docker system prune -a
docker-compose up --build -d
```

## Access Points

- **Frontend**: http://localhost:3000
- **Backend API**: http://localhost:5000
- **Health Check**: http://localhost:5000/health

## Troubleshooting

### Check Container Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f frontend
docker-compose logs -f backend
```

### Stop Containers
```bash
docker-compose down
```

### Rebuild Containers
```bash
docker-compose down
docker-compose up --build -d
```

## For External Server Deployment

1. **Update Environment Variables**: Modify the database connection settings in docker-compose.yml
2. **Security**: Change the JWT_SECRET_KEY in .env file
3. **Firewall**: Ensure ports 3000 and 5000 are open on your external server
4. **Domain/IP**: Update any hardcoded localhost references to your server's IP/domain

## Network Configuration

The containers use these networks:
- `app-network`: Internal communication between frontend and backend
- `mysql`: External network for database connection
- `proxy`: External network for reverse proxy (if used)

Make sure these external networks exist on your server or remove them from docker-compose.yml if not needed.