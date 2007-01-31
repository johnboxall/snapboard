# vim: ai ts=4 sts=4 et sw=4

from datetime import datetime

from django.db import models
from django.conf import settings
from django.contrib.auth.models import User, Group

from fields import PhotoField

## NOTES
# TODO: banlist model
#
# Field option editable=False works as advertised in the Admin pages but
# does not hide form fields when used with newforms and the functions
# form_from_model() and form_from_instance():
#   http://code.djangoproject.com/ticket/3247

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

    class Admin:
        list_display = ('subject', 'category')
        list_filter = ('closed', 'csticky', 'gsticky', 'category')


class CategoryAccessControlList(models.Model):
    category = models.ForeignKey(Category)
    user = models.ForeignKey(User)
    group = models.ForeignKey(Group)

    read = models.BooleanField(default = True)
    write = models.BooleanField(default = True)
    censor = models.BooleanField(default = False)
    close = models.BooleanField(default = False)

    # unique on category and user or category and group
    class Admin:
        list_display = ('category', 'user', 'group', 'read', 'write', 'censor')
        list_filter = ('category', 'group', 'read', 'write', 'censor', 'close')

    class Meta:
        unique_together = (('category', 'user', 'group'),)


class Post(models.Model):
    """
    Post objects store information about revisions.

    Both forward and backward revisions are stored as ForeignKeys.
    """
    user = models.ForeignKey(User)
    thread = models.ForeignKey(Thread, core=True, edit_inline=models.STACKED, num_in_admin=1)
    text = models.TextField()
    date = models.DateTimeField(editable=False,auto_now_add=True)
    ip = models.IPAddressField()
    # private (list of usernames)

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
        if self.previous is not None:
            self.odate = self.previous.odate
        elif not self.id:
            # only do the following on creation, not modification
            self.odate = datetime.now()
        super(Post, self).save()

    def get_absolute_url(self):
        return '/threads/id/' + str(self.thread.id)

    def get_edit_form(self):
        from forms import PostForm
        return PostForm(initial={'post':self.text})

    def __str__(self):
        return ''.join( (str(self.user), ': ', str(self.date)) )

    class Admin:
        list_display = ('user', 'date', 'thread', 'ip')
        list_filter    = ('censor', 'freespeech', 'user',)
        search_fields  = ('text', 'user')


class AbuseList(models.Model):
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

## TODO: currently unused
class ForumUserData(models.Model):
    '''
    User data tied to user accounts from the auth module.

    Real name, email, and date joined information are stored in the built-in
    auth module.
    '''
    user = models.ForeignKey(User, unique=True, editable=False,
            core=True, edit_inline=models.STACKED, max_num_in_admin=1)
    profile = models.TextField(blank=True)

    ## views.profile(...) does not handle this properly:
    # http://code.djangoproject.com/ticket/3297
    avatar = PhotoField(upload_to='img/snapboard/avatars/',
            width=20, height=20)
    # signature (hrm... waste of space IMHO)

    # browsing options
    ppp = models.IntegerField(null=True,
            help_text = "Posts per page")
    notify_email = models.BooleanField(default=False,
            help_text = "Email notifications for watched discussions")
    reverse_posts = models.BooleanField(
            default=False,
            help_text = "Display Newest Posts First")
    frontpage_filters = models.ManyToManyField(Category,
            help_text = "Filter your front page on these categories")

    ## edit inline
    # class Admin:
    #     fields = (
    #         (None, 
    #             {'fields': ('user', 'avatar',)}),
    #         ('Profile', 
    #             {'fields': ('profile',)}),
    #         ('Browsing Options', 
    #             {'fields': 
    #                 ('ppp', 'notify_email', 'reverse_posts', 'frontpage_filters',)}),
    #     )

