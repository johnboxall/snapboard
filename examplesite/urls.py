from django.conf.urls.defaults import *
from django.conf import settings
from django.contrib import admin
from django.contrib.auth import views as auth_views

admin.autodiscover()

urlpatterns = patterns('',
    # Example:
    (r'^snapboard/', include('snapboard.urls')),
    (r'^accounts/login/$', auth_views.login, {'template_name': 'snapboard/signin.html'}, 'auth_login'),
    (r'^accounts/logout/$', auth_views.logout, {'template_name': 'snapboard/signout.html'}, 'auth_logout'),

    # Uncomment this for admin:
    (r'^admin/(.*)', admin.site.root),
)

if settings.DEBUG:
    urlpatterns += patterns('',
        (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    )
