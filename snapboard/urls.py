from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from snapboard.feeds import LatestPosts
from snapboard.rpc import rpc_post, rpc_lookup, rpc_preview
from snapboard.views import thread, thread_index, new_thread, category_index, \
        category_thread_index, edit_post, rpc, favorite_index, private_index, \
        edit_settings

feeds = {'latest': LatestPosts}

js_info_dict = {
    'packages': ('snapboard',),
}

urlpatterns = patterns('',
    (r'^$', thread_index, {}, 'snapboard_index'),
    (r'^private/$', private_index, {}, 'snapboard_private_index'),
    (r'^newtopic/$', new_thread, {}, 'snapboard_new_thread'),
    (r'^categories/$', category_index, {}, 'snapboard_category_index'),
    (r'^favorites/$', favorite_index, {}, 'snapboard_favorite_index'),
    (r'^edit_post/(?P<original>\d+)/$', edit_post, {}, 'snapboard_edit_post'),
    (r'^threads/$', thread_index, {}, 'snapboard_thread_index'),
    (r'^threads/id/(?P<thread_id>\d+)/$', thread, {}, 'snapboard_thread'),
    (r'^threads/category/(?P<cat_id>\d+)/$', category_thread_index, {}, 'snapboard_category_thread_index'),
    (r'^settings/$', edit_settings, {}, 'snapboard_edit_settings'),

    # RPC
    (r'^rpc/action/$', rpc, {}, 'snapboard_rpc_action'),
    (r'^rpc/postrev/$', rpc_post, {}, 'snapboard_rpc_postrev'),
    (r'^rpc/preview/$', rpc_preview, {}, 'snapboard_rpc_preview'),
    (r'^rpc/user_lookup/$', rpc_lookup,
            {
                'queryset':User.objects.all(),
                'field':'username',
            }, 'snapboard_rpc_user_lookup'
        ),

    # feeds
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, 'snapboard_feeds'),

    # javascript translations
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', js_info_dict, 'snapboard_js_i18n'),
)
# vim: ai ts=4 sts=4 et sw=4
