"""
Email notification service for the Daarul Portal.
Handles sending emails for various events with configurable settings from admin panel.
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


def get_email_settings():
    """
    Retrieve email settings from SchoolSettings.
    Returns default values if SchoolSettings doesn't exist.
    """
    try:
        from .models import SchoolSettings
        settings_obj = SchoolSettings.objects.first()
        if settings_obj:
            return settings_obj
    except Exception as e:
        logger.error(f"Error retrieving email settings: {e}")
    
    # Return a default settings object with default values
    class DefaultSettings:
        admin_email = 'daarulbayaanis@gmail.com'
        admin_email_cc = ''
        send_account_creation_email = True
        send_contact_message_email = True
        send_application_email = True
        account_creation_email_subject = "New Account Created - Daarul Bayaan Islamic School"
        contact_message_email_subject = "New Contact Message - Daarul Bayaan Islamic School"
        application_email_subject = "New Application Received - Daarul Bayaan Islamic School"
        school_name = "Daarul Bayaan Islamic School"
    
    return DefaultSettings()


def parse_cc_emails(cc_string):
    """
    Parse comma-separated email addresses from a string.
    Returns a list of valid email addresses.
    """
    if not cc_string:
        return []
    
    emails = [email.strip() for email in cc_string.split(',')]
    return [email for email in emails if email and '@' in email]


def send_account_creation_email(user, template_context=None):
    """
    Send email notification when a new account is created.
    
    Args:
        user: User object
        template_context: Additional context for email template (dict)
    """
    settings_obj = get_email_settings()
    
    if not settings_obj.send_account_creation_email:
        logger.info(f"Account creation email disabled in settings")
        return False
    
    try:
        # Prepare email context
        context = {
            'user': user,
            'school_name': settings_obj.school_name,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
        }
        if template_context:
            context.update(template_context)
        
        # Format subject
        subject = settings_obj.account_creation_email_subject.format(
            school_name=settings_obj.school_name
        )
        
        # Try to use HTML template, fall back to plain text
        try:
            html_content = render_to_string('emails/account_creation.html', context)
            text_content = render_to_string('emails/account_creation.txt', context)
        except Exception as e:
            logger.warning(f"Email template not found: {e}, using plain text")
            text_content = f"""
New Account Created

User Details:
- Username: {user.username}
- Email: {user.email}
- Name: {user.first_name} {user.last_name}
- Date Joined: {user.date_joined}

Please review this account and approve if needed.
            """
            html_content = None
        
        # Prepare recipient list
        recipient_list = [settings_obj.admin_email]
        cc_emails = parse_cc_emails(settings_obj.admin_email_cc)
        
        # Send email
        if html_content:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                cc=cc_emails
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list + cc_emails,
                fail_silently=False
            )
        
        logger.info(f"Account creation email sent for user {user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send account creation email for {user.username}: {e}")
        return False


def send_contact_message_email(message_obj, template_context=None):
    """
    Send email notification when a contact form message is submitted.
    
    Args:
        message_obj: Message object with name, email, phone, message
        template_context: Additional context for email template (dict)
    """
    settings_obj = get_email_settings()
    
    if not settings_obj.send_contact_message_email:
        logger.info(f"Contact message email disabled in settings")
        return False
    
    try:
        # Prepare email context
        context = {
            'message': message_obj,
            'school_name': settings_obj.school_name,
            'sender_name': message_obj.name or 'Anonymous',
            'sender_email': message_obj.email or 'Not provided',
            'sender_phone': message_obj.phone or 'Not provided',
            'message_content': message_obj.message,
            'submitted_at': message_obj.created_at,
        }
        if template_context:
            context.update(template_context)
        
        # Format subject
        subject = settings_obj.contact_message_email_subject.format(
            school_name=settings_obj.school_name
        )
        
        # Try to use HTML template, fall back to plain text
        try:
            html_content = render_to_string('emails/contact_message.html', context)
            text_content = render_to_string('emails/contact_message.txt', context)
        except Exception as e:
            logger.warning(f"Email template not found: {e}, using plain text")
            text_content = f"""
New Contact Message Received

Sender Details:
- Name: {message_obj.name or 'Anonymous'}
- Email: {message_obj.email or 'Not provided'}
- Phone: {message_obj.phone or 'Not provided'}
- Submitted: {message_obj.created_at}

Message:
{message_obj.message}
            """
            html_content = None
        
        # Prepare recipient list
        recipient_list = [settings_obj.admin_email]
        cc_emails = parse_cc_emails(settings_obj.admin_email_cc)
        
        # Send email
        if html_content:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                cc=cc_emails
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list + cc_emails,
                fail_silently=False
            )
        
        logger.info(f"Contact message email sent from {message_obj.name or 'Anonymous'}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send contact message email: {e}")
        return False


def send_application_email(application_data, template_context=None):
    """
    Send email notification when an application/form is submitted.
    
    Args:
        application_data: Dict or object with application details
        template_context: Additional context for email template (dict)
    """
    settings_obj = get_email_settings()
    
    if not settings_obj.send_application_email:
        logger.info(f"Application email disabled in settings")
        return False
    
    try:
        # Prepare email context
        context = {
            'application': application_data,
            'school_name': settings_obj.school_name,
        }
        if template_context:
            context.update(template_context)
        
        # Format subject
        subject = settings_obj.application_email_subject.format(
            school_name=settings_obj.school_name
        )
        
        # Try to use HTML template, fall back to plain text
        try:
            html_content = render_to_string('emails/application.html', context)
            text_content = render_to_string('emails/application.txt', context)
        except Exception as e:
            logger.warning(f"Email template not found: {e}, using plain text")
            if isinstance(application_data, dict):
                app_info = "\n".join([f"- {k}: {v}" for k, v in application_data.items()])
            else:
                app_info = str(application_data)
            
            text_content = f"""
