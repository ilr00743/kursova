from django import template

register = template.Library()


@register.simple_tag
def elements_number(my_list):
    try:
        return len(my_list)
    except TypeError:
        return ''


@register.filter
def key_value(my_dict, key):
    try:
        return my_dict[key]
    except KeyError:
        return ''


@register.simple_tag
def update_variable(value):
    return value
