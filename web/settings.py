"""
Settings blueprint for configuring the application
"""

from flask import Blueprint, render_template, current_app, request, redirect, url_for, flash
import yaml
import os
import docker
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField, IntegerField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Optional, NumberRange, URL

bp = Blueprint('settings', __name__)

class ConfigForm(FlaskForm):
    """Form for editing configuration"""
    yaml_config = TextAreaField('Configuration (YAML)', validators=[DataRequired()])
    submit = SubmitField('Save Configuration')

class DockerHostForm(FlaskForm):
    """Form for Docker host configuration"""
    host_type = SelectField('Host Type', choices=[
        ('local', 'Local Docker Daemon'), 
        ('remote', 'Remote Docker Host')
    ])
    host_url = StringField('Docker Host URL', validators=[Optional()],
                          description='e.g., tcp://192.168.1.100:2375 or unix:///var/run/docker.sock')
    use_tls = BooleanField('Use TLS')
    tls_cert_path = StringField('TLS Certificate Path', validators=[Optional()])
    tls_key_path = StringField('TLS Key Path', validators=[Optional()])
    tls_ca_path = StringField('TLS CA Certificate Path', validators=[Optional()])
    timeout = IntegerField('Connection Timeout (seconds)', default=10, validators=[NumberRange(min=1, max=60)])
    submit = SubmitField('Save Docker Configuration')
    test_connection = SubmitField('Test Connection')

class MonitorForm(FlaskForm):
    """Form for adding a new container monitor"""
    monitor_type = SelectField('Monitor Type', choices=[
        ('plex', 'Plex Media Server'),
        ('jellyfin', 'Jellyfin Media Server'),
        ('sonarr', 'Sonarr'),
        ('radarr', 'Radarr'),
        ('generic', 'Generic Container')
    ])
    check_interval = IntegerField('Check Interval (seconds)', default=60, validators=[NumberRange(min=5, max=3600)])
    enabled = BooleanField('Enabled', default=True)
    submit = SubmitField('Add Monitor')

def test_docker_connection(config):
    """Test connection to Docker host and return results"""
    try:
        # Get Docker connection settings
        docker_config = config.get('docker', {})
        docker_host = docker_config.get('host', 'local')
        use_tls = docker_config.get('tls', False)
        timeout = docker_config.get('timeout', 10)
        
        # Connect to Docker
        if docker_host == 'local':
            # Connect to local Docker daemon
            client = docker.from_env(timeout=timeout)
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
            
            client = docker.DockerClient(
                base_url=docker_host,
                tls=tls_config,
                timeout=timeout
            )
        
        # Test connection
        client.ping()
        version = client.version()
        
        # Get containers
        containers = client.containers.list(all=True)
        
        return {
            'success': True,
            'version': version.get('Version', 'Unknown'),
            'api_version': version.get('ApiVersion', 'Unknown'),
            'os': version.get('Os', 'Unknown'),
            'arch': version.get('Arch', 'Unknown'),
            'containers': [
                {
                    'id': container.id[:12],
                    'name': container.name,
                    'image': container.image.tags[0] if container.image.tags else container.image.id[:12],
                    'status': container.status
                }
                for container in containers
            ]
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }

