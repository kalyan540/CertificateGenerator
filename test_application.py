#!/usr/bin/env python3
"""
Comprehensive test script for IoT Device Certificate Generator
Tests all functionality and reports issues for production deployment
"""

import requests
import json
import time
import os
from pathlib import Path

# Configuration
BASE_URL = "http://localhost:5001"
FRONTEND_URL = "http://localhost:5001"
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin123"

class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
        self.critical = []
        self.warnings = []
    
    def add_pass(self, test_name, message=""):
        self.passed.append({"test": test_name, "message": message})
        print(f"✅ PASS: {test_name}")
        if message:
            print(f"   └─ {message}")
    
    def add_fail(self, test_name, error, critical=False):
        failure = {"test": test_name, "error": str(error)}
        self.failed.append(failure)
        if critical:
            self.critical.append(failure)
        status = "🔴 CRITICAL FAIL" if critical else "❌ FAIL"
        print(f"{status}: {test_name}")
        print(f"   └─ Error: {error}")
    
    def add_warning(self, test_name, message):
        self.warnings.append({"test": test_name, "message": message})
        print(f"⚠️  WARNING: {test_name}")
        print(f"   └─ {message}")
    
    def summary(self):
        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"✅ Passed: {len(self.passed)}")
        print(f"❌ Failed: {len(self.failed)}")
        print(f"🔴 Critical: {len(self.critical)}")
        print(f"⚠️  Warnings: {len(self.warnings)}")
        
        if self.critical:
            print(f"\n🔴 CRITICAL ISSUES (Must fix before production):")
            for issue in self.critical:
                print(f"   • {issue['test']}: {issue['error']}")
        
        if self.failed:
            print(f"\n❌ FAILED TESTS:")
            for issue in self.failed:
                if issue not in self.critical:
                    print(f"   • {issue['test']}: {issue['error']}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS:")
            for warning in self.warnings:
                print(f"   • {warning['test']}: {warning['message']}")

results = TestResults()

def test_health_check():
    """Test if backend is responding"""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            data = response.json()
            results.add_pass("Health Check", f"Status: {data.get('status')}")
            return True
        else:
            results.add_fail("Health Check", f"HTTP {response.status_code}", critical=True)
            return False
    except Exception as e:
        results.add_fail("Health Check", f"Cannot connect to backend: {e}", critical=True)
        return False

def test_frontend_access():
    """Test if frontend is accessible"""
    try:
        response = requests.get(FRONTEND_URL, timeout=5)
        if response.status_code == 200:
            results.add_pass("Frontend Access", "React app accessible")
            return True
        else:
            results.add_fail("Frontend Access", f"HTTP {response.status_code}", critical=True)
            return False
    except Exception as e:
        results.add_fail("Frontend Access", f"Cannot connect to frontend: {e}", critical=True)
        return False

