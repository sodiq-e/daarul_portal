from django.contrib import admin
from .models import SchoolSettings, PageTheme, GalleryImage


class GalleryImageInline(admin.TabularInline):
    """Inline admin for gallery images within SchoolSettings"""
    model = GalleryImage
    fields = ('image', 'title', 'description', 'order')
    extra = 3
    ordering = ('order',)


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'motto', 'logo')
        }),
        ('Homepage Content', {
            'fields': ('homepage_welcome_text', 'homepage_video_description'),
            'description': 'Editable text content for the homepage.'
        }),
        ('Default Theme Colors', {
            'fields': (
                'primary_color',
                'secondary_color',
                'accent_color',
                'background_color',
                'text_color'
            ),
            'description': 'These are the default colors used across all pages. Each page can have its own custom theme.'
        }),
    )
    
    inlines = [GalleryImageInline]
    
    def has_add_permission(self, request):
        # Limit to only one school settings object
        return not SchoolSettings.objects.exists()
    
    class Media:
        css = {
            'all': ('admin-colorpicker.css',)
        }


@admin.register(PageTheme)
class PageThemeAdmin(admin.ModelAdmin):
    list_display = ('page_display_name_or_name', 'is_enabled', 'primary_color_preview')
    list_filter = ('is_enabled', 'page_name')
    list_editable = ('is_enabled',)
    search_fields = ('page_name', 'page_display_name')
    
    fieldsets = (
        ('Page Selection', {
            'fields': ('page_name', 'page_display_name', 'url_pattern', 'is_enabled'),
            'description': 'Choose which page this theme applies to. Use lowercase page names (e.g., "announcements", "library"). URL pattern is optional for custom page detection.'
        }),
        ('Custom Theme Colors', {
            'fields': (
                'primary_color',
                'secondary_color',
                'accent_color',
                'background_color',
                'text_color'
            ),
            'description': 'Customize colors for this page only'
        }),
    )
    
    def page_display_name_or_name(self, obj):
        return obj.page_display_name or f"{obj.page_name.title()}"
    page_display_name_or_name.short_description = 'Page'
    
    def primary_color_preview(self, obj):
        return f'<div style="width: 30px; height: 30px; background-color: {obj.primary_color}; border: 1px solid #ccc;"></div>'
    primary_color_preview.short_description = 'Color Preview'
    primary_color_preview.allow_tags = True
    
    class Media:
        css = {
            'all': ('admin-colorpicker.css',)
        }


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ('title_or_date', 'school_settings', 'image_preview', 'order', 'created_at')
    list_filter = ('created_at', 'school_settings')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    ordering = ('order', '-created_at')
    
    fieldsets = (
        ('Image Information', {
            'fields': ('school_settings', 'image', 'title', 'description')
        }),
        ('Display Settings', {
            'fields': ('order',),
            'description': 'Set the order to control where this image appears in the gallery'
        }),
    )
    
    def title_or_date(self, obj):
        return obj.title or f"Gallery Image - {obj.created_at.strftime('%Y-%m-%d')}"
    title_or_date.short_description = 'Title'
    
    def image_preview(self, obj):
        if obj.image:
            return f'<img src="{obj.image.url}" width="50" height="50" />'
        return 'No image'
    image_preview.short_description = 'Preview'
    image_preview.allow_tags = True
