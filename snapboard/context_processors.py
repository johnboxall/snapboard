from django.conf import settings

from snapboard.models import SNAP_MEDIA_PREFIX, SNAP_POST_FILTER


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
    }