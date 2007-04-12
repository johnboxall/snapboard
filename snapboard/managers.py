# vim: ai ts=4 sts=4 et sw=4

from django import newforms as forms
from django.contrib.auth import decorators
from django.contrib.auth import login, logout
from django.core.paginator import ObjectPaginator, InvalidPage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.views.generic.simple import redirect_to


#from models import Thread, Post, Category, WatchList
from models import *

class PostManager(models.Manager):
    def get_query_set(self):
        # get any avatars
        extra_post_avatar = """
            SELECT avatar FROM snapboard_snapboardprofile
                WHERE snapboard_snapboardprofile.user_id = snapboard_post.user_id
            """
        extra_abuse_count = """
            SELECT COUNT(*) FROM snapboard_abusereport
                WHERE snapboard_post.id = snapboard_abusereport.post_id
            """

        return super(PostManager, self).get_query_set().extra(
            select = {
                'avatar': extra_post_avatar,
                'abuse': extra_abuse_count,
            }).exclude(revision__isnull=False).order_by('-odate')

    def posts_for_thread(self, thread_id, user):
        uid = str(user.id)
        idstr = (uid + ',', ',' + uid + ',', ',' + uid)
        # filter out the private messages.  admin cannot see private messages
        # (although they can use the Django admin interface to do so)
        # TODO: there's gotta be a better way to filter out private messages
        # Tested with postgresql and sqlite
        qs = self.get_query_set().filter(Q(user__id__exact=user.id) |
                Q(private__exact='') |
                Q(private__endswith=idstr[2]) |
                Q(private__startswith=idstr[0]) |
                Q(private__contains=idstr[1]),
		thread__id=thread_id)

        if not getattr(user, 'is_staff', False):
            qs = qs.exclude(censor=True)

        return qs


class ThreadManager(models.Manager):
    def get_query_set(self):
        '''
        This generates a QuerySet containing Threads and additional data used
        in generating a web page with a listing of discussions.
        http://code.django.com/ qset allows the caller to specify an initial
        queryset to work with.  If this is not set, all Threads will be
        returned.
        '''
        # number of posts in thread
        # censored threads don't count toward the total
        extra_post_count = """
            SELECT COUNT(*) FROM snapboard_post
                WHERE snapboard_post.thread_id = snapboard_thread.id
                AND snapboard_post.revision_id IS NULL
                AND NOT snapboard_post.censor
            """
        # figure out who started the discussion
        extra_starter = """
            SELECT username FROM auth_user
                WHERE auth_user.id = (SELECT user_id
                    FROM snapboard_post WHERE snapboard_post.thread_id = snapboard_thread.id
                    ORDER BY snapboard_post.date ASC
                    LIMIT 1)
            """
        extra_last_poster = """
            SELECT username FROM auth_user
                WHERE auth_user.id = (SELECT user_id
                    FROM snapboard_post WHERE snapboard_post.thread_id = snapboard_thread.id
                    ORDER BY snapboard_post.date DESC
                    LIMIT 1)
            """
        extra_last_updated = """
            SELECT date FROM snapboard_post 
                WHERE snapboard_post.thread_id = snapboard_thread.id
                ORDER BY date DESC LIMIT 1
            """

        return super(ThreadManager, self).get_query_set().extra(
            select = {
                'post_count': extra_post_count,
                'starter': extra_starter,
                #'last_updated': extra_last_updated,  # bug: http://code.djangoproject.com/ticket/2210
                # the bug is that any extra columns must match their names
                # TODO: sorting on boolean fields is undefined in SQL theory
                'date': extra_last_updated,
                'last_poster': extra_last_poster,
            },).order_by('-gsticky', '-date')


    def get_user_query_set(self, user):
        if SnapboardProfile.objects.filter(user=user).count() > 0:
            profile = SnapboardProfile.objects.get(user=user)
            if profile.frontpage_filters.all().count() > 0:
                return self.get_query_set().filter(
                        category__in=profile.frontpage_filters.all())
        else:
            return self.get_query_set()


    def get_favorites(self, user):
        wl = WatchList.objects.filter(user=user)
        return self.get_query_set().filter(pk__in=[x.id for x in wl])


    def get_private(self, user):
        idstr = str(user.id)
        post_list = Post.objects.filter(
                Q(private__endswith=idstr) |
                Q(private__startswith=idstr) |
                Q(private__contains=idstr)).select_related()

        thread_ids = [p.thread.id for p in post_list]
        return self.get_query_set().filter(pk__in=thread_ids)


    def get_category(self, cat_id):
        return self.get_query_set().filter(category__id=cat_id)


# def category_index(request):
# 
#     extra_post_count = """
#         SELECT COUNT(*) FROM snapboard_thread
#             WHERE snapboard_thread.category_id = snapboard_category.id
#         """
#     cat_list = Category.objects.all().extra(
#         select = {'thread_count': extra_post_count},)
# 
#     return render_to_response('snapboard/category_index.html',
#             {
#             'cat_list': cat_list,
#             },
#             context_instance=RequestContext(request, processors=[login_context,]))


# vim: ai ts=4 sts=4 et sw=4
