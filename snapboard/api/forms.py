from django import forms

from snapboard.models import Thread
from snapboard.utils import RequestModelForm


class ThreadForm(RequestModelForm):
    """
    Thread creation form for use w/ the API.
    
    """    
    text = forms.CharField()
    subscribers = forms.CharField()
    
    class Meta:
        model = Thread
        fields = ("user", "category", "name", "private", "text", "subscribers",)
    
    def clean_subscribers(self):
        # subscribe user hack
        #if self.request.POST.get('subscribe_users', ''):
        #    subscribers = [x.strip() for x in self.request.POST['subscribe_users'].split(',') if x and x != ' ']
        #return subscribers
        return ""
    
    def save(self):
        thread_data = self.cleaned_data.copy()
        thread_data.pop("text")
        thread = Thread.objects.create_thread(**thread_data)
        
        post_data = self.cleaned_data.copy()
        post_data.pop("private")
        post_data.update({
            "thread": thread,
            "ip": self.request.META.get("REMOTE_ADDR")
        })
        Post.objects.create_and_notify(**post_data)
        
        for user_name in subscribe_users:
            try:
                user = User.objects.get(username=user_name)
            except User.DoesNotExist:
                continue
            user.sb_watchlist.get_or_create(thread=thread)
                
        return thread


#     user = models.ForeignKey("auth.User", verbose_name=_('user'))
#     name = models.CharField(max_length=255, verbose_name=_('subject'))
#     slug = models.SlugField(max_length=255)
#     category = models.ForeignKey(Category, verbose_name=_('category'))
#     private = models.BooleanField(default=False, verbose_name=_('private'))
#     closed = models.BooleanField(default=False, verbose_name=_('closed'))
#     sticky = models.BooleanField(default=False, verbose_name=_('sticky'))
#     date = models.DateTimeField(verbose_name=_('date'), null=True)
