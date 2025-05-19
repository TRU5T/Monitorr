# Monitorr

A Docker log monitoring application for tracking container logs and sending alerts when errors are detected.

## Features

- Monitor logs from Docker containers
- Initial support for Plex containers
- Configurable alert thresholds and patterns
- Multiple alert destinations:
  - Email (SMTP)
  - Discord
- Web interface for monitoring and configuration
- Support for remote Docker hosts

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure your monitored containers and alert destinations in `config.yml`

3. Run the application:
```bash
# Run with monitoring only (no web interface)
python monitorr.py

# Run with monitoring and web interface
python monitorr.py --web

# Run with web interface only (for configuration)
python monitorr.py --web-only
```

## Web Interface

The web interface is available at `http://localhost:5000` by default and provides:

- Dashboard with monitor status
- Log viewer for containers
- Configuration editor
- Environment variable overview
- Docker host configuration

To customize the web interface host/port:
```bash
python monitorr.py --web --host 127.0.0.1 --port 8080
```

## Security Considerations

1. **Docker Socket Access**
   - The application requires access to the Docker socket (`/var/run/docker.sock`)
   - This provides root-level access to the host system
   - Consider using Docker's built-in security features:
     - AppArmor profiles
     - Seccomp profiles
     - Read-only root filesystem

2. **Web Interface Security**
   - Change the default `FLASK_SECRET_KEY` in docker-compose.yml
   - Consider implementing authentication
   - Use HTTPS in production
   - Restrict access to trusted IP addresses

3. **Environment Variables**
   - Store sensitive information in environment variables
   - Use `.env` file for local development (not in production)
   - Never commit sensitive data to version control

## Deployment

### Docker Deployment

1. Build the image:
```bash
docker build -t monitorr:latest .
```

2. Run with docker-compose:
```bash
docker-compose up -d
```

### Production Considerations

1. **Logging**
   - Logs are stored in `monitorr.log`
   - Implement log rotation to prevent disk space issues
   - Consider using a log aggregation service

2. **Backup**
   - Regularly backup your `config.yml`
   - Consider backing up logs for historical analysis

3. **Updates**
   - Pull latest image: `docker-compose pull`
   - Restart container: `docker-compose up -d`

## Development

### Git Setup

1. Configure Git:
```bash
git config --global user.email "your.email@example.com"
git config --global user.name "Your Name"
```

2. Development workflow:
   - Create feature branches
   - Write tests for new features
   - Submit pull requests

### Testing

1. Unit Tests:
```bash
python -m pytest tests/
```

2. Integration Tests:
```bash
python -m pytest tests/integration/
```

## Troubleshooting

1. **Docker Connection Issues**
   - Verify Docker socket permissions
   - Check Docker daemon status
   - Review container logs

2. **Web Interface Issues**
   - Check port availability
   - Verify firewall settings
   - Review application logs

3. **Alert Issues**
   - Verify SMTP/Discord credentials
   - Check network connectivity
   - Review alert configuration

## Configuration

See `config.example.yml` for a sample configuration.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

[Add your license information here] 