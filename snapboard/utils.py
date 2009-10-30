from django.conf import settings
from django import forms
from django.http import HttpResponse, HttpRequest
from django.shortcuts import render_to_response
from django.template.defaultfilters import striptags
from django.template import RequestContext
from django.template.loader import render_to_string
from django.utils import simplejson

from snapboard.templatetags.snapboard_tags import render_filter
from snapboard.models import UserSettings

# USE_SNAPBOARD_LOGIN_FORM, USE_SNAPBOARD_SIGNIN should probably be removed
USE_SNAPBOARD_SIGNIN = getattr(settings, 'USE_SNAPBOARD_SIGNIN', False)
USE_SNAPBOARD_LOGIN_FORM = getattr(settings, 'USE_SNAPBOARD_LOGIN_FORM', False)


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


def sanitize(text):
    return render_filter(striptags(text), "safe")

def toggle_boolean_field(obj, field):
    '''
    Switches the a boolean value and returns the new value.
    object should be a Django Model
    '''
    setattr(obj, field, (not getattr(obj, field)))
    obj.save()
    return getattr(obj, field)
    
def JsonResponse(obj):
    return HttpResponse(simplejson.dumps(obj), mimetype='application/javascript')
