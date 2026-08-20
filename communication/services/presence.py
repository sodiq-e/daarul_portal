from __future__ import annotations

import time

from django.core.cache import cache

PRESENCE_TIMEOUT_SECONDS = 5


def get_presence_state_for_thread(thread, viewer):
    participant = thread.get_other_participant(viewer)

    now = int(time.time())
    online = False
    last_seen_at = None

    if participant:
        last_seen_at = cache.get(f'portal_presence:{thread.id}:{participant.id}')
        if last_seen_at is not None:
            online = (now - int(last_seen_at)) <= PRESENCE_TIMEOUT_SECONDS

    return {
        'participant': {
            'user_id': participant.id if participant else None,
            'is_online': online,
            'last_seen_at': last_seen_at,
            'updated_at': now,
        },
        'user_id': participant.id if participant else None,
        'is_online': online,
        'last_seen_at': last_seen_at,
        'updated_at': now,
    }
