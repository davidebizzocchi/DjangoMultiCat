from django import template
from decouple import config

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
