from django import template

register = template.Library()


@register.filter(name='underscore_to_space')
def underscore_to_space(value):
    """Convert underscores in a string to spaces."""
    try:
        return value.replace('_', ' ')
    except Exception:
        return value
