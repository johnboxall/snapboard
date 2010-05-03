# -*- coding: utf-8 -*-
from django import template
from django.conf import settings

from snapboard.models import Post


LATEST_POSTS = getattr(settings, "SB_LATEST_POSTS", 6)

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
	return text[:last_space] + u'…'

@register.filter
def markdown(value, arg=''):
    import markdown
    return markdown.markdown(value, safe_mode=False)

@register.filter
def dateisoformat(dt):
    return hasattr(dt, "isoformat") and dt.isoformat() or ""


class GetLatestPosts(template.Node):
    def __init__(self, limit):
        self.limit = int(limit)
    
    def render(self, context):
        context["latest_posts"] = Post.objects.order_by("-date")[0:self.limit]
        return ""

@register.tag
def get_latest_posts(parser, token, node_cls=GetLatestPosts):
    """
    Returns a list of the latest posts.
    
    usage:
        {% get_latest_posts %}
    
    """
    token = token.split_contents()[-1]
    limit = token.isdigit() and token or LATEST_POSTS
    return node_cls(limit)


class GetUniqueLatestPosts(GetLatestPosts):
    def render(self, context):
        # TODO: There has got to be an easier way.
        #       - don't show two posts from the same thread
        #       - don't show two posts from the same user        
        seen = set()
        latest = []
        for post in Post.objects.order_by("-date")[self.limit*2].iterator():
            uid = "u%i" % post.user_id
            tid = "t%i" % post.thread_id
            if uid in seen or tid in seen:
                continue
            seen.update([uid, tid])
            latest.append(post)
            if len(latest) > self.limit:
                break
        
        context["latest_posts"] = latest
        return ""

@register.tag
def get_unique_latest_posts(parser, token):
    return get_latest_posts(parser, token, node_cls=GetUniqueLatestPosts)



# Copyright 2009, EveryBlock
# This code is released under the GPL.
@register.tag
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