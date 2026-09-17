from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.contrib.auth.decorators import login_required
from django.contrib import messages as django_messages
from django.views.generic import ListView, DetailView, TemplateView
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from django.contrib.auth.models import User
from django.db.models import Q, Count
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.core.cache import cache
import time

from .forms import MessageForm, PortalMessageForm
from .models import Message, PortalThread, PortalMessage
from .services.threads import (
    get_or_create_class_thread_for_users,
    get_or_create_group_thread_for_users,
    get_or_create_personal_thread_for_users,
    get_or_create_thread_for_users,
    get_or_create_user_thread,
)
from .services.messages import create_portal_message, serialize_message_for_json
from .services.statuses import (
    get_status_updates_for_thread,
    mark_thread_messages_as_delivered,
    mark_thread_messages_as_read,
)
from .services.presence import get_presence_state_for_thread
from school_classes.models import SchoolClasses, ClassTeacher
from students.models import Student
from settingsapp.email_service import send_contact_message_email, send_contact_message_confirmation_email
from settingsapp.tenant_utils import get_request_tenant, user_is_tenant_admin, user_is_tenant_staff


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

def is_admin(user, request=None):
    """Check if user is an approved admin for the active tenant."""
    if user is None or not getattr(user, 'is_authenticated', False):
        return False

    if getattr(user, 'is_superuser', False) or getattr(user, 'is_staff', False):
        return True

    try:
        tenant = get_request_tenant(request) if request is not None else None
        if tenant is not None:
            profile = getattr(user, 'profile', None)
            if profile is None:
                return user_is_tenant_admin(user, tenant=tenant)
            return profile.is_approved and user_is_tenant_admin(user, tenant=tenant)
        return bool(getattr(user, 'is_superuser', False))
    except AttributeError:
        return bool(getattr(user, 'is_staff', False))


def get_active_accounts(request=None):
    accounts = User.objects.filter(is_active=True).filter(
        Q(profile__is_approved=True) | Q(profile__isnull=True)
    )
    tenant = get_request_tenant(request) if request is not None else None
    if tenant is not None:
        accounts = accounts.filter(
            tenant_memberships__tenant=tenant,
            tenant_memberships__is_active=True,
        )
    return accounts.distinct().order_by('username')


def get_user_threads(user, request=None):
    tenant = get_request_tenant(request) if request is not None else None
    queryset = PortalThread.objects.openable().all()
    if not (user.is_superuser or (tenant is not None and user_is_tenant_admin(user, tenant=tenant))):
        queryset = PortalThread.objects.openable().for_user(user)
    return queryset.deduplicated().order_by('-updated_at')


def get_user_personal_threads(user, request=None):
    tenant = get_request_tenant(request) if request is not None else None
    queryset = PortalThread.objects.openable().personal()
    if not (user.is_superuser or (tenant is not None and user_is_tenant_admin(user, tenant=tenant))):
        queryset = PortalThread.objects.openable().personal().for_user(user)
    return queryset.deduplicated().order_by('-updated_at')


def get_or_create_user_thread(user):
    return __import__('communication.services.threads', fromlist=['get_or_create_user_thread']).get_or_create_user_thread(user)


def get_or_create_thread_for_users(users, thread_type=PortalThread.THREAD_TYPE_GROUP, name=None):
    return __import__('communication.services.threads', fromlist=['get_or_create_thread_for_users']).get_or_create_thread_for_users(users, thread_type=thread_type, name=name)


def get_or_create_personal_thread_for_users(users, name=None):
    return __import__('communication.services.threads', fromlist=['get_or_create_personal_thread_for_users']).get_or_create_personal_thread_for_users(users, name=name)


def get_or_create_group_thread_for_users(users, name=None):
    return __import__('communication.services.threads', fromlist=['get_or_create_group_thread_for_users']).get_or_create_group_thread_for_users(users, name=name)


def get_or_create_class_thread_for_users(users, name):
    return __import__('communication.services.threads', fromlist=['get_or_create_class_thread_for_users']).get_or_create_class_thread_for_users(users, name=name)


def get_user_thread_or_404(user, thread_id):
    thread = PortalThread.objects.openable().for_user(user).filter(pk=thread_id).first()
    if thread is None:
        raise Http404('Thread not found')

    if thread.is_personal and thread.user == user and not thread.participants.exists():
        thread.participants.add(user)

    return thread


def _get_presence_state_for_thread(thread, viewer):
    return get_presence_state_for_thread(thread, viewer)


