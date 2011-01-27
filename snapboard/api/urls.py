from django.conf.urls.defaults import *

from piston.resource import Resource

from snapboard.api.handlers import ThreadHandler
from snapboard.api.auth import StaffHttpBasicAuthentication


auth = StaffHttpBasicAuthentication(realm="Snapboard")
thread = Resource(ThreadHandler, authentication=auth)

urlpatterns = patterns('',
   (r'^thread/$', thread),
)