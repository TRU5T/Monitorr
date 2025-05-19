#!/usr/bin/env python3
"""
Monitorr - Docker container log monitoring with alerting
"""

import os
import sys
import time
import yaml
import docker
import logging
import schedule
import threading
import argparse
from datetime import datetime
from dotenv import load_dotenv

# Local imports
from monitors import get_monitor
from alerts import AlertManager

# Ensure log file exists and has proper permissions
log_file = 'monitorr.log'
if not os.path.exists(log_file):
    with open(log_file, 'a') as f:
        pass
os.chmod(log_file, 0o666)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file)
    ]
)
logger = logging.getLogger('monitorr')

def load_config():
    """Load configuration from config.yml"""
    default_config = {
        'docker': {
            'host': 'local',
            'tls': False,
            'timeout': 10
        },
        'monitors': {},
        'alerts': {
            'smtp': {
                'enabled': False,
                'server': 'smtp.example.com',
                'port': 587,
                'use_tls': True,
                'username': 'your-email@example.com',
                'password': '',
                'from_email': 'your-email@example.com',
                'to_emails': ['alerts@example.com'],
                'cooldown': 1800
            },
            'discord': {
                'enabled': False,
                'webhook_url': '',
                'cooldown': 300,
                'mentions': ['@everyone']
            }
        }
    }
    
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
            # Ensure we have a valid config dictionary
            if not isinstance(config, dict):
                logger.warning("Invalid config.yml format. Using default configuration.")
                config = default_config
            # Ensure all required sections exist
            for section in ['docker', 'monitors', 'alerts']:
                if section not in config:
                    config[section] = default_config[section]
            return config
    except FileNotFoundError:
        logger.warning("config.yml not found. Creating default configuration.")
        try:
            with open('config.yml', 'w') as f:
                yaml.dump(default_config, f, default_flow_style=False)
            return default_config
        except Exception as e:
            logger.error(f"Failed to create default config.yml: {e}")
            return default_config
    except yaml.YAMLError as e:
        logger.error(f"Error parsing config.yml: {e}")
        return default_config
    except Exception as e:
        logger.error(f"Unexpected error loading config: {e}")
        return default_config

class Monitorr:
    def __init__(self):
        """Initialize the Monitorr application"""
        load_dotenv()
        self.config = load_config()
        
        # Initialize Docker client
        self.docker_client = self._setup_docker_client()
        
        self.alert_manager = AlertManager(self.config['alerts'])
        self.monitors = {}
        self._setup_monitors()
    
    def _setup_docker_client(self):
        """Set up Docker client based on configuration"""
        # Get Docker connection settings
        docker_config = self.config.get('docker', {})
        docker_host = docker_config.get('host', 'local')
        use_tls = docker_config.get('tls', False)
        timeout = docker_config.get('timeout', 10)
        
        # Connect to Docker
        try:
            if docker_host == 'local':
                # Connect to local Docker daemon
                client = docker.from_env(timeout=timeout)
                logger.info("Connecting to local Docker daemon")
            else:
                # Connect to remote Docker host
                tls_config = None
                if use_tls:
                    cert_path = docker_config.get('tls_cert_path')
                    key_path = docker_config.get('tls_key_path')
                    ca_path = docker_config.get('tls_ca_path')
                    
                    if cert_path and key_path and ca_path:
                        tls_config = docker.tls.TLSConfig(
                            client_cert=(cert_path, key_path),
                            ca_cert=ca_path,
                            verify=True
                        )
                
                logger.info(f"Connecting to remote Docker host at {docker_host}")
                client = docker.DockerClient(
                    base_url=docker_host,
                    tls=tls_config,
                    timeout=timeout
                )
            
            # Test connection
            client.ping()
            logger.info(f"Connected to Docker: {client.version()['Version']}")
            return client
        except docker.errors.DockerException as e:
            logger.error(f"Failed to connect to Docker: {e}")
            logger.error("Please check your Docker configuration or configure a remote Docker host through the web interface.")
            return None
        
    def _setup_monitors(self):
        """Set up container monitors based on configuration"""
        # If no Docker client, don't set up monitors
        if not self.docker_client:
            logger.warning("No Docker client available, skipping monitor setup")
            return
        
        # Ensure monitors section exists
        if 'monitors' not in self.config:
            self.config['monitors'] = {}
            logger.warning("No monitors section in config, using empty configuration")
            return
            
        for monitor_name, monitor_config in self.config['monitors'].items():
            if not isinstance(monitor_config, dict):
                logger.warning(f"Invalid configuration for monitor {monitor_name}, skipping")
                continue
                
            if not monitor_config.get('enabled', False):
                continue
                
            try:
                monitor_class = get_monitor(monitor_name)
                if monitor_class:
                    self.monitors[monitor_name] = monitor_class(
                        self.docker_client,
                        monitor_config,
                        self.alert_manager
                    )
                    logger.info(f"Initialized monitor for {monitor_name}")
                else:
                    logger.warning(f"No monitor found for {monitor_name}")
            except Exception as e:
                logger.error(f"Failed to initialize monitor {monitor_name}: {e}")
    
    def start(self, with_web=False, web_host='0.0.0.0', web_port=5000):
        """Start the monitoring process"""
        logger.info("Starting Monitorr...")
        
        # Only start monitoring if Docker client is available and monitors are configured
        if self.docker_client and self.monitors:
            # Set up schedules
            for monitor_name, monitor in self.monitors.items():
                interval = monitor.config.get('check_interval', 60)
                schedule.every(interval).seconds.do(monitor.check_logs)
                logger.info(f"Scheduled {monitor_name} monitor to run every {interval} seconds")
        else:
            logger.warning("Docker client not available or no monitors configured. Monitoring will not be active.")
        
        # Start web interface if requested
        if with_web:
            # Import here to avoid circular imports
            from web import create_app
            
            # Create Flask app with this Monitorr instance
            app = create_app(self)
            
            # Start web server in a separate thread
            web_thread = threading.Thread(
                target=app.run,
                kwargs={
                    'host': web_host,
                    'port': web_port,
                    'debug': False,
                    'use_reloader': False
                }
            )
            web_thread.daemon = True
            web_thread.start()
            logger.info(f"Web interface started on http://{web_host}:{web_port}")
        
        # Main loop
        try:
            while True:
                if self.docker_client and self.monitors:
                    schedule.run_pending()
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Shutting down Monitorr...")

def start_web_only(host='0.0.0.0', port=5000):
    """Start only the web interface without monitoring"""
    # Create a Monitorr instance but don't start the monitoring process
    monitorr = None
    try:
        monitorr = Monitorr()
    except Exception as e:
        logger.warning(f"Could not initialize Monitorr for web interface: {e}")
    
    # Import here to avoid circular imports
    from web import create_app
    
    # Create Flask app with the Monitorr instance (or None if it failed)
    app = create_app(monitorr)
    
    logger.info(f"Starting web interface only on http://{host}:{port}")
    app.run(host=host, port=port, debug=False)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Monitorr - Docker container log monitoring with alerting')
    parser.add_argument('--web', action='store_true', help='Start with web interface')
    parser.add_argument('--web-only', action='store_true', help='Start only the web interface without monitoring')
    parser.add_argument('--host', default='0.0.0.0', help='Web interface host (default: 0.0.0.0)')
    parser.add_argument('--port', type=int, default=5000, help='Web interface port (default: 5000)')
    
    args = parser.parse_args()
    
    if args.web_only:
        start_web_only(host=args.host, port=args.port)
    else:
        app = Monitorr()
        app.start(with_web=args.web, web_host=args.host, web_port=args.port) 