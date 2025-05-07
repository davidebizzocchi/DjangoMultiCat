from decouple import config
from app.pre_utils import get_version_from_file

from django import template
from django.forms.boundfield import BoundField

from icecream import ic


register = template.Library()


@register.filter
def get(dictionary, key):
    return dictionary.get(key, None)


@register.simple_tag
def messages_lifetime():
    return str(
        int(config("MESSAGE_BANNER_LIFETIME", default=5)) * 1000
    )  # In seconds (milliseconds in js)


@register.filter
def has_perm(user, perm):
    return user.has_perm(perm)

@register.simple_tag
def current_version():
    return get_version_from_file()

@register.filter(name="add_class")
def add_class(field, css_class):
    return field.as_widget(attrs={"class": css_class})

@register.filter(name="capitalize")
def capitalize(value):
    # Capitalize the first letter of a string if is not empty
    if isinstance(value, str):
        if len(value) > 0:
            return value[0].upper() + value[1:]
    return value

@register.filter(name="field_type")
def field_type(field: BoundField):
    """
    Returns the field class name of a form field.
    Usage: {{ form.field|field_type }}
    """
    return field.field.__class__.__name__
