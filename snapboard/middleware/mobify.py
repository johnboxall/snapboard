from django.contrib.sessions.middleware import SessionMiddleware

def fix_cookie(request):
    """Reset request.COOKIES using FixedCookie."""
    from bloom.http.fixedcookie import FixedCookie
    
    try:
        c = FixedCookie(request.META.get("HTTP_COOKIE", ""))
    except: # CookieError - should never happen.
        c = FixedCookie()
    
    for k in c.keys():
        request.COOKIES[k] = c.get(k).value
    request._fixedcookie = c

class MobifySessionMiddleware(SessionMiddleware):
    def process_request(self, request):
        fix_cookie(request)
        super(MobifySessionMiddleware, self).process_request(request)
    