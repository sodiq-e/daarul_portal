# Daarul Portal - PythonAnywhere Deployment Guide

## Prerequisites
- PythonAnywhere account (sign up at www.pythonanywhere.com)
- Git installed locally (or you can upload files manually)
- Your project code ready for deployment

---

## Step 1: Create a PythonAnywhere Account

1. Go to [www.pythonanywhere.com](https://www.pythonanywhere.com)
2. Sign up for a free or paid account
3. Log in to your account

---

## Step 2: Clone Your Project on PythonAnywhere

### Option A: Using Git (Recommended)

1. Open a **Bash console** from the PythonAnywhere dashboard
2. Clone your repository:
   ```bash
   cd ~
   git clone <your-repo-url> daarul_portal
   cd daarul_portal
   ```

### Option B: Using File Upload

1. Use the **Files** section in PythonAnywhere to upload your project files manually
2. Or create the directory and upload a ZIP file, then extract it

---

## Step 3: Create a Virtual Environment

1. In the **Bash console**, navigate to your project directory:
   ```bash
   cd ~/daarul_portal
   ```

2. Create a virtual environment using Python 3.10+:
   ```bash
   python3.10 -m venv venv
   ```

3. Activate the virtual environment:
   ```bash
   source venv/bin/activate
   ```

4. Upgrade pip:
   ```bash
   pip install --upgrade pip
   ```

5. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

---

## Step 4: Configure Environment Variables

Create a `.env` file in your project root:
```bash
nano .env
```

Add the following content (adjust as needed):
```
DEBUG=False
ALLOWED_HOSTS=your-username.pythonanywhere.com,www.yourdomain.com
DJANGO_SECRET_KEY=your-generated-secret-key-here
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

**To generate a secret key**, run in the bash console:
```bash
python3 -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## Step 5: Initialize the Database

In the bash console (with venv activated):

```bash
python manage.py migrate
python manage.py collectstatic --noinput
```

Create a superuser:
```bash
python manage.py createsuperuser
```

---

## Step 6: Configure the Web App on PythonAnywhere

1. Go to the **Web** tab in your PythonAnywhere dashboard
2. Click **Add a new web app**
3. Choose **Manual configuration**
4. Select **Python 3.10** (or your preferred version)
5. Complete the setup

---

## Step 7: Configure the WSGI File

1. In the **Web** tab, click on your web app
2. Under **WSGI configuration file**, click the link to edit it
3. Replace the contents with:

```python
import os
import sys
from pathlib import Path

# Add your project to the path
path = '/home/your-username/daarul_portal'
if path not in sys.path:
    sys.path.insert(0, path)

# Set the Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')

# Import the Django WSGI application
from django.core.wsgi import get_wsgi_application
application = get_wsgi_application()
```

Replace `your-username` with your actual PythonAnywhere username.

---

## Step 8: Configure Static and Media Files

In the **Web** tab, scroll down to the **Static files** section:

1. Add a new static file mapping:
   - **URL**: `/static/`
   - **Directory**: `/home/your-username/daarul_portal/staticfiles`

2. Add a new static file mapping for media:
   - **URL**: `/media/`
   - **Directory**: `/home/your-username/daarul_portal/media`

Replace `your-username` with your actual PythonAnywhere username.

---

## Step 9: Set Environment Variables in PythonAnywhere

1. Go to **Account** → **Web app** → Your web app
2. Scroll to **Environment variables**
3. Click **Add new environment variable** for each variable in your `.env` file

Or, you can load environment variables from a file by adding this to your WSGI file:
```python
from dotenv import load_dotenv
load_dotenv('/home/your-username/daarul_portal/.env')
```

First, install python-dotenv:
```bash
pip install python-dotenv
```

---

## Step 10: Reload Your Web App

1. Go to the **Web** tab
2. Click the green **Reload** button for your web app
3. Wait for it to finish (should take a few moments)

---

## Step 11: Test Your Deployment

1. Navigate to `https://your-username.pythonanywhere.com`
2. You should see your Django application
3. Log in with the superuser credentials you created

---

## Step 12: Set Up a Custom Domain (Optional)

If you have a custom domain:

1. Go to **Account** → **Domains**
2. Click **Add a domain**
3. Enter your domain name
4. Update your DNS settings with your domain registrar
5. Point your domain to PythonAnywhere's IP address

---

## Troubleshooting

### Issue: 500 Error or Blank Page

Check the error logs:
1. Go to **Web** tab
2. Find **Log files** section
3. Check **Error log** and **Server log**

### Issue: Static Files Not Loading

Ensure you've run:
```bash
python manage.py collectstatic --noinput
```

And verify the static files path in the `STATIC_ROOT` setting.

### Issue: Database Not Found

Make sure migrations have been run:
```bash
python manage.py migrate
```

### Issue: Module Not Found Errors

Verify all dependencies are installed:
```bash
source ~/daarul_portal/venv/bin/activate
pip install -r requirements.txt
```

### View Live Error Logs

```bash
tail -f /var/log/your-username.pythonanywhere.com.error.log
```

---

## Updating Your Code After Deployment

After making changes to your code:

1. Push to your Git repository (if using Git)
2. Pull changes in the PythonAnywhere bash console:
   ```bash
   cd ~/daarul_portal
   git pull
   ```

3. If you modified models:
   ```bash
   python manage.py migrate
   ```

4. Collect static files:
   ```bash
   python manage.py collectstatic --noinput
   ```

5. Reload the web app from the **Web** tab

---

## Security Tips

- ✅ Set `DEBUG = False` in production
- ✅ Keep `SECRET_KEY` secret (use environment variables)
- ✅ Enable HTTPS (PythonAnywhere provides free SSL certificates)
- ✅ Keep dependencies updated: `pip install --upgrade -r requirements.txt`
- ✅ Regularly back up your database
- ✅ Monitor error logs regularly

---

## Need Help?

- PythonAnywhere Help: https://help.pythonanywhere.com/
- Django Documentation: https://docs.djangoproject.com/
- Community Support: Django Discord/Reddit

---

Last updated: April 2026
