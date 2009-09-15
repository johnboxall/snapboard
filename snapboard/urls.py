from django.conf.urls.defaults import *
from django.contrib.auth.models import User

from snapboard.feeds import LatestPosts
from snapboard.rpc import rpc_post, rpc_lookup, rpc_preview
from snapboard.views import *

feeds = {'latest': LatestPosts}

js_info_dict = {
    'packages': ('snapboard',),
}

urlpatterns = patterns('',
    (r'^$', thread_index, {}, 'snapboard_index'),

    (r'^post/(?P<post_id>\d+)/$', locate_post, {}, 'snapboard_locate_post'),



    (r'^private/$', private_index, {}, 'snapboard_private_index'),
    (r'^categories/$', category_index, {}, 'snapboard_category_index'),
    (r'^favorites/$', favorite_index, {}, 'snapboard_favorite_index'),
    (r'^edit_post/(?P<original>\d+)/$', edit_post, {}, 'snapboard_edit_post'),

    (r'^(?P<cslug>[-_\w]+)/(?P<tslug>[-_\w]+)/$', thread, {}, 'snapboard_thread'),
    (r'^(?P<slug>[-_\w]+)/new/$', new_thread, {}, 'snapboard_new_thread'),
    (r'^(?P<slug>[-_\w]+)/$', category_thread_index, {}, 'snapboard_category_thread_index'),



    (r'^settings/$', edit_settings, {}, 'snapboard_edit_settings'),

    # Groups
    (r'^groups/(?P<group_id>\d+)/manage/$', manage_group, {}, 'snapboard_manage_group'),
    (r'^groups/(?P<group_id>\d+)/invite/$', invite_user_to_group, {}, 'snapboard_invite_user_to_group'),
    (r'^groups/(?P<group_id>\d+)/remuser/$', remove_user_from_group, {}, 'snapboard_remove_user_from_group'),
    (r'^groups/(?P<group_id>\d+)/grant_admin/$', grant_group_admin_rights, {}, 'snapboard_grant_group_admin_rights'),

    # Invitations
    (r'invitations/(?P<invitation_id>\d+)/discard/$', discard_invitation, {}, 'snapboard_discard_invitation'),
    (r'invitations/(?P<invitation_id>\d+)/answer/$', answer_invitation, {}, 'snapboard_answer_invitation'),

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
