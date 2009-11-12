# -*- coding: utf-8 -*-
from django import template
from django.conf import settings


register = template.Library()


@register.filter
def truncate(text, chars=200):
	if len(text) < chars:
		return text
	try:
		last_space = text.rindex(' ', 0, chars)
		if last_space < chars // 5:
			raise ValueError
	except ValueError:
		return text[:chars - 1] + u'…'
	else:
		return text[:last_space] + u'…'



def markdown(value, arg=''):
    import markdown
    return markdown.markdown(value, safe_mode=True)
register.filter('markdown', markdown)

# def timestamp(dt):
#     # Returns a timestamp usable by JavaScript from a datetime.
#     try:
#         return str(int(1000*mktime(dt.timetuple())))
#     except:
#         return u''
# register.filter('timestamp', timestamp)

@register.filter
def dateisoformat(dt):
    return hasattr(dt, "isoformat") and dt.isoformat() or ""



class GetLatestPosts(template.Node):
    def __init__(self, limit):
        self.limit = limit
    
    def render(self, context):
        from snapboard.models import Post
        context["latest_posts"] = Post.objects.order_by("-date")[0:self.limit]
        return ""

@register.tag
def get_latest_posts(parser, token):
    return GetLatestPosts(5)
    
    

# Copyright 2009, EveryBlock
# This code is released under the GPL.

def raw(parser, token):
    # Whatever is between {% raw %} and {% endraw %} will be preserved as
    # raw, unrendered template code.
    text = []
    parse_until = 'endraw'
    tag_mapping = {
        template.TOKEN_TEXT: ('', ''),
        template.TOKEN_VAR: ('{{', '}}'),
        template.TOKEN_BLOCK: ('{%', '%}'),
        template.TOKEN_COMMENT: ('{#', '#}'),
    }
    # By the time this template tag is called, the template system has already
    # lexed the template into tokens. Here, we loop over the tokens until
    # {% endraw %} and parse them to TextNodes. We have to add the start and
    # end bits (e.g. "{{" for variables) because those have already been
    # stripped off in a previous part of the template-parsing process.
    while parser.tokens:
        token = parser.next_token()
        if token.token_type == template.TOKEN_BLOCK and token.contents == parse_until:
            return template.TextNode(u''.join(text))
        start, end = tag_mapping[token.token_type]
        text.append(u'%s%s%s' % (start, token.contents, end))
    parser.unclosed_block_tag(parse_until)
raw = register.tag(raw)
