# Building Monitorr Image on Unraid

## Quick Build Instructions

You need to build the Docker image before you can run the container. Here are two methods:

## Method 1: Build Directly on Unraid (Recommended)

### Step 1: Copy Source Files to Unraid

From your development machine (WSL), copy the Monitorr directory to Unraid:

```bash
# Replace YOUR_UNRAID_IP with your Unraid server IP
scp -r /home/sam/Monitorr root@YOUR_UNRAID_IP:/mnt/user/appdata/monitorr-source/
```

Or use SCP from Windows:
```powershell
scp -r C:\Users\YourUser\Monitorr root@YOUR_UNRAID_IP:/mnt/user/appdata/monitorr-source/
```

### Step 2: SSH into Unraid and Build

```bash
# SSH into Unraid
ssh root@YOUR_UNRAID_IP

# Navigate to the source directory
cd /mnt/user/appdata/monitorr-source

# Build the Docker image
docker build -t monitorr:latest .

# Verify the image was created
docker images | grep monitorr
```

### Step 3: Create Config Directory and Files

```bash
# Create appdata directory
mkdir -p /mnt/user/appdata/monitorr/logs

# Copy example config
cp /mnt/user/appdata/monitorr-source/config.example.yml /mnt/user/appdata/monitorr/config.yml

# Edit config if needed
nano /mnt/user/appdata/monitorr/config.yml
```

### Step 4: Run the Container

Now you can use the Unraid Docker UI or run the command manually. The image should now be available.

## Method 2: Build on Development Machine and Transfer

### Step 1: Build on Your Development Machine

From WSL:
```bash
cd /home/sam/Monitorr
docker build -t monitorr:latest .
docker save monitorr:latest > monitorr.tar
```

### Step 2: Transfer to Unraid

```bash
# Transfer the image file
scp monitorr.tar root@YOUR_UNRAID_IP:/mnt/user/appdata/monitorr/
```

### Step 3: Load Image on Unraid

SSH into Unraid:
```bash
ssh root@YOUR_UNRAID_IP

# Load the image
docker load -i /mnt/user/appdata/monitorr/monitorr.tar

# Verify
docker images | grep monitorr
```

### Step 4: Create Config Directory

```bash
mkdir -p /mnt/user/appdata/monitorr/logs
cp /path/to/Monitorr/config.example.yml /mnt/user/appdata/monitorr/config.yml
```

## Verify Image is Ready

After building/loading, verify the image exists:

```bash
docker images | grep monitorr
```

You should see:
```
monitorr    latest    <image-id>    <time>    <size>
```

## Troubleshooting Build Issues

### If build fails due to missing files:

Make sure all source files are in the directory:
- Dockerfile
- requirements.txt
- monitorr.py
- web.py
- config.example.yml
- alerts/ directory
- monitors/ directory
- web/ directory

### If you get permission errors:

```bash
chmod -R 755 /mnt/user/appdata/monitorr-source
```

### If Docker build is slow:

Unraid's Docker may be slower. Be patient, or build on your dev machine and transfer.

## After Building

Once the image is built, you can:
1. Use the Unraid Docker UI to add the container using the template
2. Or manually run the docker command (which should now work)

The container should start successfully once the image exists!
