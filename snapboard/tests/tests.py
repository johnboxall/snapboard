import os

from django.conf import settings
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.contrib.auth.models import User

from snapboard.urls import feeds


# TODO: Well these are now good now.

class ViewsTest(TestCase):
    urls = "snapboard.tests.test_urls"
    fixtures = ["test_data"]
    template_dirs = [
        os.path.join(os.path.dirname(__file__), '../templates'),
    ]
    
    def setUp(self):
        self.old_snap_post_filter = settings.SNAP_POST_FILTER
        settings.SNAP_POST_FILTER = "markdown"
        self.old_template_dir = settings.TEMPLATE_DIRS
        settings.TEMPLATE_DIRS = self.template_dirs        
        self.user = User.objects.create_user(username="test", email="test@example.com", password="!")
        self.admin = User.objects.create_superuser(username="admin", email="admin@example.com", password="!") 
        
    def assertJSON(self, name, expected, klass="thread", pk=1, username="test"):
        self.client.login(username=username, password="!")    
        uri = reverse("snapboard_%s" % name)
        r = self.client.post(uri, {"%s_id" % klass: pk})
        self.assertEquals(r.content, expected)
    
    def tearDown(self):
        settings.TEMPLATE_DIRS = self.old_template_dir
        settings.SNAP_POST_FILTER = self.old_snap_post_filter
    
    def test_thread_index(self):
        uri = reverse("snapboard_index")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread_index.html")
     
    def test_thread(self):
        kwargs = {"cslug": "category", "tslug": "thread"}
        uri = reverse("snapboard_thread", kwargs=kwargs)
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread.html")
                
        # Creating a post eventually redirects to it.
        self.client.login(username="test", password="!")
        r = self.client.post(uri, {"subject": "subject", "post": "post"})
        expected_uri = reverse('snapboard_locate_post', args=[3])
        self.assertRedirects(r, expected_uri, target_status_code=302)
            
    def test_edit_post(self):
        self.client.login(username="test", password="!")
        uri = reverse("snapboard_edit_post", args=[2])
        r = self.client.post(uri, {"post": "update"})
        expected_uri = reverse('snapboard_locate_post', args=[2])
        self.assertRedirects(r, expected_uri, target_status_code=302)
    
    def test_new_thread(self):
        self.client.login(username="test", password="!")
        
        uri = reverse("snapboard_new_thread", kwargs={"slug": "category"})
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/newthread.html")
                
        r = self.client.post(uri, {"subject": "test-thread", "post": "post"})
        expected_uri = reverse('snapboard_thread', args=["category", "test-thread"])
        self.assertRedirects(r, expected_uri)
        
    def test_favorite_index(self):
        self.client.login(username="test", password="!")
        uri = reverse("snapboard_favorite_index")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread_index.html")
    
    def test_private_index(self):
        self.client.login(username="test", password="!")
        uri = reverse("snapboard_favorite_index")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread_index.html")
    
    def test_category_thread_index(self):
        uri = reverse("snapboard_category_thread_index", kwargs={"slug": "category"})
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/thread_index.html")
            
    def test_locate_post(self):
        uri = reverse("snapboard_locate_post", kwargs={"post_id": "1"})
        r = self.client.get(uri)
        path = reverse('snapboard_thread', args=["category", "thread"])
        expected_uri = "%s?page=1#snap_post1" % path
        self.assertRedirects(r, expected_uri)

    def test_category_index(self):
        uri = reverse("snapboard_category_index")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/category_index.html")
     
    def test_edit_settings(self):
        self.client.login(username="test", password="!")
        
        uri = reverse("snapboard_edit_settings")
        r = self.client.get(uri)
        self.assertTemplateUsed(r, "snapboard/edit_settings.html")
        
        data = {"ppp": 5, "tpp": 5, "reverse_posts": True, "frontpage_filters": 1}
        r = self.client.post(uri, data)
        self.assertRedirects(r, uri)
    
    def test_feeds(self):
        for feed in feeds.keys():
            uri = reverse("snapboard_feeds", args=[feed])
            r = self.client.get(uri)
            self.assertEquals(r.status_code, 200)
    
    def test_js18n(self):
        uri = reverse("snapboard_js_i18n")
        r = self.client.get(uri)
        self.assertEquals(r.status_code, 200)
    
    def test_post_revision(self):        
        self.client.login(username="test", password="!")
        path = reverse("snapboard_post_revision")
        uri = "%s?orig=2&show=1" % path
        r = self.client.get(uri)
        expected = '{"text": "\\n<p>text\\n</p>\\n\\n\\n", "prev_id": "", "rev_id": ""}'
        self.assertEquals(r.content, expected)
    
    def test_text_preview(self):
        uri = reverse("snapboard_text_preview")
        r = self.client.get(uri)
        expected = '{"preview": "\\n\\n\\n"}'
        self.assertEquals(r.content, expected)
    
    # def test_user_lookup(self):
    #    path = reverse("snapboard_user_lookup")
    #    uri = "%s?query=test" % path
    #    r = self.client.get(uri)
    #    expected = '{"ResultSet": {"total": "5", "Result": [{"id": 1, "name": "test"}]}}'
    #    self.assertEquals(r.content, expected)
        
    def test_censor_post(self):
        # self.assertJSON("censor_post", "<h1>Permission denied</h1>")
        expected = '{"msg": "This post is censored!", "link": "uncensor"}'
        self.assertJSON("censor_post", expected, username="admin", klass="post")
    
    def test_global_sticky_thread(self):
        # self.assertJSON("gsticky", "<h1>Permission denied</h1>")
        expected = '{"msg": "This thread is now globally sticky.", "link": "unset gsticky"}'
        self.assertJSON("global_sticky_thread", expected, username="admin")
    
    def test_category_sticky_thread(self):
        # self.assertJSON("category_sticky_thread", "<h1>Permission denied</h1>")
        expected = '{"msg": "This thread is sticky in its category.", "link": "unset csticky"}'
        self.assertJSON("category_sticky_thread", expected, username="admin")
    
    def test_close_thread(self):
        # self.assertJSON("close_thread", "<h1>Permission denied</h1>")
        expected = '{"msg": "This discussion is now CLOSED.", "link": "open thread"}'
        self.assertJSON("close_thread", expected, username="admin")

    def test_report_post(self):
        expected = '{"msg": "The moderators have been notified of possible abuse", "link": ""}'
        self.assertJSON("report_post", expected, klass="post")

    def test_watch_thread(self):
        expected = '{"msg": "This thread has been added to your favorites.", "link": "dont watch"}'
        self.assertJSON("watch_thread", expected)

    def test_quote_post(self):
        self.assertJSON("quote_post", '{"text": "text", "author": "test"}')


 
    # def test_manage_group(self):
    #     pass
    # 
    # def test_invite_user_to_group(self):
    #     pass
    # 
    # def test_remove_user_from_group(self):
    #     pass
    # 
    # def test_grant_group_admin_rights(self):
    #     pass
    # 
    # def test_discard_invitation(self):
    #     pass
    # 
    # def test_answer_invitation(self):
    #     pass



