@app.route('/api/monitors', methods=['POST'])
def add_monitor():
    """Add a new monitor"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Validate required fields
        required_fields = ['name', 'container_name', 'log_pattern']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400

        # Load current config
        config = load_config()
        
        # Add new monitor with enabled=True by default
        config['monitors'][data['name']] = {
            'enabled': True,  # Enable monitor by default
            'container_name': data['container_name'],
            'log_pattern': data['log_pattern'],
            'check_interval': data.get('check_interval', 60),
            'alert_threshold': data.get('alert_threshold', 5),
            'alert_interval': data.get('alert_interval', 300)
        }
        
        # Save updated config
        save_config(config)
        
        # Verify Docker client is available
        if not monitorr.docker_client:
            logger.error("Docker client not available. Please check Docker daemon is running.")
            return jsonify({'error': 'Docker client not available. Please check Docker daemon is running.'}), 500
        
        # Reload monitors
        if monitorr.reload_monitors():
            logger.info(f"Successfully added and started monitor: {data['name']}")
            return jsonify({
                'message': 'Monitor added and started successfully',
                'status': 'active'
            }), 201
        else:
            logger.warning(f"Monitor {data['name']} added but failed to start")
            return jsonify({
                'message': 'Monitor added but failed to start. Please check the logs for details.',
                'status': 'error'
            }), 500
            
    except Exception as e:
        logger.error(f"Error adding monitor: {e}")
        return jsonify({'error': str(e)}), 500 