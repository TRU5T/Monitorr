"""
Dashboard blueprint for Monitorr web interface
"""

from flask import Blueprint, render_template, current_app, redirect, url_for, flash
import docker
import datetime
import threading

bp = Blueprint('dashboard', __name__)

@bp.route('/')
def index():
    """Dashboard home page with monitor status"""
    monitorr = current_app.config['MONITORR_INSTANCE']
    if not monitorr:
        # No Monitorr instance available
        return render_template('dashboard/not_started.html')
    
    monitors_status = []
    for monitor_name, monitor in monitorr.monitors.items():
        try:
            container = monitor.get_container()
            container_status = container.status if container else "not found"
            
            # Get last check time
            last_check = "Never" if not monitor.last_check_time else monitor.last_check_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Get error count in the last 24 hours
            error_count = 0
            
            monitors_status.append({
                'name': monitor_name,
                'container_name': monitor.container_name,
                'status': container_status,
                'last_check': last_check,
                'error_count': error_count,
                'check_interval': monitor.config.get('check_interval', 60)
            })
        except Exception as e:
            monitors_status.append({
                'name': monitor_name,
                'container_name': monitor.container_name,
                'status': "error",
                'error': str(e),
                'last_check': "Never",
                'error_count': 0,
                'check_interval': monitor.config.get('check_interval', 60)
            })
    
    # Get alerter status
    alert_status = []
    for alerter_name, alerter in monitorr.alert_manager.alerters.items():
        alert_status.append({
            'name': alerter_name,
            'enabled': True,
            'type': alerter_name
        })
    
    return render_template('dashboard/index.html', 
                           monitors=monitors_status, 
                           alerters=alert_status,
                           monitorr_running=True)

@bp.route('/check/<monitor_name>')
def check_now(monitor_name):
    """Trigger an immediate check for a specific monitor"""
    monitorr = current_app.config['MONITORR_INSTANCE']
    
    if not monitorr or monitor_name not in monitorr.monitors:
        flash(f"Monitor {monitor_name} not found", "danger")
        return redirect(url_for('dashboard.index'))
    
    # Run check in a separate thread to avoid blocking
    def run_check():
        try:
            monitorr.monitors[monitor_name].check_logs()
            flash(f"Log check completed for {monitor_name}", "success")
        except Exception as e:
            flash(f"Error checking logs for {monitor_name}: {e}", "danger")
    
    thread = threading.Thread(target=run_check)
    thread.daemon = True
    thread.start()
    
    flash(f"Log check triggered for {monitor_name}", "info")
    return redirect(url_for('dashboard.index')) 