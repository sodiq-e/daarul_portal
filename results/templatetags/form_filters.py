from django import template

register = template.Library()


@register.filter(name='get_field')
def get_field(form, field_name):
    """
    Get a specific field from a form.
    Usage: {{ form|get_field:field_name }}
    Returns: The field with proper HTML rendering
    """
    if hasattr(form, 'fields') and field_name in form.fields:
        field = form[field_name]
        # Return the widget HTML with proper classes
        widget_html = str(field)
        return widget_html
    return ""


@register.filter(name='add_class')
def add_class(field, css_class):
    """
    Add CSS class to form field.
    Usage: {{ form|get_field:field_name|add_class:"my-class" }}
    """
    return field.as_widget(attrs={"class": css_class})


@register.filter(name='dict_lookup')
def dict_lookup(dictionary, key):
    """
    Lookup a key in a dictionary (form field).
    Usage: {{ form|dict_lookup:key_name }}
    """
    if isinstance(dictionary, dict):
        return dictionary.get(key, "")
    return ""
