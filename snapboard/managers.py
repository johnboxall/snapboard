import logging
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import Q

_log = logging.getLogger('snapboard.managers')

class PostManager(models.Manager):
    def get_query_set(self):
        return super(PostManager, self).get_query_set().exclude(
            revision__isnull=False).order_by('odate')

    def get_user_query_set(self, user):
        qs = self.get_query_set()
        if user.is_staff:
            return qs
        return qs.exclude(censor=True)

#     def posts_for_thread(self, thread_id, user):
#         '''
#         Returns a query set filtered to contain only the posts the user is 
#         allowed to see with regards the post's ``private`` and ``censor`` 
#         attributes.
#         This does not perform any category permissions check.
#         '''
#         # XXX: Before the Post.private refactor, the query here used to return
#         # duplicate values, forcing the use of SELECT DISTINCT.
#         # Do we still have such a problem, and if so, why?
#         qs = self.get_query_set().filter(thread__id=thread_id).select_related()
#         if user.is_authenticated():
#             qs = qs.filter((Q(user=user) | Q(is_private=False) | Q(private__exact=user)))
#         else:
#             qs = qs.exclude(is_private=True)
#         if not getattr(user, 'is_staff', False):
#             qs = qs.exclude(censor=True)
#         return qs

class ThreadManager(models.Manager):
    def get_query_set(self):
        return super(ThreadManager, self).get_query_set().order_by('-gsticky', '-last_update')
        
    def get_user_query_set(self, user):
        qs = self.get_query_set()
        if user.is_staff:
            return qs
        if user.is_authenticated():
            # hack alert.
            return qs.filter(Q(private=False) | Q(private=True) & Q(starter=user.username))
        return qs.exclude(private=True)
            
        #TODO: disabled the idea of sb_usersettings.
        #         try:
        #             us = user.sb_usersettings
        #         except ObjectDoesNotExist:
        #             return self.get_query_set().exclude(private=True)
        #         else:
        #             if us.frontpage_filters.count():
        #                 return self.get_query_set().filter(
        #                     category__in=us.frontpage_filters.all()).exclude(private=True, user__isnot=user)
        #         return self.get_query_set()
    
    def get_favorites(self, user):
        wl = user.sb_watchlist.all()
        return self.get_query_set().filter(pk__in=[x.thread_id for x in wl])
    
    def get_private(self, user):
        from snapboard.models import Post
        import sets
        post_list = Post.objects.filter(private__exact=user).select_related()
        thread_ids = sets.Set([p.thread.id for p in post_list])
        return self.get_query_set().filter(pk__in=thread_ids)

# class CategoryManager(models.Manager):
#     def get_query_set(self):
#         #@@@ BROKEN FOR SOME REASON
# #         thread_count = """
# #             SELECT COUNT(*) FROM snapboard_thread
# #             WHERE `snapboard_thread.category_id` = `snapboard_category.id`
# #             """
#         return super(CategoryManager, self).get_query_set()#.extra(
# #            select = {'thread_count': thread_count})