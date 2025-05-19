"""
Base monitor class for container logs
"""

import re
import logging
from datetime import datetime, timedelta

logger = logging.getLogger('monitorr.monitor')

class BaseMonitor:
    def __init__(self, docker_client, config, alert_manager):
        """Initialize base monitor with configuration"""
        self.docker_client = docker_client
        self.config = config
        self.alert_manager = alert_manager
        self.container_name = config.get('container_name')
        self.error_patterns = config.get('error_patterns', [])
        self.ignore_patterns = config.get('ignore_patterns', [])
        self.last_check_time = None
        self.compiled_error_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.error_patterns]
        self.compiled_ignore_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.ignore_patterns]
        
    def get_container(self):
        """Get the container object by name"""
        try:
            return self.docker_client.containers.get(self.container_name)
        except Exception as e:
            logger.error(f"Failed to get container {self.container_name}: {e}")
            return None
    
    def check_logs(self):
        """Check container logs for errors"""
        container = self.get_container()
        if not container:
            logger.warning(f"Container {self.container_name} not found")
            return
        
        # Only get logs since last check
        since = None
        if self.last_check_time:
            since = self.last_check_time
        
        # Get logs for the container
        try:
            logs = container.logs(
                since=since,
                timestamps=True,
                tail='all',
                stream=False
            ).decode('utf-8')
            
            self.last_check_time = datetime.now()
            self.process_logs(logs, container)
        except Exception as e:
            logger.error(f"Error fetching logs for {self.container_name}: {e}")
    
    def process_logs(self, logs, container):
        """Process container logs and detect errors"""
        if not logs:
            return
        
        # Process each log line
        errors_found = []
        for line in logs.splitlines():
            # Skip empty lines
            if not line.strip():
                continue
                
            # Check if line matches any error pattern
            for pattern in self.compiled_error_patterns:
                if pattern.search(line):
                    # Check if line matches any ignore pattern
                    if any(ignore.search(line) for ignore in self.compiled_ignore_patterns):
                        continue
                        
                    errors_found.append(line)
                    break
        
        if errors_found:
            self.handle_errors(errors_found, container)
    
    def handle_errors(self, errors, container):
        """Handle detected errors"""
        if not errors:
            return
            
        logger.info(f"Found {len(errors)} errors in {self.container_name}")
        
        # Prepare alert data
        alert_data = {
            'container_name': self.container_name,
            'container_id': container.id,
            'timestamp': datetime.now().isoformat(),
            'errors': errors,
            'monitor_type': self.__class__.__name__
        }
        
        # Send alert through alert manager
        self.alert_manager.send_alert(alert_data)
        
    def format_errors(self, errors):
        """Format errors for display in alerts"""
        return "\n".join(errors) 