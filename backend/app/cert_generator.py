import os
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Tuple, Dict
from .config import settings


class CertificateGenerator:
    """Certificate generation utility class"""
    
    def __init__(self):
        self.certs_dir = Path(settings.certs_dir)
        self.output_dir = Path(settings.certs_output_dir)
        self.output_dir.mkdir(exist_ok=True, parents=True)
    
    def check_ca_certificates(self) -> bool:
        """Check if CA certificates exist and have proper security"""
        ca_crt = self.certs_dir / "ca.crt"
        ca_key = self.certs_dir / "ca.key"
        
        if not (ca_crt.exists() and ca_key.exists()):
            return False
        
        # Security check: Ensure CA private key has proper permissions (600)
        try:
            ca_key_stat = ca_key.stat()
            # Check if permissions are too permissive (should be 600)
            permissions = oct(ca_key_stat.st_mode)[-3:]
            if permissions != '600':
                print(f"WARNING: CA private key has insecure permissions {permissions}, should be 600")
                # Try to fix permissions automatically
                try:
                    ca_key.chmod(0o600)
                    print("✅ Fixed CA private key permissions to 600")
                except Exception as e:
                    print(f"❌ Failed to fix CA key permissions: {e}")
                    raise FileNotFoundError(f"CA private key has insecure permissions ({permissions}). Please set to 600: chmod 600 {ca_key}")
        except Exception as e:
            print(f"Warning: Could not check CA key permissions: {e}")
        
        return True
    
    def generate_device_certificate(self, device_name: str, hostname: str = "localhost") -> Dict[str, str]:
        """
        Generate device certificate using OpenSSL commands
        Returns dictionary with file paths and certificate content
        """
        if not self.check_ca_certificates():
            raise FileNotFoundError("CA certificates not found. Please ensure ca.crt and ca.key exist in certs/ directory.")
        
        # Create device output directory
        device_dir = self.output_dir / "devices"
        device_dir.mkdir(exist_ok=True, parents=True)
        
        # File paths
        device_key = device_dir / f"{device_name}.key"
        device_csr = device_dir / f"{device_name}.csr"
        device_crt = device_dir / f"{device_name}.crt"
        device_bundle = device_dir / f"{device_name}.bundle.crt"
        extensions_file = device_dir / f"{device_name}.extensions.conf"
        
        ca_crt = self.certs_dir / "ca.crt"
        ca_key = self.certs_dir / "ca.key"
        
        try:
            # Step 1: Generate device private key
            subprocess.run([
                "openssl", "genrsa",
                "-out", str(device_key),
                str(settings.cert_key_size)
            ], check=True, capture_output=True)
            
            # Step 2: Generate certificate signing request
            subject = (
                f"/C={settings.cert_country}"
                f"/ST={settings.cert_state}"
                f"/L={settings.cert_city}"
                f"/O={settings.cert_organization}"
                f"/OU={settings.cert_org_unit}"
                f"/CN={device_name}"
            )
            
            subprocess.run([
                "openssl", "req", "-new",
                "-key", str(device_key),
                "-out", str(device_csr),
                "-subj", subject
            ], check=True, capture_output=True)
            
            # Step 3: Create extensions file
            extensions_content = f"""[v3_req]
authorityKeyIdentifier=keyid,issuer
basicConstraints=CA:FALSE
keyUsage = digitalSignature, nonRepudiation, keyEncipherment, dataEncipherment
extendedKeyUsage = clientAuth
subjectAltName = @alt_names

[alt_names]
DNS.1 = {device_name}
DNS.2 = {device_name}.local
"""
            with open(extensions_file, 'w') as f:
                f.write(extensions_content)
            
            # Step 4: Sign device certificate with CA
            # Copy CA files to output directory to avoid permission issues
            temp_ca_crt = device_dir / "temp_ca.crt"
            temp_ca_key = device_dir / "temp_ca.key"
            
            # Copy CA files to writable location
            subprocess.run([
                "cp", str(ca_crt), str(temp_ca_crt)
            ], check=True, capture_output=True)
            
            subprocess.run([
                "cp", str(ca_key), str(temp_ca_key)
            ], check=True, capture_output=True)
            
            # Sign certificate using temp CA files
            subprocess.run([
                "openssl", "x509", "-req",
                "-in", str(device_csr),
                "-CA", str(temp_ca_crt),
                "-CAkey", str(temp_ca_key),
                "-CAcreateserial",
                "-out", str(device_crt),
                "-days", str(settings.cert_validity_days),
                "-extensions", "v3_req",
                "-extfile", str(extensions_file)
            ], check=True, capture_output=True)
            
            # Clean up temp files
            temp_ca_crt.unlink(missing_ok=True)
            temp_ca_key.unlink(missing_ok=True)
            (device_dir / "temp_ca.srl").unlink(missing_ok=True)
            
            # Step 5: Create certificate bundle
            with open(device_bundle, 'w') as bundle_file:
                with open(device_crt, 'r') as cert_file:
                    bundle_file.write(cert_file.read())
                with open(ca_crt, 'r') as ca_file:
                    bundle_file.write(ca_file.read())
            
            # Step 6: Set permissions
            os.chmod(device_key, 0o600)
            os.chmod(device_crt, 0o644)
            os.chmod(device_bundle, 0o644)
            
            # Step 7: Clean up temporary files
            device_csr.unlink(missing_ok=True)
            extensions_file.unlink(missing_ok=True)
            
            # Read certificate content
            with open(device_crt, 'r') as f:
                cert_content = f.read()
            
            # Create zip file
            zip_path = self.create_certificate_zip(device_name, device_dir)
            
            return {
                "device_key": str(device_key),
                "device_crt": str(device_crt),
                "device_bundle": str(device_bundle),
                "cert_content": cert_content,
                "zip_path": zip_path
            }
            
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Certificate generation failed: {e.stderr.decode() if e.stderr else str(e)}")
        except Exception as e:
            raise RuntimeError(f"Certificate generation error: {str(e)}")
    
    def create_certificate_zip(self, device_name: str, device_dir: Path) -> str:
        """Create a zip file containing all certificate files"""
        zip_filename = f"{device_name}_certificates.zip"
        zip_path = self.output_dir / zip_filename
        
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add device files
            files_to_zip = [
                f"{device_name}.key",
                f"{device_name}.crt",
                f"{device_name}.bundle.crt"
            ]
            
            for filename in files_to_zip:
                file_path = device_dir / filename
                if file_path.exists():
                    zipf.write(file_path, filename)
            
            # Add CA certificate
            ca_crt = self.certs_dir / "ca.crt"
            if ca_crt.exists():
                zipf.write(ca_crt, "ca.crt")
            
            # Add usage instructions
            instructions = self.generate_usage_instructions(device_name)
            zipf.writestr("USAGE_INSTRUCTIONS.txt", instructions)
        
        return str(zip_path)
    
    def generate_usage_instructions(self, device_name: str) -> str:
        """Generate usage instructions for the certificates"""
        instructions = f"""IoT Device Certificate Usage Instructions
========================================

Device Name: {device_name}
Generated: {os.popen('date').read().strip()}

Files included in this package:
-------------------------------
- ca.crt: Root CA Certificate (for server verification)
- {device_name}.crt: Device Certificate (client certificate)
- {device_name}.key: Device Private Key (keep secure!)
- {device_name}.bundle.crt: Certificate Bundle (device cert + CA cert)

MQTT Configuration:
------------------
For secure MQTT connection, use these files:

1. CA Certificate: ca.crt
2. Client Certificate: {device_name}.crt
3. Client Private Key: {device_name}.key

Example mosquitto_pub command:
mosquitto_pub -h your-mqtt-broker.com -p 8883 \\
  --cafile ca.crt \\
  --cert {device_name}.crt \\
  --key {device_name}.key \\
  -t test/topic \\
  -m "Hello from {device_name}"

Example mosquitto_sub command:
mosquitto_sub -h your-mqtt-broker.com -p 8883 \\
  --cafile ca.crt \\
  --cert {device_name}.crt \\
  --key {device_name}.key \\
  -t test/topic

Security Notes:
--------------
- Keep the private key ({device_name}.key) secure and never share it
- The certificate is valid for {settings.cert_validity_days} days
- Use TLS/SSL port (usually 8883) for MQTT connections
- Verify the server certificate using the provided CA certificate

Organization: {settings.cert_organization}
Location: {settings.cert_city}, {settings.cert_state}, {settings.cert_country}
"""
        return instructions


# Create a global instance
cert_generator = CertificateGenerator()
