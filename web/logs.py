"""
Logs blueprint for viewing container logs
"""

from flask import Blueprint, render_template, current_app, request, jsonify
import docker
from datetime import datetime, timedelta
import re

bp = Blueprint('logs', __name__)

@bp.route('/')
def index():
    """Logs overview page"""
    monitorr = current_app.config['MONITORR_INSTANCE']
    if not monitorr:
        return render_template('logs/not_available.html')
    
    monitors = []
    for monitor_name, monitor in monitorr.monitors.items():
        container = monitor.get_container()
        if container:
            monitors.append({
                'name': monitor_name,
                'container_name': monitor.container_name,
                'status': container.status
            })
    
    return render_template('logs/index.html', monitors=monitors)

@bp.route('/<monitor_name>')
def view_logs(monitor_name):
    """View logs for a specific monitor/container"""
    monitorr = current_app.config['MONITORR_INSTANCE']
    
    # Check if this is a monitor or a direct container request
    if monitorr and monitor_name in monitorr.monitors:
        # This is a monitored container
        monitor = monitorr.monitors[monitor_name]
        container_name = monitor.container_name
        error_patterns = monitor.error_patterns
        ignore_patterns = monitor.ignore_patterns
        compiled_error_patterns = monitor.compiled_error_patterns
        compiled_ignore_patterns = monitor.compiled_ignore_patterns
        is_monitored = True
    else:
        # This is a direct container request (not monitored)
        container_name = monitor_name
        # Create default patterns for direct container access
        error_patterns = [r'error', r'exception', r'fatal', r'failed']
        ignore_patterns = []
        # Compile patterns
        compiled_error_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in error_patterns]
        compiled_ignore_patterns = []
        is_monitored = False
    
    # Get Docker client
    docker_client = None
    if monitorr and monitorr.docker_client:
        docker_client = monitorr.docker_client
    else:
        # Try to get docker client from config
        try:
            from web.containers import get_docker_client
            docker_client = get_docker_client()
        except Exception as e:
            return render_template('logs/error.html', 
                                  monitor_name=monitor_name,
                                  container_name=container_name,
                                  error=f"Could not connect to Docker: {str(e)}")
    
    if not docker_client:
        return render_template('logs/error.html', 
                              monitor_name=monitor_name,
                              container_name=container_name,
                              error="Could not connect to Docker")
    
    # Get container
    try:
        container = docker_client.containers.get(container_name)
    except Exception as e:
        return render_template('logs/container_not_found.html', 
                              monitor_name=monitor_name,
                              container_name=container_name)
    
    # Get time range for logs
    time_range = request.args.get('range', '1h')  # Default 1 hour
    
    # Get filtering options
    filter_type = request.args.get('filter', 'all')  # all, errors, custom
    filter_text = request.args.get('text', '')  # custom filter text
    
    since = None
    if time_range == '1h':
        since = datetime.now() - timedelta(hours=1)
    elif time_range == '24h':
        since = datetime.now() - timedelta(hours=24)
    elif time_range == '7d':
        since = datetime.now() - timedelta(days=7)
    elif time_range == 'all':
        since = None
    
    # Limit number of lines based on time range
    if time_range == 'all':
        tail = 5000  # Higher limit for all logs
    else:
        tail = 2000  # Reasonable limit for other time ranges
    
    # Get logs
    try:
        logs = container.logs(
            since=since,
            timestamps=True,
            tail=tail,
            stream=False
        ).decode('utf-8')
        
        # Compile custom filter if provided
        custom_filter = None
        if filter_text:
            try:
                custom_filter = re.compile(filter_text, re.IGNORECASE)
            except re.error:
                # If regex is invalid, use plain text search
                custom_filter = filter_text.lower()
        
        # Process logs
        log_lines = []
        for line in logs.splitlines():
            if not line.strip():
                continue
                
            # Check if line matches any error pattern
            is_error = any(pattern.search(line) for pattern in compiled_error_patterns)
            # Check if line matches any ignore pattern 
            is_ignored = any(pattern.search(line) for pattern in compiled_ignore_patterns)
            
            # Apply filters
            if filter_type == 'errors' and (not is_error or is_ignored):
                continue
                
            if filter_type == 'custom' and custom_filter:
                if isinstance(custom_filter, re.Pattern):
                    if not custom_filter.search(line):
                        continue
                else:
                    if custom_filter not in line.lower():
                        continue
            
            line_class = ""
            if is_error and not is_ignored:
                line_class = "error"
            
            log_lines.append({
                'line': line,
                'class': line_class,
                'timestamp': line.split(' ')[0] if ' ' in line else ''
            })
        
    except Exception as e:
        return render_template('logs/error.html', 
                                monitor_name=monitor_name,
                                container_name=container_name,
                                error=str(e))
    
    return render_template('logs/view.html',
                            monitor_name=monitor_name,
                            container_name=container_name,
                            logs=log_lines,
                            time_range=time_range,
                            filter_type=filter_type,
                            filter_text=filter_text,
                            error_patterns=error_patterns,
                            ignore_patterns=ignore_patterns,
                            is_monitored=is_monitored)

