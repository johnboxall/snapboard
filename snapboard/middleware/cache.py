from django.conf import settings
from django.core.cache import cache
from django.template import Template
from django.template.context import RequestContext

from snapboard.utils import get_response_cache_key, get_prefix_cache_key


class CachedTemplateMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        # TODO: In DEV don't try to grab media out of the cache.
        if settings.DEBUG and "." in request.path:
            return
        
        response = None
        if request.method == "GET":
            prefix_key = get_prefix_cache_key(request)
            prefix = cache.get(prefix_key, "0")
            
            response_key = get_response_cache_key(prefix, request)
            response = cache.get(response_key)
        
        if response is None:
            response = view_func(request, *view_args, **view_kwargs)
        
        if response['content-type'].startswith('text/html'):
            t = Template(response.content)
            response.content = t.render(RequestContext(request))
        
        # TODO: This problem has to do with a conflict between this caching
        #       and the built in cache middleware.
        # TODO: Safari is caching pages for too long!
        #       These headers help it forget ...
        response['Cache-Control'] = "private"    
        response['Expires'] = "Thu, 1 Jan 70 00:00:00 GMT"
        return response