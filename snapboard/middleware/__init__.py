from django.conf import settings
from django.shortcuts import render_to_response

class BanMiddleware(object):
    """
    Bans based on IP's or users

    This middleware attempts to grab SNAP_BANNED_IPS and SNAP_BANNED_USERS
    from the settings module.  Said variables are created/updated on
    initialization of the snapboard application (__init__.py) and
    post_save/post_update/post_delete of either model BannedIP or BannedUser.
    """
    def process_request(self, request):
        ip = request.META.get('REMOTE_ADDR', None)
        u = request.user

        banned_ips = getattr(settings, 'SNAP_BANNED_IPS', [])
        banned_users = getattr(settings, 'SNAP_BANNED_USERS', [])

        if ip in banned_ips or u in banned_users:
            # show a banned page
            return render_to_response('snapboard/banned.html')

# vim: ai ts=4 sts=4 et sw=4