New Application Received

Application Details:
{app_info}
            """
            html_content = None
        
        # Prepare recipient list
        recipient_list = [settings_obj.admin_email]
        cc_emails = parse_cc_emails(settings_obj.admin_email_cc)
        
        # Send email
        if html_content:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                cc=cc_emails
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list + cc_emails,
                fail_silently=False
            )
        
        logger.info(f"Application email sent")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send application email: {e}")
        return False


def send_custom_email(email_type, recipient_list, subject, message=None, 
                      html_message=None, cc_list=None, context_data=None):
    """
    Generic function to send custom emails.
    
    Args:
        email_type: Type of email ('custom', 'alert', 'notification', etc.)
        recipient_list: List of recipient email addresses
        subject: Email subject
        message: Plain text message
        html_message: HTML message
        cc_list: List of CC email addresses
        context_data: Additional context data (dict)
    """
    try:
        cc_list = cc_list or []
        
        if html_message:
            email = EmailMultiAlternatives(
                subject=subject,
                body=message or '',
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=recipient_list,
                cc=cc_list
            )
            email.attach_alternative(html_message, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=message or '',
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list + cc_list,
                fail_silently=False
            )
        
        logger.info(f"Custom email ({email_type}) sent to {len(recipient_list)} recipients")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send custom email ({email_type}): {e}")
        return False


def send_account_approval_email(user, template_context=None):
    """
    Send email notification when a user account is approved.
    
    Args:
        user: User object whose account has been approved
        template_context: Additional context for email template (dict)
    """
    try:
        # Prepare email context
        context = {
            'user': user,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'school_name': 'Daarul Bayaan Islamic School',
        }
        if template_context:
            context.update(template_context)
        
        # Format subject
        subject = f"Account Approved - Welcome to {context['school_name']}"
        
        # Try to use HTML template, fall back to plain text
        try:
            html_content = render_to_string('emails/account_approval.html', context)
            text_content = render_to_string('emails/account_approval.txt', context)
        except Exception as e:
            logger.warning(f"Email template not found: {e}, using plain text")
            text_content = f"""
Welcome to {context['school_name']}!

Dear {user.first_name} {user.last_name},

Your account has been approved! You can now log in to the portal using your credentials:

- Username: {user.username}
- Email: {user.email}

Log in here: {settings.SITE_URL if hasattr(settings, 'SITE_URL') else 'https://daarulbayaan.pythonanywhere.com'}/login/

If you have any issues, please contact the school administration.

Best regards,
{context['school_name']} Administration
            """
            html_content = None
        
        # Send email to user
        if html_content:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[user.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[user.email],
                fail_silently=False
            )
        
        logger.info(f"Account approval email sent to {user.username}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send account approval email for {user.username}: {e}")
        return False


def send_contact_message_confirmation_email(message_obj, template_context=None):
    """
    Send confirmation email to the message sender.
    
    Args:
        message_obj: Message object with sender contact info
        template_context: Additional context for email template (dict)
    """
    if not message_obj.email:
        logger.warning(f"No email for message sender: {message_obj.name}")
        return False
    
    try:
        # Prepare email context
        context = {
            'message': message_obj,
            'school_name': 'Daarul Bayaan Islamic School',
            'sender_name': message_obj.name or 'Valued Visitor',
            'message_id': message_obj.id,
            'submitted_at': message_obj.created_at,
        }
        if template_context:
            context.update(template_context)
        
        # Format subject
        subject = f"Message Received - Thank You for Contacting {context['school_name']}"
        
        # Try to use HTML template, fall back to plain text
        try:
            html_content = render_to_string('emails/contact_confirmation.html', context)
            text_content = render_to_string('emails/contact_confirmation.txt', context)
        except Exception as e:
            logger.warning(f"Email template not found: {e}, using plain text")
            text_content = f"""
Thank you for contacting {context['school_name']}!

Dear {message_obj.name or 'Valued Visitor'},

We have received your message and appreciate you taking the time to get in touch with us.

Message Details:
- Submitted: {message_obj.created_at}
- Reference ID: #{message_obj.id}

Our administration team will review your message and respond as soon as possible.

Best regards,
{context['school_name']} Administration
            """
            html_content = None
        
        # Send email to message sender
        if html_content:
            email = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[message_obj.email]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
        else:
            send_mail(
                subject=subject,
                message=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message_obj.email],
                fail_silently=False
            )
        
        logger.info(f"Contact confirmation email sent to {message_obj.email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send contact confirmation email: {e}")
        return False
