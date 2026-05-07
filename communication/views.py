from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib import messages as django_messages
from django.views.generic import ListView, DetailView, TemplateView
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q

from .forms import MessageForm, PortalMessageForm
from .models import Message, PortalThread, PortalMessage
from settingsapp.email_service import send_contact_message_email, send_contact_message_confirmation_email


def contact_view(request):
    if request.method == 'POST':
        form = MessageForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            if request.user.is_authenticated:
                message.user = request.user
                if not message.email:
                    message.email = request.user.email
                if not message.name:
                    message.name = request.user.get_full_name() or request.user.username
            message.save()
            send_contact_message_email(message)
            if message.email:
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


def get_active_accounts():
    return User.objects.filter(is_active=True).filter(
        Q(profile__is_approved=True) | Q(profile__isnull=True)
    ).order_by('username')


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

        if message.user:
            message.reply_message = reply_text
            message.replied_at = timezone.now()
            message.replied_by = request.user
            message.is_replied = True
            message.reply_method = 'portal'
            message.save()

            thread, _ = PortalThread.objects.get_or_create(user=message.user)
            PortalMessage.objects.create(
                thread=thread,
                sender=request.user,
                content=reply_text
            )
            django_messages.success(request, 'Reply saved to the user portal conversation.')
        else:
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


class AdminPortalUserListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    model = User
    template_name = 'communication/admin_portal_users_list.html'
    context_object_name = 'users'

    def test_func(self):
        return is_admin(self.request.user)

    def get_queryset(self):
        return get_active_accounts()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users_with_counts = []
        for user in context['users']:
            thread = getattr(user, 'portal_thread', None)
            unread_count = 0
            total_messages = 0
            if thread:
                total_messages = thread.messages.count()
                unread_count = thread.messages.exclude(sender=user).filter(is_read=False).count()
            users_with_counts.append({
                'user': user,
                'thread': thread,
                'total_messages': total_messages,
                'unread_count': unread_count,
            })
        context['users_with_counts'] = users_with_counts
        context['form'] = PortalMessageForm()
        return context

    def post(self, request, *args, **kwargs):
        """Handle bulk message sending"""
        selected_users = request.POST.getlist('selected_users')
        bulk_message = request.POST.get('bulk_message', '').strip()

        if not selected_users:
            django_messages.error(request, 'Please select at least one user to send the message to.')
            return redirect('admin_portal_users_list')

        if not bulk_message:
            django_messages.error(request, 'Please enter a message to send.')
            return redirect('admin_portal_users_list')

        sent_count = 0
        for user_id in selected_users:
            try:
                user = User.objects.get(id=user_id, is_active=True)
                thread, _ = PortalThread.objects.get_or_create(user=user)
                PortalMessage.objects.create(
                    thread=thread,
                    sender=request.user,
                    content=bulk_message
                )
                thread.updated_at = timezone.now()
                thread.save()
                sent_count += 1
            except User.DoesNotExist:
                continue

        if sent_count > 0:
            django_messages.success(request, f'Bulk message sent to {sent_count} user(s).')
        else:
            django_messages.error(request, 'No messages were sent. Please check your selections.')

        return redirect('admin_portal_users_list')


class AdminPortalThreadView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'communication/admin_portal_thread_detail.html'

    def test_func(self):
        return is_admin(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = get_object_or_404(get_active_accounts(), pk=self.kwargs['user_id'])
        thread, _ = PortalThread.objects.get_or_create(user=user)
        context['thread'] = thread
        context['messages'] = thread.messages.select_related('sender').all()
        context['form'] = PortalMessageForm()
        return context

    def post(self, request, *args, **kwargs):
        user = get_object_or_404(get_active_accounts(), pk=self.kwargs['user_id'])
        thread, _ = PortalThread.objects.get_or_create(user=user)
        content = request.POST.get('content', '').strip()
        if not content:
            django_messages.error(request, 'Please enter a reply message.')
            return redirect('admin_portal_thread_detail', user_id=user.id)

        PortalMessage.objects.create(
            thread=thread,
            sender=request.user,
            content=content
        )
        thread.updated_at = timezone.now()
        thread.save()
        django_messages.success(request, 'Portal reply sent to the selected account.')
        return redirect('admin_portal_thread_detail', user_id=user.id)


class PortalInboxView(LoginRequiredMixin, TemplateView):
    template_name = 'communication/portal_messages_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = getattr(self.request.user, 'portal_thread', None)
        context['thread'] = thread
        context['unread_count'] = thread.messages.filter(is_read=False).exclude(sender=self.request.user).count() if thread else 0
        if thread and thread.messages.exists():
            context['latest_message'] = thread.messages.last().content
        else:
            context['latest_message'] = None
        return context


class PortalThreadDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'communication/portal_thread_detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread, _ = PortalThread.objects.get_or_create(user=self.request.user)
        messages_qs = thread.messages.select_related('sender').all()
        messages_qs.filter(is_read=False).exclude(sender=self.request.user).update(is_read=True)
        context['thread'] = thread
        context['messages'] = messages_qs
        context['form'] = PortalMessageForm()
        return context

    def post(self, request, *args, **kwargs):
        thread, _ = PortalThread.objects.get_or_create(user=self.request.user)
        content = request.POST.get('content', '').strip()
        if not content:
            django_messages.error(request, 'Please enter a message.')
            return redirect('portal_thread_detail')

        PortalMessage.objects.create(
            thread=thread,
            sender=request.user,
            content=content
        )
        thread.updated_at = timezone.now()
        thread.save()
        django_messages.success(request, 'Your message was sent to the administration.')
        return redirect('portal_thread_detail')
