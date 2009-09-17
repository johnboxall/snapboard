from django.conf import settings
from django import forms
from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.template.defaultfilters import striptags
from django.template import RequestContext
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

def render(template_name, context, request=None):
    context_instance = RequestContext(request, processors=extra_processors)
    return render_to_response(template_name, context, 
        context_instance=context_instance)


DEFAULT_USER_SETTINGS  = UserSettings()


def get_user_settings(user):
    if not user.is_authenticated():
        return DEFAULT_USER_SETTINGS
    try:
        return user.sb_usersettings
    except UserSettings.DoesNotExist:
        return DEFAULT_USER_SETTINGS

def user_settings_context(request):
    return {'user_settings': get_user_settings(request.user)}


if USE_SNAPBOARD_LOGIN_FORM:
    def login_context(request):
        """
        All content pages that have additional content for authenticated users but
        that are also publicly viewable should have a login form in the side panel.
        """
        from snapboard.forms import LoginForm
        ctx = {}
        if not request.user.is_authenticated():
            ctx.update({'login_form': LoginForm()})
        return ctx
    extra_processors = [user_settings_context, login_context]
else:
    extra_processors = [user_settings_context]


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
