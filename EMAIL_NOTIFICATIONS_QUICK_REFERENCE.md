# Email Notifications - Quick Reference

## For Admins

### Configure Email Settings

1. Go to **Admin Panel** → **Settings** → **School Settings**
2. Find the **Email Notifications** section
3. Enter your preferred email address in **Admin Email** field
4. (Optional) Add more emails in **Admin Email CC** (comma-separated)
5. Toggle email types on/off as needed
6. Click **Save**

### Email Settings at a Glance

```
┌─────────────────────────────────────────┐
│      EMAIL NOTIFICATION SETTINGS        │
├─────────────────────────────────────────┤
│ Admin Email:        daarulbayaanis@gmail.com
│ Admin Email CC:     [optional emails]   
│                                         │
│ ✓ Send Account Creation Emails          
│ ✓ Send Contact Message Emails           
│ ✓ Send Application Emails               
└─────────────────────────────────────────┘
```

---

## For Developers

### Basic Usage

#### 1. Send Account Creation Email

```python
from settingsapp.email_service import send_account_creation_email

# When a new user is created
send_account_creation_email(user_object)
```

#### 2. Send Contact Message Email

```python
from settingsapp.email_service import send_contact_message_email

# When contact form is submitted
send_contact_message_email(message_object)
```

#### 3. Send Application Email

```python
from settingsapp.email_service import send_application_email

# When an application is submitted
send_application_email({
    'name': 'John Doe',
    'email': 'john@example.com',
    'phone': '08123456789'
})
```

#### 4. Send Custom Email

```python
from settingsapp.email_service import send_custom_email

send_custom_email(
    email_type='payment',
    recipient_list=['student@example.com'],
    subject='Payment Received',
    message='Your payment has been confirmed.',
    cc_list=['admin@school.com']
)
```

### Integration Examples

#### In Django Signals

```python
from django.db.models.signals import post_save
from django.dispatch import receiver
from settingsapp.email_service import send_application_email

@receiver(post_save, sender=Admission)
def send_admission_notification(sender, instance, created, **kwargs):
    if created:
        send_application_email({
            'name': instance.student_name,
            'email': instance.student_email,
            'status': 'Submitted'
        })
```

#### In Views

```python
from django.shortcuts import render, redirect
from settingsapp.email_service import send_contact_message_email

def contact_view(request):
    if request.method == 'POST':
        message = Message.objects.create(
            name=request.POST['name'],
            email=request.POST['email'],
            message=request.POST['message']
        )
        send_contact_message_email(message)
        return redirect('success')
    return render(request, 'contact.html')
```

#### In Class-Based Views

```python
from django.views.generic import CreateView
from settingsapp.email_service import send_application_email

class ApplicationCreateView(CreateView):
    model = Application
    fields = '__all__'
    
    def form_valid(self, form):
        response = super().form_valid(form)
        send_application_email({
            'name': form.instance.name,
            'email': form.instance.email
        })
        return response
```

---

## Email Events Currently Implemented

| Event | Triggered | Email Sent To |
|-------|-----------|---------------|
| 👤 User Registration | New user account created | Admin Email + CC |
| 💬 Contact Form | Visitor submits contact form | Admin Email + CC |
| 📋 Application | Any application submitted | Admin Email + CC |

---

## Configuration Files

| File | Purpose |
|------|---------|
| `settingsapp/models.py` | Email settings model |
| `settingsapp/email_service.py` | Email sending functions |
| `daarul_portal/settings.py` | Email backend config |
| `templates/emails/*.html` | HTML email templates |
| `templates/emails/*.txt` | Plain text email templates |

---

## Environment Variables (for Production)

```bash
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-specific-password
DEFAULT_FROM_EMAIL=noreply@school.com
```

---

## Customizing Email Templates

Templates are located in `templates/emails/`:

- `account_creation.html` / `.txt`
- `contact_message.html` / `.txt`
- `application.html` / `.txt`

Edit these files to customize:
- Email design and layout (HTML)
- Content and formatting
- Use template variables: `{{ school_name }}`, `{{ user }}`, etc.

---

## Testing

### Development (Console Backend)
Emails print to console instead of being sent. Perfect for testing!

### Production Testing
```python
python manage.py shell

from django.contrib.auth.models import User
from settingsapp.email_service import send_account_creation_email

user = User.objects.first()
send_account_creation_email(user)  # Sends real email
```

---

## Common Issues & Solutions

| Issue | Solution |
|-------|----------|
| Emails not sent | Check admin panel → verify "Send X Email" is ✓ |
| Wrong recipient | Admin panel → verify Admin Email field |
| Template errors | Check `templates/emails/` folder exists |
| SMTP auth failed | Verify EMAIL_HOST_USER and EMAIL_HOST_PASSWORD |
| No CC emails | Use comma-separated format: `email1@test.com, email2@test.com` |

---

## Database Migration

Already applied! No action needed.

```bash
# If starting fresh:
python manage.py makemigrations
python manage.py migrate
```

---

## Files Changed

### Code
- ✅ `settingsapp/models.py` - Added email fields to SchoolSettings
- ✅ `settingsapp/admin.py` - Updated admin interface  
- ✅ `settingsapp/email_service.py` - NEW email utility service
- ✅ `accounts/signals.py` - Updated to send emails on registration
- ✅ `communication/views.py` - Updated to send emails on contact

### Database
- ✅ `settingsapp/migrations/0013_*` - NEW migration for email fields

### Templates  
- ✅ `templates/emails/account_creation.html` - NEW
- ✅ `templates/emails/account_creation.txt` - NEW
- ✅ `templates/emails/contact_message.html` - NEW
- ✅ `templates/emails/contact_message.txt` - NEW
- ✅ `templates/emails/application.html` - NEW
- ✅ `templates/emails/application.txt` - NEW

### Documentation
- ✅ `EMAIL_NOTIFICATION_GUIDE.md` - Complete guide
- ✅ `EMAIL_NOTIFICATIONS_QUICK_REFERENCE.md` - This file

---

**That's it!** Your email notification system is ready to use! 🎉
