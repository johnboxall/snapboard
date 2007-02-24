import sets
from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User, Group
from django.core import validators
from django.db import models
from django.db.models import signals
from django.dispatch import dispatcher

from fields import PhotoField
from middleware import threadlocals

SNAP_PREFIX = getattr(settings, 'SNAP_PREFIX', '/snapboard')
SNAP_MEDIA_PREFIX = getattr(settings, 'SNAP_MEDIA_PREFIX', 
        getattr(settings, 'MEDIA_URL', '') + '/media')
SNAP_LOGIN_URL = SNAP_PREFIX + '/signin'


def isIPAddressList(field_data, all_data):
    l = str(field_data).splitlines()
    line = 1
    for ip in l:
        try:
            validators.isValidIPAddress4(ip, all_data)
            line = line + 1
        except validators.ValidationError:
            raise validators.ValidationError(
                    "Line " + str(line) + " has an invalid IP address")


class Category(models.Model):
    label = models.CharField(maxlength=32)

    def __str__(self):
        return self.label

    def moderators(self):
        mods = Moderator.objects.filter(category=self.id)
        if mods.count() > 0:
            return ', '.join([m.user.username for m in mods])
        else:
            return None

    class Admin:
        pass


class Moderator(models.Model):
    category = models.ForeignKey(Category)
    user = models.ForeignKey(User)


class Thread(models.Model):
    subject = models.CharField(maxlength=160)
    category = models.ForeignKey(Category)

    closed = models.BooleanField(default=False)

    # Category sticky - will show up at the top of category listings.
    csticky = models.BooleanField(default=False)

    # Global sticky - will show up at the top of home listing.
    gsticky = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

    def get_url(self):
        return SNAP_PREFIX + '/threads/id/' + self.id + '/'

    class Admin:
        list_display = ('subject', 'category')
        list_filter = ('closed', 'csticky', 'gsticky', 'category')


class Post(models.Model):
    """
    Post objects store information about revisions.

    Both forward and backward revisions are stored as ForeignKeys.
    """

    # blank=True to get admin to work when the user field is missing
    user = models.ForeignKey(User, editable=False, blank=True, default=None)

    thread = models.ForeignKey(Thread,
            core=True, edit_inline=models.STACKED, num_in_admin=1)
    text = models.TextField()
    date = models.DateTimeField(editable=False,auto_now_add=True)
    ip = models.IPAddressField(blank=True)

    ## Note: I can see the max_length coming back to bite me in the ass...
    # for now, 256 should be reasonable.
    # TODO: make this a textfield (and set columns to 1)
    private = models.CommaSeparatedIntegerField(maxlength=256, blank=True, default='')

    # (null or ID of post - most recent revision is always a diff of previous)
    odate = models.DateTimeField(editable=False, null=True)
    revision = models.ForeignKey("self", related_name="rev",
            editable=False, null=True, blank=True)
    previous = models.ForeignKey("self", related_name="prev",
            editable=False, null=True, blank=True)

    # (boolean set by mod.; true if abuse report deemed false)
    censor = models.BooleanField(default=False) # moderator level access
    freespeech = models.BooleanField(default=False) # superuser level access

    def save(self):
        #print 'user =', threadlocals.get_current_user()
        #print threadlocals.get_current_ip(), type(threadlocals.get_current_ip())

        # hack to disallow admin setting arbitrary users to posts
        if getattr(self, 'user_id', None) is None:
            self.user_id = threadlocals.get_current_user().id

        # disregard any modifications to ip address
        self.ip = threadlocals.get_current_ip()
        # self.ip = '127.0.0.1'

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

    def __str__(self):
        return ''.join( (str(self.user), ': ', str(self.date)) )

    class Admin:
        list_display = ('user', 'date', 'thread', 'ip')
        list_filter    = ('censor', 'freespeech', 'user',)
        search_fields  = ('text', 'user')


