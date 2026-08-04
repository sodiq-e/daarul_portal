from django import template

register = template.Library()

@register.simple_tag
def thread_display_title(thread, current_user, default_label='Conversation'):
    if not thread or isinstance(thread, str):
        return default_label

    title = getattr(thread, 'get_display_title', None)
    if callable(title):
        return title(current_user=current_user, default_label=default_label)

    if getattr(thread, 'name', None):
        return thread.name

    participants = getattr(thread, 'participants', None)
    if participants is None:
        return default_label

    other_participants = participants.exclude(pk=current_user.pk)
    first_participant = other_participants.first()
    if first_participant:
        return first_participant.get_full_name() or first_participant.username

    return default_label
