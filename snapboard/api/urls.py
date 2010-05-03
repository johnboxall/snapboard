from django.conf.urls.defaults import *

from piston.resource import Resource

from snapboard.api.handlers import ThreadHandler
from snapboard.api.auth import StaffHttpBasicAuthentication


auth = StaffHttpBasicAuthentication(realm="Snapboard")
thread_handler = Resource(ThreadHandler, authentication=auth)


urlpatterns = patterns('',
   (r'^thread/$', thread_handler),
)
# 
# 
# 
# 
# 
# from django.conf.urls.defaults import *
# from piston.resource import Resource
# 
# from piston.doc import documentation_view
# 
# from blogserver.api.handlers import BlogpostHandler
# 
# auth = HttpBasicAuthentication(realm='My sample API')
# 
# blogposts = Resource(handler=BlogpostHandler, authentication=auth)
# 
# urlpatterns = patterns('',
#     url(r'^posts/$', blogposts),
#     url(r'^posts/(?P<emitter_format>.+)/$', blogposts),
#     url(r'^posts\.(?P<emitter_format>.+)', blogposts, name='blogposts'),
# 
#     # automated documentation
#     url(r'^$', documentation_view),
# )