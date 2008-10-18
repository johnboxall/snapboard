import logging
from datetime import datetime
from django.conf import settings
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import signals
from django.dispatch import dispatcher
from django.utils.translation import ugettext_lazy as _

from snapboard import managers
from snapboard.middleware import threadlocals

_log = logging.getLogger('snapboard.models')

SNAP_PREFIX = getattr(settings, 'SNAP_PREFIX', '/snapboard')
SNAP_MEDIA_PREFIX = getattr(settings, 'SNAP_MEDIA_PREFIX', 
        getattr(settings, 'MEDIA_URL', '') + '/snapboard')
SNAP_POST_FILTER = getattr(settings, 'SNAP_POST_FILTER', 'markdown').lower()

def is_user_banned(user):
    return user.id in settings.SNAP_BANNED_USERS

def is_ip_banned(ip):
    return ip in settings.SNAP_BANNED_IPS

class Category(models.Model):
    label = models.CharField(max_length=32, verbose_name=_('label'))

    objects = managers.CategoryManager()    # adds thread_count

    def __unicode__(self):
        return self.label

    def moderators(self):
        mods = Moderator.objects.filter(category=self.id)
        if mods.count() > 0:
            return ', '.join([m.user.username for m in mods])
        else:
            return None

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

    class Admin:
        pass


class Moderator(models.Model):
    category = models.ForeignKey(Category, verbose_name=_('category'))
    user = models.ForeignKey(User, verbose_name=_('user'))

    class Meta:
        verbose_name = _('moderator')
        verbose_name_plural = _('moderators')


class Thread(models.Model):
    subject = models.CharField(max_length=160, verbose_name=_('subject'))
    category = models.ForeignKey(Category, verbose_name=_('category'))

    closed = models.BooleanField(default=False, verbose_name=_('closed'))

    # Category sticky - will show up at the top of category listings.
    csticky = models.BooleanField(default=False, verbose_name=_('category sticky'))

    # Global sticky - will show up at the top of home listing.
    gsticky = models.BooleanField(default=False, verbose_name=_('global sticky'))

    objects = models.Manager() # needs to be explicit due to below
    view_manager = managers.ThreadManager()

    def __unicode__(self):
        return self.subject

    def get_url(self):
        return reverse('snapboard_thread', args=(self.id,))

    class Meta:
        verbose_name = _('thread')
        verbose_name_plural = _('threads')


class Post(models.Model):
    """
    Post objects store information about revisions.

    Both forward and backward revisions are stored as ForeignKeys.
    """
    # blank=True to get admin to work when the user field is missing
    user = models.ForeignKey(User, editable=False, blank=True, default=None, verbose_name=_('user'))

    thread = models.ForeignKey(Thread, verbose_name=_('thread'))
    text = models.TextField(verbose_name=_('text'))
    date = models.DateTimeField(editable=False,auto_now_add=True, verbose_name=_('date'))
    ip = models.IPAddressField(blank=True, verbose_name=_('ip address'))

    private = models.ManyToManyField(User,
            related_name="private_recipients", null=True, verbose_name=_('private recipients'))

    # (null or ID of post - most recent revision is always a diff of previous)
    odate = models.DateTimeField(editable=False, null=True)
    revision = models.ForeignKey("self", related_name="rev",
            editable=False, null=True, blank=True)
    previous = models.ForeignKey("self", related_name="prev",
            editable=False, null=True, blank=True)

    # (boolean set by mod.; true if abuse report deemed false)
    censor = models.BooleanField(default=False, verbose_name=_('censored')) # moderator level access
    freespeech = models.BooleanField(default=False, verbose_name=_('protected')) # superuser level access


    objects = models.Manager() # needs to be explicit due to below
    view_manager = managers.PostManager()

    def save(self):
        _log.debug('user = %s, ip = %s' % (threadlocals.get_current_ip(),
            threadlocals.get_current_user()))

        # hack to disallow admin setting arbitrary users to posts
        if getattr(self, 'user_id', None) is None:
            self.user_id = threadlocals.get_current_user().id

        # disregard any modifications to ip address
        self.ip = threadlocals.get_current_ip()

        if self.previous is not None:
            self.odate = self.previous.odate
        elif not self.id:
            # only do the following on creation, not modification
            self.odate = datetime.now()
        super(Post, self).save()


    def management_save(self):
        if self.previous is not None:
            self.odate = self.previous.odate
        elif not self.id:
            # only do the following on creation, not modification
            self.odate = datetime.now()
        super(Post, self).save()


    def get_absolute_url(self):
        return ''.join(('/threads/id/', str(self.thread.id), '/#post', str(self.id)))

    def get_edit_form(self):
        from forms import PostForm
        return PostForm(initial={'post':self.text})

    def __unicode__(self):
        return u''.join( (unicode(self.user), u': ', unicode(self.date)) )

    class Meta:
        verbose_name = _('post')
        verbose_name_plural = _('posts')

