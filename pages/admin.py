from django.contrib import admin
from django.utils.text import slugify
from .models import Page


@admin.register(Page)
class PageAdmin(admin.ModelAdmin):
    """Admin interface for dynamic pages"""
    
    list_display = ('title', 'slug', 'page_type', 'is_published', 'created_at')
    list_filter = ('is_published', 'page_type', 'created_at')
    search_fields = ('title', 'slug', 'content')
    readonly_fields = ('created_at', 'updated_at', 'slug')
    
    fieldsets = (
        ('Page Information', {
            'fields': ('title', 'slug', 'page_type', 'is_published')
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
