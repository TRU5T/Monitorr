"""
Monitors module for different container types
"""

from monitors.base import BaseMonitor
from monitors.plex import PlexMonitor
from monitors.sonarr import SonarrMonitor
from monitors.radarr import RadarrMonitor
from monitors.jellyfin import JellyfinMonitor

def get_monitor(monitor_type):
    """Get the appropriate monitor class for the given type"""
    monitors = {
        'plex': PlexMonitor,
        'sonarr': SonarrMonitor,
        'radarr': RadarrMonitor,
        'jellyfin': JellyfinMonitor,
        'generic': BaseMonitor
    }
    return monitors.get(monitor_type.lower()) 