

from django.core.cache import cache
from django.template import Template
from django.template.context import RequestContext

from snapboard.utils import get_request_cache_key

class CachedTemplateMiddleware(object):
    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method != 'GET':
            return
        
        #import pdb;pdb.set_trace()
        
        cache_key = get_request_cache_key(request)
        response = cache.get(cache_key, None)
        if response is None:
            response = view_func(request, *view_args, **view_kwargs)

        if response['content-type'].startswith('text/html'):
            t = Template(response.content)
            response.content = t.render(RequestContext(request))

        return response