class AdminMessageListView(LoginRequiredMixin, UserPassesTestMixin, ListView):
    """List all contact messages for admin"""
    model = Message
    template_name = 'communication/admin_messages_list.html'
    context_object_name = 'messages'
    paginate_by = 20
    ordering = ['-created_at']

    def test_func(self):
        return is_admin(self.request.user, request=self.request)

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
        return is_admin(self.request.user, request=self.request)

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

            thread = get_or_create_personal_thread_for_users([request.user, message.user])
            create_portal_message(thread, request.user, reply_text)
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
        return is_admin(self.request.user, request=self.request)

    def get_queryset(self):
        return get_active_accounts(self.request)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        users_with_counts = []
        for user in context['users']:
            threads = get_user_personal_threads(user, request=self.request)
            unread_count = 0
            total_messages = 0
            if threads.exists():
                total_messages = sum(thread.messages.count() for thread in threads)
                unread_count = sum(
                    thread.messages.exclude(sender=user).filter(is_read=False).count()
                    for thread in threads
                )
            users_with_counts.append({
                'user': user,
                'threads': threads,
                'total_messages': total_messages,
                'unread_count': unread_count,
            })
        context['users_with_counts'] = users_with_counts
        context['form'] = PortalMessageForm()

        selected_user_id = self.request.GET.get('user_id')
        selected_user = None
        selected_thread = None
        if selected_user_id:
            try:
                selected_user = get_active_accounts(self.request).get(pk=selected_user_id)
            except (ValueError, User.DoesNotExist):
                selected_user = None

        if selected_user is not None and selected_user != self.request.user:
            selected_thread = get_or_create_personal_thread_for_users([self.request.user, selected_user])
            mark_thread_messages_as_read(selected_thread, self.request.user)
            context['selected_user'] = selected_user
            context['selected_thread'] = selected_thread
            context['selected_other_participant'] = selected_thread.get_other_participant(self.request.user)
            context['selected_messages'] = selected_thread.messages.select_related('sender').all()

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

        participants = []
        for user_id in selected_users:
            try:
                user = User.objects.get(id=user_id, is_active=True)
                participants.append(user)
            except User.DoesNotExist:
                continue

        if not participants:
            django_messages.error(request, 'No valid selected users found.')
            return redirect('admin_portal_users_list')

        sent_count = 0
        for user in participants:
            if user == request.user:
                continue
            thread = get_or_create_personal_thread_for_users([request.user, user])
            create_portal_message(thread, request.user, bulk_message)
            sent_count += 1

        if sent_count > 0:
            django_messages.success(request, f'Bulk message sent to {sent_count} user(s).')
        else:
            django_messages.error(request, 'No messages were sent. Please check your selections.')

        return redirect('admin_portal_users_list')


class AdminPortalThreadView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'communication/admin_portal_thread_detail.html'

    def test_func(self):
        return is_admin(self.request.user, request=self.request)

    def dispatch(self, request, *args, **kwargs):
        thread_id = kwargs.get('thread_id')
        if thread_id:
            thread = PortalThread.objects.openable().filter(pk=thread_id).first()
            if thread is None:
                django_messages.error(request, 'This conversation no longer exists or is no longer available.')
                return redirect('admin_portal_users_list')
        return super().dispatch(request, *args, **kwargs)

    def get_thread(self, **kwargs):
        thread_id = kwargs.get('thread_id')
        if thread_id:
            return PortalThread.objects.openable().filter(pk=thread_id).first()

        user_id = kwargs.get('user_id')
        if user_id:
            user = get_object_or_404(get_active_accounts(self.request), pk=user_id)
            return get_or_create_personal_thread_for_users([self.request.user, user])

        raise Http404('Thread not found.')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.get_thread(**kwargs)
        mark_thread_messages_as_read(thread, self.request.user)
        other_participant = thread.get_other_participant(self.request.user)
        last_other_message = thread.messages.exclude(sender=self.request.user).order_by('-created_at').first()

        context['thread'] = thread
        context['messages'] = thread.messages.select_related('sender').all()
        context['form'] = PortalMessageForm()
        context['other_participant'] = other_participant
        context['other_last_seen_at'] = last_other_message.created_at if last_other_message else None
        return context

    def post(self, request, *args, **kwargs):
        thread = self.get_thread(**kwargs)
        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')

        if not content and not attachment:
            if kwargs.get('thread_id'):
                return redirect('admin_portal_thread_detail', thread_id=thread.id)
            other_participant = thread.get_other_participant(request.user)
            return redirect('admin_portal_thread_detail', user_id=other_participant.id if other_participant else request.user.id)

        msg = create_portal_message(thread, request.user, content, attachment=attachment, status='sent')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = {
                'id': msg.id,
                'content': msg.content,
                'created_at': msg.created_at.strftime('%b %d, %Y %H:%M'),
                'created_at_iso': msg.created_at.isoformat(),
                'sender': request.user.get_full_name() or request.user.username,
                'attachment_url': msg.attachment.url if msg.attachment else None,
                'attachment_name': getattr(msg.attachment, 'name', None),
                'status': msg.status,
            }
            return JsonResponse({'success': True, 'message': data})

        django_messages.success(request, 'Portal reply sent.')
        if kwargs.get('thread_id'):
            return redirect('admin_portal_thread_detail', thread_id=thread.id)
        if kwargs.get('user_id'):
            return redirect('admin_portal_thread_detail', user_id=kwargs.get('user_id'))
        other_participant = thread.participants.exclude(pk=request.user.pk).first()
        if other_participant:
            return redirect('admin_portal_thread_detail', user_id=other_participant.id)
        return redirect('admin_portal_thread_detail', thread_id=thread.id)


