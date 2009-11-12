# TODO: this whole file is old now.
from django.conf import settings

from snapboard.models import SNAP_MEDIA_PREFIX, SNAP_POST_FILTER
from snapboard.utils import get_user_settings

def snapboard_default_context(request):
    """
    Provides some default information for all templates.

    This should be added tothesettingsvariableTEMPLATE_CONTEXT_PROCESSORS
    """
    return {
        'SNAP_MEDIA_PREFIX':SNAP_MEDIA_PREFIX,
        'SNAP_POST_FILTER': SNAP_POST_FILTER,
        'LOGIN_URL': settings.LOGIN_URL,
        'LOGOUT_URL': settings.LOGOUT_URL,
        'ADMIN_ROOT': getattr(settings, "ADMIN_ROOT", "/admin/"),
        #'user_settings':get_user_settings(request)
    }
    
    
#     
#     
# DROP TABLE snapboard_abusereport; 
# DROP TABLE snapboard_category ;
# DROP TABLE snapboard_group ;
# DROP TABLE snapboard_group_admins ;
# DROP TABLE snapboard_group_users ;
# DROP TABLE snapboard_invitation ;
# DROP TABLE snapboard_ipban ;
# DROP TABLE snapboard_moderator ;
# DROP TABLE snapboard_post ;
# DROP TABLE snapboard_post_private ;
# DROP TABLE snapboard_thread ;
# DROP TABLE snapboard_userban ;
# DROP TABLE snapboard_usersettings ;
# DROP TABLE snapboard_usersettings_frontpage_filters ;
# DROP TABLE snapboard_watchlist;