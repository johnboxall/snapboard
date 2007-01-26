from django import template

register = template.Library()

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
