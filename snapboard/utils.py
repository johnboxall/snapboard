import time
import urllib

from django.conf import settings
from django.core.cache import cache
from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string


# Forms ########################################################################

class RequestFormMixin(object):
    def __init__(self, data=None, files=None, request=None, *args, **kwargs):
        super(RequestFormMixin, self).__init__(data=data, files=files, *args, **kwargs)
        self.request = request
    
class RequestForm(RequestFormMixin, forms.Form):
    pass
    
class RequestModelForm(RequestFormMixin, forms.ModelForm):
    pass  

# Models  ######################################################################

def toggle_boolean_field(obj, field):
    # Toggles and returns a boolean field of a model instance.
    setattr(obj, field, (not getattr(obj, field)))
    obj.save()
    return getattr(obj, field)


# Rendering ####################################################################

def render(template_name, context, request):
    return render_to_response(template_name, context, 
                              context_instance=RequestContext(request))

def renders(template_name, context):
    return render_to_string(template_name, context)

def JSONResponse(o):
    from snapboard.json import dumps
    return HttpResponse(dumps(o), mimetype='application/javascript')

def json_response(view):
    def wrapper(*args, **kwargs):
        return JSONResponse(view(*args, **kwargs))
    return wrapper

def sanitize(s):
    import markdown
    return markdown.markdown(s, safe_mode=True)


# Caching ######################################################################

def render_and_cache(template_name, context, request, prefix="", timeout=None):
    response = render(template_name, context, request)
    if request.method == "POST":
        return response
    
    prefix_key = get_prefix_cache_key(request)
    prefix = cache.get(prefix_key)
    if prefix is None:
        
        prefix = int(time.time())
        cache.set(prefix_key, prefix)
    
    response_key = get_response_cache_key(prefix, request)
    cache.set(response_key, response, timeout)
    
    return response

# TODO: Document
#       Last updated doesn't have to take into account ?page
#       update.<path> --- cached timestamp
#       <timestamp>.<path> --- cached template
def get_response_cache_key(prefix, request):
    return "%s.%s" % (prefix, urllib.quote(request.get_full_path()))

def get_prefix_cache_key(request):
    return "updated.%s" % getattr(request, "path", request)


# Mail #########################################################################

def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, bcc=None):
    from django.core.mail import SMTPConnection, EmailMessage
    # Send mail w/ bcc
    connection = SMTPConnection(username=auth_user, password=auth_password,
                               fail_silently=fail_silently)
    return EmailMessage(subject, message, from_email, recipient_list, bcc, 
       connection).send()

       
# Helpers ######################################################################

def safe_int(s, default=None):
    try:
        return int(s)
    except ValueError:
        return default

