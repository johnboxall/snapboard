from django.conf import settings
from django.views.generic.simple import direct_to_template

from snapboard.models import is_ip_banned, IPBan, is_user_banned, UserBan

class IPBanMiddleware(object):
    """
    Bans based on IP address.

    This middleware attempts to grab SNAP_BANNED_IPS from the settings module.
    This variable holds a set of all the banned IP addresses, which is defined 
    in the database and automatically cached for efficiency.
    """

    def process_request(self, request):
        if not hasattr(settings, 'SNAP_BANNED_IPS'):
            IPBan.update_cache()
        ip_address = request.META.get('REMOTE_ADDR', None)
        if ip_address in settings.SNAP_BANNED_IPS:
            return direct_to_template(request, 'snapboard/banned_ip.html', {'reason': IPBan.objects.get(address=ip_address).reason})

class UserBanMiddleware(object):
    """
    Shows an error page to banned users and stop them from using the forum.
    """

    def process_view(self, request, view_func, view_args, view_kwargs):
        if not hasattr(settings, 'SNAP_BANNED_USERS'):
            UserBan.update_cache()
        if hasattr(view_func, '_snapboard') and request.user.is_authenticated() and is_user_banned(request.user):
            return direct_to_template(request, 'snapboard/banned_user.html', {'reason': UserBan.objects.get(user=request.user).reason})

