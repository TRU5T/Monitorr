"""
Alerts module for sending notifications
"""

import logging
from datetime import datetime, timedelta
from alerts.smtp import SMTPAlerter
from alerts.discord import DiscordAlerter

logger = logging.getLogger('monitorr.alerts')

class AlertManager:
    def __init__(self, alert_config):
        """Initialize alert manager with configuration"""
        self.config = alert_config
        self.alerters = {}
        self.last_alert_time = {}
        
        # Initialize alerters
        self._init_alerters()
    
    def _init_alerters(self):
        """Initialize configured alerters"""
        # SMTP Alerter
        if 'smtp' in self.config and self.config['smtp'].get('enabled', False):
            try:
                self.alerters['smtp'] = SMTPAlerter(self.config['smtp'])
                logger.info("SMTP alerter initialized")
            except Exception as e:
                logger.error(f"Failed to initialize SMTP alerter: {e}")
        
        # Discord Alerter
        if 'discord' in self.config and self.config['discord'].get('enabled', False):
            try:
                self.alerters['discord'] = DiscordAlerter(self.config['discord'])
                logger.info("Discord alerter initialized")
            except Exception as e:
                logger.error(f"Failed to initialize Discord alerter: {e}")
    
    def send_alert(self, alert_data):
        """Send alerts through all configured alerters"""
        if not self.alerters:
            logger.warning("No alerters configured")
            return
        
        container_name = alert_data.get('container_name')
        now = datetime.now()
        
        for alerter_name, alerter in self.alerters.items():
            # Check cooldown period
            cooldown_key = f"{alerter_name}_{container_name}"
            cooldown = self.config[alerter_name].get('cooldown', 0)
            
            if cooldown_key in self.last_alert_time:
                time_since_last = now - self.last_alert_time[cooldown_key]
                if time_since_last < timedelta(seconds=cooldown):
                    logger.info(f"Skipping {alerter_name} alert for {container_name} (cooldown period)")
                    continue
            
            # Send alert and update last alert time
            try:
                alerter.send(alert_data)
                self.last_alert_time[cooldown_key] = now
                logger.info(f"Sent {alerter_name} alert for {container_name}")
            except Exception as e:
                logger.error(f"Error sending {alerter_name} alert: {e}") 