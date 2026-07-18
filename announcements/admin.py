from django.contrib import admin
from django.utils.html import format_html
from .models import Announcement, AnnouncementCategory
from .forms import AnnouncementForm


@admin.register(Announcement)
class AnnouncementAdmin(admin.ModelAdmin):
    form = AnnouncementForm
    list_display = ('title', 'created_by', 'category', 'priority', 'is_active', 'created_at')
    list_filter = ('is_active', 'priority', 'created_at', 'created_by', 'category')
    search_fields = ('title', 'excerpt', 'content', 'created_by__username')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at', 'featured_image_preview')
    filter_horizontal = ('galleries',)

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'title_size', 'title_alignment', 'excerpt', 'content', 'category', 'priority')
        }),
        ('Media', {
            'fields': ('featured_image', 'featured_image_preview', 'video_thumbnail', 'video_url', 'galleries')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def featured_image_preview(self, obj):
        if obj.featured_image:
            return format_html('<img src="{}" style="max-height:120px; border-radius:6px;"/>', obj.featured_image.url)
        return '(No image)'

    featured_image_preview.short_description = 'Featured Image Preview'

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new announcement
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(AnnouncementCategory)
class AnnouncementCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)
