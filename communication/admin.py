from django.contrib import admin
from .models import Message, PortalThread, PortalMessage


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


@admin.register(PortalThread)
class PortalThreadAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')


@admin.register(PortalMessage)
class PortalMessageAdmin(admin.ModelAdmin):
    list_display = ('thread', 'sender', 'created_at', 'is_read')
    list_filter = ('is_read', 'created_at')
    search_fields = ('thread__user__username', 'sender__username', 'content')
    readonly_fields = ('created_at',)
