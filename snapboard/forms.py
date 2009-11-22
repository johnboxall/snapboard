from django import forms
from django.template.defaultfilters import slugify
from django.utils.translation import ugettext_lazy as _

from snapboard.models import Category, Thread, Post, WatchList, UserSettings
from snapboard.utils import RequestForm, RequestModelForm


__all__ = ["PostForm", "ThreadForm", "UserSettingsForm"]

Textarea = lambda cols: forms.Textarea(attrs={'rows':'8', 'cols': str(cols)})

class PostForm(RequestModelForm):
    post = forms.CharField(label='', widget=Textarea(120))
    
    class Meta:
        model = Post
        fields = ("post",)
    
    def save(self, thread=None):

        data = self.cleaned_data


        # This is kinda dumb.
        if self.instance is not None:
            self.instance.text = data["post"]
            self.instance.save()
            return self.instance
        else:
            user = self.request.user
            ip = self.request.META.get("REMOTE_ADDR")
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
    
    def __init__(self, *args, **kwargs):
        super(UserSettingsForm, self).__init__(*args, **kwargs)
    
    def save(self, commit=True):
        self.request.user.message_set.create(message="Preferences Updated.")
        return super(UserSettingsForm, self).save(commit)