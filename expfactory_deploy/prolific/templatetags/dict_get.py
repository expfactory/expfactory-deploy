from django import template

register = template.Library()


@register.filter(name="dict_get")
def dict_get(value, arg):
    return value.get(arg, None)
