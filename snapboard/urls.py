from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from snapboard.feeds import LatestPosts

feeds = {
    'latest': LatestPosts
}

js_info_dict = {
    'packages': ('snapboard',),
}

urlpatterns = patterns('',
    # Feeds
    (r'^feeds/(?P<url>.*)/$', 'django.contrib.syndication.views.feed', {'feed_dict': feeds}, 'snapboard_feeds'),

    # JavaScript
    (r'^jsi18n/$', 'django.views.i18n.null_javascript_catalog', js_info_dict, 'snapboard_js_i18n'),
)

lookup_dict = {
    'queryset':User.objects.all(),
    'field':'username',
}

urlpatterns += patterns('snapboard.views',
    # Forum
    (r'^$', 'category_index', {}, 'snapboard_category_index'),
    (r'^threads/$', 'thread_index', {}, 'snapboard_index'),
    (r'^post/(?P<post_id>\d+)/$', 'locate_post', {}, 'snapboard_locate_post'),
    (r'^edit_post/(?P<post_id>\d+)/$', 'edit_post', {}, 'snapboard_edit_post'),
    (r'^private/$', 'private_index', {}, 'snapboard_private_index'),
    (r'^favorites/$', 'favorite_index', {}, 'snapboard_favorite_index'),
    (r'^settings/$', 'edit_settings', {}, 'snapboard_edit_settings'),

    # Groups
    (r'^groups/(?P<group_id>\d+)/manage/$', 'manage_group', {}, 'snapboard_manage_group'),
    (r'^groups/(?P<group_id>\d+)/invite/$', 'invite_user_to_group', {}, 'snapboard_invite_user_to_group'),
    (r'^groups/(?P<group_id>\d+)/remuser/$', 'remove_user_from_group', {}, 'snapboard_remove_user_from_group'),
    (r'^groups/(?P<group_id>\d+)/grant_admin/$', 'grant_group_admin_rights', {}, 'snapboard_grant_group_admin_rights'),

    # Invitations
    (r'invitations/(?P<invitation_id>\d+)/discard/$', 'discard_invitation', {}, 'snapboard_discard_invitation'),
    (r'invitations/(?P<invitation_id>\d+)/answer/$', 'answer_invitation', {}, 'snapboard_answer_invitation'),

    # RPC
    (r'^rpc/post_revision/$', 'post_revision', {}, 'snapboard_post_revision'),
    (r'^rpc/text_preview/$', 'text_preview', {}, 'snapboard_text_preview'),
    (r'^rpc/lookup/$', 'lookup', lookup_dict, 'snapboard_user_lookup'),
    (r'^rpc/category_sticky_thread/$', 'category_sticky_thread', {}, 'snapboard_category_sticky_thread'),
    (r'^rpc/global_sticky_thread/$', 'global_sticky_thread', {}, 'snapboard_global_sticky_thread'),
    (r'^rpc/close_thread/$', 'close_thread', {}, 'snapboard_close_thread'),
    (r'^rpc/watch_thread/$', 'watch_thread', {}, 'snapboard_watch_thread'),
    (r'^rpc/censor_post/$', 'censor_post', {}, 'snapboard_censor_post'),
    (r'^rpc/report_post/$', 'report_post', {}, 'snapboard_report_post'),
    (r'^rpc/quote_post/$', 'quote_post', {}, 'snapboard_quote_post'),

    # Forum
    (r'^(?P<slug>[-_\w]+)/new/$', 'new_thread', {}, 'snapboard_new_thread'),
    (r'^(?P<cslug>[-_\w]+)/(?P<tslug>[-_\w]+)/$', 'thread', {}, 'snapboard_thread'),
    (r'^(?P<slug>[-_\w]+)/$', 'category_thread_index', {}, 'snapboard_category_thread_index'),
)