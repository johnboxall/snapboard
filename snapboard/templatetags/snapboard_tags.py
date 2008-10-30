# -*- coding: utf-8 -*-
'''
SNAPboard specific template tags.
'''
# TODO: moves tags in extras.py to this file
# This will prevent potential namespace conflicts with other applications

from django import template

register = template.Library()

def truncatechars(text, chars=200):
	if len(text) < chars:
		return text
	try:
		last_space = text.rindex(' ', 0, chars)
		if last_space < chars // 5:
			raise ValueError
	except ValueError:
		return text[:chars - 1] + u'…'
	else:
		return text[:last_space] + u'…'
register.filter(truncatechars)

