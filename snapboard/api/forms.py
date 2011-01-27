from django import forms
from django.contrib.auth.models import User

from snapboard.models import Thread, Post
from snapboard.utils import RequestModelForm


class ThreadForm(RequestModelForm):
    """
    Thread creation form for use with the API.
    
    """    
    text = forms.CharField()
    subscribers = forms.ModelMultipleChoiceField(queryset=User.objects.all())
    
    class Meta:
        model = Thread
        fields = ("user", "category", "name", "private", "text", "subscribers",)
    
    def save(self):
        thread_data = self.cleaned_data.copy()
        thread_data.pop("text")
        subscribers =  thread_data.pop("subscribers")
        thread = Thread.objects.create_thread(**thread_data)
        thread.subscribers.add(*subscribers)
        
        post_data = self.cleaned_data.copy()
        post_data.pop("subscribers")
        post_data.pop("private")
        post_data.pop("category")
        post_data.pop("name")
        post_data.update({
            "thread": thread,
            "ip": self.request.META.get("REMOTE_ADDR")
        })        
        Post.objects.create_and_notify(**post_data)
        
        return thread