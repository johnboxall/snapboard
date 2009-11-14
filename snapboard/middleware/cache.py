from django.conf import settings
from django.core.cache import cache
from django.template import Template
from django.template.context import RequestContext

from snapboard.utils import get_response_cache_key, get_prefix_cache_key


class CachedTemplateMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != 'GET':
            return

        # TODO: In DEV don't try to grab media out of the cache.
        if settings.DEBUG and "." in request.path:
            return
        
        prefix_key = get_prefix_cache_key(request)
        prefix = cache.get(prefix_key, "0")
        
        response_key = get_response_cache_key(prefix, request)
        response = cache.get(response_key)
        
        if response is None:
            response = view_func(request, *view_args, **view_kwargs)
        
        if response['content-type'].startswith('text/html'):
            t = Template(response.content)
            response.content = t.render(RequestContext(request))
        
        return response