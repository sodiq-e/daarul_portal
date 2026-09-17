from __future__ import annotations

from typing import Iterable, List, Optional

from django.contrib.auth.models import User

from communication.models import PortalThread
from settingsapp.tenant_utils import get_current_tenant


def normalize_users(users: Iterable[Optional[User]]) -> List[User]:
    """Return deduplicated users while preserving encounter order."""
    normalized: List[User] = []
    seen_ids = set()
    for user in users:
        if user is None or user.id in seen_ids:
            continue
        seen_ids.add(user.id)
        normalized.append(user)
    return normalized


def get_or_create_user_thread(user: User) -> PortalThread:
    """Create or retrieve a personal thread for a single user."""
    thread, created = PortalThread.objects.personal().get_or_create(
        user=user,
        defaults={
            'thread_type': PortalThread.THREAD_TYPE_PERSONAL,
            'tenant': get_current_tenant(),
        }
    )
    if not thread.participants.filter(pk=user.pk).exists():
        thread.participants.add(user)
    return thread


def get_or_create_thread_for_users(
    users,
    thread_type=PortalThread.THREAD_TYPE_GROUP,
    name=None,
):
    users = normalize_users(users)
    if len(users) < 2:
        raise ValueError('At least two participants are required for this thread type.')

    before = PortalThread.objects.filter(thread_type=thread_type).prefetch_related('participants')
    request_ids = {u.id for u in users}
    thread = None
    for candidate in before.distinct():
        candidate_ids = set(candidate.participants.values_list('id', flat=True))
        if candidate.user_id is not None:
            candidate_ids.add(candidate.user_id)
        if candidate_ids == request_ids:
            thread = candidate
            break

    if thread is None:
        thread = PortalThread.objects.create(
            thread_type=thread_type,
            name=name or '',
            tenant=get_current_tenant(),
        )
        thread.participants.set(users)
        if thread_type != PortalThread.THREAD_TYPE_PERSONAL and users and not thread.participants.filter(pk=users[0].pk).exists():
            thread.participants.add(users[0])
    else:
        if name and not thread.name:
            thread.name = name
            thread.save(update_fields=['name'])

    return thread


def get_or_create_personal_thread_for_users(users, name=None):
    users = normalize_users(users)
    if len(users) != 2:
        raise ValueError('Personal threads must have exactly two participants.')
    return get_or_create_thread_for_users(users, thread_type=PortalThread.THREAD_TYPE_PERSONAL, name=name)


def get_or_create_group_thread_for_users(users, name=None):
    users = normalize_users(users)
    if not name:
        raise ValueError('Group threads must have a name.')
    return get_or_create_thread_for_users(users, thread_type=PortalThread.THREAD_TYPE_GROUP, name=name)


def get_or_create_class_thread_for_users(users, name):
    users = normalize_users(users)
    if not name:
        raise ValueError('Class threads must have a name.')
    return get_or_create_thread_for_users(users, thread_type=PortalThread.THREAD_TYPE_CLASS, name=name)
