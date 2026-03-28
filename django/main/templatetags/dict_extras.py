from django import template

register = template.Library()

@register.filter   # ✅ CORRECT
def get_item(dictionary, key):
    return dictionary.get(key, 0)