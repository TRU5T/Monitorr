"""
Radarr monitor for Docker container logs
"""

import re
import logging
from .base import BaseMonitor

logger = logging.getLogger('monitorr.monitor.radarr')

class RadarrMonitor(BaseMonitor):
    """Monitor for Radarr Docker container logs"""
    
    def __init__(self, docker_client, config, alert_manager):
        """Initialize Radarr monitor with configuration"""
        # Default error patterns for Radarr if none specified
        if 'error_patterns' not in config:
            config['error_patterns'] = [
                r'error',
                r'failed',
                r'exception',
                r'fatal',
                r'unable to',
                r'could not'
            ]
            
        # Default ignore patterns for Radarr if none specified
        if 'ignore_patterns' not in config:
            config['ignore_patterns'] = [
                r'rss sync completed',
                r'certificate validation disabled'
            ]
            
        super().__init__(docker_client, config, alert_manager)
        
    def handle_errors(self, errors, container):
        """Handle detected errors with Radarr specific formatting"""
        if not errors:
            return
            
        logger.info(f"Found {len(errors)} errors in Radarr container {self.container_name}")
        
        # Prepare alert data with Radarr specific formatting
        alert_data = {
            'container_name': self.container_name,
            'container_id': container.id,
            'service_name': 'Radarr',
            'errors': errors,
            'monitor_type': 'RadarrMonitor'
        }
        
        # Send alert through alert manager
        self.alert_manager.send_alert(alert_data) 