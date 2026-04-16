from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone


GROUP_CLASSIFICATION_CHOICES = [
    ('Student', 'Student'),
    ('Teacher', 'Teacher'),
    ('Staff', 'Staff'),
    ('Parent', 'Parent'),
]


class Profile(models.Model):
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='profile'
    )
    requested_group = models.CharField(
        max_length=50,
        choices=GROUP_CLASSIFICATION_CHOICES,
        blank=True,
        null=True,
        help_text='The user role requested during registration.'
    )
    is_approved = models.BooleanField(
        default=False,
        help_text='Whether an admin has approved this user and granted access.'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='approved_profiles'
    )

    def save(self, *args, **kwargs):
        original = None
        if self.pk:
            original = Profile.objects.filter(pk=self.pk).first()

        super().save(*args, **kwargs)

        if self.is_approved and (original is None or not original.is_approved):
            self.user.is_active = True
            self.user.save()
            if self.requested_group:
                group, _ = Group.objects.get_or_create(name=self.requested_group)
                self.user.groups.add(group)

    def __str__(self):
        return f'{self.user.username} profile'
