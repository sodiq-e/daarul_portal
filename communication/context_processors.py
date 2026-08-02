from communication.views import get_user_threads


def portal_messages_context(request):
    """
    Context processor that adds portal messages info to all templates.
    """
    if not request.user.is_authenticated:
        return {'portal_unread_count': 0}

    try:
        threads = get_user_threads(request.user)
        unread_count = sum(
            thread.messages.exclude(sender=request.user).filter(is_read=False).count()
            for thread in threads
        )
    except Exception:
        unread_count = 0

    return {
        'portal_unread_count': unread_count,
    }