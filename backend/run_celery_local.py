#!/usr/bin/env python3
"""
Script to run Celery worker locally for development.

This script sets up the environment for local development where:
- Redis runs in Docker (redis:6379)
- Celery worker runs locally in venv

Usage:
    python run_celery_local.py
"""

import os
import sys
import subprocess

def main():
    """Run Celery worker with local development settings."""
    
    # Set environment variables for local development
    env = os.environ.copy()
    env.update({
        'REDIS_HOST': 'localhost',
        'REDIS_PORT': '6379',
        'DATABASE_URL': 'sqlite:///./worqly.db',  # Use SQLite for local dev
        'SECRET_KEY': 'your-secret-key-change-in-production',
        'ENVIRONMENT': 'development'
    })
    
    print("🚀 Starting Celery worker for local development...")
    print(f"📡 Redis Host: {env['REDIS_HOST']}:{env['REDIS_PORT']}")
    print("💡 Make sure Redis is running in Docker: docker-compose up redis")
    print("-" * 50)
    
    try:
        # Run Celery worker
        cmd = [
            sys.executable, '-m', 'celery', 
            '-A', 'worker', 
            'worker', 
            '--loglevel=info',
            '--concurrency=2'
        ]
        
        subprocess.run(cmd, env=env, check=True)
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error running Celery worker: {e}")
        print("\n🔧 Troubleshooting:")
        print("1. Make sure Redis is running: docker-compose up redis")
        print("2. Check if Redis is accessible: redis-cli ping")
        print("3. Verify virtual environment is activated")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\n👋 Celery worker stopped by user")
        sys.exit(0)

if __name__ == '__main__':
    main()
