import logging
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.urlresolvers import reverse
from django.db import models, connection
from django.db.models import signals, Q
from django.dispatch import dispatcher
from django.utils.translation import ugettext_lazy as _

try:
    from notification import models as notification
except ImportError:
    notification = None

from snapboard import managers
from snapboard.middleware import threadlocals

__all__ = [
    'SNAP_PREFIX', 'SNAP_MEDIA_PREFIX', 'SNAP_POST_FILTER',
    'NOBODY', 'ALL', 'USERS', 'CUSTOM', 'PERM_CHOICES', 'PERM_CHOICES_RESTRICTED',
    'PermissionError', 'is_user_banned', 'is_ip_banned', 
    'Category', 'Invitation', 'Group', 'Thread', 'Post', 'Moderator',
    'WatchList', 'AbuseReport', 'UserSettings', 'IPBan', 'UserBan',
    ]

_log = logging.getLogger('snapboard.models')

SNAP_PREFIX = getattr(settings, 'SNAP_PREFIX', '/snapboard')
SNAP_MEDIA_PREFIX = getattr(settings, 'SNAP_MEDIA_PREFIX', 
        getattr(settings, 'MEDIA_URL', '') + '/snapboard')
SNAP_POST_FILTER = getattr(settings, 'SNAP_POST_FILTER', 'markdown').lower()

NOBODY = 0
ALL = 1
USERS = 2
CUSTOM = 3

PERM_CHOICES = (
    (NOBODY, _('Nobody')),
    (ALL, _('All')),
    (USERS, _('Users')),
    (CUSTOM, _('Custom')),
)

PERM_CHOICES_RESTRICTED = (
    (NOBODY, _('Nobody')),
    (ALL, _('All')),
    (USERS, _('Users')),
    (CUSTOM, _('Custom')),
)

class PermissionError(PermissionDenied):
    '''
    Raised when a user tries to perform a forbidden operation, as per the 
    permissions defined by Category objects.
    '''
    pass

def is_user_banned(user):
    return user.id in settings.SNAP_BANNED_USERS

def is_ip_banned(ip):
    return ip in settings.SNAP_BANNED_IPS

class Group(models.Model):
    '''
    User-administerable group, be used to assign permissions to possibly 
    several users.

    Administrators of the group need to be explicitely added to the users
    list to be considered members.
    '''

    name = models.CharField(_('name'), max_length=36)
    users = models.ManyToManyField(User, verbose_name=_('users'), related_name='sb_member_of_group_set')
    admins = models.ManyToManyField(User, verbose_name=_('admins'), related_name='sb_admin_of_group_set') 

    class Meta:
        verbose_name = _('group')
        verbose_name_plural = _('groups')

    def __unicode__(self):
        return _('Group "%s"') % self.name

    def has_user(self, user):
        return self.users.filter(pk=user.pk).count() != 0

    def has_admin(self, user):
        return self.admins.filter(pk=user.pk).count() != 0

class Invitation(models.Model):
    '''
    Group admins create invitations for users to join their group.

    Staff with site admin access can assign users to groups without
    restriction.
    '''

    group = models.ForeignKey(Group, verbose_name=_('group'), related_name='sb_invitation_set')
    sent_by = models.ForeignKey(User, verbose_name=_('sent by'), related_name='sb_sent_invitation_set')
    sent_to = models.ForeignKey(User, verbose_name=_('sent to'), related_name='sb_received_invitation_set')
    sent_date = models.DateTimeField(_('sent date'), auto_now_add=True)
    response_date = models.DateTimeField(_('response date'), blank=True, null=True)
    accepted = models.BooleanField(_('accepted'), blank=True, null=True)

    class Meta:
        verbose_name = _('invitation')
        verbose_name_plural = _('invitations')

    def __unicode__(self):
        return _('Invitation for "%(group)s" sent by %(sent_by)s to %(sent_to)s.') % {
                'group': self.group.name,
                'sent_by': self.sent_by,
                'sent_to': self.sent_to }

    def notify_received(instance, **kwargs):
        '''
        Notifies of new invitations.
        '''
        if not notification:
            return
        if instance.accepted is None:
            notification.send(
                [instance.sent_to],
                'group_invitation_received',
                {'invitation': instance})
    notify_received = staticmethod(notify_received)

    def notify_cancelled(instance, **kwargs):
        '''
        Notifies of cancelled invitations.
        '''
        if not notification:
            return
        if instance.accepted is None:
            notification.send(
                [instance.sent_to],
                'group_invitation_cancelled',
                {'invitation': instance})
    notify_cancelled = staticmethod(notify_cancelled)

