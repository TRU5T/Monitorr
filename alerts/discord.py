"""
Discord alerter for sending webhook notifications
"""

import os
import logging
from datetime import datetime
from discord_webhook import DiscordWebhook, DiscordEmbed

logger = logging.getLogger('monitorr.alerts.discord')

class DiscordAlerter:
    def __init__(self, config):
        """Initialize Discord alerter with configuration"""
        self.config = config
        
        # Get webhook URL from environment variable
        self.webhook_url = os.environ.get('DISCORD_WEBHOOK_URL')
        if not self.webhook_url:
            logger.warning("Discord webhook URL not found in environment variables")
            self.webhook_url = config.get('webhook_url', '')
            
        self.mentions = config.get('mentions', [])
        
        # Validate configuration
        self._validate_config()
    
    def _validate_config(self):
        """Validate Discord configuration"""
        if not self.webhook_url:
            raise ValueError("Missing Discord webhook URL")
    
    def send(self, alert_data):
        """Send Discord alert"""
        container_name = alert_data.get('container_name')
        container_id = alert_data.get('container_id', '')[:8]  # First 8 chars of container ID
        timestamp = alert_data.get('timestamp')
        errors = alert_data.get('errors', [])
        
        if not errors:
            logger.warning("No errors to report")
            return
        
        try:
            # Create webhook
            webhook = DiscordWebhook(url=self.webhook_url)
            
            # Add mentions if configured
            if self.mentions:
                content = " ".join(self.mentions)
                webhook.content = content
            
            # Create embed
            embed = DiscordEmbed(
                title=f"🚨 Alert: Errors in {container_name}",
                color=0xFF0000  # Red
            )
            
            # Add fields
            embed.add_embed_field(name="Container", value=f"{container_name} ({container_id})")
            embed.add_embed_field(name="Time", value=timestamp)
            embed.add_embed_field(name="Error Count", value=str(len(errors)))
            
            # Format and add errors
            formatted_errors = self._format_errors(errors)
            embed.add_embed_field(name="Errors", value=formatted_errors, inline=False)
            
            # Set footer
            embed.set_footer(text="Monitorr - Docker Log Monitor")
            
            # Add embed to webhook
            webhook.add_embed(embed)
            
            # Execute webhook
            response = webhook.execute()
            
            if response.status_code == 204:
                logger.info("Discord alert sent successfully")
            else:
                logger.warning(f"Discord webhook returned status code {response.status_code}")
                
        except Exception as e:
            logger.error(f"Failed to send Discord alert: {e}")
            raise
    
    def _format_errors(self, errors):
        """Format errors for Discord message"""
        # Discord has a limit on field value length, so we need to truncate
        MAX_LENGTH = 1000
        
        # Join errors with newlines
        formatted = "\n".join([f"• {error[:100]}{'...' if len(error) > 100 else ''}" for error in errors[:5]])
        
        # If there are more errors, add a note
        if len(errors) > 5:
            formatted += f"\n\n... and {len(errors) - 5} more errors"
            
        # Truncate if still too long
        if len(formatted) > MAX_LENGTH:
            formatted = formatted[:MAX_LENGTH-3] + "..."
            
        return formatted 