def get_auth_token():
    """Get JWT token for authentication"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": TEST_USERNAME,
            "password": TEST_PASSWORD
        })
        if response.status_code == 200:
            token = response.json()["access_token"]
            results.add_pass("Authentication", "Login successful")
            return token
        else:
            results.add_fail("Authentication", f"Login failed: HTTP {response.status_code}", critical=True)
            return None
    except Exception as e:
        results.add_fail("Authentication", f"Login error: {e}", critical=True)
        return None

def test_invalid_login():
    """Test invalid login credentials"""
    try:
        response = requests.post(f"{BASE_URL}/auth/login", json={
            "username": "invalid",
            "password": "wrong"
        })
        if response.status_code == 401:
            results.add_pass("Invalid Login Protection", "Correctly rejects invalid credentials")
        else:
            results.add_fail("Invalid Login Protection", f"Should return 401, got {response.status_code}")
    except Exception as e:
        results.add_fail("Invalid Login Protection", f"Error: {e}")

def test_certificate_generation(token):
    """Test certificate generation with various inputs"""
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test valid device name
    try:
        response = requests.post(f"{BASE_URL}/devices/create", 
                               json={"name": "test-device-01"}, 
                               headers=headers)
        if response.status_code == 200:
            data = response.json()
            device_id = data["device"]["id"]
            results.add_pass("Certificate Generation", f"Generated for test-device-01, ID: {device_id}")
            return device_id
        else:
            results.add_fail("Certificate Generation", f"HTTP {response.status_code}: {response.text}", critical=True)
            return None
    except Exception as e:
        results.add_fail("Certificate Generation", f"Error: {e}", critical=True)
        return None

def test_invalid_device_names(token):
    """Test validation with invalid device names"""
    headers = {"Authorization": f"Bearer {token}"}
    
    invalid_names = [
        "device with spaces",
        "device@invalid",
        "device#name",
        "",
        "   ",
        "device/test"
    ]
    
    for name in invalid_names:
        try:
            response = requests.post(f"{BASE_URL}/devices/create", 
                                   json={"name": name}, 
                                   headers=headers)
            if response.status_code == 422:
                results.add_pass(f"Validation: '{name}'", "Correctly rejected")
            else:
                results.add_fail(f"Validation: '{name}'", f"Should reject but got HTTP {response.status_code}")
        except Exception as e:
            results.add_fail(f"Validation: '{name}'", f"Error: {e}")

def test_duplicate_device_name(token):
    """Test duplicate device name handling"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        # Try to create same device again
        response = requests.post(f"{BASE_URL}/devices/create", 
                               json={"name": "test-device-01"}, 
                               headers=headers)
        if response.status_code == 400:
            results.add_pass("Duplicate Name Protection", "Correctly prevents duplicate device names")
        else:
            results.add_fail("Duplicate Name Protection", f"Should return 400, got {response.status_code}")
    except Exception as e:
        results.add_fail("Duplicate Name Protection", f"Error: {e}")

def test_certificate_viewing(token, device_id):
    """Test viewing different certificate types"""
    if not device_id:
        results.add_fail("Certificate Viewing", "No device ID available", critical=True)
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    cert_types = ["device_cert", "ca_cert", "private_key", "bundle"]
    
    for cert_type in cert_types:
        try:
            response = requests.get(f"{BASE_URL}/devices/{device_id}/view",
                                  params={"cert_type": cert_type},
                                  headers=headers)
            if response.status_code == 200:
                data = response.json()
                if data.get("cert_text"):
                    results.add_pass(f"View {cert_type}", f"Certificate text retrieved")
                else:
                    results.add_fail(f"View {cert_type}", "Empty certificate text")
            else:
                results.add_fail(f"View {cert_type}", f"HTTP {response.status_code}", 
                               critical=(cert_type == "device_cert"))
        except Exception as e:
            results.add_fail(f"View {cert_type}", f"Error: {e}")

def test_device_list(token):
    """Test device listing"""
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/devices/", headers=headers)
        if response.status_code == 200:
            devices = response.json()
            if isinstance(devices, list) and len(devices) > 0:
                results.add_pass("Device Listing", f"Found {len(devices)} devices")
            else:
                results.add_warning("Device Listing", "No devices found in list")
        else:
            results.add_fail("Device Listing", f"HTTP {response.status_code}", critical=True)
    except Exception as e:
        results.add_fail("Device Listing", f"Error: {e}", critical=True)

