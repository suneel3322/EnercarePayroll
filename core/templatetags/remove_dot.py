from django import template

register = template.Library()

@register.filter
def remove_dot(value):
    return value.replace('.',' ').title()
