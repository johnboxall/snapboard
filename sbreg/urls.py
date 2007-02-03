from django.conf.urls.defaults import *

from views import register, confirm

urlpatterns = patterns('',
    (r'^register/$', register),
    (r'^confirm/(?P<activation_key>[^/]+)/$', confirm),
)
