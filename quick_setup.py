#!/usr/bin/env python3
"""
Quick setup script for Worqly workflow automation
This script sets up the environment and starts the services
"""

import subprocess
import sys
import os
import time
import requests
from pathlib import Path

def run_command(command, cwd=None, shell=False):
    """Run a command and return success status"""
    try:
        print(f"Running: {command}")
        result = subprocess.run(
            command,
            cwd=cwd,
            shell=shell,
            check=True,
            capture_output=True,
            text=True
        )
        print(f"✅ Success: {command}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Failed: {command}")
        print(f"Error: {e.stderr}")
        return False

def check_backend_health():
    """Check if backend is running"""
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        return response.status_code == 200
    except:
        return False

def check_frontend_health():
    """Check if frontend is running"""
    try:
        response = requests.get("http://localhost:3000", timeout=5)
        return response.status_code == 200
    except:
        return False

def setup_backend():
    """Setup backend"""
    print("🔧 Setting up backend...")
    
    backend_dir = Path("backend")
    if not backend_dir.exists():
        print("❌ Backend directory not found")
        return False
    
    # Install dependencies
    if not run_command([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], cwd=backend_dir):
        print("❌ Failed to install backend dependencies")
        return False
    
    # Create test user
    if not run_command([sys.executable, "create_test_user.py"], cwd=backend_dir):
        print("⚠️ Failed to create test user (may already exist)")
    
    print("✅ Backend setup complete")
    return True

def setup_frontend():
    """Setup frontend"""
    print("🔧 Setting up frontend...")
    
    frontend_dir = Path("frontend")
    if not frontend_dir.exists():
        print("❌ Frontend directory not found")
        return False
    
    # Install dependencies
    if not run_command(["npm", "install"], cwd=frontend_dir):
        print("❌ Failed to install frontend dependencies")
        return False
    
    print("✅ Frontend setup complete")
    return True

def start_backend():
    """Start backend server"""
    print("🚀 Starting backend server...")
    
    backend_dir = Path("backend")
    
    # Start backend in background
    try:
        process = subprocess.Popen(
            [sys.executable, "-m", "uvicorn", "app.main:app", "--reload", "--host", "0.0.0.0", "--port", "8000"],
            cwd=backend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for backend to start
        for i in range(30):  # Wait up to 30 seconds
            if check_backend_health():
                print("✅ Backend server is running on http://localhost:8000")
                return process
            time.sleep(1)
        
        print("❌ Backend server failed to start")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start backend: {e}")
        return None

def start_frontend():
    """Start frontend server"""
    print("🚀 Starting frontend server...")
    
    frontend_dir = Path("frontend")
    
    # Start frontend in background
    try:
        process = subprocess.Popen(
            ["npm", "run", "dev"],
            cwd=frontend_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Wait for frontend to start
        for i in range(30):  # Wait up to 30 seconds
            if check_frontend_health():
                print("✅ Frontend server is running on http://localhost:3000")
                return process
            time.sleep(1)
        
        print("❌ Frontend server failed to start")
        process.terminate()
        return None
        
    except Exception as e:
        print(f"❌ Failed to start frontend: {e}")
        return None

def run_tests():
    """Run workflow automation tests"""
    print("🧪 Running workflow automation tests...")
    
    if not run_command([sys.executable, "test_workflow_automation.py"]):
        print("❌ Tests failed")
        return False
    
    print("✅ All tests passed!")
    return True

def main():
    """Main setup function"""
    print("🚀 Worqly Workflow Automation Quick Setup")
    print("=" * 50)
    
    # Check if we're in the right directory
    if not Path("backend").exists() or not Path("frontend").exists():
        print("❌ Please run this script from the flowmaker root directory")
        return 1
    
    # Setup services
    if not setup_backend():
        return 1
    
    if not setup_frontend():
        return 1
    
    # Start services
    backend_process = start_backend()
    if not backend_process:
        return 1
    
    frontend_process = start_frontend()
    if not frontend_process:
        backend_process.terminate()
        return 1
    
    try:
        # Run tests
        if not run_tests():
            print("⚠️ Tests failed, but services are running")
        
        print("\n🎉 Setup complete!")
        print("📱 Frontend: http://localhost:3000")
        print("🔧 Backend API: http://localhost:8000")
        print("📚 API Docs: http://localhost:8000/docs")
        print("\nPress Ctrl+C to stop all services")
        
        # Keep services running
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping services...")
        backend_process.terminate()
        frontend_process.terminate()
        print("✅ Services stopped")
        return 0

if __name__ == "__main__":
    sys.exit(main())
