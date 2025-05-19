"""
Jellyfin monitor for Docker container logs
"""

import re
import logging
from .base import BaseMonitor

logger = logging.getLogger('monitorr.monitor.jellyfin')

class JellyfinMonitor(BaseMonitor):
    """Monitor for Jellyfin Docker container logs"""
    
    def __init__(self, docker_client, config, alert_manager):
        """Initialize Jellyfin monitor with configuration"""
        # Default error patterns for Jellyfin if none specified
        if 'error_patterns' not in config:
            config['error_patterns'] = [
                r'error',
                r'exception',
                r'fatal',
                r'failure',
                r'failed to',
                r'cannot access',
                r'access denied',
                r'permission denied',
                r'unexpected error',
                r'database error',
                r'transcode error'
            ]
            
        # Default ignore patterns for Jellyfin if none specified
        if 'ignore_patterns' not in config:
            config['ignore_patterns'] = [
                r'info>',
                r'debug>',
                r'verbose>',
                r'certificate validation',
                r'heartbeat',
                r'health check'
            ]
            
        super().__init__(docker_client, config, alert_manager)
        
    def handle_errors(self, errors, container):
        """Handle detected errors with Jellyfin specific formatting"""
        if not errors:
            return
            
        logger.info(f"Found {len(errors)} errors in Jellyfin container {self.container_name}")
        
        # Format errors for Jellyfin - remove timestamps and server info if present
        formatted_errors = []
        for error in errors:
            # Try to clean up Jellyfin log format
            error = re.sub(r'^\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d+\]', '', error).strip()
            error = re.sub(r'^\[\w+\]', '', error).strip()
            formatted_errors.append(error)
        
        # Prepare alert data
        alert_data = {
            'container_name': self.container_name,
            'container_id': container.id,
            'service_name': 'Jellyfin',
            'errors': formatted_errors,
            'monitor_type': 'JellyfinMonitor'
        }
        
        # Send alert through alert manager
        self.alert_manager.send_alert(alert_data) 