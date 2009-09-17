from django.contrib.sites.models import Site
from django.contrib.syndication.feeds import Feed
from django.utils.translation import ugettext_lazy as _

from snapboard.models import Post


SITE = Site.objects.get_current()

class LatestPosts(Feed):
    title = _('%s Latest Discussions') % str(SITE)
    link = "/snapboard/"
    description = _("The latest contributions to discussions.")

    title_template = "snapboard/feeds/latest_title.html"
    description_template = "snapboard/feeds/latest_description.html"

    def items(self):
        qs = Post.objects.filter(is_private=False).order_by('-date')[:10]
        return [p for p in qs if p.thread.category.can_read(self.request.user)]