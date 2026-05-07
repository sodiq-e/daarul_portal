from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages as django_messages
from django.views.generic import ListView, DetailView
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from .forms import MessageForm
from .models import Message
from settingsapp.email_service import send_contact_message_email, send_contact_message_confirmation_email


def contact_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save()
            # Send email notification to admin
            send_contact_message_email(message)
            # Send confirmation email to sender
            send_contact_message_confirmation_email(message)
            return redirect('contact_success')
    else:
        form = MessageForm()

    return render(request, 'contact.html', {'form': form})


def contact_success(request):
    return render(request, 'contact_success.html')


# ============ ADMIN MESSAGE MANAGEMENT VIEWS ============

def is_admin(user):
    """Check if user is admin"""
    try:
        return user.is_staff and user.profile.is_approved
    except AttributeError:
        return user.is_staff


class AdminMessageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all contact messages for admin"""
    model = Message
    template_name = 'communication/admin_messages_list.html'
    context_object_name = 'messages'
    paginate_by = 20
    ordering = ['-created_at']

    def test_func(self):
        return is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unreplied_count'] = Message.objects.filter(is_replied=False).count()
        context['replied_count'] = Message.objects.filter(is_replied=True).count()
        return context


class AdminMessageDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):
    """View single message and send reply"""
    model = Message
    template_name = 'communication/admin_message_detail.html'
    context_object_name = 'message'

    def test_func(self):
        return is_admin(self.request.user)

    def post(self, request, *args, **kwargs):
        """Handle reply submission"""
        message = self.get_object()
        reply_text = request.POST.get('reply_message', '').strip()

        if not reply_text:
            django_messages.error(request, 'Reply message cannot be empty.')
            return redirect('admin_message_detail', pk=message.pk)

        # Determine if sender has an account
        has_account = message.user is not None

        if has_account:
            # Send portal message notification
            message.reply_message = reply_text
            message.replied_at = timezone.now()
            message.replied_by = request.user
            message.is_replied = True
            message.reply_method = 'portal'
            message.save()

            # Send email notification to user about portal message
            subject = f"Reply to Your Message - {settings.SCHOOL_NAME}"
            email_body = f"""
Hello {message.name or message.user.get_full_name()},

Thank you for contacting us. Here is our reply to your message:

{reply_text}

You can also log in to your portal to view this message.

Best regards,
{settings.SCHOOL_NAME}
            """
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message.email or message.user.email],
                fail_silently=True
            )
            django_messages.success(request, 'Reply sent via email and portal message created.')
        else:
            # Send email reply
            message.reply_message = reply_text
            message.replied_at = timezone.now()
            message.replied_by = request.user
            message.is_replied = True
            message.reply_method = 'email'
            message.save()

            subject = f"Reply to Your Message - {settings.SCHOOL_NAME}"
            email_body = f"""
Hello {message.name},

Thank you for contacting us. Here is our reply to your message:

{reply_text}

Best regards,
{settings.SCHOOL_NAME}
            """
            send_mail(
                subject=subject,
                message=email_body,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[message.email],
                fail_silently=False
            )
            django_messages.success(request, 'Reply sent via email.')

        return redirect('admin_message_detail', pk=message.pk)