class AdminPortalGroupsListView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'communication/admin_portal_groups_list.html'

    def test_func(self):
        return is_admin(self.request.user, request=self.request)

    def get_context_data(self, **kwargs):
        from school_classes.models import SchoolClasses
        users = get_active_accounts(self.request).select_related('profile').prefetch_related('groups')
        classes = SchoolClasses.objects.all().order_by('class_name')
        threads = PortalThread.objects.openable().filter(
            thread_type__in=[PortalThread.THREAD_TYPE_GROUP, PortalThread.THREAD_TYPE_CLASS]
        ).order_by('-updated_at')
        context = super().get_context_data(**kwargs)
        context.update({
            'threads': threads,
            'users': users,
            'classes': classes,
        })
        return context


class AdminPortalGroupCreateView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'communication/admin_portal_group_form.html'

    def test_func(self):
        return is_admin(self.request.user, request=self.request)

    def get_context_data(self, **kwargs):
        from school_classes.models import SchoolClasses
        users = get_active_accounts(self.request).select_related('profile').prefetch_related('groups')
        classes = SchoolClasses.objects.all().order_by('class_name')
        context = super().get_context_data(**kwargs)
        context.update({
            'users': users,
            'classes': classes,
            'selected_ids': [],
            'thread': None,
        })
        return context

    def post(self, request, *args, **kwargs):
        selected_user_ids = request.POST.getlist('participants')
        name = request.POST.get('name', '').strip()
        include_admin = request.POST.get('include_admin') == 'on'

        if not name:
            django_messages.error(request, 'Group chat name is required.')
            return self.get(request, *args, **kwargs)

        if not selected_user_ids:
            django_messages.error(request, 'Please select at least one participant.')
            return self.get(request, *args, **kwargs)

        participants = list(User.objects.filter(id__in=selected_user_ids, is_active=True))
        if include_admin and request.user not in participants:
            participants.append(request.user)

        thread = PortalThread.objects.create(thread_type=PortalThread.THREAD_TYPE_GROUP, name=name)
        thread.participants.set(participants)
        thread.user = None
        thread.updated_at = timezone.now()
        thread.save()

        django_messages.success(request, f'Group chat "{name}" created successfully.')
        return redirect('admin_portal_group_edit', thread_id=thread.id)


class AdminPortalGroupEditView(LoginRequiredMixin, UserPassesTestMixin, TemplateView):
    template_name = 'communication/admin_portal_group_form.html'

    def test_func(self):
        return is_admin(self.request.user, request=self.request)

    def get_context_data(self, **kwargs):
        from school_classes.models import SchoolClasses
        thread = get_object_or_404(PortalThread, pk=self.kwargs['thread_id'])
        users = get_active_accounts(self.request).select_related('profile').prefetch_related('groups')
        classes = SchoolClasses.objects.all().order_by('class_name')
        context = super().get_context_data(**kwargs)
        context.update({
            'thread': thread,
            'users': users,
            'classes': classes,
            'selected_ids': [u.id for u in thread.participants.all()],
        })
        return context

    def post(self, request, *args, **kwargs):
        thread = get_object_or_404(PortalThread, pk=self.kwargs['thread_id'])
        selected_user_ids = request.POST.getlist('participants')
        name = request.POST.get('name', '').strip()
        include_admin = request.POST.get('include_admin') == 'on'

        if not name:
            django_messages.error(request, 'Group chat name is required.')
            return self.get(request, *args, **kwargs)

        if not selected_user_ids:
            django_messages.error(request, 'Please select at least one participant.')
            return self.get(request, *args, **kwargs)

        participants = list(User.objects.filter(id__in=selected_user_ids, is_active=True))
        if include_admin and request.user not in participants:
            participants.append(request.user)

        thread.thread_type = PortalThread.THREAD_TYPE_GROUP
        thread.user = None
        thread.name = name
        thread.participants.set(participants)
        thread.updated_at = timezone.now()
        thread.save()

        django_messages.success(request, f'Group chat "{name}" updated successfully.')
        return redirect('admin_portal_group_edit', thread_id=thread.id)


