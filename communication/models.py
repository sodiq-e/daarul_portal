from django.db import models
from django.db.models import Count, Q
from django.contrib.auth.models import User


class PortalThreadQuerySet(models.QuerySet):
    def for_user(self, user):
        return self.filter(Q(participants=user) | Q(user=user)).distinct()

    def personal(self):
        return self.filter(thread_type='personal')

    def group(self):
        return self.filter(thread_type='group')

    def class_threads(self):
        return self.filter(thread_type='class')

    def with_exact_participants(self, users, thread_type=None):
        user_ids = sorted({u.id for u in users if u is not None})
        qs = self.filter(thread_type=thread_type) if thread_type else self
        for uid in user_ids:
            qs = qs.filter(participants__id=uid)
        return qs.annotate(num_participants=Count('participants', distinct=True)).filter(num_participants=len(user_ids)).distinct()


class PortalThreadManager(models.Manager.from_queryset(PortalThreadQuerySet)):
    pass


class Message(models.Model):
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


class PortalThread(models.Model):
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
