# Publishing Monitorr to GitHub Container Registry (GHCR)

This guide explains how to publish the Monitorr Docker image to GitHub Container Registry so it can be pulled directly on Unraid without building locally.

## Prerequisites

- GitHub repository: `https://github.com/TRU5T/Monitorr`
- GitHub Actions enabled (enabled by default)
- Dockerfile in the repository root

## Automatic Publishing (Recommended)

The repository includes a GitHub Actions workflow (`.github/workflows/docker-publish.yml`) that automatically builds and publishes the image when you:

1. **Push to main branch** - Builds and publishes `latest` tag
2. **Create a release tag** (e.g., `v1.0.0`) - Builds and publishes versioned tags
3. **Manually trigger** - Use "Run workflow" button in GitHub Actions

### First Time Setup

1. **Push your code to GitHub:**
   ```bash
   git add .
   git commit -m "Add Docker image publishing"
   git push origin main
   ```

2. **Check GitHub Actions:**
   - Go to your repository: `https://github.com/TRU5T/Monitorr`
   - Click on "Actions" tab
   - You should see the workflow running
   - Wait for it to complete (usually 2-5 minutes)

3. **Make the package public (required for Unraid):**
   - Go to: `https://github.com/TRU5T/Monitorr/pkgs/container/monitorr`
   - Click "Package settings" (gear icon)
   - Scroll down to "Danger Zone"
   - Click "Change visibility" → Select "Public"
   - Confirm the change

4. **Verify the image is available:**
   ```bash
   docker pull ghcr.io/tru5t/monitorr:latest
   ```

## Manual Publishing (Alternative)

If you prefer to build and push manually:

### Step 1: Authenticate with GHCR

```bash
# Create a GitHub Personal Access Token (PAT)
# Go to: https://github.com/settings/tokens
# Create token with "write:packages" permission

# Login to GHCR
echo $GITHUB_TOKEN | docker login ghcr.io -u TRU5T --password-stdin
```

### Step 2: Build and Tag the Image

```bash
cd /home/sam/Monitorr

# Build the image
docker build -t ghcr.io/tru5t/monitorr:latest .

# Optionally tag with version
docker tag ghcr.io/tru5t/monitorr:latest ghcr.io/tru5t/monitorr:v1.0.0
```

### Step 3: Push to GHCR

```bash
# Push latest
docker push ghcr.io/tru5t/monitorr:latest

# Push versioned tag (if created)
docker push ghcr.io/tru5t/monitorr:v1.0.0
```

### Step 4: Make Package Public

1. Go to: `https://github.com/TRU5T/Monitorr/pkgs/container/monitorr`
2. Click "Package settings" → "Change visibility" → "Public"

## Using the Published Image on Unraid

Once published, the Unraid template will automatically pull from GHCR:

1. **The template is already configured** with:
   ```xml
   <Repository>ghcr.io/tru5t/monitorr:latest</Repository>
   ```

2. **On Unraid:**
   - Add container using the Monitorr template
   - Unraid will automatically pull `ghcr.io/tru5t/monitorr:latest`
   - No local build required!

## Updating the Image

### Automatic Updates

Every push to `main` branch automatically rebuilds and publishes the `latest` tag.

### Manual Update on Unraid

```bash
# Pull latest image
docker pull ghcr.io/tru5t/monitorr:latest

# Restart container in Unraid UI
```

Or use Unraid's "Force Update" feature in the Docker interface.

## Versioning

The workflow supports semantic versioning:

- **Tag `v1.0.0`** → Creates: `ghcr.io/tru5t/monitorr:v1.0.0`, `v1.0`, `v1`
- **Push to main** → Creates: `ghcr.io/tru5t/monitorr:latest`, `main`

To create a versioned release:

```bash
git tag v1.0.0
git push origin v1.0.0
```

## Troubleshooting

### Image Not Found Error

- **Check package visibility:** Must be public for Unraid to pull
- **Verify repository name:** Should be `ghcr.io/tru5t/monitorr:latest`
- **Check Actions:** Ensure workflow completed successfully

### Authentication Errors

- **For Actions:** Uses `GITHUB_TOKEN` automatically (no setup needed)
- **For manual push:** Ensure PAT has `write:packages` permission

### Build Failures

- Check GitHub Actions logs for errors
- Verify Dockerfile is correct
- Ensure all required files are in repository

## Image Location

Once published, your image will be available at:
- **Registry:** `https://github.com/TRU5T/Monitorr/pkgs/container/monitorr`
- **Pull command:** `docker pull ghcr.io/tru5t/monitorr:latest`

## Benefits of GHCR

✅ **No local builds** - Unraid pulls directly from registry  
✅ **Automatic updates** - GitHub Actions builds on every push  
✅ **Version control** - Tag releases for stability  
✅ **Free** - GitHub Container Registry is free for public packages  
✅ **Fast** - CDN-backed, fast downloads worldwide  
