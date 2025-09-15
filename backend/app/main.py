from fastapi import FastAPI, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from datetime import datetime
import os
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from .database import engine, get_db
from .models import Base
from .auth import create_default_admin_user
from .routers import auth, devices
from .schemas import HealthResponse
from .config import settings

# Create database tables safely
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Database tables might already exist: {e}")

# Create rate limiter
limiter = Limiter(key_func=get_remote_address)

# Create FastAPI app
app = FastAPI(
    title="IoT Device Certificate Generator",
    description="Generate and manage IoT device certificates with FastAPI",
    version="1.0.0",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5001", "http://localhost:5003", "https://api.eknow.in"],  # React development server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(devices.router)


@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    # Create default admin user
    db = next(get_db())
    try:
        create_default_admin_user(db)
        print("Application startup completed successfully")
    except Exception as e:
        print(f"Startup error: {e}")
    finally:
        db.close()
    
    # Create output directories
    os.makedirs(settings.certs_output_dir, exist_ok=True)
    os.makedirs(os.path.join(settings.certs_output_dir, "devices"), exist_ok=True)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow()
    )


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": "IoT Device Certificate Generator API",
        "version": "1.0.0",
        "docs": "/docs" if settings.debug else "Documentation disabled in production",
        "health": "/health"
    }


@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom 404 handler"""
    return JSONResponse(
        status_code=404,
        content={
            "message": "Endpoint not found",
            "path": str(request.url.path)
        }
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=5003,
        reload=settings.debug
    )
