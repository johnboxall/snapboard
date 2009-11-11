from django.conf.urls.defaults import *
from snapboard.feeds import LatestPosts

feeds = {
    'latest': LatestPosts
}

urlpatterns = patterns('',
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, 'sb_feeds'),
)

urlpatterns += patterns('snapboard.views',
    (r'^new/$', 'new_thread'),
    (r'^(?P<slug>[-_\w]+)/new/$', 'new_thread', {}, 'sb_new_thread'),



    (r'^$', 'category_list', {}, 'sb_category_list'),
    (r'^latest/$', 'thread_list', {}, 'sb_thread_list'),
    (r'^search/$', 'search', {}, 'sb_search'),

    (r'^favorites/$', 'favorites', {}, 'sb_favorites'),
    (r'^settings/$', 'edit_settings', {}, 'sb_edit_settings'),

    (r'^rpc/preview/$', 'preview', {}, 'sb_preview'),
    (r'^rpc/sticky/$', 'sticky', {}, 'sb_sticky'),
    (r'^rpc/close/$', 'close', {}, 'sb_close'),
    (r'^rpc/watch/$', 'watch', {}, 'sb_watch'),

    (r'^(?P<cslug>[-_\w]+)/(?P<tslug>[-_\w]+)/$', 'thread', {}, 'sb_thread'),
    (r'^(?P<slug>[-_\w]+)/$', 'category', {}, 'sb_category'),
)