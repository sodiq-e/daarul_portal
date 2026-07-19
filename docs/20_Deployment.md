# 20. Deployment Architecture

## Runtime Environment
The project is a Django application intended for deployment to hosting platforms such as PythonAnywhere and Render.

## Current Configuration
- Django settings are configured for SQLite locally
- The settings file contains host allowances for local and cloud deployments
- WhiteNoise is enabled for static file serving
- Media files are served locally in DEBUG mode and should be configured for production storage

## Deployment Considerations
- Switch from the temporary secret key to environment-based configuration
- Configure a production database instead of SQLite for multi-user deployments
- Set proper email backend credentials
- Configure media storage for uploaded files
- Ensure static files are collected and served correctly

## Suggested Production Setup
- Use PostgreSQL or MySQL in production
- Configure environment variables for database URL, secret key, email credentials, AI provider credentials
- Set DEBUG to False
- Enable proper security middleware and SSL settings
