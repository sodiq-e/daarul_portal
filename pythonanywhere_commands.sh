#!/bin/bash
# PythonAnywhere Quick Commands Reference
# Use these commands from the bash console on PythonAnywhere

# ==========================================
# SETUP & INITIAL DEPLOYMENT
# ==========================================

# Create virtual environment
python3.10 -m venv ~/daarul_portal/venv

# Activate virtual environment
source ~/daarul_portal/venv/bin/activate

# Install dependencies
pip install -r ~/daarul_portal/requirements.txt

# Initialize database
python ~/daarul_portal/manage.py migrate

# Collect static files
python ~/daarul_portal/manage.py collectstatic --noinput

# Create superuser
python ~/daarul_portal/manage.py createsuperuser

# ==========================================
# AFTER UPDATES/CHANGES
# ==========================================

# Pull latest code (if using Git)
cd ~/daarul_portal && git pull

# Apply migrations if models changed
python ~/daarul_portal/manage.py migrate

# Collect static files again
python ~/daarul_portal/manage.py collectstatic --noinput

# ==========================================
# MAINTENANCE & DEBUGGING
# ==========================================

# Check for any Django issues
python ~/daarul_portal/manage.py check

# View database info
python ~/daarul_portal/manage.py dbshell

# Create a dump of the database
python ~/daarul_portal/manage.py dumpdata > ~/daarul_portal/backup.json

# Load data from dump
python ~/daarul_portal/manage.py loaddata ~/daarul_portal/backup.json

# Run Django shell for testing
python ~/daarul_portal/manage.py shell

# ==========================================
# LOG MONITORING
# ==========================================

# View error logs (replace username)
tail -f /var/log/username.pythonanywhere.com.error.log

# View server logs (replace username)
tail -f /var/log/username.pythonanywhere.com.server.log

# ==========================================
# ENVIRONMENT SETUP
# ==========================================

# Create .env file (edit and add your values)
nano ~/daarul_portal/.env

# Test environment variables are loaded
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print(os.environ.get('DEBUG'))"

# ==========================================
# RELOADING WEB APP
# ==========================================

# After changes, reload web app from Web tab in dashboard
# Or use the API:
# curl -X POST https://www.pythonanywhere.com/api/v0/user/YOUR_USERNAME/webapps/YOUR_DOMAIN.pythonanywhere.com/reload/ \
#  -H "Authorization: Token YOUR_API_TOKEN"