def test_download_certificate(token, device_id):
    """Test certificate download"""
    if not device_id:
        results.add_fail("Certificate Download", "No device ID available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        response = requests.get(f"{BASE_URL}/devices/{device_id}/download", headers=headers)
        if response.status_code == 200:
            if response.headers.get('content-type') == 'application/zip':
                results.add_pass("Certificate Download", f"ZIP file downloaded ({len(response.content)} bytes)")
            else:
                results.add_fail("Certificate Download", "Response is not a ZIP file")
        else:
            results.add_fail("Certificate Download", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Certificate Download", f"Error: {e}")

def test_unauthorized_access():
    """Test endpoints without authentication"""
    endpoints = [
        "/devices/",
        "/devices/create",
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(f"{BASE_URL}{endpoint}")
            if response.status_code == 401:
                results.add_pass(f"Unauthorized Access: {endpoint}", "Correctly requires authentication")
            else:
                results.add_fail(f"Unauthorized Access: {endpoint}", 
                               f"Should return 401, got {response.status_code}")
        except Exception as e:
            results.add_fail(f"Unauthorized Access: {endpoint}", f"Error: {e}")

def test_file_system_security():
    """Test file system security"""
    # Check if certificate directories exist and have correct permissions
    certs_dir = Path("certs")
    output_dir = Path("certs_output")
    
    if certs_dir.exists():
        results.add_pass("Certs Directory", "Input directory exists")
        
        # Check for CA files
        ca_crt = certs_dir / "ca.crt"
        ca_key = certs_dir / "ca.key"
        
        if ca_crt.exists():
            results.add_pass("CA Certificate", "Root CA certificate found")
        else:
            results.add_fail("CA Certificate", "ca.crt not found", critical=True)
        
        if ca_key.exists():
            results.add_pass("CA Private Key", "Root CA private key found")
            # Check permissions (should be restrictive)
            stat = ca_key.stat()
            if oct(stat.st_mode)[-3:] == '600':
                results.add_pass("CA Key Permissions", "Properly secured (600)")
            else:
                results.add_warning("CA Key Permissions", f"Permissions: {oct(stat.st_mode)[-3:]} (should be 600)")
        else:
            results.add_fail("CA Private Key", "ca.key not found", critical=True)
    else:
        results.add_fail("Certs Directory", "Input directory missing", critical=True)
    
    if output_dir.exists():
        results.add_pass("Output Directory", "Certificate output directory exists")
    else:
        results.add_warning("Output Directory", "Output directory not found")

def test_device_deletion(token, device_id):
    """Test device deletion with password verification"""
    if not device_id:
        results.add_fail("Device Deletion", "No device ID available")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test with wrong password
    try:
        response = requests.delete(f"{BASE_URL}/devices/{device_id}",
                                 params={"password": "wrongpassword"},
                                 headers=headers)
        if response.status_code == 401:
            results.add_pass("Delete Wrong Password", "Correctly rejects wrong password")
        else:
            results.add_fail("Delete Wrong Password", f"Should return 401, got {response.status_code}")
    except Exception as e:
        results.add_fail("Delete Wrong Password", f"Error: {e}")
    
    # Test with correct password
    try:
        response = requests.delete(f"{BASE_URL}/devices/{device_id}",
                                 params={"password": TEST_PASSWORD},
                                 headers=headers)
        if response.status_code == 200:
            results.add_pass("Device Deletion", "Successfully deleted with correct password")
        else:
            results.add_fail("Device Deletion", f"HTTP {response.status_code}")
    except Exception as e:
        results.add_fail("Device Deletion", f"Error: {e}")

def main():
    print("🚀 Starting IoT Device Certificate Generator Tests")
    print("="*60)
    
    # Basic connectivity tests
    if not test_health_check():
        results.summary()
        return
    
    test_frontend_access()
    
    # Authentication tests
    token = get_auth_token()
    if not token:
        results.summary()
        return
    
    test_invalid_login()
    test_unauthorized_access()
    
    # Certificate generation tests
    device_id = test_certificate_generation(token)
    test_invalid_device_names(token)
    test_duplicate_device_name(token)
    
    # Certificate viewing and download tests
    test_certificate_viewing(token, device_id)
    test_device_list(token)
    test_download_certificate(token, device_id)
    
    # Security tests
    test_file_system_security()
    
    # Cleanup tests (delete device)
    test_device_deletion(token, device_id)
    
    # Final summary
    results.summary()
    
    # Production readiness assessment
    print(f"\n🏭 PRODUCTION READINESS ASSESSMENT")
    print("="*60)
    
    if len(results.critical) == 0:
        print("✅ No critical issues found")
        if len(results.failed) == 0:
            print("🎉 Application is PRODUCTION READY!")
        else:
            print("⚠️  Minor issues found, but application can be deployed")
    else:
        print("🔴 CRITICAL ISSUES MUST BE FIXED BEFORE PRODUCTION DEPLOYMENT")
    
    print(f"\nTotal issues to review: {len(results.failed) + len(results.warnings)}")

if __name__ == "__main__":
    main()
