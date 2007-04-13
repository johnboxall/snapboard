from django import template
from django.contrib.auth.models import User

from textile import textile

import markdown

register = template.Library()


register.filter('textile', textile)


def post_summary(value, arg):
    """
    Returns the first N characters of a block of text where N is the only argument.
    """
    l = int(arg)
    if len(value) > arg:
        return value
    else:
        return value[:l] + '...'
register.filter('post_summary', post_summary)


def markdown_filter(value, arg=''):
    extensions=arg.split(",")
    if len(extensions) == 1 and extensions[0] == '':
        # if we don't do this, no arguments will generate critical warnings
        # in markdown
        extensions = []
    elif len(extensions) > 0 and extensions[0] == "safe":
        extensions = extensions[1:]
        safe_mode = True
    else:
        safe_mode = False

    return markdown.markdown(value, extensions, safe_mode=safe_mode)
register.filter('markdown', markdown_filter)

# vim: ai ts=4 sts=4 et sw=4