@login_required
@require_POST
def admin_portal_thread_start(request, user_id):
    if not is_admin(request.user, request=request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    user = get_object_or_404(get_active_accounts(request), pk=user_id)
    thread = get_or_create_personal_thread_for_users([request.user, user])
    return redirect('admin_portal_thread_detail', thread_id=thread.id)


@login_required
def start_class_thread(request, class_id):
    """Create/open a class-wide thread (teacher + students).

    Only users with a teacher/staff membership for the active tenant may start a class thread.
    """
    tenant = get_request_tenant(request)
    if not (request.user.is_superuser or user_is_tenant_staff(request.user, tenant=tenant)):
        django_messages.error(request, 'You do not have permission to start a class thread for this tenant.')
        return redirect('school_classes:class_list')

    try:
        school_class = SchoolClasses.objects.get(pk=class_id)
    except SchoolClasses.DoesNotExist:
        django_messages.error(request, 'Class not found.')
        return redirect('school_classes:class_list')

    # Collect participant user accounts (students and class teachers)
    participants = []
    for s in school_class.students.all():
        if getattr(s, 'user', None):
            participants.append(s.user)
    for ct in school_class.teachers.select_related('teacher__user').all():
        user_obj = getattr(ct.teacher, 'user', None)
        if user_obj:
            participants.append(user_obj)

    # Ensure current user is included
    if request.user not in participants:
        participants.append(request.user)

    if not participants:
        django_messages.error(request, 'No participants with user accounts found for this class.')
        return redirect('school_classes:class_detail', class_id)

    name = f"{school_class.class_name} — Class Chat"
    thread = get_or_create_class_thread_for_users(participants, name=name)

    return redirect(f"{reverse('portal_thread_detail')}?thread_id={thread.id}")


@login_required
def student_message_teacher(request, student_id):
    """Start a conversation between a student and their class teacher(s).

    If multiple teachers exist, include them all (creates a small group).
    """
    try:
        student = Student.objects.select_related('user', 'student_class').get(pk=student_id)
    except Student.DoesNotExist:
        django_messages.error(request, 'Student not found.')
        return redirect('students:student_list')

    school_class = getattr(student, 'student_class', None)
    if not school_class:
        django_messages.error(request, 'Student is not assigned to a class.')
        return redirect('students:student_detail', student.pk)

    tenant = get_request_tenant(request)
    if hasattr(request.user, 'teacher_profile') and not user_is_tenant_staff(request.user, tenant=tenant):
        if request.user != getattr(student, 'user', None):
            is_assigned_teacher = ClassTeacher.objects.filter(
                teacher=request.user.teacher_profile,
                school_class=school_class,
                is_active=True
            ).exists()
            if not is_assigned_teacher:
                django_messages.error(request, 'You are not assigned to this student\'s class.')
                return redirect('students:student_detail', student.pk)

    participants = []
    if getattr(student, 'user', None):
        participants.append(student.user)

    for ct in school_class.teachers.select_related('teacher__user').all():
        user_obj = getattr(ct.teacher, 'user', None)
        if user_obj and user_obj not in participants:
            participants.append(user_obj)

    if not participants or len(participants) < 2:
        django_messages.error(request, 'No teacher accounts available to message for this student.')
        return redirect('student_detail', student.pk)

    name = f"{school_class.class_name} — Teachers & {student.full_name()}"
    if len(participants) == 2:
        thread = get_or_create_personal_thread_for_users(participants)
    else:
        thread = get_or_create_group_thread_for_users(participants, name=name)
    return redirect(f"{reverse('portal_thread_detail')}?thread_id={thread.id}")


class PortalInboxView(LoginRequiredMixin, TemplateView):
    template_name = 'communication/portal_messages_list.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        threads = get_user_threads(self.request.user, request=self.request).prefetch_related('participants').annotate(
            unread_count=Count(
                'messages',
                filter=Q(messages__is_read=False) & ~Q(messages__sender=self.request.user)
            )
        )
        context['threads'] = threads
        context['unread_count'] = sum(thread.unread_count for thread in threads)
        return context


