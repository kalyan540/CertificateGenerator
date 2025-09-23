#!/bin/bash

# Certificate Generator Deployment Script
# This script helps deploy the application with proper configuration

set -e

echo "🚀 Starting Certificate Generator Deployment..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "❌ .env file not found!"
    echo "📝 Please copy env.production to .env and update with your values:"
    echo "   cp env.production .env"
    echo "   nano .env  # Edit with your actual values"
    exit 1
fi

# Load environment variables
source .env

# Validate required environment variables
required_vars=("POSTGRES_PASSWORD" "JWT_SECRET_KEY" "DEFAULT_ADMIN_PASSWORD")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Required environment variable $var is not set in .env file"
        exit 1
    fi
done

echo "✅ Environment variables validated"

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p certs_output/devices
mkdir -p backups
mkdir -p nginx/ssl

# Set proper permissions
chmod 755 certs_output
chmod 755 certs_output/devices

echo "🔧 Building and starting services..."

# Stop existing containers
docker-compose -f docker-compose.deploy.yml down || true

# Build and start services
docker-compose -f docker-compose.deploy.yml up --build -d

echo "⏳ Waiting for services to be ready..."
sleep 30

# Check if services are running
echo "🔍 Checking service health..."

# Check nginx
if curl -f http://localhost/health > /dev/null 2>&1; then
    echo "✅ Nginx is healthy"
else
    echo "❌ Nginx health check failed"
    echo "📋 Checking nginx logs:"
    docker-compose -f docker-compose.deploy.yml logs nginx
fi

# Check backend
if curl -f http://localhost/api/health > /dev/null 2>&1; then
    echo "✅ Backend API is healthy"
else
    echo "❌ Backend API health check failed"
    echo "📋 Checking backend logs:"
    docker-compose -f docker-compose.deploy.yml logs backend
fi

echo ""
echo "🎉 Deployment completed!"
echo ""
echo "📋 Service Information:"
echo "   🌐 Frontend: http://localhost"
echo "   🔧 API: http://localhost/api"
echo "   📊 Health: http://localhost/health"
echo ""
echo "🔐 Default Admin Credentials:"
echo "   Username: ${DEFAULT_ADMIN_USERNAME:-admin}"
echo "   Password: ${DEFAULT_ADMIN_PASSWORD}"
echo ""
echo "📝 To view logs:"
echo "   docker-compose -f docker-compose.deploy.yml logs -f"
echo ""
echo "🛑 To stop services:"
echo "   docker-compose -f docker-compose.deploy.yml down"
echo ""

# Show running containers
echo "📦 Running containers:"
docker-compose -f docker-compose.deploy.yml ps
