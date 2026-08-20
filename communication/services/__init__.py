"""Communication services for thread, message, status, and presence behavior."""

from .messages import create_portal_message, serialize_message_for_json
from .threads import (
    get_or_create_thread_for_users,
    get_or_create_personal_thread_for_users,
    get_or_create_group_thread_for_users,
    get_or_create_class_thread_for_users,
    get_or_create_user_thread,
)
from .statuses import mark_thread_messages_as_delivered, mark_thread_messages_as_read
from .presence import get_presence_state_for_thread

__all__ = [
    'create_portal_message',
    'serialize_message_for_json',
    'get_or_create_thread_for_users',
    'get_or_create_personal_thread_for_users',
    'get_or_create_group_thread_for_users',
    'get_or_create_class_thread_for_users',
    'get_or_create_user_thread',
    'mark_thread_messages_as_delivered',
    'mark_thread_messages_as_read',
    'get_presence_state_for_thread',
]
