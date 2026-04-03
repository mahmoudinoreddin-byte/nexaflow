from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """{{ my_dict|get_item:key }}"""
    return dictionary.get(key)

@register.filter
def in_dict(dictionary, key):
    """{% if key|in_dict:my_dict %}"""
    return key in dictionary
