from django import template

register = template.Library()


@register.filter(name='replace')
def replace(value, args):
    """Replace substrings in templates using syntax: value|replace:"old,new".

    Example: {{ 'hello_world'|replace:'_ , ' }} -> 'hello world'
    Args should be a single string with the old and new values separated by a comma.
    """
    try:
        old, new = [p for p in args.split(',')]
    except Exception:
        return value
    # strip optional whitespace
    old = old.strip()
    new = new.strip()
    try:
        return value.replace(old, new)
    except Exception:
        return value
