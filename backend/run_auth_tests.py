#!/usr/bin/env python3
"""
Script to run the authentication tests
"""

import subprocess
import sys
import time
import os
from pathlib import Path

def run_command(command, cwd=None):
    """Run a command and return the result"""
    try:
        result = subprocess.run(
            command, 
            shell=True, 
            cwd=cwd, 
            capture_output=True, 
            text=True,
            timeout=30
        )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Command timed out"
    except Exception as e:
        return False, "", str(e)

def main():
    """Main function to run authentication tests"""
    print("🚀 Starting Authentication Tests")
    print("=" * 50)
    
    # Get the backend directory
    backend_dir = Path(__file__).parent
    
    # Check if we're in the right directory
    if not (backend_dir / "app").exists():
        print("❌ Error: app directory not found. Please run this script from the backend directory.")
        sys.exit(1)
    
    # Check if the server is already running
    print("🔍 Checking if server is already running...")
    success, stdout, stderr = run_command("curl -s http://localhost:8000/health")
    if success:
        print("✅ Server is already running!")
    else:
        print("⚠️ Server is not running. Please start the server first with:")
        print("   cd flowmaker/backend")
        print("   python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000")
        print("\nThen run this test script again.")
        sys.exit(1)
    
    # Run the authentication tests
    print("\n🧪 Running authentication flow tests...")
    test_script = backend_dir / "test_auth_flows.py"
    
    if not test_script.exists():
        print(f"❌ Test script not found: {test_script}")
        sys.exit(1)
    
    success, stdout, stderr = run_command(f"python {test_script}", cwd=backend_dir)
    
    if success:
        print("✅ Authentication tests completed successfully!")
        print(stdout)
    else:
        print("❌ Authentication tests failed!")
        print("STDOUT:", stdout)
        print("STDERR:", stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
