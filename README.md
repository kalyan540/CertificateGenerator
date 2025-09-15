# IoT Device Certificate Generator

A full-stack application for generating and managing IoT device certificates using FastAPI, React, PostgreSQL, and Docker.

## Features

- **Authentication**: JWT-based login system
- **Certificate Generation**: Generate unique device certificates using Root CA
- **Device Management**: View, download, and manage generated certificates
- **Modern UI**: React with Tailwind CSS for responsive design
- **Containerized**: Complete Docker setup for easy deployment

## Project Structure

```
CertificateGenerator/
├── backend/                 # FastAPI backend
├── frontend/               # React frontend
├── certs/                  # Root CA certificates (input)
├── certs_output/          # Generated device certificates (output)
├── docker-compose.yml     # Docker services configuration
└── env.example           # Environment variables template
```

## Quick Start

### Option 1: Automated Setup (Recommended)

**For Windows:**
```cmd
setup.bat
```

**For Linux/Mac:**
```bash
chmod +x setup.sh
./setup.sh
```

### Option 2: Manual Setup

1. **Prepare Environment**:
   ```bash
   cp env.example .env
   ```

2. **Generate Root CA** (if you don't have one):
   ```bash
   # For Linux/Mac
   chmod +x generate-sample-ca.sh
   ./generate-sample-ca.sh
   
   # Or manually
   mkdir -p certs
   openssl genrsa -out certs/ca.key 4096
   openssl req -new -x509 -days 3650 -key certs/ca.key -out certs/ca.crt \
     -subj "/C=IN/ST=Gujarat/L=Vadodara/O=Prahari Technologies/OU=Prahari Technologies/CN=Prahari Root CA"
   ```

3. **Build and Run**:
   ```bash
   docker-compose up --build
   ```

4. **Access Application**: Open http://localhost:3000

## Default Credentials

- **Username**: admin
- **Password**: admin123

## Security Notes

- Change the default JWT secret in production
- Update default admin credentials
- Ensure proper file permissions for certificate directories
- Use HTTPS in production environment

## Development

### Local Development Setup

1. **Backend** (Python 3.9+):
   ```bash
   cd backend
   pip install -r requirements.txt
   uvicorn app.main:app --reload --host 0.0.0.0 --port 3001
   ```

2. **Frontend** (Node.js 16+):
   ```bash
   cd frontend
   npm install
   npm start
   ```

3. **Database**:
   ```bash
   docker run -p 5432:5432 -e POSTGRES_DB=certificate_generator -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres postgres:15
   ```

## API Endpoints

- `POST /auth/login` - User authentication
- `POST /devices/create` - Generate device certificate
- `GET /devices` - List all devices
- `GET /devices/{id}/download` - Download certificate zip
- `GET /devices/{id}/view` - View certificate text
- `GET /health` - Health check

## Certificate Generation

The application generates the following files for each device:
- Device private key (`.key`)
- Device certificate (`.crt`)
- Certificate bundle (`.bundle.crt`)
- Compressed zip file for download

## Production Deployment

1. Update environment variables in `.env`
2. Use proper SSL certificates
3. Configure reverse proxy (nginx/traefik)
4. Set up proper backup for PostgreSQL
5. Monitor logs and health endpoints

## Troubleshooting

### Common Issues

1. **Port conflicts**: If ports 3000, 3001, or 5432 are in use:
   ```bash
   # Check what's using the ports
   netstat -an | findstr "3000\|3001\|5432"  # Windows
   lsof -i :3000,3001,5432                   # Linux/Mac
   ```

2. **Docker issues**:
   ```bash
   # Restart Docker services
   docker-compose down
   docker-compose up --build
   
   # Clean up Docker resources
   docker system prune
   ```

3. **Certificate generation fails**:
   - Ensure OpenSSL is installed
   - Check that `certs/ca.crt` and `certs/ca.key` exist
   - Verify file permissions (ca.key should be 600)

4. **Frontend can't connect to backend**:
   - Check if backend is running: `curl http://localhost:3001/health`
   - Verify CORS settings in backend
   - Check browser console for errors

### Logs

```bash
# View all logs
docker-compose logs

# View specific service logs
docker-compose logs backend
docker-compose logs frontend
docker-compose logs db

# Follow logs in real-time
docker-compose logs -f
```

### Development Mode

For development with hot reload:

```bash
# Backend only
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 3001

# Frontend only
cd frontend
npm install
npm start
```
