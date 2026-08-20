from __future__ import annotations

from django.utils import timezone

from communication.models import PortalMessage, PortalThread


def create_portal_message(thread: PortalThread, sender, content: str = '', attachment=None, status: str = 'sent') -> PortalMessage:
    """Create a PortalMessage while preserving the exact existing behavior and response contract."""
    if not thread.participants.filter(pk=sender.pk).exists():
        thread.participants.add(sender)

    message = PortalMessage.objects.create(
        thread=thread,
        sender=sender,
        content=content,
        attachment=attachment,
        status=status,
    )
    thread.updated_at = timezone.now()
    thread.save(update_fields=['updated_at'])
    return message


def serialize_message_for_json(message: PortalMessage):
    """Mirror the JSON contract already expected by the frontend."""
    return {
        'id': message.id,
        'sender_id': message.sender.id if message.sender else None,
        'sender': message.sender.get_full_name() if message.sender else 'System',
        'content': message.content,
        'created_at': message.created_at.strftime('%b %d, %Y %H:%M'),
        'created_at_iso': message.created_at.isoformat(),
        'attachment_url': message.attachment.url if message.attachment else None,
        'attachment_name': getattr(message.attachment, 'name', None),
        'is_read': message.is_read,
        'status': message.status,
    }
