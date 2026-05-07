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