signals.post_save.connect(Invitation.notify_received, sender=Invitation)
signals.pre_delete.connect(Invitation.notify_cancelled, sender=Invitation)

class Category(models.Model):

    label = models.CharField(max_length=32, verbose_name=_('label'))

    view_perms = models.PositiveSmallIntegerField(_('view permission'), 
        choices=PERM_CHOICES, default=ALL,
        help_text=_('Limits the category\'s visibility.'))
    read_perms = models.PositiveSmallIntegerField(_('read permission'),
        choices=PERM_CHOICES, help_text=_('Limits the ability to read the '\
        'category\'s contents.'), default=ALL)
    post_perms = models.PositiveSmallIntegerField(_('post permission'),
        choices=PERM_CHOICES_RESTRICTED, help_text=_('Limits the ability to '\
        'post in the category.'), default=USERS)
    new_thread_perms = models.PositiveSmallIntegerField(
        _('create thread permission'), choices=PERM_CHOICES_RESTRICTED, 
        help_text=_('Limits the ability to create new threads in the '\
        'category. Only users with permission to post can create new threads,'\
        'unless a group is specified.'), default=USERS)

    view_group = models.ForeignKey(Group, verbose_name=_('view group'),
        blank=True, null=True, related_name='can_view_category_set')
    read_group = models.ForeignKey(Group, verbose_name=_('read group'),
        blank=True, null=True, related_name='can_read_category_set')
    post_group = models.ForeignKey(Group, verbose_name=_('post group'),
        blank=True, null=True, related_name='can_post_category_set')
    new_thread_group = models.ForeignKey(Group, verbose_name=_('create thread group'),
        blank=True, null=True, related_name='can_create_thread_category_set')

    objects = managers.CategoryManager()    # adds thread_count

    def __unicode__(self):
        return self.label

    def moderators(self):
        mods = Moderator.objects.filter(category=self.id)
        if mods.count() > 0:
            return ', '.join([m.user.username for m in mods])
        else:
            return None

    def can_view(self, user):
        flag = False
        if self.view_perms == ALL:
            flag = True
        elif self.view_perms == USERS:
            flag = user.is_authenticated()
        elif self.view_perms == CUSTOM:
            flag = user.is_superuser or (user.is_authenticated() and self.view_group.has_user(user))
        return flag

    def can_read(self, user):
        flag = False
        if self.read_perms == ALL:
            flag = True
        elif self.read_perms == USERS:
            flag = user.is_authenticated()
        elif self.read_perms == CUSTOM:
            flag = user.is_superuser or (user.is_authenticated() and self.read_group.has_user(user))
        return flag

    def can_post(self, user):
        flag = False
        if self.post_perms == USERS:
            flag = user.is_authenticated()
        elif self.post_perms == CUSTOM:
            flag = user.is_superuser or (user.is_authenticated() and self.post_group.has_user(user))
        return flag

    def can_create_thread(self, user):
        flag = False
        if self.new_thread_perms == USERS:
            flag = user.is_authenticated()
        elif self.new_thread_perms == CUSTOM:
            flag = user.is_superuser or (user.is_authenticated() and self.new_thread_group.has_user(user))
        return flag

    class Meta:
        verbose_name = _('category')
        verbose_name_plural = _('categories')

