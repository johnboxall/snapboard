from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r"", include("snapboard.urls")),
    # TODO: Templates have a dependance on named login/logout urls.
    (r'^login/$', 'django.contrib.auth.views.login', '', 'login'),
    (r'^logout/$', 'django.contrib.auth.views.logout', '', 'logout'),
)