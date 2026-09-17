from django.db import models
from django.db.models import Count, Q, Case, When, IntegerField, F
from django.contrib.auth.models import User
from settingsapp.models import TenantModel
from settingsapp.tenant_utils import TenantAwareManager


class PortalThreadQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(Q(participants=user) | Q(user=user)).distinct()

    def personal(self):
        return self.filter(thread_type='personal')

    def group(self):
        return self.filter(thread_type='group')

    def class_threads(self):
        return self.filter(thread_type='class')

    def openable(self):
        """Exclude stale or orphaned threads that cannot be opened or replied to."""
        qs = self.annotate(
            active_participant_count=Count('participants', filter=Q(participants__is_active=True), distinct=True),
            user_is_active=Case(
                When(user__is_active=True, then=1),
                default=0,
                output_field=IntegerField(),
            )
        )
        return qs.annotate(
            active_user_count=F('active_participant_count') + F('user_is_active')
        ).filter(
            Q(thread_type='personal', active_user_count__gte=2)
            | Q(thread_type__in=['group', 'class'], active_participant_count__gte=1)
        ).distinct()

    def with_exact_participants(self, users, thread_type=None):
        user_ids = sorted({u.id for u in users if u is not None})
        qs = self.filter(thread_type=thread_type) if thread_type else self
        for uid in user_ids:
            qs = qs.filter(participants__id=uid)
        return qs.annotate(num_participants=Count('participants', distinct=True)).filter(num_participants=len(user_ids)).distinct()

    def deduplicated(self):
        """Keep only one personal thread per exact participant set, preferring the newest active thread."""
        ordered = self.select_related('user').prefetch_related('participants').order_by('-updated_at')
        seen = set()
        keep_ids = []
        for thread in ordered:
            participants = {user.id for user in thread.participants.all()}
            if thread.user_id is not None:
                participants.add(thread.user_id)
            key = tuple(sorted(participants))
            if thread.thread_type == self.model.THREAD_TYPE_PERSONAL:
                if key in seen:
                    continue
                seen.add(key)
            keep_ids.append(thread.id)
        return self.filter(pk__in=keep_ids).distinct().order_by('-updated_at')


class PortalThreadManager(TenantAwareManager):
    def create(self, **kwargs):
        kwargs.setdefault('tenant', self.get_current_tenant())
        return super().create(**kwargs)

    def get_queryset(self):
        tenant = self.get_current_tenant()
        queryset = PortalThreadQuerySet(self.model, using=self._db)
        if tenant is not None:
            return queryset.filter(tenant=tenant)
        return queryset.none()

    def for_user(self, user):
        return self.get_queryset().for_user(user)

    def personal(self):
        return self.get_queryset().personal()

    def group(self):
        return self.get_queryset().group()

    def class_threads(self):
        return self.get_queryset().class_threads()

    def openable(self):
        return self.get_queryset().openable().deduplicated()

    def deduplicated(self):
        return self.get_queryset().deduplicated()

    def get_current_tenant(self):
        from settingsapp.tenant_utils import get_current_tenant
        return get_current_tenant()


class Message(TenantModel):
    name = models.CharField(max_length=100, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Optional: Link to user if they have an account
    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='contact_messages'
    )
    
    # Reply tracking
    is_replied = models.BooleanField(default=False)
    reply_message = models.TextField(blank=True, null=True)
    replied_at = models.DateTimeField(blank=True, null=True)
    replied_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replied_messages'
    )
    reply_method = models.CharField(
        max_length=20,
        choices=[('email', 'Email'), ('portal', 'Portal Message')],
        blank=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.name if self.name else "Anonymous Message"


class PortalThread(TenantModel):
    THREAD_TYPE_PERSONAL = 'personal'
    THREAD_TYPE_GROUP = 'group'
    THREAD_TYPE_CLASS = 'class'

    THREAD_TYPE_CHOICES = [
        (THREAD_TYPE_PERSONAL, 'Personal'),
        (THREAD_TYPE_GROUP, 'Group'),
        (THREAD_TYPE_CLASS, 'Class'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='portal_thread',
        null=True,
        blank=True
    )
    participants = models.ManyToManyField(
        User,
        related_name='portal_threads',
        blank=True
    )
    name = models.CharField(max_length=150, blank=True)
    thread_type = models.CharField(
        max_length=10,
        choices=THREAD_TYPE_CHOICES,
        default=THREAD_TYPE_GROUP,
        help_text='Explicit type of portal conversation.'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = PortalThreadManager()

    class Meta:
        ordering = ['-updated_at']

    @property
    def is_personal(self):
        return self.thread_type == self.THREAD_TYPE_PERSONAL

    @property
    def is_group(self):
        return self.thread_type == self.THREAD_TYPE_GROUP

    @property
    def is_class(self):
        return self.thread_type == self.THREAD_TYPE_CLASS

    def get_other_participant(self, viewer):
        participants = self.participants.exclude(pk=viewer.pk)
        if participants.exists():
            return participants.first()
        if self.user and self.user != viewer:
            return self.user
        return None

    def get_display_title(self, current_user=None, default_label='Conversation'):
        if self.name:
            return self.name
        if self.is_personal:
            if current_user:
                other = self.get_other_participant(current_user)
                if other:
                    return other.get_full_name() or other.username
            return 'Personal Conversation'
        if self.is_class:
            return self.name or 'Class Conversation'
        if self.is_group:
            return self.name or 'Group Conversation'
        return default_label

    @property
    def is_openable(self):
        active_participants = self.participants.filter(is_active=True)
        active_user_count = active_participants.count()

        if self.user_id is not None and self.user.is_active:
            active_user_count += 1

        if self.thread_type == self.THREAD_TYPE_PERSONAL:
            return active_user_count >= 2

        return active_user_count >= 1

    def __str__(self):
        return self.get_display_title()


class PortalMessage(models.Model):
    thread = models.ForeignKey(
        PortalThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='sent_portal_messages'
    )
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    # Attachment support
    attachment = models.FileField(upload_to='portal_attachments/', null=True, blank=True)
    # Message delivery status: sent -> delivered -> read
    status = models.CharField(max_length=12, choices=[('sent', 'Sent'), ('delivered', 'Delivered'), ('read', 'Read')], default='sent')

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender_label = self.sender.get_full_name() if self.sender else 'System'
        return f'{sender_label} • {self.created_at:%Y-%m-%d %H:%M}'