class Moderator(models.Model):
    category = models.ForeignKey(Category, verbose_name=_('category'))
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='sb_moderator_set')

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

    def count_posts(self, user, before=None):
        '''
        Returns the number of visible posts in the thread or, if ``before`` is 
        a Post object, the number of visible posts in the thread that are
        older.
        '''
        # This partly does what Thread.objects.get_query_set() does, except 
        # it takes into account the user and therefore knows what posts
        # are visible to him
        qs = self.post_set.filter(revision=None)
        if user.is_authenticated():
            qs = qs.filter(Q(user=user) | Q(is_private=False) | Q(private__exact=user))
        if not getattr(user, 'is_staff', False):
            qs = qs.exclude(censor=True)
        if before:
            qs.filter(date__lt=before.date)
        return qs.count()

class Post(models.Model):
    """
    Post objects store information about revisions.

    Both forward and backward revisions are stored as ForeignKeys.
    """
    # blank=True to get admin to work when the user field is missing
    user = models.ForeignKey(User, editable=False, blank=True, default=None,
            verbose_name=_('user'), related_name='sb_created_posts_set')

    thread = models.ForeignKey(Thread, verbose_name=_('thread'))
    text = models.TextField(verbose_name=_('text'))
    date = models.DateTimeField(editable=False,auto_now_add=True, verbose_name=_('date'))
    ip = models.IPAddressField(verbose_name=_('ip address'), blank=True, null=True)

    private = models.ManyToManyField(User,
            related_name="sb_private_posts_set", null=True, verbose_name=_('private recipients'))
    # The 'private message' status is denormalized by the ``is_private`` flag.
    # It's currently quite hard to do the denormalization automatically 
    # If ManyRelatedManager._add_items() fired some signal on update, it would help.
    # Right now it's up to the code that changes the 'private' many-to-many field to 
    # change ``is_private``.
    is_private = models.BooleanField(_('private'), default=False, editable=False)

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

    def save(self, force_insert=False, force_update=False):
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
        super(Post, self).save(force_insert, force_update)


    def management_save(self):
        if self.previous is not None:
            self.odate = self.previous.odate
        elif not self.id:
            # only do the following on creation, not modification
            self.odate = datetime.now()
        super(Post, self).save(False, False)

    def notify(self, **kwargs):
        if not notification:
            return
        if not self.previous:
            all_recipients = set()
            if self.is_private:
                recipients = set(self.private.all())
                if recipients:
                    notification.send(
                        recipients,
                        'private_post_received',
                        {'post': self}
                    )
                    all_recipients = all_recipients.union(recipients)
            recipients = set((wl.user for wl in WatchList.objects.filter(thread=self.thread) if wl.user not in all_recipients))
            if recipients:
                notification.send(
                    recipients,
                    'new_post_in_watched_thread',
                    {'post': self}
                )
                all_recipients = all_recipients.union(recipients)

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

# Signals make it hard to handle the notification of private recipients
#if notification:
#    signals.post_save.connect(Post.notify, sender=Post)

class AbuseReport(models.Model):
    '''
    When an abuse report is filed by a registered User, the post is listed
    in this table.

    If the abuse report is rejected as false, the post.freespeech flag can be
    set to disallow further abuse reports on said thread.
    '''
    post = models.ForeignKey(Post, verbose_name=_('post'))
    submitter = models.ForeignKey(User, verbose_name=_('submitter'), related_name='sb_abusereport_set')

    class Meta:
        verbose_name = _('abuse report')
        verbose_name_plural = _('abuse reports')
        unique_together = (('post', 'submitter'),)

class WatchList(models.Model):
    """
    Keep track of who is watching what thread.  Notify on change (sidebar).
    """
    user = models.ForeignKey(User, verbose_name=_('user'), related_name='sb_watchlist')
    thread = models.ForeignKey(Thread, verbose_name=_('thread'))
    # no need to be in the admin

class UserSettings(models.Model):
    '''
    User data tied to user accounts from the auth module.

    Real name, email, and date joined information are stored in the built-in
    auth module.

    After logging in, save these values in a session variable.
    '''
    user = models.OneToOneField(User, unique=True, 
            verbose_name=_('user'), related_name='sb_usersettings')
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
            related_name='sb_userban_set',
            help_text=_('The user may still browse the forums anonymously. '
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
            help_text=_('A person\'s IP address may change and an IP address may be '
            'used by more than one person, or by different people over time. '
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