class PortalThreadDetailView(LoginRequiredMixin, TemplateView):
    template_name = 'communication/portal_thread_detail.html'

    def get(self, request, *args, **kwargs):
        thread_id = request.GET.get('thread_id')
        if thread_id:
            try:
                thread = get_user_thread_or_404(request.user, thread_id)
            except Http404:
                return redirect('portal_messages_list')
        else:
            thread = get_user_threads(request.user, request=request).first()

        if not thread:
            return redirect('portal_messages_list')

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread_id = self.request.GET.get('thread_id')
        if thread_id:
            thread = get_user_thread_or_404(self.request.user, thread_id)
        else:
            thread = get_user_threads(self.request.user, request=self.request).first()

        mark_thread_messages_as_read(thread, self.request.user)
        other_participant = thread.get_other_participant(self.request.user)

        last_other_message = thread.messages.exclude(sender=self.request.user).order_by('-created_at').first()

        context['thread'] = thread
        context['messages'] = thread.messages.select_related('sender').all()
        context['form'] = PortalMessageForm()
        context['other_participant'] = other_participant
        context['other_last_seen_at'] = last_other_message.created_at if last_other_message else None
        return context

    def post(self, request, *args, **kwargs):
        thread_id = request.POST.get('thread_id') or request.GET.get('thread_id')
        if thread_id:
            thread = get_user_thread_or_404(request.user, thread_id)
        else:
            thread = get_user_threads(request.user, request=request).first()
            if not thread:
                return redirect('portal_messages_list')

        content = request.POST.get('content', '').strip()
        attachment = request.FILES.get('attachment')

        if not content and not attachment:
            django_messages.error(request, 'Please enter a message or attach a file.')
            return redirect(f'{reverse("portal_thread_detail")}?thread_id={thread.id}')

        msg = create_portal_message(thread, request.user, content, attachment=attachment, status='sent')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            data = {
                'id': msg.id,
                'content': msg.content,
                'created_at': msg.created_at.strftime('%b %d, %Y %H:%M'),
                'created_at_iso': msg.created_at.isoformat(),
                'sender': request.user.get_full_name() or request.user.username,
                'sender_id': request.user.id,
                'attachment_url': msg.attachment.url if msg.attachment else None,
                'attachment_name': getattr(msg.attachment, 'name', None),
                'status': msg.status,
                'is_read': msg.is_read,
            }
            return JsonResponse({'success': True, 'message': data})

        django_messages.success(request, 'Your message was sent.')
        return redirect(f'{reverse("portal_thread_detail")}?thread_id={thread.id}')


@login_required
@require_POST
def sync_portal_presence(request):
    """Record a heartbeat from the current user for the active thread and return presence for the other participant."""
    thread_id = request.POST.get('thread_id')
    if thread_id:
        thread = get_user_thread_or_404(request.user, thread_id)
    else:
        thread = get_or_create_user_thread(request.user)

    now = int(time.time())
    cache.set(f'portal_presence:{thread.id}:{request.user.id}', now, 10)

    presence = _get_presence_state_for_thread(thread, request.user)
    return JsonResponse({'success': True, 'presence': presence})


@login_required
@require_POST
def send_portal_message_ajax(request):
    """AJAX endpoint to send a portal message (used by JS)."""
    thread_id = request.POST.get('thread_id')
    if thread_id:
        thread = get_user_thread_or_404(request.user, thread_id)
    else:
        thread = get_or_create_user_thread(request.user)

    content = request.POST.get('content', '').strip()
    attachment = request.FILES.get('attachment')

    if not content and not attachment:
        return JsonResponse({'success': False, 'error': 'Empty message.'}, status=400)

    msg = create_portal_message(thread, request.user, content, attachment=attachment, status='sent')

    data = {
        'id': msg.id,
        'content': msg.content,
        'created_at': msg.created_at.strftime('%b %d, %Y %H:%M'),
        'created_at_iso': msg.created_at.isoformat(),
        'sender': request.user.get_full_name() or request.user.username,
        'attachment_url': msg.attachment.url if msg.attachment else None,
        'attachment_name': getattr(msg.attachment, 'name', None),
        'status': msg.status,
    }
    return JsonResponse({'success': True, 'message': data})