class AbuseReport(models.Model):
    '''
    When an abuse report is filed by a registered User, the post is listed
    in this table.

    If the abuse report is rejected as false, the post.freespeech flag can be
    set to disallow further abuse reports on said thread.
    '''
    post = models.ForeignKey(Post, verbose_name=_('post'))
    submitter = models.ForeignKey(User, verbose_name=_('submitter'))

    class Meta:
        verbose_name = _('abuse report')
        verbose_name_plural = _('abuse reports')
        unique_together = (('post', 'submitter'),)

class WatchList(models.Model):
    """
    Keep track of who is watching what thread.  Notify on change (sidebar).
    """
    user = models.ForeignKey(User, verbose_name=_('user'))
    thread = models.ForeignKey(Thread, verbose_name=_('thread'))
    # no need to be in the admin

# from django.contrib.site.models import Site
# def watched_thread_notify(instance):
#     thread_id = instance.thread.id
#     watchlist = WatchList.objects.select_related().filter(thread__id=thread_id)
# 
#     site = Site.objects.get(pk=settings.SITE_ID)
# 
#     people = [w.user.email for w in watchlist]
#     subject_tmp = loader.get_template("tracker/watched_thread_notify_subject.txt")
#     body_tmp = loader.get_template("tracker/watched_thread_notify_body.txt")
# 
#     ctx = Context({'post':instance, 'site':site})
#     subject = subject_tmp.render(ctx).strip()
#     body = body_tmp.render(ctx)
# 
#     send_mail(subject, body, 'snapboard@'+site.domain, people)
# connect this handler
#dispatcher.connect(watched_thread_notify, sender=Post, signal=signals.post_save)

class UserSettings(models.Model):
    '''
    User data tied to user accounts from the auth module.

    Real name, email, and date joined information are stored in the built-in
    auth module.

    After logging in, save these values in a session variable.
    '''
    user = models.OneToOneField(User, unique=True, 
            verbose_name=_('user'), related_name='snapboard_usersettings')
    ppp = models.IntegerField(
            choices = ((5, '5'), (10, '10'), (20, '20'), (50, '50')),
            default = 20,
            help_text = _('Posts per page'), verbose_name=_('posts per page'))
    tpp = models.IntegerField(
            choices = ((5, '5'), (10, '10'), (20, '20'), (50, '50')),
            default = 20,
            help_text = _('Threads per page'), verbose_name=_('threads per page'))
#    notify_email = models.BooleanField(default=False, blank=True,
#            help_text = "Email notifications for watched discussions.", verbose_name=_('notify'))
    reverse_posts = models.BooleanField(
            default=False,
            help_text = _('Display newest posts first.'), verbose_name=_('new posts first'))
    frontpage_filters = models.ManyToManyField(Category,
            null=True, blank=True,
            help_text = _('Filter the list of all topics on these categories.'), verbose_name=_('front page categories'))

    class Meta:
        verbose_name = _('User settings')
        verbose_name_plural = _('User settings')

    def __unicode__(self):
        return _('%s\'s preferences') % self.user
    
class UserBan(models.Model):
    '''
    This bans the user from posting messages on the forum. He can still log in.
    '''
    user = models.ForeignKey(User, unique=True, verbose_name=_('user'), db_index=True,
            help_text=_('The user may still browse the forums anonymously. '\
            'Other functions may also still be available to him if he is logged in.'))
    reason = models.CharField(max_length=255, verbose_name=_('reason'),
        help_text=_('This may be displayed to the banned user.'))

    class Meta:
        verbose_name = _('banned user')
        verbose_name_plural = _('banned users')

    def __unicode__(self):
        return _('Banned user: %s') % self.user

    @classmethod
    def update_cache(cls, **kwargs):
        c = connection.cursor()
        c.execute('SELECT user_id FROM %s;' % cls._meta.db_table)
        settings.SNAP_BANNED_USERS = set((x for (x,) in c.fetchall()))

signals.post_save.connect(UserBan.update_cache, sender=UserBan)
signals.post_delete.connect(UserBan.update_cache, sender=UserBan)

class IPBan(models.Model):
    '''
    IPs in the list are not allowed to use the boards.
    Only IPv4 addresses are supported, one per record. (patch with IPv6 and/or address range support welcome)
    '''
    address = models.IPAddressField(unique=True, verbose_name=_('IP address'), 
            help_text=_('A person\'s IP address may change and an IP address may be '\
            'used by more than one person, or by different people over time. '\
            'Be careful when using this.'), db_index=True)
    reason = models.CharField(max_length=255, verbose_name=_('reason'),
        help_text=_('This may be displayed to the people concerned by the ban.'))

    class Meta:
        verbose_name = _('banned IP address')
        verbose_name_plural = _('banned IP addresses')
    
    def __unicode__(self):
        return _('Banned IP: %s') % self.address

    @classmethod
    def update_cache(cls, **kwargs):
        c = connection.cursor()
        c.execute('SELECT address FROM %s;' % cls._meta.db_table)
        settings.SNAP_BANNED_IPS = set((x for (x,) in c.fetchall()))

signals.post_save.connect(IPBan.update_cache, sender=IPBan)
signals.post_delete.connect(IPBan.update_cache, sender=IPBan)

# vim: ai ts=4 sts=4 et sw=4

