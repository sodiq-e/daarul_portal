from django.db.models import Q
from communication.models import PortalThread


def portal_messages_context(request):
    """
    Context processor that adds portal messages info to all templates.
    """
    if request.user.is_authenticated:
        try:
            threads = PortalThread.objects.filter(
                Q(participants=request.user) | Q(user=request.user)
            ).distinct()
            unread_count = sum(
                thread.messages.exclude(sender=request.user).filter(is_read=False).count()
                for thread in threads
            )
        except Exception:
            unread_count = 0
    else:
        unread_count = 0

    return {
        'portal_unread_count': unread_count,
    }