@login_required
@require_POST
def edit_portal_message_ajax(request, message_id):
    """Edit a user's own portal message via AJAX."""
    message = get_object_or_404(PortalMessage, pk=message_id)
    if message.sender_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    content = request.POST.get('content', '').strip()
    if not content:
        return JsonResponse({'success': False, 'error': 'Empty message.'}, status=400)

    message.content = content
    message.save(update_fields=['content'])

    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'status': message.status,
            'created_at': message.created_at.strftime('%b %d, %Y %H:%M'),
        }
    })


@login_required
@require_POST
def delete_portal_message_ajax(request, message_id):
    """Delete a user's own portal message via AJAX."""
    message = get_object_or_404(PortalMessage, pk=message_id)
    if message.sender_id != request.user.id:
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    message.delete()
    return JsonResponse({'success': True, 'deleted_id': message_id})


@login_required
def fetch_portal_messages(request):
    """Return messages for the current user's thread as JSON. Optionally accepts ?thread_id=<id> and ?since_id=<id>."""
    thread_id = request.GET.get('thread_id')
    if thread_id:
        thread = get_user_thread_or_404(request.user, thread_id)
    else:
        thread = get_user_threads(request.user, request=request).first()
        if not thread:
            return JsonResponse({'success': True, 'messages': []})

    since_id = request.GET.get('since_id')
    qs = thread.messages.select_related('sender')
    if since_id:
        try:
            since_id = int(since_id)
            qs = qs.filter(id__gt=since_id)
        except ValueError:
            pass

    messages_qs = qs.order_by('created_at')
    mark_thread_messages_as_delivered(thread, request.user)

    messages_list = [serialize_message_for_json(m) for m in messages_qs]

    return JsonResponse({'success': True, 'messages': messages_list})


@login_required
def portal_message_compose(request):
    target_user_id = request.GET.get('user_id') or request.GET.get('teacher_id') or request.GET.get('student_id')
    if not target_user_id:
        return redirect('portal_messages_list')

    try:
        target_user = get_active_accounts(request).get(pk=target_user_id)
    except (ValueError, User.DoesNotExist):
        return redirect('portal_messages_list')

    if target_user == request.user:
        return redirect('portal_messages_list')

    thread = get_or_create_personal_thread_for_users([request.user, target_user])
    return redirect(f'{reverse("portal_thread_detail")}?thread_id={thread.id}')


@login_required
def fetch_admin_portal_messages(request, user_id=None, thread_id=None):
    if not is_admin(request.user, request=request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if thread_id:
        thread = get_object_or_404(PortalThread, pk=thread_id)
    else:
        user = get_object_or_404(get_active_accounts(request), pk=user_id)
        thread = get_or_create_personal_thread_for_users([request.user, user])

    since_id = request.GET.get('since_id')
    qs = thread.messages.select_related('sender')
    if since_id:
        try:
            since_id = int(since_id)
            qs = qs.filter(id__gt=since_id)
        except ValueError:
            pass

    messages_qs = qs.order_by('created_at')
    mark_thread_messages_as_delivered(thread, request.user)
    thread.messages.exclude(sender=request.user).filter(is_read=False).update(is_read=True)

    messages_list = [serialize_message_for_json(m) for m in messages_qs]

    return JsonResponse({'success': True, 'messages': messages_list})


@login_required
def fetch_admin_portal_statuses(request, user_id=None, thread_id=None):
    if not is_admin(request.user, request=request):
        return JsonResponse({'success': False, 'error': 'Unauthorized'}, status=403)

    if thread_id:
        thread = get_object_or_404(PortalThread, pk=thread_id)
    else:
        user = get_object_or_404(get_active_accounts(request), pk=user_id)
        thread = get_or_create_personal_thread_for_users([request.user, user])

    statuses = get_status_updates_for_thread(thread, sender=request.user)
    return JsonResponse({'success': True, 'statuses': statuses})


@login_required
def fetch_portal_statuses(request):
    """Return status updates for messages belonging to the current user's thread."""
    thread_id = request.GET.get('thread_id')
    if thread_id:
        thread = get_user_thread_or_404(request.user, thread_id)
    else:
        thread = get_or_create_user_thread(request.user)
    statuses = get_status_updates_for_thread(thread, sender=request.user)
    return JsonResponse({'success': True, 'statuses': statuses})
