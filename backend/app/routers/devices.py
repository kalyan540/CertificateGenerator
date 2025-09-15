from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
from pathlib import Path
import os
from slowapi import Limiter
from slowapi.util import get_remote_address
from ..database import get_db
from ..auth import get_current_user, verify_password
from ..models import User, Device
from ..schemas import DeviceCreate, DeviceResponse, DeviceCreateResponse, DeviceCertResponse
from ..cert_generator import cert_generator

router = APIRouter(prefix="/devices", tags=["devices"])

# Rate limiter - 10 certificate generations per minute per user
limiter = Limiter(key_func=get_remote_address)

@router.post("/create", response_model=DeviceCreateResponse)
@limiter.limit("10/minute")
async def create_device_certificate(
    request: Request,
    device_data: DeviceCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate a new device certificate
    """
    # Check if device name already exists
    existing_device = db.query(Device).filter(Device.name == device_data.name).first()
    if existing_device:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with name '{device_data.name}' already exists"
        )
    
    try:
        # Generate certificate
        cert_result = cert_generator.generate_device_certificate(device_data.name)
        
        # Create device record in database
        new_device = Device(
            name=device_data.name,
            cert_text=cert_result["cert_content"],
            zip_path=cert_result["zip_path"]
        )
        
        db.add(new_device)
        db.commit()
        db.refresh(new_device)
        
        return DeviceCreateResponse(
            device=DeviceResponse.from_orm(new_device),
            cert_text=cert_result["cert_content"],
            message=f"Certificate generated successfully for device '{device_data.name}'"
        )
        
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with name '{device_data.name}' already exists"
        )
    except FileNotFoundError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Certificate generation failed: {str(e)}"
        )
    except RuntimeError as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Certificate generation failed: {str(e)}"
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {str(e)}"
        )


@router.get("/", response_model=List[DeviceResponse])
async def list_devices(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get list of all devices
    """
    devices = db.query(Device).order_by(Device.created_at.desc()).all()
    return [DeviceResponse.from_orm(device) for device in devices]


@router.get("/{device_id}/view", response_model=DeviceCertResponse)
async def view_device_certificate(
    device_id: str,
    cert_type: str = "device_cert",  # device_cert, ca_cert, private_key, bundle
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    View device certificate files (device cert, CA cert, private key, or bundle)
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    try:
        if cert_type == "device_cert":
            return DeviceCertResponse(
                cert_text=device.cert_text,
                device_name=device.name
            )
        
        # Get file paths
        device_dir = Path(cert_generator.output_dir) / "devices"
        ca_crt_path = Path(cert_generator.certs_dir) / "ca.crt"
        device_key_path = device_dir / f"{device.name}.key"
        device_bundle_path = device_dir / f"{device.name}.bundle.crt"
        
        if cert_type == "ca_cert":
            if ca_crt_path.exists():
                with open(ca_crt_path, 'r') as f:
                    cert_content = f.read()
                return DeviceCertResponse(
                    cert_text=cert_content,
                    device_name=f"CA Certificate"
                )
        
        elif cert_type == "private_key":
            if device_key_path.exists():
                with open(device_key_path, 'r') as f:
                    key_content = f.read()
                return DeviceCertResponse(
                    cert_text=key_content,
                    device_name=f"{device.name} - Private Key"
                )
        
        elif cert_type == "bundle":
            if device_bundle_path.exists():
                with open(device_bundle_path, 'r') as f:
                    bundle_content = f.read()
                return DeviceCertResponse(
                    cert_text=bundle_content,
                    device_name=f"{device.name} - Certificate Bundle"
                )
        
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Certificate file not found for type: {cert_type}"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading certificate file: {str(e)}"
        )


@router.get("/{device_id}/download")
async def download_device_certificate(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Download device certificate zip file
    """
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    if not os.path.exists(device.zip_path):
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Certificate file not found"
        )
    
    return FileResponse(
        path=device.zip_path,
        filename=f"{device.name}_certificates.zip",
        media_type="application/zip"
    )


@router.delete("/{device_id}")
async def delete_device(
    device_id: str,
    password: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete device after password verification
    """
    # Verify user password
    if not verify_password(password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password"
        )
    
    device = db.query(Device).filter(Device.id == device_id).first()
    if not device:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device not found"
        )
    
    try:
        # Delete physical files
        device_dir = Path(cert_generator.output_dir) / "devices"
        files_to_delete = [
            device_dir / f"{device.name}.key",
            device_dir / f"{device.name}.crt", 
            device_dir / f"{device.name}.bundle.crt"
        ]
        
        for file_path in files_to_delete:
            if file_path.exists():
                file_path.unlink()
        
        # Delete zip file
        if os.path.exists(device.zip_path):
            os.remove(device.zip_path)
        
        # Delete from database
        db.delete(device)
        db.commit()
        
        return {"message": f"Device '{device.name}' deleted successfully"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting device: {str(e)}"
        )
