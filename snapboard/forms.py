from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from snapboard.models import Category, Thread, Post, WatchList, UserSettings
from snapboard.utils import RequestForm, RequestModelForm

from django.contrib.auth.models import User

try:
    import wingdbstub
except:
    pass

__all__ = ["PostForm", "ThreadForm", "UserSettingsForm", "UserNameForm"]

Textarea = lambda cols: forms.Textarea(attrs={'rows':'8', 'cols': str(cols)})

class PostForm(RequestModelForm):
    post = forms.CharField(label='', widget=Textarea(120))
    
    class Meta:
        model = Post
        fields = ("post",)
    
    def save(self, thread=None):
        data = self.cleaned_data
        ip = self.request.META.get("REMOTE_ADDR")

        # TODO: Make this less stupid.

        # Editing an existing post.
        if self.instance.id is not None:
            self.instance.text = data["post"]
            self.instance.ip = ip
            self.instance.save()
            return self.instance
        # Working on a new post.
        else:
            user = self.request.user
            return Post.objects.create_and_notify(thread, user, text=data['post'], ip=ip)

class ThreadForm(RequestForm):
    subject = forms.CharField(max_length=80, label=_('Subject'))
    post = forms.CharField(label=_('Message'), widget=Textarea(80))
    private = forms.BooleanField(initial=False, required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop("category", None)
        super(ThreadForm, self).__init__(*args, **kwargs)
        if self.category is not None:
            self.fields.pop("category")
            # TODO: Would be nice to set the selected here.
    
    def save(self):
        data = self.cleaned_data
        user = self.request.user
        category = self.category or data["category"]
                
        thread = Thread.objects.create_thread(
            user=user,
            category=category,
            name=data['subject'],
            slug=slugify(data['subject']),
            private=data['private']
        )
        
        ip = self.request.META.get("REMOTE_ADDR")
        Post.objects.create_and_notify(thread, user, text=data['post'], ip=ip)
        return thread


class UserSettingsForm(RequestModelForm):
    class Meta:
        model = UserSettings
        fields = ("email",)
    
    def save(self, commit=True):
        self.request.user.message_set.create(message="Preferences Updated.")
        return super(UserSettingsForm, self).save(commit)
    
    
class UserNameForm(RequestModelForm):
    class Meta:
        model = User
        fields = ("username",)
    
    def __init__(self, *args, **kwargs):
        super(UserNameForm, self).__init__(*args, **kwargs)
        self.fields["username"].help_text = "30 characters or fewer. Letters, digits and underscores only."
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if not username:
            raise forms.ValidationError("You must enter a username")
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            if user != self.request.user:
                raise forms.ValidationError("A user with that username already exists")

        import re
        for c in tuple(username):
            if not re.match('([_a-z0-9])', c, re.I):
                raise forms.ValidationError("Illegal character in username")
        
        return username
    
    def save(self, commit=True):
        # self.request.user.message_set.create(message="Preferences Updated.")
        return super(UserNameForm, self).save(commit)    