from django.conf import settings
from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson
from django.core.cache import cache

import urllib


from snapboard.models import UserSettings


# __all__ = [
#     "RequestForm", "get_user_settings", "sanitize", 
#     "toggle_boolean_field", "JSONResponse", "safe_int", "json_response",
#     "DEFAULT_USER_SETTINGS"
# ]


class RequestFormMixin(object):
    def __init__(self, data=None, files=None, request=None, *args, **kwargs):
        super(RequestFormMixin, self).__init__(data=data, files=files, *args, **kwargs)
        self.request = request
    
class RequestForm(RequestFormMixin, forms.Form):
    pass
    
class RequestModelForm(RequestFormMixin, forms.ModelForm):
    pass  

def render(template_name, context, request):
    return render_to_response(template_name, context, 
                              context_instance=RequestContext(request))
                              
def render_and_cache(template_name, context, request, prefix="", timeout=None):
    response = render(template_name, context, request)
    cache_key = get_request_cache_key(request)
    cache.set(cache_key, response, timeout)
    return response


def get_request_cache_key(request):
    # NEEED TO THINK ABOUT THIS A LITTLE HARDER FOR POST PAGES.
    return urllib.quote(request.path)
    


def renders(template_name, context):
    return render_to_string(template_name, context)


DEFAULT_USER_SETTINGS  = UserSettings()

def get_user_settings(request):
    if hasattr(request, "user"):
        if hasattr(request, "_sb_settings_cache"):
            return request._sb_settings_cache
    
    user = getattr(request, "user", request)
    
    if not user.is_authenticated():
        user_settings = DEFAULT_USER_SETTINGS
    else:
        try:
            user_settings = user.sb_usersettings
        except UserSettings.DoesNotExist:
            user_settings = DEFAULT_USER_SETTINGS
    
    if hasattr(request, "user"):
        request._sb_settings_cache = user_settings
    return user_settings


def sanitize(s):
    import markdown
    return markdown.markdown(s, safe_mode=True)

def toggle_boolean_field(obj, field):
    # Toggles and returns a boolean field of a model instance.
    setattr(obj, field, (not getattr(obj, field)))
    obj.save()
    return getattr(obj, field)

def JSONResponse(obj):
    return HttpResponse(simplejson.dumps(obj), mimetype='application/javascript')


def safe_int(s, default=None):
    try:
        return int(s)
    except ValueError:
        return default

def json_response(view):
    def wrapper(*args, **kwargs):
        return JSONResponse(view(*args, **kwargs))
    return wrapper

def send_mail(subject, message, from_email, recipient_list,
              fail_silently=False, auth_user=None, auth_password=None,
              connection=None, bcc=None):
    from django.core.mail import SMTPConnection, EmailMessage
    # Send mail w/ bcc
    #import pdb;pdb.set_trace()
    pass
    #connection = SMTPConnection(username=auth_user, password=auth_password,
    #                            fail_silently=fail_silently)
    #return EmailMessage(subject, message, from_email, recipient_list, bcc, 
    #    connection).send()

