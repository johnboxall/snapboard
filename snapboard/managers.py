from django.db import models
from django.db.models import Q
from django.template.defaultfilters import slugify


class ThreadManager(models.Manager):
    def get_user_query_set(self, user):
        qs = self.get_query_set().order_by("-sticky", "-date")
        if user.is_staff:
            return qs
        if user.is_authenticated():
            return qs.filter(Q(private=False) | Q(private=True) & Q(user=user))
        return qs.filter(private=False)
        
    def create_thread(self, **kwargs):
        kwargs['slug'] = self.get_slug(kwargs['slug'])
        return self.create(**kwargs)
    
    def get_slug(self, slug):
        """Returns a unique slug."""
        # TODO: Unique within Category is good enough?
        get = lambda: self.filter(slug=slug)
        slug = s = slugify(slug)
        counter = 1
        while get():
            slug = "%s-%s" % (s, counter)
            counter += 1
        return slug
    
    def favorites(self, user):
        """Returns threads watched or owned by user."""
        watch_pks = user.sb_watchlist.values_list("id", flat=True)
        return self.filter(Q(user=user) | Q(pk__in=watch_pks)).order_by("-date")


class PostManager(models.Manager):
    def get_user_query_set(self, user):
        qs = self.get_query_set()
        if user.is_staff:
            return qs
        if user.is_authenticated():
            return qs.filter(user=user)
        return qs.none()

    def create_and_notify(self, thread, user, **kwargs):
        post = self.create(thread=thread, user=user, **kwargs)
        
        # Auto-watch the threads you post in.
        user.sb_watchlist.get_or_create(thread=thread)
        
        post.notify()
        
        thread.date = post.date
        thread.save()
        
        return post