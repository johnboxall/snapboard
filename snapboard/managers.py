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
        from snapboard.models import WatchList
        watch_pks = WatchList.objects.filter(user=user).values_list("id", flat=True)
        return self.filter(Q(user=user) | Q(pk__in=watch_pks)).order_by("-date")

        
class PostManager(models.Manager):
    def create_and_notify(self, **kwargs):
        assert "thread" in kwargs
        
        post = self.create(**kwargs)
        post.notify()
        
        thread = kwargs["thread"]
        thread.date = post.date
        thread.save()
        
        return post