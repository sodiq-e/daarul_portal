from django.db import models
from django.utils.text import slugify
import json


class Page(models.Model):
    """
    Dynamic Page model for flexible content management.
    Designed for extensibility - can support future sections/components via metadata.
    """
    
    PAGE_TYPE_CHOICES = [
        ('normal', 'Normal Page'),
        ('messages', 'Messages Page'),
        ('news', 'News Page'),
    ]
    
    title = models.CharField(
        max_length=200,
        help_text="Page title displayed on the website"
    )
    
    slug = models.SlugField(
        unique=True,
        help_text="URL-friendly unique identifier (auto-generated from title)"
    )
    
    content = models.TextField(
        blank=True,
        null=True,
        help_text="Main content for the page (optional)"
    )
    
    template = models.CharField(
        max_length=100,
        default='default.html',
        help_text="Template file to render (relative to pages/ directory)"
    )
    
    page_type = models.CharField(
        max_length=20,
        choices=PAGE_TYPE_CHOICES,
        default='normal',
        help_text="Type of page - determines how content is fetched and displayed"
    )
    
    metadata = models.JSONField(
        blank=True,
        null=True,
        default=dict,
        help_text="Flexible JSON field for future extensions and component data"
    )
    
    is_published = models.BooleanField(
        default=True,
        help_text="Only published pages are visible on the website"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Page"
        verbose_name_plural = "Pages"
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        """Auto-generate slug from title if not provided"""
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


class PageContent(models.Model):
    """
    Structured content entries for Pages.
    Supports lesson notes, scheme of work, and other structured content.
    
    Each entry belongs to a Page and can be ordered for display.
    Future-proof with extra_data JSONField for flexible extensions.
    """
    
    page = models.ForeignKey(
        Page,
        on_delete=models.CASCADE,
        related_name='contents',
        help_text="The page this content belongs to"
    )
    
    title = models.CharField(
        max_length=255,
        help_text="Title or heading for this content section"
    )
    
    body = models.TextField(
        help_text="Main content body (supports HTML in future)"
    )
    
    image = models.ImageField(
        upload_to='page_contents/',
        null=True,
        blank=True,
        help_text="Optional image for this content section"
    )
    
    extra_data = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Flexible JSON field for future extensions (e.g., lessons, objectives)"
    )
    
    created_by = models.ForeignKey(
        'auth.User',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='page_contents_created',
        help_text="User who created this content"
    )
    
    is_published = models.BooleanField(
        default=True,
        help_text="Only published content is visible to users"
    )
    
    order = models.IntegerField(
        default=0,
        help_text="Display order (lower numbers appear first)"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['order', '-created_at']
        verbose_name = "Page Content"
        verbose_name_plural = "Page Contents"
        indexes = [
            models.Index(fields=['page', 'is_published', 'order']),
        ]
    
    def __str__(self):
        return f"{self.page.title} - {self.title}"
