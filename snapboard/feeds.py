from django.contrib.syndication.feeds import Feed
from models import Post

class LatestPosts(Feed):
    title = "Latest Posts"
    link = "/snapboard/"
    description = "The latest contributions to discussions."

    title_template = "snapboard/feeds/latest_title.html"
    description_template = "snapboard/feeds/latest_description.html"

    def items(self):
        return Post.objects.order_by('-date')[:10]
# vim: ai ts=4 sts=4 et sw=4
