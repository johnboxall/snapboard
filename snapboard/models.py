from django.db import models

from django.contrib.auth.models import User


# Create your models here.

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
    user = models.ForeignKey(User)
    category = models.ForeignKey(Category)
    class Admin:
        list_display = ('user', 'category')

class Thread(models.Model):
    subject = models.CharField(maxlength=80)
    category = models.ForeignKey(Category)

    closed = models.BooleanField(default=False)

    # (Boolean, "Category sticky - will show up at the top of category listings.")
    csticky = models.BooleanField(default=False)

    # (Boolean, "Global sticky - will show up at the top of home listing.")
    gsticky = models.BooleanField(default=False)

    def __str__(self):
        return self.subject

    class Admin:
        list_display = ('subject', 'category')

class Post(models.Model):
    """
    Logins are integrated into the post form.  If you aren't logged in and
    authentication is required, a username/password entry will be integrated
    into the post form.  Otherwise, business as usual.
    """
    user = models.ForeignKey(User)
    thread = models.ForeignKey(Thread)
    text = models.TextField()
    date = models.DateTimeField(editable=False,auto_now_add=True)
    ip = models.IPAddressField()
    # private (list of usernames)

    # (null or ID of post - most recent revision is always a diff of previous)
    revision = models.ForeignKey("self", related_name="rev",
            editable=False, null=True, blank=True)
    previous = models.ForeignKey("self", related_name="prev",
            editable=False, null=True, blank=True)

    # (boolean set by mod.; true if abuse report deemed false)
    censor = models.BooleanField(default=False) # moderator level access
    freespeech = models.BooleanField(default=False) # superuser level access

    def get_edit_form(self):
        from forms import PostForm
        return PostForm(initial={'post':self.text})

    def __str__(self):
        return ''.join( (str(self.user), ': ', str(self.date)) )

    class Admin:
        list_display = ('user', 'date', 'thread', 'ip')


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
    class Admin:
        pass

class ForumUserData(models.Model):
    user = models.OneToOneField(User)
    nickname = models.CharField(maxlength=32)
    posts = models.IntegerField()
    profile = models.TextField()
    # avatar (15x15 xpm/svg)
    # signature (hrm... waste of space IMHO)

    ppp = models.IntegerField()

    notify_email = models.BooleanField(default=False)
    reverse_date_disp = models.BooleanField(default=False)
    # frontpage_filter
    class Admin:
        pass

    # class Meta:
    #     permissions = (
    #         ("moderator", "Forum Moderator Status"),
    #     )
