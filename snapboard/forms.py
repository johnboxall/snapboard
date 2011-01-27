from django.contrib.auth.models import User
from django.contrib.auth.forms import UserChangeForm
from django import forms
from django.utils.translation import ugettext_lazy as _

from snapboard.models import Category, Thread, Post, UserSettings
from snapboard.utils import RequestForm, RequestModelForm


__all__ = ['PostForm', 'ThreadForm', 'UserSettingsForm', 'UserNameForm']

Textarea = lambda cols: forms.Textarea(attrs={'rows':'8', 'cols': str(cols)})


class PostForm(RequestModelForm):
    post = forms.CharField(label='', widget=Textarea(120))
    
    class Meta:
        model = Post
        fields = ('post',)
    
    def save(self, thread=None):
        data = self.cleaned_data
        ip = self.request.META.get('REMOTE_ADDR')
        # TODO: Make this less stupid.

        # Editing an existing post.
        if self.instance.id is not None:
            self.instance.text = data['post']
            self.instance.ip = ip
            self.instance.save()
            return self.instance
        # Working on a new post.
        else:
            user = self.request.user
            post = Post.objects.create_and_notify(thread, user, text=data['post'], ip=ip)
            return post

class ThreadForm(RequestForm):
    subject = forms.CharField(max_length=80, label=_('Subject'))
    post = forms.CharField(label=_('Message'), widget=Textarea(80))
    private = forms.BooleanField(initial=False, required=False)
    category = forms.ModelChoiceField(queryset=Category.objects.all())
    
    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop('category', None)
        super(ThreadForm, self).__init__(*args, **kwargs)
        if self.category is not None:
            self.fields.pop('category')
        # TODO: Set selected category is provided.
    
    def save(self):
        data = self.cleaned_data
        user = self.request.user
        category = self.category or data['category']
        
        thread = Thread.objects.create_thread(**{
            'user': user,
            'category': category,
            'name': data['subject'],
            'private': data['private']
        })
        
        ip = self.request.META.get('REMOTE_ADDR')
        post = Post.objects.create_and_notify(thread, user, text=data['post'], ip=ip)                
        return thread


class UserSettingsForm(RequestModelForm):
    class Meta:
        model = UserSettings
        fields = ('email',)

    
class UserNameForm(UserChangeForm):
    class Meta:
        fields = ('username',)
    
    def __init__(self, *args, **kwargs):
        super(UserNameForm, self).__init__(*args, **kwargs)
        self.fields['username'].help_text = \
            '30 characters or fewer. Letters, digits and underscores only.'
    
    def clean_username(self):
        username = self.cleaned_data['username']
        if not username:
            raise forms.ValidationError('You must enter a username.')
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            pass
        else:
            if user != self.request.user:
                raise forms.ValidationError('A user with that username already exists.')
        
        return username