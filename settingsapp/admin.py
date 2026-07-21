from django.contrib import admin
from .models import SchoolSettings, PageTheme, GalleryImage
from .models import HeroText, HeroButton


class GalleryImageInline(admin.TabularInline):
    """Inline admin for gallery images within SchoolSettings"""
    model = GalleryImage
    fields = ('image', 'title', 'description', 'order')
    extra = 3
    ordering = ('order',)


class HeroTextInline(admin.TabularInline):
    model = HeroText
    fields = ('title', 'subtitle', 'button_text', 'button_url', 'order', 'active')
    extra = 2
    ordering = ('order',)


class HeroButtonInline(admin.TabularInline):
    model = HeroButton
    fields = ('label', 'url', 'order', 'active', 'open_in_new_tab')
    extra = 3
    ordering = ('order',)


@admin.register(SchoolSettings)
class SchoolSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('School Information', {
            'fields': ('school_name', 'motto', 'logo')
        }),
        ('School Contact Information', {
            'fields': ('school_address', 'school_phone', 'school_email'),
            'description': 'School contact details displayed in header and printed documents'
        }),
        ('Homepage Content', {
    'fields': (
        'homepage_hero_enabled',
        'homepage_hero_slide_duration',
        'homepage_hero_show_announcements',
        'homepage_hero_show_counters',
        'homepage_welcome_text',
        'homepage_video_description',
        'homepage_video',
        'homepage_video_url'
    ),
    'description': 'Editable text and homepage hero settings for visitors.'
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
        ('Email Notifications', {
            'fields': (
                'admin_email',
                'admin_email_cc',
                'send_account_creation_email',
                'send_contact_message_email',
                'send_application_email',
            ),
            'description': 'Configure email notifications for various events'
        }),
        ('Email Templates & Subjects', {
            'fields': (
                'account_creation_email_subject',
                'contact_message_email_subject',
                'application_email_subject',
            ),
            'description': 'Customize email subjects. Use {school_name} as placeholder',
            'classes': ('collapse',)
        }),
    )

    inlines = [GalleryImageInline]
    # Add hero inlines so admins can manage hero texts and CTA buttons from the same screen
    inlines += [HeroTextInline, HeroButtonInline]

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
    list_display = ('title_or_date', 'school_settings', 'usage', 'image_preview', 'order', 'created_at')
    list_filter = ('usage', 'created_at', 'school_settings')
    list_editable = ('order',)
    search_fields = ('title', 'description')
    ordering = ('order', '-created_at')

    fieldsets = (
        ('Image Information', {
            'fields': ('school_settings', 'image', 'video', 'homepage_video_url', 'usage', 'title', 'description')
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
