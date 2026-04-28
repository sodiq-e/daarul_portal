# Email Notification System - Complete Setup Guide

## Overview

The email notification system allows admins to configure and manage email notifications for various events in the Daarul Portal application. All email settings are configurable from the Django admin panel.

## Features

✅ **Account Creation Emails** - Notify admin when new users register
✅ **Contact Message Emails** - Notify admin when contact form is submitted  
✅ **Application Emails** - Notify admin when applications/forms are submitted
✅ **Configurable Recipients** - Set primary admin email and CC multiple addresses
✅ **Custom Email Subjects** - Customize email subjects with placeholders
✅ **Enable/Disable per Event** - Toggle email notifications on/off for each event type
✅ **HTML & Plain Text** - Professional HTML templates with plain text fallback

## Configuration in Admin Panel

### Accessing Email Settings

1. Go to **Admin Panel** → **Settings** → **School Settings**
2. Scroll to the **Email Notifications** section

### Email Settings Available

| Setting | Description |
|---------|-------------|
| **Admin Email** | Primary email address for receiving notifications (default: `daarulbayaanis@gmail.com`) |
| **Admin Email CC** | Additional emails to CC (comma-separated, e.g., `admin@school.com, principal@school.com`) |
| **Send Account Creation Email** | Toggle email notifications when new accounts are created |
| **Send Contact Message Email** | Toggle email notifications for contact form submissions |
| **Send Application Email** | Toggle email notifications for application submissions |

### Email Subject Customization

Expand the **"Email Templates & Subjects"** section to customize email subjects:

- **Account Creation Subject** - Default: `"New Account Created - {school_name}"`
- **Contact Message Subject** - Default: `"New Contact Message - {school_name}"`
- **Application Subject** - Default: `"New Application Received - {school_name}"`

**Note:** Use `{school_name}` as a placeholder which will be replaced with your school name.

## Implementation Details

### 1. Email Service Module

**Location:** `settingsapp/email_service.py`

Contains all email-sending functions:
- `send_account_creation_email(user)` - Send email when user registers
- `send_contact_message_email(message_obj)` - Send email for contact messages
- `send_application_email(application_data)` - Send email for applications
- `send_custom_email()` - Generic function for custom emails

### 2. Email Templates

**Location:** `templates/emails/`

Four template sets available (HTML + Plain Text):
- `account_creation.html` / `account_creation.txt`
- `contact_message.html` / `contact_message.txt`
- `application.html` / `application.txt`

## How It Works

### 1. Account Creation

**Triggered:** When a new user registers on the portal
**Flow:**
```
User Registration Form Submitted
    ↓
User account created (signal fires)
    ↓
send_account_creation_email() called
    ↓
Email sent to admin_email + CC addresses
```

**Example Email Content:**
- New user's username, email, name
- Account status (Pending Approval)
- Creation timestamp

### 2. Contact Messages

**Triggered:** When a visitor submits the contact form
**Flow:**
```
Contact Form Submitted
    ↓
Message saved to database
    ↓
send_contact_message_email() called
    ↓
Email sent to admin_email + CC addresses
```

**Example Email Content:**
- Sender name, email, phone
- Full message content
- Submission timestamp

### 3. Application Submissions

**Triggered:** When an application/form is submitted
**Flow:**
```
Application Form Submitted
    ↓
Application saved to database
    ↓
send_application_email() called
    ↓
Email sent to admin_email + CC addresses
```

## Integration Guide for Developers

### Add Email Notifications to Other Features

To add email notifications to other parts of your application:

#### 1. For New User Actions

```python
from settingsapp.email_service import send_account_creation_email

# After creating a user or in a signal
send_account_creation_email(user_object)
```

#### 2. For Contact/Message Events

```python
from settingsapp.email_service import send_contact_message_email

# After creating a message
send_contact_message_email(message_object)
```

#### 3. For Application Events

```python
from settingsapp.email_service import send_application_email

# After creating an application
application_data = {
    'name': 'John Doe',
    'email': 'john@example.com',
    'phone': '08123456789',
    'status': 'Submitted',
    'notes': 'Admission form for JSS1'
}
send_application_email(application_data)
```

#### 4. For Custom Email Events

```python
from settingsapp.email_service import send_custom_email

send_custom_email(
    email_type='payment_confirmation',
    recipient_list=['student@example.com'],
    subject='Payment Confirmation - Daarul Portal',
    message='Your payment has been received.',
    cc_list=['admin@school.com']
)
```

### Using Email Service in Views

Example in a class-based view:

```python
from django.views.generic import CreateView
from settingsapp.email_service import send_application_email

class ApplicationCreateView(CreateView):
    model = Application
    form_class = ApplicationForm
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Send email notification
        send_application_email({
            'name': form.cleaned_data['name'],
            'email': form.cleaned_data['email'],
            'phone': form.cleaned_data['phone'],
        })
        
        return response
```

### Using Email Service in Signals

Example in Django signals:

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from settingsapp.email_service import send_application_email

@receiver(post_save, sender=Application)
def send_application_notification(sender, instance, created, **kwargs):
    if created:
        send_application_email({
            'name': instance.applicant_name,
            'email': instance.applicant_email,
            'status': instance.status,
        })