@bp.route('/', methods=['GET', 'POST'])
def index():
    """Settings page"""
    form = ConfigForm()
    
    # If form is submitted and valid
    if form.validate_on_submit():
        try:
            # Parse YAML to validate it
            config = yaml.safe_load(form.yaml_config.data)
            
            # Save to config.yml
            with open('config.yml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Get Monitorr instance and reload monitors
            monitorr = current_app.config.get('MONITORR_INSTANCE')
            if monitorr and monitorr.reload_monitors():
                flash('Configuration saved and monitors reloaded successfully.', 'success')
            else:
                flash('Configuration saved but failed to reload monitors. Please check the logs.', 'warning')
            
            return redirect(url_for('settings.index'))
        except yaml.YAMLError as e:
            flash(f'Invalid YAML configuration: {str(e)}', 'danger')
    
    # Load current configuration for display
    current_config = ""
    try:
        with open('config.yml', 'r') as f:
            current_config = f.read()
    except FileNotFoundError:
        # If config.yml doesn't exist, try to read from config.example.yml
        try:
            with open('config.example.yml', 'r') as f:
                current_config = f.read()
        except FileNotFoundError:
            flash('No configuration file found', 'warning')
    
    # Set form data if not already set
    if not form.yaml_config.data:
        form.yaml_config.data = current_config
    
    return render_template('settings/index.html', form=form)

@bp.route('/docker', methods=['GET', 'POST'])
def docker_settings():
    """Docker host configuration page"""
    form = DockerHostForm()
    
    # Load current configuration
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        config = {}
    
    docker_config = config.get('docker', {})
    connection_test_result = None
    
    # If form is submitted and valid
    if form.validate_on_submit():
        # Create docker config if it doesn't exist
        if 'docker' not in config:
            config['docker'] = {}
        
        # Update docker configuration
        if form.host_type.data == 'local':
            config['docker']['host'] = 'local'
        else:
            config['docker']['host'] = form.host_url.data
        
        config['docker']['tls'] = form.use_tls.data
        config['docker']['timeout'] = form.timeout.data
        
        # Add TLS certificate paths if TLS is enabled
        if form.use_tls.data:
            if form.tls_cert_path.data:
                config['docker']['tls_cert_path'] = form.tls_cert_path.data
            if form.tls_key_path.data:
                config['docker']['tls_key_path'] = form.tls_key_path.data
            if form.tls_ca_path.data:
                config['docker']['tls_ca_path'] = form.tls_ca_path.data
        else:
            # Remove TLS config if not using TLS
            for key in ['tls_cert_path', 'tls_key_path', 'tls_ca_path']:
                if key in config['docker']:
                    del config['docker'][key]
        
        # Remove testing mode if present
        if 'testing' in config:
            del config['testing']
        
        # Test connection if requested
        if form.test_connection.data:
            connection_test_result = test_docker_connection(config)
            if connection_test_result['success']:
                flash('Successfully connected to Docker host!', 'success')
            else:
                flash(f'Failed to connect to Docker host: {connection_test_result["error"]}', 'danger')
        else:
            # Save configuration
            try:
                with open('config.yml', 'w') as f:
                    yaml.dump(config, f, default_flow_style=False)
                
                flash('Docker configuration saved successfully. Restart Monitorr to apply changes.', 'success')
                
                # Test connection after saving
                connection_test_result = test_docker_connection(config)
                if not connection_test_result['success']:
                    flash(f'Warning: Could not connect to configured Docker host: {connection_test_result["error"]}', 'warning')
                
                return redirect(url_for('settings.docker_settings'))
            except Exception as e:
                flash(f'Error saving configuration: {str(e)}', 'danger')
    
    # Populate form with current values
    if not form.is_submitted():
        host = docker_config.get('host', 'local')
        if host == 'local':
            form.host_type.data = 'local'
        else:
            form.host_type.data = 'remote'
            form.host_url.data = host
        
        form.use_tls.data = docker_config.get('tls', False)
        form.timeout.data = docker_config.get('timeout', 10)
        
        # Set TLS certificate paths if available
        form.tls_cert_path.data = docker_config.get('tls_cert_path', '')
        form.tls_key_path.data = docker_config.get('tls_key_path', '')
        form.tls_ca_path.data = docker_config.get('tls_ca_path', '')
        
        # Test current connection
        connection_test_result = test_docker_connection(config)
    
    return render_template('settings/docker.html', form=form, connection_test=connection_test_result)

@bp.route('/add_monitor/<container_name>', methods=['GET', 'POST'])
def add_monitor(container_name):
    """Add a new container monitor"""
    form = MonitorForm()
    
    # Load current configuration
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
    except (FileNotFoundError, yaml.YAMLError):
        config = {}
    
    # If form is submitted and valid
    if form.validate_on_submit():
        # Create monitors section if it doesn't exist
        if 'monitors' not in config:
            config['monitors'] = {}
        
        # Get monitor type and create appropriate configuration
        monitor_type = form.monitor_type.data
        monitor_name = f"{monitor_type}_{container_name}"
        
        # Create monitor configuration
        monitor_config = {
            'enabled': form.enabled.data,
            'container_name': container_name,
            'check_interval': form.check_interval.data,
            'alert_threshold': 5,  # Default values
            'alert_interval': 300
        }
        
        # Add type-specific configuration
        if monitor_type == 'plex':
            monitor_config['log_pattern'] = r'error|exception|failed'
        elif monitor_type == 'jellyfin':
            monitor_config['log_pattern'] = r'error|exception|failed'
        elif monitor_type == 'sonarr':
            monitor_config['log_pattern'] = r'error|exception|failed'
        elif monitor_type == 'radarr':
            monitor_config['log_pattern'] = r'error|exception|failed'
        else:  # generic
            monitor_config['log_pattern'] = r'error|exception|failed'
        
        # Add monitor to configuration
        config['monitors'][monitor_name] = monitor_config
        
        # Save updated configuration
        try:
            with open('config.yml', 'w') as f:
                yaml.dump(config, f, default_flow_style=False)
            
            # Get Monitorr instance and reload monitors
            monitorr = current_app.config.get('MONITORR_INSTANCE')
            if monitorr and monitorr.reload_monitors():
                flash(f'Monitor {monitor_name} added and started successfully.', 'success')
            else:
                flash(f'Monitor {monitor_name} added but failed to start. Please check the logs.', 'warning')
            
            return redirect(url_for('settings.index'))
        except Exception as e:
            flash(f'Error saving configuration: {str(e)}', 'danger')
    
    return render_template('settings/add_monitor.html', form=form, container_name=container_name)

@bp.route('/env')
def environment():
    """Display environment variables (excluding sensitive ones)"""
    env_vars = {}
    
    # Get all environment variables
    for key, value in os.environ.items():
        # Skip sensitive variables
        if any(s in key.lower() for s in ['password', 'secret', 'key', 'token']):
            value = '******'
        
        env_vars[key] = value
    
    return render_template('settings/environment.html', env_vars=env_vars)

@bp.route('/restart')
def restart():
    """Restart the Monitorr service (not implemented in web interface)"""
    flash('Restart functionality is not implemented in the web interface. Please restart the service manually.', 'warning')
    return redirect(url_for('settings.index'))
 