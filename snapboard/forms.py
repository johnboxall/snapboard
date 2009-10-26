from sets import Set

from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.forms import widgets, ValidationError
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from snapboard.models import Category, UserSettings, Thread, Post, WatchList
from snapboard.utils import RequestForm, RequestModelForm


__all__ = [
    "PostForm", "ThreadForm", "UserSettingsForm", "LoginForm", "InviteForm", 
    "AnwserInvitationForm"
]


class PostForm(RequestForm):
    post = forms.CharField(label = '', widget=forms.Textarea(attrs={'rows':'8',
        'cols':'120',}))
    private = forms.CharField(label=_("Recipients"), max_length=150, 
        widget=forms.TextInput(), required=False)

    def edit(self, opost):
        """Create a revision of an existing post."""
        data = self.cleaned_data
        user = self.request.user

        # Create the new edition.
        post = Post.objects.create(thread=opost.thread, user=user, 
            text=data["post"], previous=opost)
        post.private = opost.private.all()
        post.is_private = opost.is_private
        post.save()

        # Update the old one.
        opost.revision = post
        opost.save()
        
        return post
    
    def save(self, thread):
        """Create a new post."""
        data = self.cleaned_data
        user = self.request.user
            
        post = Post.objects.create(thread=thread, user=user, text=data['post'])
        
        if len(data['private']):
            post.private = data['private']
            post.is_private = True
            post.save()
        
        post.notify()
        
        return post
    
    def clean_private(self):
        recipients = self.cleaned_data['private']
        if not len(recipients.strip()):
            return []
        recipients = filter(lambda x: len(x.strip()) > 0, recipients.split(','))
        recipients = Set([x.strip() for x in recipients]) # string of usernames

        u = User.objects.filter(username__in=recipients).order_by('username')
        if len(u) != len(recipients):
            u_set = Set([str(x.username) for x in u])
            u_diff = recipients.difference(u_set)
            raise ValidationError(ungettext(
                    "The following is not a valid user:", "The following are not valid user(s): ",
                    len(u_diff)) + ' '.join(u_diff))
        return u


class ThreadForm(RequestForm):
    subject = forms.CharField(max_length=80, label=_('Subject'),
        widget=forms.TextInput(attrs={'size': '80',}))
    post = forms.CharField(label=_('Message'), widget=forms.Textarea(
        attrs={'rows':'8', 'cols': '80',}))
    private = forms.BooleanField(initial=False, required=False)

    def save(self, category):
        data = self.cleaned_data
        user = self.request.user
        
        subj = data['subject']
        
        thread = Thread.objects.create(
            subject=subj,
            category=category,
            slug=slugify(subj),
            private=data['private']
        )
        
        ip = self.request.META.get("REMOTE_ADDR")
        post = Post.objects.create(user=user, thread=thread, text=data['post'], ip=ip)
        
        
        # Add it to you favs. 
        
        return thread


class UserSettingsForm(RequestModelForm):
    # frontpage_filters = forms.MultipleChoiceField(label=_('Front page categories'))
    
    class Meta:
        model = UserSettings
        fields = ("notify_email",)
        # exclude = ('user',)
    
    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)
        #self.fields['frontpage_filters'].choices = [
        #    (cat.id, cat.label) for cat in Category.objects.all() if 
        #    cat.can_read(self.request.user)
        #]
    
    def save(self, commit=True):
        self.request.user.message_set.create(message="Preferences Updated.")
        return super(UserSettingsForm, self).save(commit)
    
    #def clean_frontpage_filters(self):
    #    frontpage_filters = [cat for cat in (Category.objects.get(pk=id) for id in
    #            self.cleaned_data['frontpage_filters']) if cat.can_read(self.request.user)]
    #    return frontpage_filters

class LoginForm(forms.Form):
    username = forms.CharField(max_length=30, label=_("Username"))
    password = forms.CharField(widget=widgets.PasswordInput, label=_("Password"))

    def clean_password(self):
        scd = self.cleaned_data
        self.user = authenticate(username=scd['username'], password=scd['password'])

        if self.user is not None:
            if self.user.is_active:
                return self.cleaned_data['password']
            else:
                raise ValidationError(_('Your account has been disabled.'))
        else:
            raise ValidationError(_('Your username or password were incorrect.'))

class InviteForm(forms.Form):
    user = forms.CharField(max_length=30, label=_('Username'))

    def clean_user(self):
        user = self.cleaned_data['user']
        try:
            user = User.objects.get(username=user)
        except User.DoesNotExist:
            raise ValidationError(_('Unknown username'))
        return user

class AnwserInvitationForm(forms.Form):
    decision = forms.ChoiceField(label=_('Answer'), choices=((0, _('Decline')), (1, _('Accept'))))