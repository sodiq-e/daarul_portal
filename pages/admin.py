from django.contrib import admin
from django.utils.text import slugify
from .models import Page, PageContent


class PageContentInline(admin.TabularInline):
    """Inline admin for PageContent within Page admin"""
    model = PageContent
    fields = ('title', 'order', 'is_published', 'created_by')
    readonly_fields = ('created_by',)
    extra = 1

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin interface for dynamic pages"""

    list_display = ('title', 'slug', 'page_type', 'is_published', 'created_at')
    list_filter = ('is_published', 'page_type', 'created_at')
    search_fields = ('title', 'slug', 'content')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    inlines = [PageContentInline]

    fieldsets = (
        ('Page Information', {
            'fields': ('title', 'slug', 'url_prefix', 'page_type', 'is_published', 'show_in_navigation',)
        }),
        ('Content', {
            'fields': ('content', 'template')
        }),
        ('Metadata', {
            'fields': ('metadata',),
            'classes': ('collapse',),
            'description': 'JSON data for future extensions and components'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        """Auto-generate slug if empty"""
        if not obj.slug:
            obj.slug = slugify(obj.title)
        super().save_model(request, obj, form, change)


@admin.register(PageContent)
class PageContentAdmin(admin.ModelAdmin):
    """Admin interface for page contents"""

    list_display = ('title', 'page', 'order', 'is_published', 'created_by', 'created_at')
    list_filter = ('page', 'is_published', 'created_at')
    search_fields = ('title', 'body', 'page__title')
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    fieldsets = (
        ('Content Information', {
            'fields': ('page', 'title', 'order', 'is_published')
        }),
        ('Body', {
            'fields': ('body',),
            'classes': ('wide',)
        }),
        ('Media', {
            'fields': ('image',),
            'classes': ('collapse',)
        }),
        ('Extended Data', {
            'fields': ('extra_data',),
            'classes': ('collapse',),
            'description': 'JSON field for flexible future extensions'
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),

    )

    def save_model(self, request, obj, form, change):
        """Auto-set created_by to current user on creation"""
        if not obj.created_by:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
