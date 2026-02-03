# Quick Start Guide - Monitorr on Unraid

## Quick Setup (5 minutes)

### 1. Build and Transfer Image

On your development machine:
```bash
cd /home/sam/Monitorr
docker build -t monitorr:latest .
docker save monitorr:latest > monitorr.tar
```

Transfer to Unraid (replace with your Unraid IP):
```bash
scp monitorr.tar root@YOUR_UNRAID_IP:/mnt/user/appdata/monitorr/
```

### 2. On Unraid Server

SSH into Unraid and run:
```bash
# Load the image
docker load -i /mnt/user/appdata/monitorr/monitorr.tar

# Create directories
mkdir -p /mnt/user/appdata/monitorr/logs

# Copy config template
cp /mnt/user/appdata/monitorr/config.example.yml /mnt/user/appdata/monitorr/config.yml
```

### 3. Install Template

Copy the template to Unraid:
```bash
# On your development machine
scp monitorr.xml root@YOUR_UNRAID_IP:/boot/config/plugins/dockerMan/templates-user/
```

Or manually:
1. Copy `monitorr.xml` to your Unraid flash drive: `/boot/config/plugins/dockerMan/templates-user/monitorr.xml`
2. Refresh Docker page in Unraid web interface

### 4. Add Container in Unraid

1. Go to **Docker** tab
2. Click **Add Container**
3. Select **Monitorr** from template dropdown
4. Configure:
   - **WebUI Port:** `5000` (or your choice)
   - **Config Path:** `/mnt/user/appdata/monitorr/config.yml`
   - **Logs Path:** `/mnt/user/appdata/monitorr/logs`
   - **Docker Socket:** `/var/run/docker.sock`
   - **Timezone:** Your timezone (e.g., `America/New_York`)
   - **Flask Secret Key:** Generate random string (e.g., `openssl rand -hex 32`)
5. Click **Apply**

### 5. Access and Configure

1. Open browser: `http://YOUR_UNRAID_IP:5000`
2. Go to **Settings** → **Docker Settings** → Test connection
3. Go to **Containers** → Click **Monitor** on containers you want to monitor
4. Configure alerts in **Settings** → **Configuration** (optional)

## Minimal Config Example

Edit `/mnt/user/appdata/monitorr/config.yml`:

```yaml
docker:
  host: "local"

monitors:
  plex:
    container_name: "plex"  # Change to your container name
    enabled: true
    error_patterns:
      - "Error:"
      - "Exception:"
      - "Fatal:"
    check_interval: 60

alerts:
  discord:
    enabled: false  # Set to true and add webhook URL if desired
    webhook_url: ""
    cooldown: 300
```

## Verify It's Working

```bash
# Check container is running
docker ps | grep monitorr

# Check logs
docker logs monitorr

# Check application logs
tail -f /mnt/user/appdata/monitorr/logs/monitorr.log
```

## Common Issues

**Container won't start:**
- Check: `docker logs monitorr`
- Verify paths exist: `ls -la /mnt/user/appdata/monitorr/`

**Can't access web UI:**
- Check port isn't in use: `netstat -tuln | grep 5000`
- Verify container is running: `docker ps`

**Docker connection fails:**
- Verify socket is mounted: Check container settings
- Test: `docker exec monitorr python -c "import docker; docker.from_env().ping()"`

For detailed setup, see `UNRAID_SETUP.md`
