#!/bin/bash

# Script to generate sample Root CA for testing
# Use this only for development/testing purposes

set -e

echo "=== Generating Sample Root CA for Testing ==="
echo "⚠️  This is for TESTING ONLY - Do not use in production!"
echo

# Create certs directory if it doesn't exist
mkdir -p certs

# Check if CA files already exist
if [ -f "certs/ca.crt" ] && [ -f "certs/ca.key" ]; then
    echo "Root CA files already exist!"
    read -p "Do you want to overwrite them? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        echo "Aborted."
        exit 1
    fi
fi

# Generate Root CA private key
echo "Step 1: Generating Root CA private key (4096 bits)..."
openssl genrsa -out certs/ca.key 4096

# Generate Root CA certificate
echo "Step 2: Generating Root CA certificate (valid for 10 years)..."
openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt \
    -subj "/C=IN/ST=Gujarat/L=Vadodara/O=Prahari Technologies/OU=Prahari Technologies/CN=Prahari Root CA"

# Set proper permissions
echo "Step 3: Setting proper permissions..."
chmod 600 certs/ca.key
chmod 644 certs/ca.crt

echo ""
echo "=== Root CA Generation Complete ==="
echo "Files created:"
echo "  - Root CA Certificate: certs/ca.crt"
echo "  - Root CA Private Key: certs/ca.key"
echo ""
echo "Certificate Information:"
openssl x509 -in certs/ca.crt -text -noout | grep -E "(Subject:|Not Before|Not After)"
echo ""
echo "✅ Ready to generate device certificates!"
echo "Now you can run: docker-compose up --build"
