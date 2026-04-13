"""
Run server with unbuffered output for real-time logging
This ensures logs appear immediately
"""
import os
import sys

# Set unbuffered environment variable BEFORE importing anything
os.environ['PYTHONUNBUFFERED'] = '1'

# Force unbuffered stdout/stderr
if hasattr(sys.stdout, 'fileno'):
    sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 0)
if hasattr(sys.stderr, 'fileno'):
    sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 0)

# Now import and run the app
if __name__ == "__main__":
    import uvicorn
    from app import app
    
    print("=" * 60, flush=True)
    print("🚀 Starting Survey Analysis API Server (UNBUFFERED MODE)", flush=True)
    print("📊 Logs will appear in real-time", flush=True)
    print("=" * 60 + "\n", flush=True)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        access_log=True
    )

