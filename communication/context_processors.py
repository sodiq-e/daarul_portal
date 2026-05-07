from communication.models import PortalMessage


def portal_messages_context(request):
    """
    Context processor that adds portal messages info to all templates.
    """
    if request.user.is_authenticated:
        try:
            thread = request.user.portal_thread
            unread_count = thread.messages.exclude(sender=request.user).filter(is_read=False).count()
        except:
            unread_count = 0
    else:
        unread_count = 0

    return {
        'portal_unread_count': unread_count,
    }