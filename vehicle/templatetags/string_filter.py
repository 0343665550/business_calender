from django import template

register = template.Library()

@register.filter
def replace_string(value):
    if '(' in value and ')' in value:
        return value.split('(')[0]
    return value