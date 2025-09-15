@echo off
setlocal enabledelayedexpansion

REM IoT Device Certificate Generator Setup Script for Windows
REM This script helps set up the project for first-time use

echo === IoT Device Certificate Generator Setup ===
echo.

REM Check if Docker is installed
docker --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker is not installed. Please install Docker Desktop first.
    echo Visit: https://docs.docker.com/desktop/windows/
    pause
    exit /b 1
)

REM Check if Docker Compose is installed
docker-compose --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Docker Compose is not installed. Please install Docker Compose first.
    echo Visit: https://docs.docker.com/compose/install/
    pause
    exit /b 1
)

echo ✅ Docker and Docker Compose are installed
echo.

REM Create environment file from example
if not exist .env (
    if exist env.example (
        copy env.example .env >nul
        echo ✅ Created .env file from env.example
        echo 📝 Please review and update the .env file with your settings
    ) else (
        echo ❌ env.example file not found
        pause
        exit /b 1
    )
) else (
    echo ✅ .env file already exists
)

echo.

REM Create necessary directories
echo 📁 Creating necessary directories...
if not exist certs mkdir certs
if not exist certs_output mkdir certs_output
if not exist certs_output\devices mkdir certs_output\devices

echo ✅ Directories created
echo.

REM Check for Root CA certificates
echo 🔐 Checking for Root CA certificates...
if not exist "certs\ca.crt" (
    set MISSING_CA=1
) else if not exist "certs\ca.key" (
    set MISSING_CA=1
) else (
    set MISSING_CA=0
)

if !MISSING_CA!==1 (
    echo ⚠️  Root CA certificates not found!
    echo.
    echo You need to place the following files in the certs\ directory:
    echo   - ca.crt ^(Root CA Certificate^)
    echo   - ca.key ^(Root CA Private Key^)
    echo.
    echo If you don't have these files, you can generate them using OpenSSL:
    echo.
    echo # Generate Root CA private key
    echo openssl genrsa -out certs\ca.key 4096
    echo.
    echo # Generate Root CA certificate
    echo openssl req -new -x509 -days 3650 -key certs\ca.key -out certs\ca.crt -subj "/C=IN/ST=Gujarat/L=Vadodara/O=Prahari Technologies/OU=Prahari Technologies/CN=Prahari Root CA"
    echo.
    echo Please install OpenSSL for Windows or use an existing Root CA.
    echo After creating the certificates, run this setup script again.
    echo.
    pause
    exit /b 1
) else (
    echo ✅ Root CA certificates found
)

echo.

REM Build and start the application
echo 🚀 Building and starting the application...
echo This may take a few minutes for the first build...
echo.

docker-compose up --build -d

echo.
echo ⏳ Waiting for services to start...
timeout /t 30 /nobreak >nul

REM Check if services are running
docker-compose ps | findstr "Up" >nul
if errorlevel 1 (
    echo ❌ Some services failed to start. Check the logs:
    echo docker-compose logs
) else (
    echo ✅ Application started successfully!
    echo.
    echo 🌐 Access the application at: https://data.eknow.in
    echo.
    echo 🔑 Default login credentials:
    echo    Username: admin
    echo    Password: admin123
    echo.
    echo 📖 API Documentation: https://data.eknow.in/docs
    echo 🏥 Health Check: https://data.eknow.in/health
    echo.
    echo To stop the application: docker-compose down
    echo To view logs: docker-compose logs -f
    echo.
)

echo === Setup Complete ===
pause
