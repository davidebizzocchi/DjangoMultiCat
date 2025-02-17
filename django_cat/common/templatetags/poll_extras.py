from django import template
from decouple import config
from app.pre_utils import get_version_from_file
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