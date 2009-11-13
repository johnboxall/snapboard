from django.conf import settings
from snapboard.models import MEDIA_PREFIX, POSTS_PER_PAGE, THREADS_PER_PAGE


def snapboard_default_context(request):
    return {
        'SB_MEDIA_PREFIX': MEDIA_PREFIX,
        'SB_POSTS_PER_PAGE': POSTS_PER_PAGE,
        'SB_THREADS_PER_PAGE': THREADS_PER_PAGE
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