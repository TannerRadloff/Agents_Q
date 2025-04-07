#!/usr/bin/env python3
"""
Test script for Agents_Q workflow system.
This script starts the Flask server and runs a test workflow.
"""

import subprocess
import time
import os
import sys
import signal
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_runner.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_runner")

def run_server():
    """Start the Flask server in a subprocess."""
    logger.info("Starting Flask server...")
    server_process = subprocess.Popen(
        ["python", "run.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )
    
    # Wait for server to start
    time.sleep(5)
    
    # Check if server is running
    if server_process.poll() is not None:
        stdout, stderr = server_process.communicate()
        logger.error(f"Server failed to start:\nSTDOUT: {stdout}\nSTDERR: {stderr}")
        return None
    
    logger.info("Server started successfully")
    return server_process

def run_test():
    """Run the workflow test script."""
    logger.info("Running workflow test...")
    test_process = subprocess.run(
        ["python", "test_workflow.py"],
        capture_output=True,
        text=True
    )
    
    # Log test output
    logger.info(f"Test STDOUT:\n{test_process.stdout}")
    if test_process.stderr:
        logger.error(f"Test STDERR:\n{test_process.stderr}")
    
    return test_process.returncode == 0

if __name__ == "__main__":
    # Install required packages
    logger.info("Installing required packages...")
    subprocess.run(["pip", "install", "python-socketio[client]", "requests"], check=True)
    
    # Start server
    server_process = run_server()
    if not server_process:
        sys.exit(1)
    
    try:
        # Run test
        success = run_test()
        
        if success:
            logger.info("✅ Test completed successfully")
        else:
            logger.error("❌ Test failed")
            sys.exit(1)
    finally:
        # Terminate server
        logger.info("Terminating server...")
        os.kill(server_process.pid, signal.SIGTERM)
        server_process.wait()
        logger.info("Server terminated")
