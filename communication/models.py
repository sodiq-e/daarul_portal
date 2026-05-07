from django.db import models
from django.contrib.auth.models import User


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
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='portal_thread'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f'Portal thread for {self.user.get_full_name() or self.user.username}'


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

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        sender_label = self.sender.get_full_name() if self.sender else 'System'
        return f'{sender_label} • {self.created_at:%Y-%m-%d %H:%M}'
