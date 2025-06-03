# Multi-stage build for React frontend
FROM node:18-alpine AS builder

# Set working directory
WORKDIR /app

# Set build environment variables early
ENV NODE_OPTIONS="--max-old-space-size=2048"
ENV GENERATE_SOURCEMAP=false
ENV BABEL_ENV=production
ENV NODE_ENV=production
ENV CI=true
ENV DISABLE_ESLINT_PLUGIN=true

# Install dependencies first (for better caching)
COPY package*.json ./
RUN npm ci --only=production --silent

# Copy source and build
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=builder /app/build /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
