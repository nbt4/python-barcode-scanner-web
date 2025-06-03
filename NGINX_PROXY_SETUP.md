# Nginx Proxy Manager Setup for job.tsunamievents.de

## 1. Deploy the Application

Use the production docker-compose file that exposes ports instead of mapping them:

```bash
cd webapp
docker-compose -f docker-compose.prod.yml up --build -d
```

## 2. Nginx Proxy Manager Configuration

### Add Proxy Host in NPM Dashboard

1. **Domain Names**: `job.tsunamievents.de`
2. **Scheme**: `http`
3. **Forward Hostname/IP**: `barcodescanner-frontend` (container name)
4. **Forward Port**: `80`
5. **Cache Assets**: ✅ Enabled
6. **Block Common Exploits**: ✅ Enabled
7. **Websockets Support**: ✅ Enabled

### SSL Configuration

1. **SSL Certificate**: Request a new SSL certificate
2. **Force SSL**: ✅ Enabled
3. **HTTP/2 Support**: ✅ Enabled
4. **HSTS Enabled**: ✅ Enabled

### Advanced Configuration

Add this to the **Advanced** tab in NPM:

```nginx
# API Proxy Configuration
location /api/v1/ {
    proxy_pass http://barcodescanner-backend:5000/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
    proxy_set_header X-Forwarded-Host $host;
    
    # CORS headers
    add_header 'Access-Control-Allow-Origin' 'https://job.tsunamievents.de' always;
    add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
    add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
    add_header 'Access-Control-Allow-Credentials' 'true' always;
    
    # Handle preflight requests
    if ($request_method = 'OPTIONS') {
        add_header 'Access-Control-Allow-Origin' 'https://job.tsunamievents.de' always;
        add_header 'Access-Control-Allow-Methods' 'GET, POST, OPTIONS, PUT, DELETE' always;
        add_header 'Access-Control-Allow-Headers' 'DNT,User-Agent,X-Requested-With,If-Modified-Since,Cache-Control,Content-Type,Range,Authorization' always;
        add_header 'Access-Control-Max-Age' 1728000;
        add_header 'Content-Type' 'text/plain; charset=utf-8';
        add_header 'Content-Length' 0;
        return 204;
    }
}

# Health check endpoint
location /health {
    proxy_pass http://barcodescanner-backend:5000/health;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;
}

# Security headers
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header X-Content-Type-Options "nosniff" always;
add_header Referrer-Policy "no-referrer-when-downgrade" always;
add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;
```

## 3. DNS Configuration

Make sure your DNS points to your server:
```
job.tsunamievents.de A [YOUR_SERVER_IP]
```

## 4. Firewall Configuration

Ensure these ports are open on your server:
- Port 80 (HTTP)
- Port 443 (HTTPS)
- Port 22 (SSH)

## 5. Container Network

Make sure your containers are on the same network as NPM:
```bash
# Check if proxy network exists
docker network ls | grep proxy

# If not, create it
docker network create proxy

# Restart containers
docker-compose -f docker-compose.prod.yml down
docker-compose -f docker-compose.prod.yml up -d
```

## 6. Testing

1. **Health Check**: https://job.tsunamievents.de/health
2. **Frontend**: https://job.tsunamievents.de
3. **API**: https://job.tsunamievents.de/api/v1/

## 7. Troubleshooting

### Check Container Status
```bash
docker-compose -f docker-compose.prod.yml ps
```

### Check Logs
```bash
docker-compose -f docker-compose.prod.yml logs -f
```

### Check Network Connectivity
```bash
# From NPM container, test connectivity
docker exec -it nginx-proxy-manager-app-1 ping barcodescanner-frontend
docker exec -it nginx-proxy-manager-app-1 curl http://barcodescanner-frontend:80
```

### Common Issues

1. **502 Bad Gateway**: Container not reachable
   - Check if containers are on the same network
   - Verify container names match NPM configuration

2. **CORS Errors**: 
   - Ensure CORS_ORIGINS is set to your domain
   - Check Advanced nginx configuration in NPM

3. **SSL Issues**:
   - Verify domain DNS points to your server
   - Check if ports 80/443 are accessible from internet

## 8. Production Checklist

- [ ] Change JWT_SECRET_KEY in .env file
- [ ] Update database credentials if needed
- [ ] Set FLASK_DEBUG=false
- [ ] Configure proper CORS origins
- [ ] Set up SSL certificate
- [ ] Configure firewall rules
- [ ] Test all endpoints
- [ ] Set up monitoring/logging