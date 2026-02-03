"""
Containers blueprint for viewing and managing Docker containers
"""

from flask import Blueprint, render_template, current_app, redirect, url_for, flash, request
import docker
import yaml

bp = Blueprint('containers', __name__)

def get_docker_client():
    """Get Docker client based on current configuration"""
    monitorr = current_app.config['MONITORR_INSTANCE']
    if monitorr and monitorr.docker_client:
        return monitorr.docker_client
    
    # If no Monitorr instance or Docker client, try to create a new one from config
    try:
        with open('config.yml', 'r') as f:
            config = yaml.safe_load(f)
            
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
        return client
    except Exception as e:
        current_app.logger.error(f"Failed to connect to Docker: {e}")
        return None


def _container_image_display(container):
    """Get image name/ID for display without fetching the image (avoids 404 if image was removed)."""
    config_image = container.attrs.get('Config', {}).get('Image') or ''
    if config_image:
        return config_image
    image_id = container.attrs.get('Image', '')
    if image_id.startswith('sha256:'):
        return image_id[7:19]  # 12-char short ID
    return image_id[:12] if len(image_id) >= 12 else image_id


@bp.route('/')
def index():
    """List all containers"""
    docker_client = get_docker_client()
    
    if not docker_client:
        flash("Cannot connect to Docker. Please check your Docker settings.", "danger")
        return redirect(url_for('settings.docker_settings'))
    
    # Get all containers
    try:
        containers = docker_client.containers.list(all=True)
        
        # Get list of existing monitors
        monitorr = current_app.config['MONITORR_INSTANCE']
        monitored_containers = set()
        if monitorr:
            for monitor in monitorr.monitors.values():
                monitored_containers.add(monitor.container_name)
        
        # Format container data for display (use attrs to avoid fetching image;
        # image may have been removed after container was created, causing 404)
        container_list = []
        for container in containers:
            image_display = _container_image_display(container)
            container_list.append({
                'id': container.id[:12],
                'name': container.name,
                'image': image_display,
                'status': container.status,
                'monitored': container.name in monitored_containers
            })
        
        return render_template('containers/index.html', containers=container_list)
    except Exception as e:
        flash(f"Error listing containers: {str(e)}", "danger")
        return redirect(url_for('dashboard.index'))

@bp.route('/details/<container_name>')
def details(container_name):
    """Show container details"""
    docker_client = get_docker_client()
    
    if not docker_client:
        flash("Cannot connect to Docker. Please check your Docker settings.", "danger")
        return redirect(url_for('settings.docker_settings'))
    
    try:
        # Get container
        container = docker_client.containers.get(container_name)
        
        # Get container information (use attrs for image to avoid 404 if image was removed)
        info = {
            'id': container.id,
            'name': container.name,
            'image': _container_image_display(container),
            'status': container.status,
            'created': container.attrs.get('Created', 'Unknown'),
            'ports': container.ports,
            'labels': container.labels,
            'environment': container.attrs.get('Config', {}).get('Env', []),
            'command': container.attrs.get('Config', {}).get('Cmd', []),
            'volumes': container.attrs.get('Mounts', []),
            'networks': container.attrs.get('NetworkSettings', {}).get('Networks', {})
        }
        
        return render_template('containers/details.html', container=info)
    except docker.errors.NotFound:
        flash(f"Container {container_name} not found", "danger")
        return redirect(url_for('containers.index'))
    except Exception as e:
        flash(f"Error getting container details: {str(e)}", "danger")
        return redirect(url_for('containers.index')) 