from time import mktime

from django import template
from django.conf import settings

from snapboard.templatetags.textile import textile
from snapboard.templatetags import markdown
from snapboard.templatetags import bbcode

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
        safe_mode = False
    elif len(extensions) > 0 and extensions[0] == "safe":
        extensions = extensions[1:]
        safe_mode = True
    else:
        safe_mode = False

    return markdown.markdown(value, extensions, safe_mode=safe_mode)
register.filter('markdown', markdown_filter)

def bbcode_filter(value, arg=''):
    return bbcode.bb2xhtml(value, True)
register.filter('bbcode', bbcode_filter)

snap_filter = getattr(settings, 'SNAP_POST_FILTER', 'markdown').lower()
if snap_filter == 'bbcode':
    render_filter = bbcode_filter
elif snap_filter == 'textile':
    render_filter = lambda text, arg: textile(text)
else:
    render_filter = markdown_filter
register.filter('render_post', render_filter)

def timestamp(dt):
    """
    Returns a timestamp usable by JavaScript from a datetime.
    """
    try:
        return str(int(1000*mktime(dt.timetuple())))
    except:
        return u''
register.filter('timestamp', timestamp)

# vim: ai ts=4 sts=4 et sw=4
