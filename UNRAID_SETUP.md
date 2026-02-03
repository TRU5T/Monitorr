# Monitorr Unraid Setup Guide

This guide will help you set up Monitorr on your Unraid server using the provided template.

## Prerequisites

- Unraid 6.9.0 or higher
- Docker enabled on your Unraid server
- Basic understanding of Docker containers

## Installation Steps

### Step 1: Prepare the Application Directory

1. SSH into your Unraid server or use the terminal in the Unraid web interface
2. Create the application directory:
   ```bash
   mkdir -p /mnt/user/appdata/monitorr/logs
   ```

### Step 2: Copy Files to Unraid

You have two options:

#### Option A: Build and Transfer Docker Image

1. On your development machine, build the image:
   ```bash
   cd /path/to/Monitorr
   docker build -t monitorr:latest .
   docker save monitorr:latest > monitorr.tar
   ```

2. Transfer `monitorr.tar` to your Unraid server (e.g., to `/mnt/user/appdata/monitorr/`)

3. On Unraid, load the image:
   ```bash
   docker load -i /mnt/user/appdata/monitorr/monitorr.tar
   ```

#### Option B: Build on Unraid

1. Copy the entire Monitorr directory to your Unraid server:
   ```bash
   # On your development machine
   scp -r /path/to/Monitorr root@your-unraid-ip:/mnt/user/appdata/monitorr/
   ```

2. SSH into Unraid and build:
   ```bash
   cd /mnt/user/appdata/monitorr
   docker build -t monitorr:latest .
   ```

### Step 3: Create Initial Configuration

1. Copy the example config:
   ```bash
   cp /mnt/user/appdata/monitorr/config.example.yml /mnt/user/appdata/monitorr/config.yml
   ```

2. Edit the config file to match your setup:
   ```bash
   nano /mnt/user/appdata/monitorr/config.yml
   ```

   At minimum, configure:
   - Docker host (should be "local" for Unraid)
   - At least one monitor (e.g., your Plex container)
   - Alert settings if you want notifications

### Step 4: Install Using Unraid Template

1. **Copy the template file:**
   - Copy `monitorr.xml` to your Unraid flash drive in the `config/plugins/dockerMan/templates-user/` directory
   - Or use the Unraid web interface to add a custom template

2. **Add Container in Unraid:**
   - Go to the **Docker** tab in Unraid
   - Click **Add Container**
   - Click **Template Repositories** → **Add Template**
   - Enter the path to your template or select it from the list
   - Click **Add Container** again and select **Monitorr** from the template dropdown

3. **Configure the Container:**
   - **Name:** monitorr (or your preferred name)
   - **Repository:** monitorr:latest
   - **WebUI Port:** 5000 (or your preferred port)
   - **Config Path:** `/mnt/user/appdata/monitorr/config.yml`
   - **Logs Path:** `/mnt/user/appdata/monitorr/logs`
   - **Docker Socket:** `/var/run/docker.sock`
   - **Timezone:** Set to your timezone (e.g., `America/New_York`, `Europe/London`)
   - **Flask Secret Key:** Generate a random string (important for security!)
   - **SMTP Password:** (Optional) If using email alerts
   - **Discord Webhook URL:** (Optional) If using Discord alerts

4. **Click Apply** to create and start the container

### Step 5: Access Monitorr

1. Open your web browser
2. Navigate to: `http://your-unraid-ip:5000`
3. You should see the Monitorr dashboard

### Step 6: Initial Configuration via Web UI

1. **Configure Docker Connection:**
   - Go to **Settings** → **Docker Settings**
   - The local Docker socket should be auto-detected
   - Click **Test Connection** to verify

2. **Add Monitors:**
   - Go to **Containers** tab
   - View available containers
   - Click **Monitor** next to containers you want to monitor
   - Configure error patterns and check intervals

3. **Configure Alerts (Optional):**
   - Go to **Settings** → **Configuration**
   - Enable and configure SMTP or Discord alerts
   - Save the configuration

## Configuration Examples

### Example: Monitor Plex Container

Edit `/mnt/user/appdata/monitorr/config.yml`:

```yaml
docker:
  host: "local"
  tls: false
  timeout: 10

monitors:
  plex:
    container_name: "plex"
    enabled: true
    error_patterns:
      - "Error:"
      - "Exception:"
      - "Fatal:"
      - "Critical:"
    check_interval: 60
    ignore_patterns: []

alerts:
  discord:
    enabled: true
    webhook_url: ""  # Set via DISCORD_WEBHOOK_URL env var
    cooldown: 300
    mentions: []
```

### Example: Monitor Multiple Containers

```yaml
monitors:
  plex:
    container_name: "plex"
    enabled: true
    error_patterns:
      - "Error:"
      - "Exception:"
    check_interval: 60
    
  jellyfin:
    container_name: "jellyfin"
    enabled: true
    error_patterns:
      - "Error:"
      - "Fatal:"
    check_interval: 120
    
  radarr:
    container_name: "radarr"
    enabled: true
    error_patterns:
      - "Error:"
    check_interval: 60
```

## Troubleshooting

### Container Won't Start

1. **Check container logs:**
   ```bash
   docker logs monitorr
   ```

2. **Verify file permissions:**
   ```bash
   ls -la /mnt/user/appdata/monitorr/
   chmod 644 /mnt/user/appdata/monitorr/config.yml
   chmod -R 777 /mnt/user/appdata/monitorr/logs
   ```

3. **Verify Docker socket access:**
   ```bash
   ls -la /var/run/docker.sock
   ```

### Web Interface Not Accessible

1. **Check if port is in use:**
   ```bash
   netstat -tuln | grep 5000
   ```

2. **Verify firewall settings** (if using Unraid firewall)

3. **Check container is running:**
   ```bash
   docker ps | grep monitorr
   ```

### Docker Connection Issues

1. **Verify Docker socket is mounted:**
   - Check container settings in Unraid
   - Ensure `/var/run/docker.sock` is mapped correctly

2. **Test Docker connection manually:**
   ```bash
   docker exec monitorr python -c "import docker; c=docker.from_env(); print(c.ping())"
   ```

### Configuration Not Saving

1. **Check file permissions:**
   ```bash
   chmod 644 /mnt/user/appdata/monitorr/config.yml
   ```

2. **Verify volume mapping** in container settings

3. **Check application logs:**
   ```bash
   tail -f /mnt/user/appdata/monitorr/logs/monitorr.log
   ```

## Updating Monitorr

1. **Stop the container** in Unraid Docker interface

2. **Pull/build new image:**
   ```bash
   cd /mnt/user/appdata/monitorr
   docker build -t monitorr:latest .
   ```

3. **Start the container** again

## Security Notes

1. **Change Flask Secret Key:** Always set a unique `FLASK_SECRET_KEY` environment variable
2. **Docker Socket Access:** The container has access to the Docker socket, which provides significant privileges
3. **Network Access:** Consider restricting web UI access to your local network
4. **Sensitive Data:** Store passwords and API keys in environment variables, not in config.yml

## Support

For issues, feature requests, or contributions:
- GitHub: https://github.com/yourusername/Monitorr
- Check logs: `/mnt/user/appdata/monitorr/logs/monitorr.log`
