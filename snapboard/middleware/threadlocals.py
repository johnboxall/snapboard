# http://code.djangoproject.com/wiki/CookBookThreadlocalsAndUser

try:
    from threading import local
except ImportError:
    from django.utils._threading_local import local


_thread_locals = local()

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_ip():
    return getattr(_thread_locals, 'ip', None)

class ThreadLocals(object):
    """Middleware that gets various objects from the
    request object and saves them in thread local storage."""
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        _thread_locals.ip = request.META.get('REMOTE_ADDR', None)
# vim: ai ts=4 sts=4 et sw=4
