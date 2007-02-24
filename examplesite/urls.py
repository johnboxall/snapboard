from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('',
    # Example:
    (r'^snapboard/', include('examplesite.snapboard.urls')),
    (r'^snapchat/', include('examplesite.snapchat.urls')),
    (r'^accounts/', include('examplesite.sbreg.urls')),

    # Uncomment this for admin:
    (r'^admin/', include('django.contrib.admin.urls')),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