# class PostAdminOptions(models.options.AdminOptions):
#     '''
#     Replaces AdminOptions for Post model
#     '''
#     def _fields(self):
#         user = threadlocals.get_current_user()
#         assert(not(user is None or user.is_anonymous()))
# 
#         if user.has_perm('moderator.superuser'):
#             pass
#         else:
#             pass
#     fields = property(_fields)
# 
# # register PostAdminOptions
# #del Post._meta.admin.fields
# #Post._meta.admin.__class__ = PostAdminOptions


class AbuseReport(models.Model):
    '''
    When an abuse report is filed by a registered User, the post is listed
    in this table.

    If the abuse report is rejected as false, the post.freespeech flag can be
    set to disallow further abuse reports on said thread.
    '''
    post = models.ForeignKey(Post)
    submitter = models.ForeignKey(User)
    class Admin:
        list_display = ('post', 'submitter')

    class Meta:
        unique_together = (('post', 'submitter'),)


class WatchList(models.Model):
    """
    Keep track of who is watching what thread.  Notify on change (sidebar).
    """
    user = models.ForeignKey(User)
    thread = models.ForeignKey(Thread)
    # no need to be in the admin


class SnapboardProfile(models.Model):
    '''
    User data tied to user accounts from the auth module.

    Real name, email, and date joined information are stored in the built-in
    auth module.

    After logging in, save these values in a session variable.
    '''
    user = models.ForeignKey(User, unique=True, editable=False,
            core=True, edit_inline=models.STACKED, max_num_in_admin=1)
    profile = models.TextField(blank=True)

    avatar = PhotoField(blank=True, upload_to='img/snapboard/avatars/',
            width=24, height=24)

    # browsing options
    ppp = models.IntegerField(null=True, blank=True,
            choices = ((5, '5'), (10, '10'), (20, '20'), (50, '50')),
            default = 20,
            help_text = "Posts per page")
    tpp = models.IntegerField(null=True, blank=True,
            choices = ((5, '5'), (10, '10'), (20, '20'), (50, '50')),
            default = 20,
            help_text = "Threads per page")
    notify_email = models.BooleanField(default=False, blank=True,
            help_text = "Email notifications for watched discussions.")
    reverse_posts = models.BooleanField(
            default=False,
            help_text = "Display newest posts first.")
    frontpage_filters = models.ManyToManyField(Category,
            null=True, blank=True,
            help_text = "Filter your front page on these categories.")

    ## edit inline
    class Admin:
        fields = (
            (None, 
                {'fields': ('user', 'avatar',)}),
            ('Profile', 
                {'fields': ('profile',)}),
            ('Browsing Options', 
                {'fields': 
                    ('ppp', 'notify_email', 'reverse_posts', 'frontpage_filters',)}),
        )


class BannedUser(models.Model):
    '''
    This is a login-level ban.  These users will be able to browse the board
    but will not be able to log in.
    '''
    user = models.ForeignKey(User, unique=True)
    reason = models.TextField()
    def __str__(self):
        return str(self.user)

    class Admin:
        pass


class BannedIP(models.Model):
    '''
    Each line should have an IP address.
    
    The objects in this model are not allowed to log in or register new
    accounts.
    '''

    iplist = models.TextField(validator_list=[isIPAddressList])
    reason = models.TextField()

    def get_ips(self):
        return [i.strip() for i in str(self.iplist).splitlines()]

    def __str__(self):
        return ','.join(self.get_ips())

    class Admin:
        pass

def update_ban_cache():
    ips = []
    users = [int(u.id) for u in BannedUser.objects.all()]

    for ip in BannedIP.objects.all():
        ips.extend(ip.get_ips())

    settings.SNAP_BANNED_IPS = sets.Set(ips)
    settings.SNAP_BANNED_USERS = sets.Set(users)

dispatcher.connect(update_ban_cache, sender=BannedIP, signal=signals.post_save)
dispatcher.connect(update_ban_cache, sender=BannedIP, signal=signals.post_delete)
dispatcher.connect(update_ban_cache, sender=BannedUser, signal=signals.post_save)
dispatcher.connect(update_ban_cache, sender=BannedUser, signal=signals.post_delete)

# vim: ai ts=4 sts=4 et sw=4
