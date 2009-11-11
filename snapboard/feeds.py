from django.contrib.sites.models import Site
from django.contrib.syndication.feeds import Feed
from django.utils.translation import ugettext_lazy as _

from snapboard.models import Post


class LatestPosts(Feed):
    title = _('%s Latest Discussions') % Site.objects.get_current()
    link = "/"
    description = _("The latest contributions to discussions.")

    title_template = "snapboard/feeds/latest_title.html"
    description_template = "snapboard/feeds/latest_description.html"

    def items(self):
        # select_related_user?
        return Post.objects.filter(thread__private=False).order_by('-date')[:10]
        
    def item_pubdate(self, obj):
        return obj.date
        
    def item_author_name(self, obj):
        return obj.user.username