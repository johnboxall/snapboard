import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core import mail
from django.core.urlresolvers import reverse
from django.test import TestCase

from snapboard.urls import feeds
from snapboard.models import *
from snapboard.utils import *


class ViewsTest(TestCase):
    urls = "snapboard.tests.test_urls"
    fixtures = ["test_data.json"]
#     template_dirs = [
#         os.path.join(os.path.dirname(__file__), '../templates'),
#     ]
    
#     def setUp(self):
#         self.old_snap_post_filter = settings.SNAP_POST_FILTER
#         settings.SNAP_POST_FILTER = "markdown"
#         self.old_template_dir = settings.TEMPLATE_DIRS
#         settings.TEMPLATE_DIRS = self.template_dirs        
#         self.user = User.objects.create_user(username="test", email="test@example.com", password="!")
#         self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="!") 
        
#     
#     def tearDown(self):
#         settings.TEMPLATE_DIRS = self.old_template_dir
#         settings.SNAP_POST_FILTER = self.old_snap_post_filter
#     

    # Helpers ##################################################################

    def login(self):
        self.client.login(username="test", password="!")

    def assertJSON(self, name, expected=None, pk=1, post=None):
        self.login()
        uri = reverse("sb_%s" % name)
        if post is None:
            post = {"id": pk}
        r = self.client.post(uri, post)
        
        if expected is not None:
            self.assertEquals(r.content, expected)
        else:
            self.assertEquals(r.status_code, 200)


    # Tests ####################################################################

    def test_preview(self):
       self.assertJSON("preview")
    
    def test_sticky(self):
        self.assertJSON("sticky")

    def test_close(self):
        self.assertJSON("close")

    def test_watch(self):
        self.assertJSON("watch")
    
    def test_edit(self):
        self.assertJSON("edit")

    def test_category_list(self):
        uri = reverse("sb_category_list")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/category_list.html")

    def test_category(self):
        uri = reverse("sb_category", kwargs={"slug": "category"})
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/category.html")

    def test_thread_list(self):
        uri = reverse("sb_thread_list")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread_list.html")
    
    def test_thread(self):
        uri = reverse("sb_thread", kwargs={"cslug": "category", "tslug": "thread"})
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread.html")
        
        # Log in to create a post.
        self.login()

        # Creating a post redirects to the new post.
        r = self.client.post(uri, {"subject": "subject", "post": "post"})
        new_post = Post.objects.order_by("-date")[0]
        expected_uri = new_post.get_url()
        self.assertRedirects(r, expected_uri)
        
    def test_search(self):
        uri = "%s?q=thread" % reverse("sb_search")
        self.client.login(username="test", password="!")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/search.html")
        
    def test_new_thread(self):
        # Log in to create a thread.
        self.login()

        uri = reverse("sb_new_thread", args=["category"])
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/new_thread.html")
        
        # Creating a thread redirects to the new thread.
        r = self.client.post(uri, {"subject": "subject", "post": "post"})
        new_thread = Thread.objects.order_by("-date")[0]
        expected_uri = new_thread.get_url()
        self.assertRedirects(r, expected_uri)

    def test_favorites(self):
        # Login to see favs.
        self.login()    
        uri = reverse("sb_favorites")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/favorites.html")
    
    def test_edit_settings(self):
        # Login to edit settings.
        self.login()
        uri = reverse("sb_edit_settings")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/edit_settings.html")

    def test_feeds(self):
        for feed in feeds.keys():
            uri = reverse("sb_feeds", args=[feed])
            r = self.client.get(uri)
            self.assertEquals(r.status_code, 200)
    
    def test_thread_slug(self):
        # No problems with dupe slugs right? There is a existing thread w/ slug "thread"
        self.login()
        uri = reverse("sb_new_thread", args=["category"])        
        r = self.client.post(uri, {"subject": "thread", "post": "post"})
        new_thread = Thread.objects.order_by("-date")[0]
        self.assertEquals(new_thread.slug, "thread-1")
        

class ThreadTest(TestCase):
    fixtures = ["test_data.json"]

    def test_get_notify_recipients(self):
        # should just return a set of the admins
        r = Thread.objects.get(pk=1).get_notify_recipients()
        self.assertEquals(r, set([t[1] for t in settings.ADMINS]))
        
        
class UtilsTest(TestCase):
    def test_bcc_mail(self):
        recipient_list = ["to@example.com"]
        bcc_mail("subj", "body", "from@example.com", recipient_list)
        self.assertEquals(len(mail.outbox), 1)
        self.assertEquals(mail.outbox[0].to, [])
        self.assertEquals(mail.outbox[0].bcc, recipient_list)