#!/bin/bash

# IoT Device Certificate Generator Setup Script
# This script helps set up the project for first-time use

set -e

echo "=== IoT Device Certificate Generator Setup ==="
echo

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "❌ Docker is not installed. Please install Docker first."
    echo "Visit: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install Docker Compose first."
    echo "Visit: https://docs.docker.com/compose/install/"
    exit 1
fi

echo "✅ Docker and Docker Compose are installed"
echo

# Create environment file from example
if [ ! -f .env ]; then
    if [ -f env.example ]; then
        cp env.example .env
        echo "✅ Created .env file from env.example"
        echo "📝 Please review and update the .env file with your settings"
    else
        echo "❌ env.example file not found"
        exit 1
    fi
else
    echo "✅ .env file already exists"
fi

echo

# Create necessary directories
echo "📁 Creating necessary directories..."
mkdir -p certs
mkdir -p certs_output
mkdir -p certs_output/devices

echo "✅ Directories created"
echo

# Check for Root CA certificates
echo "🔐 Checking for Root CA certificates..."
if [ ! -f "certs/ca.crt" ] || [ ! -f "certs/ca.key" ]; then
    echo "⚠️  Root CA certificates not found!"
    echo
    echo "You need to place the following files in the certs/ directory:"
    echo "  - ca.crt (Root CA Certificate)"
    echo "  - ca.key (Root CA Private Key)"
    echo
    echo "If you don't have these files, you can generate them using:"
    echo
    echo "# Generate Root CA private key"
    echo "openssl genrsa -out certs/ca.key 4096"
    echo
    echo "# Generate Root CA certificate"
    echo 'openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt -subj "/C=IN/ST=Gujarat/L=Vadodara/O=Prahari Technologies/OU=Prahari Technologies/CN=Prahari Root CA"'
    echo
    echo "After creating the certificates, run this setup script again."
    echo
    read -p "Do you want to generate Root CA certificates now? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "🔑 Generating Root CA certificates..."
        
        # Generate Root CA private key
        openssl genrsa -out certs/ca.key 4096
        
        # Generate Root CA certificate
        openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt -subj "/C=IN/ST=Gujarat/L=Vadodara/O=Prahari Technologies/OU=Prahari Technologies/CN=Prahari Root CA"
        
        # Set proper permissions
        chmod 600 certs/ca.key
        chmod 644 certs/ca.crt
        
        echo "✅ Root CA certificates generated successfully!"
        echo "   - Private Key: certs/ca.key (keep secure!)"
        echo "   - Certificate: certs/ca.crt"
    else
        echo "Please create the Root CA certificates manually and run this script again."
        exit 1
    fi
else
    echo "✅ Root CA certificates found"
fi

echo

# Set proper permissions for certificate directories
echo "🔒 Setting proper permissions..."
chmod 755 certs
chmod 755 certs_output
chmod 755 certs_output/devices

if [ -f "certs/ca.key" ]; then
    chmod 600 certs/ca.key
fi

if [ -f "certs/ca.crt" ]; then
    chmod 644 certs/ca.crt
fi

echo "✅ Permissions set correctly"
echo

# Build and start the application
echo "🚀 Building and starting the application..."
echo "This may take a few minutes for the first build..."
echo

docker-compose up --build -d

echo
echo "⏳ Waiting for services to start..."
sleep 30

# Check if services are running
if docker-compose ps | grep -q "Up"; then
    echo "✅ Application started successfully!"
    echo
    echo "🌐 Access the application at: http://localhost:5003"
    echo
    echo "🔑 Default login credentials:"
    echo "   Username: admin"
    echo "   Password: admin123"
    echo
    echo "📖 API Documentation: http://localhost:5003/docs"
    echo "🏥 Health Check: http://localhost:5003/health"
    echo
    echo "To stop the application: docker-compose down"
    echo "To view logs: docker-compose logs -f"
    echo
else
    echo "❌ Some services failed to start. Check the logs:"
    echo "docker-compose logs"
fi

echo "=== Setup Complete ==="