@bp.route('/api/<monitor_name>')
def api_logs(monitor_name):
    """API endpoint for fetching logs (for AJAX)"""
    monitorr = current_app.config['MONITORR_INSTANCE']
    
    # Check if this is a monitor or a direct container request
    if monitorr and monitor_name in monitorr.monitors:
        # This is a monitored container
        monitor = monitorr.monitors[monitor_name]
        container_name = monitor.container_name
        compiled_error_patterns = monitor.compiled_error_patterns
        compiled_ignore_patterns = monitor.compiled_ignore_patterns
        is_monitored = True
    else:
        # This is a direct container request (not monitored)
        container_name = monitor_name
        # Create default patterns for direct container access
        error_patterns = [r'error', r'exception', r'fatal', r'failed']
        ignore_patterns = []
        # Compile patterns
        compiled_error_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in error_patterns]
        compiled_ignore_patterns = []
        is_monitored = False
    
    # Get Docker client
    docker_client = None
    if monitorr and monitorr.docker_client:
        docker_client = monitorr.docker_client
    else:
        # Try to get docker client from config
        try:
            from web.containers import get_docker_client
            docker_client = get_docker_client()
        except Exception as e:
            return jsonify({'error': f"Could not connect to Docker: {str(e)}"}), 500
    
    if not docker_client:
        return jsonify({'error': "Could not connect to Docker"}), 500
    
    # Get container
    try:
        container = docker_client.containers.get(container_name)
    except Exception as e:
        return jsonify({'error': f'Container {container_name} not found'}), 404
    
    # Get time range for logs
    time_range = request.args.get('range', '1h')  # Default 1 hour
    
    # Get filtering options
    filter_type = request.args.get('filter', 'all')  # all, errors, custom
    filter_text = request.args.get('text', '')  # custom filter text
    
    since = None
    if time_range == '1h':
        since = datetime.now() - timedelta(hours=1)
    elif time_range == '24h':
        since = datetime.now() - timedelta(hours=24)
    elif time_range == '7d':
        since = datetime.now() - timedelta(days=7)
    elif time_range == 'all':
        since = None
    
    # Limit number of lines based on time range
    if time_range == 'all':
        tail = 5000  # Higher limit for all logs
    else:
        tail = 2000  # Reasonable limit for other time ranges
    
    # Get logs
    try:
        logs = container.logs(
            since=since,
            timestamps=True,
            tail=tail,
            stream=False
        ).decode('utf-8')
        
        # Compile custom filter if provided
        custom_filter = None
        if filter_text:
            try:
                custom_filter = re.compile(filter_text, re.IGNORECASE)
            except re.error:
                # If regex is invalid, use plain text search
                custom_filter = filter_text.lower()
        
        # Process logs
        log_lines = []
        for line in logs.splitlines():
            if not line.strip():
                continue
            
            # Check if line matches any error pattern
            is_error = any(pattern.search(line) for pattern in compiled_error_patterns)
            # Check if line matches any ignore pattern 
            is_ignored = any(pattern.search(line) for pattern in compiled_ignore_patterns)
            
            # Apply filters
            if filter_type == 'errors' and (not is_error or is_ignored):
                continue
                
            if filter_type == 'custom' and custom_filter:
                if isinstance(custom_filter, re.Pattern):
                    if not custom_filter.search(line):
                        continue
                else:
                    if custom_filter not in line.lower():
                        continue
            
            timestamp = line.split(' ')[0] if ' ' in line else ''
            
            log_lines.append({
                'line': line,
                'is_error': is_error and not is_ignored,
                'timestamp': timestamp
            })
        
        return jsonify({
            'monitor': monitor_name,
            'container': container_name,
            'logs': log_lines,
            'is_monitored': is_monitored,
            'filter': {
                'type': filter_type,
                'text': filter_text
            }
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 