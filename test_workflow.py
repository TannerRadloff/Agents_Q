#!/usr/bin/env python3
"""
Test script for Agents_Q workflow system.
This script simulates a user query, logs agent actions, and verifies workflow execution.
"""

import requests
import socketio
import time
import json
import logging
import sys
import os
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("test_workflow.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_workflow")

# Configuration
BASE_URL = "http://localhost:5001"
TEST_QUERY = "Research the latest advancements in renewable energy and create a summary report with the top 3 innovations."

class WorkflowTester:
    def __init__(self):
        self.session_id = None
        self.plan = None
        self.workflow_completed = False
        self.final_result = None
        self.updates = []
        
        # Initialize Socket.IO client
        self.sio = socketio.Client()
        self.setup_socketio_handlers()
    
    def setup_socketio_handlers(self):
        """Set up Socket.IO event handlers."""
        
        @self.sio.event
        def connect():
            logger.info("Connected to server")
        
        @self.sio.event
        def disconnect():
            logger.info("Disconnected from server")
        
        @self.sio.on('plan_created')
        def on_plan_created(data):
            self.session_id = data['session_id']
            self.plan = data['plan']
            logger.info(f"Plan created with {len(self.plan['steps'])} steps")
            logger.info(f"Plan summary: {self.plan['summary']}")
            
            # Log each step
            for i, step in enumerate(self.plan['steps']):
                logger.info(f"Step {i+1}: {step['title']} - {step['description']}")
        
        @self.sio.on('plan_accepted')
        def on_plan_accepted(data):
            logger.info(f"Plan accepted for session {data['session_id']}")
        
        @self.sio.on('workflow_update')
        def on_workflow_update(data):
            update = data['message']
            self.updates.append(update)
            logger.info(f"Workflow update: {update}")
        
        @self.sio.on('workflow_completed')
        def on_workflow_completed(data):
            self.workflow_completed = True
            self.final_result = data['result']
            logger.info("Workflow completed")
            logger.info(f"Final result: {self.final_result[:200]}...")  # Log first 200 chars
        
        @self.sio.on('error')
        def on_error(data):
            logger.error(f"Error: {data['message']}")
    
    def run_test(self):
        """Run the complete workflow test."""
        try:
            # Connect to Socket.IO server
            logger.info(f"Connecting to {BASE_URL}")
            self.sio.connect(BASE_URL)
            
            # Create a new session by visiting the index page
            response = requests.get(f"{BASE_URL}/")
            if response.status_code != 200:
                logger.error(f"Failed to access index page: {response.status_code}")
                return False
            
            # Extract session ID from the page (this is a simplification, in reality you might need to parse HTML)
            # For our test, we'll create a session ID via Socket.IO
            
            # Submit the test query
            logger.info(f"Submitting test query: {TEST_QUERY}")
            self.sio.emit('create_plan', {
                'message': TEST_QUERY,
                'session_id': ''  # Empty string will create a new session
            })
            
            # Wait for plan creation (max 60 seconds)
            timeout = 60
            start_time = time.time()
            while not self.plan and time.time() - start_time < timeout:
                time.sleep(1)
            
            if not self.plan:
                logger.error("Timeout waiting for plan creation")
                return False
            
            logger.info("Plan created successfully")
            
            # Accept the plan
            logger.info("Accepting plan")
            self.sio.emit('accept_plan', {
                'session_id': self.session_id
            })
            
            # Wait for workflow completion (max 5 minutes)
            timeout = 300
            start_time = time.time()
            while not self.workflow_completed and time.time() - start_time < timeout:
                time.sleep(2)
            
            if not self.workflow_completed:
                logger.error("Timeout waiting for workflow completion")
                return False
            
            # Verify results
            logger.info("Verifying workflow results")
            
            # Check if we have updates for each step
            step_count = len(self.plan['steps'])
            start_updates = [u for u in self.updates if u.startswith('Starting step')]
            complete_updates = [u for u in self.updates if u.startswith('Completed step')]
            
            if len(start_updates) < step_count or len(complete_updates) < step_count:
                logger.warning(f"Not all steps have updates: {len(start_updates)}/{step_count} started, {len(complete_updates)}/{step_count} completed")
            
            # Check if final result contains expected content
            if "renewable energy" in self.final_result.lower() and "innovations" in self.final_result.lower():
                logger.info("Final result contains expected content")
            else:
                logger.warning("Final result may not address the query correctly")
            
            # Save the final result to a file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            result_file = f"workflow_result_{timestamp}.txt"
            with open(result_file, 'w') as f:
                f.write(self.final_result)
            logger.info(f"Saved final result to {result_file}")
            
            logger.info("Test completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Test failed with error: {str(e)}", exc_info=True)
            return False
        finally:
            # Disconnect from Socket.IO server
            if self.sio.connected:
                self.sio.disconnect()

if __name__ == "__main__":
    # Check if the server is running
    try:
        response = requests.get(f"{BASE_URL}/")
        if response.status_code != 200:
            logger.error(f"Server is not responding correctly: {response.status_code}")
            sys.exit(1)
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to server at {BASE_URL}. Make sure it's running.")
        sys.exit(1)
    
    # Install required packages if not already installed
    try:
        import socketio
    except ImportError:
        logger.info("Installing required packages...")
        os.system("pip install python-socketio[client] requests")
        logger.info("Packages installed, restarting script...")
        os.execv(sys.executable, ['python'] + sys.argv)
    
    tester = WorkflowTester()
    success = tester.run_test()
    
    if success:
        logger.info("✅ Workflow test passed")
        sys.exit(0)
    else:
        logger.error("❌ Workflow test failed")
        sys.exit(1)
