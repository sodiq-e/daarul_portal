from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.html import format_html
from settingsapp.models import GalleryImage


class Announcement(models.Model):
    title = models.CharField(max_length=200, help_text='Title of the announcement')
    content = models.TextField(help_text='Full content of the announcement')
    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='announcements'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text='Whether this announcement is currently active and visible'
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('low', 'Low'),
            ('normal', 'Normal'),
            ('high', 'High'),
            ('urgent', 'Urgent'),
        ],
        default='normal',
        help_text='Priority level of the announcement'
    )
    title_size = models.CharField(
        max_length=10,
        choices=[
            ('small', 'Small'),
            ('medium', 'Medium'),
            ('large', 'Large'),
        ],
        default='large',
        help_text='Title size shown on the announcement page'
    )
    title_alignment = models.CharField(
        max_length=10,
        choices=[
            ('start', 'Left'),
            ('center', 'Center'),
            ('end', 'Right'),
        ],
        default='start',
        help_text='Title alignment on the announcement page'
    )
    # Added fields for media and excerpts
    excerpt = models.CharField(max_length=500, blank=True, help_text='Short summary shown in lists')
    featured_image = models.ImageField(upload_to='announcements/images/', blank=True, null=True)
    video_thumbnail = models.ImageField(upload_to='announcements/videos/thumbnails/', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text='Optional video URL (YouTube embed or mp4 link)')
    # Link to existing gallery images (reuse existing GalleryImage model)
    galleries = models.ManyToManyField(GalleryImage, blank=True, related_name='announcements')
    # Optional category
    # Simple lightweight category model is defined below
    category = models.ForeignKey('AnnouncementCategory', blank=True, null=True, on_delete=models.SET_NULL, related_name='announcements')

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Announcement'
        verbose_name_plural = 'Announcements'

    def __str__(self):
        return self.title

    def get_priority_color(self):
        """Return CSS color class based on priority"""
        colors = {
            'low': 'info',
            'normal': 'secondary',
            'high': 'warning',
            'urgent': 'danger'
        }
        return colors.get(self.priority, 'secondary')

    def has_gallery(self):
        return self.galleries.exists()

    def gallery_cover(self):
        first = self.galleries.first()
        if first and first.image:
            return first.image.url
        return None

    def gallery_counts(self):
        photos = self.galleries.filter(image__isnull=False).count()
        videos = self.galleries.filter(video__isnull=False).count()
        return {'photos': photos, 'videos': videos}

    def featured_image_tag(self):
        if self.featured_image:
            return format_html('<img src="{}" style="max-height:120px;"/>', self.featured_image.url)
        return ''

    def title_size_class(self):
        return {
            'small': 'title-small',
            'medium': 'title-medium',
            'large': 'title-large',
        }.get(self.title_size, 'title-large')

    def title_alignment_class(self):
        return {
            'start': 'text-start',
            'center': 'text-center',
            'end': 'text-end',
        }.get(self.title_alignment, 'text-start')


class AnnouncementCategory(models.Model):
    """Lightweight category model for announcements"""
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Announcement Category'
        verbose_name_plural = 'Announcement Categories'

    def __str__(self):
        return self.name
