from django.conf import settings

from snapboard.models import MEDIA_PREFIX, POSTS_PER_PAGE, THREADS_PER_PAGE


def snapboard_default_context(request):
    return {
        'SB_MEDIA_PREFIX': MEDIA_PREFIX,
        'SB_POSTS_PER_PAGE': POSTS_PER_PAGE,
        'SB_THREADS_PER_PAGE': THREADS_PER_PAGE,
    }