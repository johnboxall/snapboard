from django.conf import settings

from snapboard.models import SNAP_MEDIA_PREFIX, SNAP_POST_FILTER
from snapboard.utils import get_user_settings

def snapboard_default_context(request):
    """
    Provides some default information for all templates.

    This should be added to the settings variable TEMPLATE_CONTEXT_PROCESSORS
    """
    return {
        'SNAP_MEDIA_PREFIX': SNAP_MEDIA_PREFIX,
        'SNAP_POST_FILTER': SNAP_POST_FILTER,
        'LOGIN_URL': settings.LOGIN_URL,
        'LOGOUT_URL': settings.LOGOUT_URL,
        'ADMIN_ROOT': getattr(settings, "ADMIN_ROOT", "/admin/"),
        'user_settings': get_user_settings(request.user)
    }