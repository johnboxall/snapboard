from django.conf.urls.defaults import *

from views import thread, thread_index, new_thread, category_index, edit_post, rpc

urlpatterns = patterns('',
    (r'^$', thread_index),
    (r'^newtopic/$', new_thread),
    (r'^threads/$', thread_index),
    (r'^categories/$', category_index),
    (r'^edit_post/(?P<original>\d+)/$', edit_post),
    (r'^threads/id/(?P<thread_id>\d+)/$', thread),
    (r'^threads/id/(?P<thread_id>\d+)/page(?P<page>\d+)/$', thread),
    (r'^threads/category/(?P<cat_id>\d+)/$', thread_index),

    (r'^rpc/action/$', rpc),
)
