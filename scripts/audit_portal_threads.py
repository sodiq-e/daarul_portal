import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'daarul_portal.settings')
import django
django.setup()
from communication.models import PortalThread
from django.db.models import Count

qs = PortalThread.objects.annotate(num_participants=Count('participants')).filter(user__isnull=False, num_participants__gt=1)
print('Found', qs.count(), 'threads with user set and multiple participants')
for t in qs:
    parts = list(t.participants.all())
    print('Thread id=', t.id, 'name=', repr(t.name), 'user_id=', getattr(t.user, 'id', None), 'num_participants=', len(parts), 'participants=', [p.id for p in parts], 'messages=', t.messages.count())
