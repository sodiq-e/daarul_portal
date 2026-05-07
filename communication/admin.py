from django.contrib import admin
from .models import Message


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'created_at', 'is_replied', 'reply_method')
    list_filter = ('is_replied', 'created_at', 'reply_method')
    search_fields = ('name', 'email', 'message')
    readonly_fields = ('created_at', 'replied_at', 'replied_by')
    
    fieldsets = (
        ('Message Details', {
            'fields': ('name', 'email', 'phone', 'message', 'user', 'created_at')
        }),
        ('Reply Information', {
            'fields': ('is_replied', 'reply_method', 'reply_message', 'replied_at', 'replied_by'),
            'classes': ('collapse',)
        }),
    )
