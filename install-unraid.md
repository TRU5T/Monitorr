# Installing Monitorr on Unraid

This guide explains how to install Monitorr on your Unraid server to monitor Docker containers and their logs.

## Method 1: Using Docker Compose (Recommended)

1. **SSH into your Unraid server**

2. **Create a directory for Monitorr:**
   ```bash
   mkdir -p /mnt/user/appdata/monitorr
   cd /mnt/user/appdata/monitorr
   ```

3. **Copy all Monitorr files to this directory:**
   - Transfer the Monitorr files from your development PC to this directory using SFTP or another file transfer method
   - Alternatively, you can clone from a Git repository if you've pushed your code there

4. **Build and start the container:**
   ```bash
   docker-compose up -d
   ```

5. **Access Monitorr:**
   - Open a web browser and navigate to `http://your-unraid-ip:5000`

## Method 2: Using Unraid Docker UI

1. **Build the Docker image locally on your development PC:**
   ```bash
   docker build -t monitorr:latest .
   docker save monitorr:latest > monitorr.tar
   ```

2. **Transfer the image to your Unraid server:**
   - Copy the `monitorr.tar` file to your Unraid server

3. **Import the image on Unraid:**
   ```bash
   docker load -i monitorr.tar
   ```

4. **Add the Docker container in Unraid UI:**
   - Go to the Docker tab in Unraid web interface
   - Click "Add Container"
   - Fill in the following details:
     - Name: monitorr
     - Repository: monitorr:latest
     - Network Type: Bridge
     - Port Mappings: 5000:5000
     - Add the following volumes:
       - `/mnt/user/appdata/monitorr/config.yml:/app/config.yml`
       - `/mnt/user/appdata/monitorr/monitorr.log:/app/monitorr.log`
       - `/var/run/docker.sock:/var/run/docker.sock`
     - Environment Variables:
       - `TZ=America/New_York` (adjust to your timezone)
       - `FLASK_SECRET_KEY=change_this_to_a_random_string`

5. **Start the container and access Monitorr:**
   - Open a web browser and navigate to `http://your-unraid-ip:5000`

## Method 3: Using Unraid Community Applications (Future)

When Monitorr is published as a Community Application:
1. Go to the Apps tab in Unraid
2. Search for "Monitorr"
3. Click Install and follow the prompts

## Configuration

1. **Initial Setup:**
   - Navigate to Settings → Docker Settings
   - The local Docker socket should be automatically detected
   - Click "Test Connection" to verify

2. **Add Monitors:**
   - Navigate to Containers
   - Click "Monitor" next to any container you want to monitor
   - Choose the appropriate monitor type and settings

## Troubleshooting

If the Docker connection fails:
1. Make sure `/var/run/docker.sock` is properly mounted in the container
2. Check if the Docker socket is accessible and has proper permissions
3. Review the logs at `/mnt/user/appdata/monitorr/monitorr.log`

For any other issues, check the container logs:
```bash
docker logs monitorr
``` 