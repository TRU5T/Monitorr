"""
SMTP alerter for sending email notifications
"""

import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime

logger = logging.getLogger('monitorr.alerts.smtp')

class SMTPAlerter:
    def __init__(self, config):
        """Initialize SMTP alerter with configuration"""
        self.config = config
        self.server = config.get('server')
        self.port = config.get('port', 587)
        self.use_tls = config.get('use_tls', True)
        self.username = config.get('username')
        
        # Get password from environment variable
        self.password = os.environ.get('SMTP_PASSWORD')
        if not self.password:
            logger.warning("SMTP password not found in environment variables")
            self.password = config.get('password', '')
            
        self.from_email = config.get('from_email')
        self.to_emails = config.get('to_emails', [])
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate SMTP configuration"""
        required_fields = ['server', 'username', 'from_email']
        missing_fields = [field for field in required_fields if not self.config.get(field)]
        
        if missing_fields:
            raise ValueError(f"Missing required SMTP configuration: {', '.join(missing_fields)}")
        
        if not self.to_emails:
            raise ValueError("No recipient email addresses configured")
    
    def send(self, alert_data):
        """Send email alert"""
        if not self.to_emails:
            logger.warning("No recipient email addresses configured")
            return
        
        container_name = alert_data.get('container_name')
        timestamp = alert_data.get('timestamp')
        errors = alert_data.get('errors', [])
        
        if not errors:
            logger.warning("No errors to report")
            return
        
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.from_email
            msg['To'] = ', '.join(self.to_emails)
            msg['Subject'] = f"Monitorr Alert: Errors detected in {container_name}"
            
            # Email body
            body = self._format_email_body(alert_data)
            msg.attach(MIMEText(body, 'plain'))
            
            # Connect to server
            server = smtplib.SMTP(self.server, self.port)
            if self.use_tls:
                server.starttls()
            
            # Login if credentials provided
            if self.username and self.password:
                server.login(self.username, self.password)
            
            # Send email
            server.send_message(msg)
            server.quit()
            logger.info(f"Sent email alert to {len(self.to_emails)} recipients")
            
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            raise
    
    def _format_email_body(self, alert_data):
        """Format email body with alert information"""
        container_name = alert_data.get('container_name')
        container_id = alert_data.get('container_id')
        timestamp = alert_data.get('timestamp')
        errors = alert_data.get('errors', [])
        
        body = f"Monitorr Alert: Errors detected in {container_name}\n\n"
        body += f"Container: {container_name} ({container_id})\n"
        body += f"Time: {timestamp}\n"
        body += f"Number of errors: {len(errors)}\n\n"
        body += "Errors:\n"
        
        # Add errors to body
        for i, error in enumerate(errors, 1):
            body += f"{i}. {error}\n"
        
        body += "\n\nThis is an automated alert from Monitorr."
        return body 