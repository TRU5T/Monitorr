"""
Plex-specific monitor for detecting errors in Plex Media Server logs
"""

import logging
from monitors.base import BaseMonitor
import re

logger = logging.getLogger('monitorr.monitor.plex')

class PlexMonitor(BaseMonitor):
    def __init__(self, docker_client, config, alert_manager):
        """Initialize Plex monitor with specific configuration"""
        super().__init__(docker_client, config, alert_manager)
        
        # Add default Plex error patterns if none specified
        if not self.error_patterns:
            self.error_patterns = [
                "Error:",
                "Exception:",
                "Fatal:",
                "Critical:",
                "Crash detected",
                "failed to",
                "failure"
            ]
            # Recompile patterns
            self.compiled_error_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.error_patterns]
    
    def process_logs(self, logs, container):
        """Process Plex-specific logs"""
        # Call base implementation
        super().process_logs(logs, container)
        
    def handle_errors(self, errors, container):
        """Handle Plex-specific error processing"""
        # Add Plex-specific context to the errors
        categorized_errors = self.categorize_plex_errors(errors)
        
        # Call the base implementation with processed errors
        super().handle_errors(categorized_errors, container)
    
    def categorize_plex_errors(self, errors):
        """Categorize Plex errors by type for better reporting"""
        # This is a placeholder for more sophisticated error categorization
        # In a real implementation, this would parse the Plex log format and categorize errors
        return errors 