```

## Email Configuration (settings.py)

The project uses the following email backend configuration:

```python
# Email Configuration
EMAIL_BACKEND = os.environ.get(
    'EMAIL_BACKEND',
    'django.core.mail.backends.console.EmailBackend'
)

# For production, configure with actual email service:
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')

DEFAULT_FROM_EMAIL = 'noreply@daaraulportal.com'
```

### For Development (Console Backend)
Emails are printed to console instead of sent. Useful for testing without SMTP server.

### For Production (Gmail)
Set these environment variables:

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-gmail@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## Error Handling & Logging

All email operations are logged. Check Django logs for:
- Successful email sends: `"Account creation email sent for user {username}"`
- Failed attempts: `"Failed to send account creation email for {username}: {error}"`
- Settings retrieval: `"Error retrieving email settings: {error}"`

## Customizing Email Templates

To customize email templates, edit the files in `templates/emails/`:

### Template Variables Available

**Account Creation Emails:**
- `{{ user }}` - User object
- `{{ username }}` - Username
- `{{ email }}` - User email
- `{{ first_name }}`, `{{ last_name }}` - User names
- `{{ school_name }}` - School name

**Contact Message Emails:**
- `{{ message }}` - Message object
- `{{ sender_name }}` - Message sender name
- `{{ sender_email }}` - Sender email
- `{{ sender_phone }}` - Sender phone
- `{{ message_content }}` - Message text
- `{{ submitted_at }}` - Submission timestamp
- `{{ school_name }}` - School name

**Application Emails:**
- `{{ application }}` - Application object/dict
- `{{ school_name }}` - School name

### Example: Customizing Account Creation Template

Edit `templates/emails/account_creation.html`:

```html
<h2>Welcome to {{ school_name }}!</h2>
<p>Username: <strong>{{ username }}</strong></p>
<p>Email: <strong>{{ email }}</strong></p>
<!-- Add your custom content here -->
```

## Testing Email Functionality

### 1. Test with Console Backend (Development)

```bash
# Set in settings or environment
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend
```

Then emails will print to console:

```
Content-Type: text/plain; charset="utf-8"
MIME-Version: 1.0
Content-Transfer-Encoding: 7bit
Subject: New Account Created - Daarul Bayaan Islamic School
From: noreply@daaraulportal.com
To: daarulbayaanis@gmail.com

[Email content here...]
```

### 2. Test by Creating Test User

```bash
# In Django shell or test script
python manage.py shell

from django.contrib.auth.models import User
user = User.objects.create_user(
    username='testuser',
    email='test@example.com',
    password='testpass123'
)
# Signal will automatically trigger email sending
```

### 3. Manual Testing in Django Shell

```python
from django.contrib.auth.models import User
from settingsapp.email_service import send_account_creation_email

# Create a test user or get existing one
user = User.objects.first()

# Send test email
send_account_creation_email(user)
```

## Troubleshooting

### Emails Not Being Sent

1. **Check Settings:**
   - Admin Panel → Settings → Verify "Send X Email" checkbox is enabled
   - Check `admin_email` is not empty

2. **Check Email Backend:**
   - Ensure `EMAIL_BACKEND` is configured correctly in `settings.py`
   - For Gmail, verify SMTP credentials and app password

3. **Check Logs:**
   - Django logs should show error messages
   - Enable DEBUG mode to see full error traces

4. **Test Manually:**
   ```python
   from settingsapp.email_service import get_email_settings
   settings_obj = get_email_settings()
   print(settings_obj.admin_email)
   print(settings_obj.send_account_creation_email)
   ```

### Email Template Not Found

If templates are missing:
1. Create missing template files in `templates/emails/`
2. Use provided templates as reference
3. Ensure `.html` and `.txt` versions exist

### SMTP Authentication Failed

For Gmail:
1. Generate an App-specific Password (not your regular password)
2. Enable 2-factor authentication
3. Set `EMAIL_HOST_PASSWORD` to the App-specific Password

## Files Modified/Created

### Modified Files:
- `settingsapp/models.py` - Added email configuration fields
- `settingsapp/admin.py` - Added email settings to admin panel
- `accounts/signals.py` - Added email sending on user creation
- `communication/views.py` - Added email sending on contact form

### New Files Created:
- `settingsapp/email_service.py` - Email notification service
- `templates/emails/account_creation.html` - HTML template
- `templates/emails/account_creation.txt` - Plain text template
- `templates/emails/contact_message.html` - HTML template
- `templates/emails/contact_message.txt` - Plain text template
- `templates/emails/application.html` - HTML template
- `templates/emails/application.txt` - Plain text template
- `EMAIL_NOTIFICATION_GUIDE.md` - This guide

## Next Steps

1. **Verify Setup:**
   - Check admin panel email settings are visible
   - Set preferred admin email address
   - Add CC emails if needed

2. **Test:**
   - Create test user account
   - Check if email notification works
   - Verify content and formatting

3. **Customize:**
   - Adjust email templates as needed
   - Modify email subjects
   - Add more email types as needed

4. **Production Deployment:**
   - Configure SMTP server credentials
   - Test email sending in production
   - Monitor email logs

## Support

For issues or questions:
1. Check the logs: `tail -f logs/django.log`
2. Test in Django shell
3. Verify email settings in admin panel
4. Check email backend configuration
