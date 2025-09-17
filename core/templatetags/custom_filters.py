# templatetags/custom_filters.py
from django import template
register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows dict[key] lookup in templates."""
    if dictionary is None:
        return None
    return dictionary.get(key)
