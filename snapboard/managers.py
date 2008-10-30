import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q

_log = logging.getLogger('snapboard.managers')

class PostManager(models.Manager):
    def get_query_set(self):
        select = {}
        extra_abuse_count = """
            SELECT COUNT(*) FROM snapboard_abusereport
                WHERE snapboard_post.id = snapboard_abusereport.post_id
            """
        select['abuse'] = extra_abuse_count

        return super(PostManager, self).get_query_set().extra(
            select = select).exclude(revision__isnull=False).order_by('odate')

    def posts_for_thread(self, thread_id, user):
        '''
        Returns a query set filtered to contain only the posts the user is 
        allowed to see with regards the post's ``private`` and ``censor`` 
        attributes.
        This does not perform any category permissions check.
        '''
        # XXX: Before the Post.private refactor, the query here used to return
        # duplicate values, forcing the use of SELECT DISTINCT.
        # Do we still have such a problem, and if so, why?
        qs = self.get_query_set().filter(thread__id=thread_id).select_related().distinct()
        if user.is_authenticated():
            qs = qs.filter((Q(user=user) | Q(is_private=False) | Q(private__exact=user)))
        else:
            qs = qs.exclude(is_private=True)
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
        try:
            us = user.sb_usersettings
        except ObjectDoesNotExist:
            pass
        else:
            if us.frontpage_filters.count():
                return self.get_query_set().filter(
                    category__in=us.frontpage_filters.all())
        return self.get_query_set()

    def get_favorites(self, user):
        wl = user.sb_watchlist.all()
        return self.get_query_set().filter(pk__in=[x.thread_id for x in wl])

    def get_private(self, user):
        from snapboard.models import Post
        import sets
        post_list = Post.objects.filter(private__exact=user).select_related()
        thread_ids = sets.Set([p.thread.id for p in post_list])
        return self.get_query_set().filter(pk__in=thread_ids)

    def get_category(self, cat_id):
        return self.get_query_set().filter(category__id=cat_id)

class CategoryManager(models.Manager):
    def get_query_set(self):
        thread_count = """
            SELECT COUNT(*) FROM snapboard_thread
            WHERE snapboard_thread.category_id = snapboard_category.id
            """
        return super(CategoryManager, self).get_query_set().extra(
            select = {'thread_count': thread_count})
                
# vim: ai ts=4 sts=4 et sw=4
