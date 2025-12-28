# Installation & Deployment

This directory contains installation and deployment guides for different platforms and environments.

## Quick Start

**New to the Media Player?** Start here:

👉 **[Quick Start Guide](quickstart.md)** - Get up and running in 5 minutes

## Guides

### Development & Testing

- **[Quick Start](quickstart.md)** - Fast setup for local development and testing
  - Prerequisites
  - 5-minute setup
  - Development mode with hot reload
  - Troubleshooting

### Production Deployment

- **[Raspberry Pi Setup](raspberry-pi.md)** - Complete guide for Raspberry Pi deployment
  - Hardware requirements
  - OS installation
  - Audio configuration (HDMI)
  - Network storage setup
  - Auto-start configuration
  - Performance tuning
  - Comprehensive troubleshooting

- **[Deployment Guide](deployment.md)** - Deployment options and best practices
  - Development deployment
  - Production deployment
  - Bundled distribution
  - Reverse proxy setup (Nginx, Apache)
  - Security considerations
  - Performance optimization
  - Monitoring and backups

### Package Management

- **[UV Setup](uv-setup.md)** - Using uv for fast Python environment management
  - What is uv and why use it
  - Installation instructions
  - 10-100x faster than pip
  - Backward compatibility with pip

## Recommended Paths

### For Local Testing
1. [Quick Start Guide](quickstart.md) → Done! 🎉

### For Raspberry Pi Production
1. [Quick Start Guide](quickstart.md) - Get familiar with the app
2. [Raspberry Pi Setup](raspberry-pi.md) - Complete Pi setup
3. [Deployment Guide](deployment.md) - Production hardening

### For Other Platforms
1. [Quick Start Guide](quickstart.md) - Basic setup
2. [Deployment Guide](deployment.md) - Adapt to your platform
3. [UV Setup](uv-setup.md) - Optional performance boost

## Common Tasks

### Installing on Raspberry Pi
See: [Raspberry Pi Setup Guide](raspberry-pi.md)

### Setting up HTTPS
See: [Deployment Guide - HTTPS Setup](deployment.md#https-setup-with-lets-encrypt)

### Auto-starting the application
See: [Raspberry Pi Setup - Auto-Start Configuration](raspberry-pi.md#auto-start-configuration)

### Using uv instead of pip
See: [UV Setup Guide](uv-setup.md)

### Bundling for distribution
See: [Deployment Guide - Bundled Distribution](deployment.md#bundled-distribution) or [Bundling Guide](../technical/bundling.md)

## System Requirements

### Minimum Requirements
- **Python**: 3.8 or higher
- **Node.js**: 14 or higher
- **RAM**: 2GB (4GB recommended for Raspberry Pi)
- **Storage**: 1GB for application + space for media files

### Recommended for Production (Raspberry Pi)
- **Device**: Raspberry Pi 4 (4GB RAM)
- **Storage**: 32GB SD card (Class 10 or better)
- **Network**: Ethernet connection (more stable than WiFi)
- **Audio**: HDMI connection to AV receiver or powered speakers

## Support

### Troubleshooting
- [Quick Start - Troubleshooting](quickstart.md#troubleshooting)
- [Raspberry Pi - Troubleshooting](raspberry-pi.md#troubleshooting)
- [Deployment - Troubleshooting](deployment.md#troubleshooting-deployment)

### Getting Help
- Check the guides above for your specific issue
- Review the [main documentation](../README.md)
- Open an issue on GitHub

## Related Documentation

- [Technical Documentation](../technical/README.md) - Architecture, APIs, implementation details
- [Requirements](../requirements/README.md) - UI behavior specifications
- [UI Guidance](../ui-guidance/README.md) - UI design guidelines