# from unittest import TestSuite
# 
# from django.contrib.auth.models import User, AnonymousUser
# from django.core.urlresolvers import reverse
# from django.test import TestCase
# from django.test.client import Client
# 
# from snapboard.models import *
# 
# class TestBasicViews(TestCase):
# 	'''
# 	Tests the board's basic views, that deal with categories, threads and 
# 	posts. User settings and group administration are excluded.
# 	'''
# 
# 	def setUp(self):
# 		self.john = User.objects.create_user('john', 'john@example.com', 'test')
# 		self.jane = User.objects.create_user('jane', 'jane@example.com', 'test')
# 	
# 	def test_new_post(self):
# 		gd = Category.objects.create(label='General discussion')
# 		c = Client()
# 		c.login(username='john', password='test')
# 		r = c.post(reverse('snapboard_new_thread', args=(gd.id,)),{
# 			'subject': 'Test topic',
# 			'post': 'Lorem ipsum dolor sit amet.',
# 		})
# 		self.assertRedirects(r, reverse('snapboard_thread', args=(1,)))
# 	
# class TestCategoryPermissions(TestCase):
# 	'''
# 	Tests that the specified permissions are honored.
# 
# 	This DOES NOT test that the Category.can_xxx() methods do what they should.
# 	It only tests that the views use these methods correctly.
# 	'''
# 	
# 	def __init__(self, user, view_perms, read_perms, post_perms, new_thread_perms, view_group=[], read_group=[], post_group=[], new_thread_group=[]):
# 		self.view_perms, self.read_perms, self.post_perms, \
# 		self.new_thread_perms, self.view_group, self.read_group,\
# 		self.post_group, self.new_thread_group = view_perms, \
# 		read_perms, post_perms, new_thread_perms, \
# 		view_group, read_group, post_group, \
# 		new_thread_group
# 		self.password = 'test'
# 		self.test_user = user
# 		TestCase.__init__(self)
# 
# 	def setUp(self):
# 		# Save the users, create the groups, create the category
# 		for user in self.view_group + self.read_group + self.post_group + self.new_thread_group:
# 			if not user.pk:
# 				user.save()
# 		if not isinstance(self.test_user, AnonymousUser):
# 			self.test_user.set_password(self.password)
# 			self.test_user.save()
# 		self.super_user = User(username='super', email='root@example.com', password='')
# 		self.super_user.set_password(self.password)
# 		self.super_user.save()
# 		def _create_group(group):
# 			gobj = Group.objects.create(name='group')
# 			for user in group:
# 				gobj.users.add(user)
# 			return gobj
# 		self.view_group = _create_group(self.view_group)
# 		self.read_group = _create_group(self.read_group)
# 		self.post_group = _create_group(self.post_group)
# 		self.new_thread_group = _create_group(self.new_thread_group)
# 		self.category = Category.objects.create(label='category', view_perms=self.view_perms, read_perms=self.read_perms,
# 				post_perms=self.post_perms, new_thread_perms=self.new_thread_perms, view_group=self.view_group, read_group=self.read_group,
# 				post_group=self.post_group, new_thread_group=self.new_thread_group)
# 		sample_thread = Thread.objects.create(
# 				subject='Test',
# 				category=self.category)
# 		first_post = Post.objects.create(
# 				user=self.super_user,
# 				thread=sample_thread,
# 				text='Lorem ipsum dolor sit amet.')
# 
# 	def shortDescription(self):
# 		return u'Tests permissions of a category with permissions %s/%s/%s/%s and groups %s/%s/%s/%s.' % (
# 				self.category.get_view_perms_display(),
# 				self.category.get_read_perms_display(),
# 				self.category.get_post_perms_display(),
# 				self.category.get_new_thread_perms_display(),
# 				list(self.category.view_group.users.all()),
# 				list(self.category.read_group.users.all()),
# 				list(self.category.post_group.users.all()),
# 				list(self.category.new_thread_group.users.all()))
# 
# 	def runTest(self):
# 		c = Client()
# 		user = self.test_user
# 		thread_id = None
# 		post_id = None
# 		if not isinstance(user, AnonymousUser):
# 			self.failUnless(c.login(username=user.username, password=self.password))
# 		# Create a new thread
# 		r = c.post(reverse('snapboard_new_thread', args=(self.category.id,)),{
# 			'subject': 'Test topic',
# 			'post': 'Lorem ipsum dolor sit amet.',
# 		})
# 		if self.category.can_create_thread(user):
# 			thread_id = Post.objects.all().order_by('-pk')[0].id
# 			self.assertRedirects(r,
# 				reverse('snapboard_thread', args=(thread_id,)),
# 				target_status_code=200 if self.category.can_read(user) else 403)
# 		else:
# 			if isinstance(user, AnonymousUser):
# 				self.assertRedirects(r,
# 					'%s?next=%s' % (
# 						reverse('auth_login'),
# 						reverse('snapboard_new_thread', args=(self.category.id,))))
# 			else:
# 				self.failUnlessEqual(r.status_code, 403)
# 		# Add a post; there is a sample thread already in case the thread was not created
# 		if not thread_id:
# 			thread_id = Post.objects.all().order_by('-pk')[0].id
# 		r = c.post(reverse('snapboard_thread', args=(thread_id,)),{
# 			'post': 'Testing.',
# 			'private': '',
# 		})
# 		post_id = Post.objects.all().order_by('-pk')[0].id
# 		if self.category.can_post(user):
# 			self.assertRedirects(r,
# 				reverse('snapboard_locate_post', args=(post_id,)),
# 				target_status_code=302 if self.category.can_read(user) else 403)
# 		else:
# 			self.failUnlessEqual(r.status_code, 403) # forbidden
# 		# Quote a post
# 		r = c.post(reverse('snapboard_rpc_action'), {
# 			'action': 'quote',
# 			'oid': str(post_id),
# 		})
# 		if isinstance(user, AnonymousUser):
# 			self.assert_(r.status_code in (500, 403))
# 		else:
# 			self.failUnlessEqual(r.status_code, 200 if self.category.can_read(user) else 403)
# 
# def permutations(seq, k):
# 	if not len(seq):
# 		yield seq
# 	elif k == 1:
# 		for i in seq:
# 			yield [i]
# 	else:
# 		for i in seq:
# 			for tail in permutations(seq, k-1):
# 				yield [i] + tail
# 
# def suite():
# 	suite = TestSuite()
# 	suite.addTest(TestBasicViews('test_new_post'))
# 	# Test all sensible permission configurations
# 	jane = User(username='jane', email='jane@example.com', password='')
# 	john = User(username='john', email='john@example.com', password='')
# 	perms = (NOBODY, ALL, USERS, CUSTOM)
# 	groups = [[jane],] * 4
# 	for permissions in [p for p in permutations(perms, 4) if sorted(p, reverse=True) == p]:
# 		suite.addTest(TestCategoryPermissions(jane, *(permissions + groups)))
# 		suite.addTest(TestCategoryPermissions(john, *(permissions + groups)))
# 		suite.addTest(TestCategoryPermissions(AnonymousUser(), *(permissions + groups)))
# 	return suite
# 
# 
