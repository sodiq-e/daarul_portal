from __future__ import annotations

from communication.models import PortalMessage


STATUS_SENT = 'sent'
STATUS_DELIVERED = 'delivered'
STATUS_READ = 'read'


def mark_thread_messages_as_delivered(thread, reader):
    """Mark all undelivered incoming messages as delivered when read by the recipient."""
    return thread.messages.exclude(sender=reader).filter(status=STATUS_SENT).update(status=STATUS_DELIVERED)


def mark_thread_messages_as_read(thread, reader):
    """Mark incoming messages as read when the recipient opens the thread."""
    return thread.messages.exclude(sender=reader).filter(is_read=False).update(is_read=True, status=STATUS_READ)


def mark_sent_messages_for_thread(thread, sender=None):
    queryset = PortalMessage.objects.filter(thread=thread)
    if sender is not None:
        queryset = queryset.filter(sender=sender)
    return queryset.exclude(status=STATUS_SENT).count()


def serialize_status_for_json(message):
    """Mirror the frontend contract for message status payloads."""
    return {'id': message.id, 'status': message.status}


def get_status_updates_for_thread(thread, sender=None):
    """Return status updates for messages in the given thread, preserving the API contract."""
    queryset = PortalMessage.objects.filter(thread=thread)
    if sender is not None:
        queryset = queryset.filter(sender=sender)
    return [serialize_status_for_json(message) for message in queryset.exclude(status=STATUS_SENT)]
