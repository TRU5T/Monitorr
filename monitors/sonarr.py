"""
Sonarr-specific monitor for detecting errors in Sonarr logs
"""

import logging
import re
from monitors.base import BaseMonitor

logger = logging.getLogger('monitorr.monitor.sonarr')

class SonarrMonitor(BaseMonitor):
    def __init__(self, docker_client, config, alert_manager):
        """Initialize Sonarr monitor with specific configuration"""
        super().__init__(docker_client, config, alert_manager)
        
        # Add default Sonarr error patterns if none specified
        if not self.error_patterns:
            self.error_patterns = [
                "Error:",
                "ERROR",
                "Exception:",
                "Fatal:",
                "failure detected"
            ]
            # Recompile patterns
            self.compiled_error_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.error_patterns]
    
    def process_logs(self, logs, container):
        """Process Sonarr-specific logs"""
        # Call base implementation
        super().process_logs(logs, container)
        
    def handle_errors(self, errors, container):
        """Handle Sonarr-specific error processing"""
        # Add Sonarr-specific context to the errors
        categorized_errors = self.categorize_sonarr_errors(errors)
        
        # Call the base implementation with processed errors
        super().handle_errors(categorized_errors, container)
    
    def categorize_sonarr_errors(self, errors):
        """Categorize Sonarr errors by type for better reporting"""
        # This is a placeholder for more sophisticated error categorization
        # In a real implementation, this would parse the Sonarr log format and categorize errors
        return errors 