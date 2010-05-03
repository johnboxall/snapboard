from datetime import datetime
import time

from django.conf import settings
from django.core.cache import cache
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.translation import ugettext_lazy as _

from snapboard.fields import SignalSlugField, fields_updated
from snapboard.managers import ThreadManager, PostManager


THREADS_PER_PAGE = getattr(settings, "SB_THREADS_PER_PAGE", 10)
POSTS_PER_PAGE = getattr(settings, "SB_POSTS_PER_PAGE", 10)
MEDIA_PREFIX = getattr(settings, 'SNAP_MEDIA_PREFIX')

# TODO: Add created/updated dates.
# should add created...
# should add updated...


class Category(models.Model):
    name = models.CharField(max_length=64, verbose_name=_('name'))
    description = models.CharField(max_length=255, blank=True, 
        verbose_name=_('description'))
    slug = SignalSlugField()
    
    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')
    
    def __unicode__(self):
        return self.name

# TODO: Update cache when a thread is updated (sticky/delete/private etc).
class Thread(models.Model):
    user = models.ForeignKey("auth.User", verbose_name=_('user'))
    name = models.CharField(max_length=255, verbose_name=_('subject'))
    # TODO: SignalSlugField allows you to do things when a slug is changed,
    #       like create a redirect for a previous slug. Is this something
    #       that should be included in the app? Or should you just be able to
    #       swap in a proxy model for what you want...
    slug = SignalSlugField(max_length=255)
    category = models.ForeignKey(Category, verbose_name=_('category'))
    private = models.BooleanField(default=False, verbose_name=_('private'))
    closed = models.BooleanField(default=False, verbose_name=_('closed'))
    sticky = models.BooleanField(default=False, verbose_name=_('sticky'))
    date = models.DateTimeField(verbose_name=_('date'), null=True)
    
    objects = ThreadManager()
    
    class Meta:
        verbose_name = _('thread')
        verbose_name_plural = _('threads')
    
    def __unicode__(self):
        return self.name
    
    def is_fav(self, u):
        # True if user is watching this thread.
        return user.is_authenticated() and self.watchlist_set.filter(user=user).count() != 0

    def get_notify_recipients(self):
        # Returns a set of emails watching this thread.
        mail_dict = dict(self.watchlist_set.values_list("user__id", "user__email"))
        dont_mail_pks = UserSettings.objects.filter(user__id__in=mail_dict.keys(), email=False)
        dont_mail_pks = dont_mail_pks.values_list("user__id", flat=True)
        for pk in dont_mail_pks:
            mail_dict.pop(pk)
        
        recipients = set(mail_dict.values())
        [recipients.add(t[1]) for t in settings.ADMINS]
        return recipients
    
    def get_post_count(self):
        return self.post_set.count()
    
    def get_posts(self):
        return self.post_set.order_by("date")
    
    def get_last_post(self):
        try:
            return self.post_set.order_by("-date")[0]
        except IndexError:
            return None
    
    def get_url(self):
        return reverse('sb_thread', args=(self.category.slug, self.slug,))
    get_absolute_url = get_url

class Post(models.Model):
    user = models.ForeignKey("auth.User", verbose_name=_('user'))
    thread = models.ForeignKey(Thread, verbose_name=_('thread'))
    text = models.TextField(verbose_name=_('text'))
    # TODO: Avoid double renders.
    # rendered_text = models.TextField(verbose_name=_('rendered_text'))
    
    
    date = models.DateTimeField(verbose_name=_('date'), null=True)
    ip = models.IPAddressField(verbose_name=_('ip address'), blank=True, null=True)
    
    objects = PostManager()
    
    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')
    
    def __unicode__(self):
        return u''.join([str(self.user), ': ', str(self.date)])
    
    def invalidate_cache(self):
        from snapboard.utils import get_prefix_cache_key
        
        prefix = int(time.time())

        cslug = self.thread.category.slug
        tslug = self.thread.slug

        # Views to clear:
        path = [
            reverse("sb_category_list"),
            reverse("sb_thread_list"),
            reverse("sb_category", args=[cslug]),
            reverse("sb_thread", args=[cslug, tslug])
        ]
        
        for path in paths:
            prefix_key = get_prefix_cache_key(path)
            cache.set(prefix_key, prefix)
        
    def save(self, force_insert=False, force_update=False):
        if self.id is None:
            self.date = datetime.now()
        self.invalidate_cache()                
        return super(Post, self).save(force_insert, force_update)        
        
    def notify(self):
        from snapboard.utils import renders, bcc_mail
        
        subj = self.thread.name
        body = renders("notify/notify_body.txt", {"post": self, "subj": subj})
        recipients = self.thread.get_notify_recipients()
        bcc_mail(subj, body, settings.DEFAULT_FROM_EMAIL, recipients,
            fail_silently=settings.DEBUG)
    
    def _get_page_number(self):
        # Returns the page number this post is on. If not paginated, returns None.
        posts = list(self.thread.post_set.values_list("pk", flat=True))
        total = len(posts)
        preceding_count = posts.index(self.pk)
        
        if total > POSTS_PER_PAGE:
            return preceding_count // POSTS_PER_PAGE + 1
        return None
    
    def get_url(self):
        query = "#post%i" % self.pk
        page = self._get_page_number()
        if page is not None:
            query = "?page=%s%s" % (page, query)
        
        args = [self.thread.category.slug, self.thread.slug]
        path = reverse('sb_thread', args=args)
        next = "%s%s" % (path, query)
        return next
    get_absolute_url = get_url
    

class WatchList(models.Model):
    user = models.ForeignKey("auth.User", verbose_name=_('user'), 
        related_name='sb_watchlist')
    thread = models.ForeignKey(Thread, verbose_name=_('thread'))


class UserSettings(models.Model):
    user = models.OneToOneField("auth.User", unique=True, 
            verbose_name=_('user'), related_name='sb_usersettings')
    email = models.BooleanField(default=True, 
        help_text=_("Check if you would like to receive email about posts you are watching."))
    
    class Meta:
        verbose_name = _('User settings')
        verbose_name_plural = _('User settings')
    
    def __unicode__(self):
        return _('%s\'s preferences') % self.user