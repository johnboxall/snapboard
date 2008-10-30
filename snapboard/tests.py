from django.contrib.auth.models import User
from django.core.urlresolvers import reverse
from django.test import TestCase
from django.test.client import Client

from snapboard.models import *

class TestViews(TestCase):

	def setUp(self):
		self.john = User.objects.create_user('john', 'john@example.com', 'test')
		self.jane = User.objects.create_user('jane', 'jane@example.com', 'test')
	
	def test_new_post(self):
		gd = Category.objects.create(label='General discussion')
		c = Client()
		c.login(username='john', password='test')
		r = c.post(reverse('snapboard_new_thread', args=(gd.id,)),{
			'subject': 'Test topic',
			'post': 'Lorem ipsum dolor sit amet.',
		})
		self.assertRedirects(r, reverse('snapboard_thread', args=(1,)))

