from django.conf.urls.defaults import *

from views import register, confirm, signin, signout

urlpatterns = patterns('',
    (r'^register/$', register),
    (r'^confirm/(?P<activation_key>[^/]+)/$', confirm),
    (r'^login/$', signin),
    (r'^logout/$', signout),
)
