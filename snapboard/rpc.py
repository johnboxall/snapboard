from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from models import Thread, Post, Category, WatchList
from forms import PostForm, ThreadForm


def rpc_csticky(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_csticky() requires "thread"')
    thr = kwargs['thread']

    thr.csticky = (not thr.csticky)
    thr.save()
    if thr.csticky:
        return {'link':'unset csticky',
                'msg':'Removed thread from category sticky list',
                }
    else:
        return {'link':'set csticky',
                'msg':'This thread is sticky in its category.',
                }


def rpc_gsticky(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_gsticky() requires "thread"')
    thr = kwargs['thread']

    thr.gsticky = (not thr.gsticky)
    thr.save()
    if thr.gsticky:
        return {'link':'unset gsticky',
                'msg':'Removed thread from global sticky list',
                }
    else:
        return {'link':'set gsticky',
                'msg':'This thread is now globally sticky.',
                }


def rpc_watch(request, **kwargs):
    assert('thread' in kwargs, 'rpc_gsticky() requires "thread"')
    try:
        # it exists, stop watching it
        wl = WatchList.objects.get(user=request.user, thread=thr)
        wl.delete()
        return {'link':'watch'}
    except WatchList.DoesNotExist:
        # create it
        wl = WatchList(user=request.user, thread=thr)
        wl.save()
        return {'link':'dont watch'}


def rpc_abuse(request, **kwargs):
    # TODO: test this
    assert('post' in kwargs, 'rpc_gsticky() requires "post"')
    abuse = AbuseList.objects.get_or_create(
            user = request.user,
            post_id__exact = int(kwargs['post'])
            )
    return {'link': '',
            'msg':'The moderators have been notified of possible abuse'}


def rpc_censor(request, **kwargs):
    assert(request.user.is_staff)
    assert('post' in kwargs, 'rpc_gsticky() requires "post"')
    post = kwargs['post']

    post.censor = (not post.censor)
    post.save()
    if post.censor:
        return {'link':'uncensor',
                'msg':'This post is censored!',
                }
    else:
        return {'link':'censor',
                'msg':'This post is no longer censored.',
                }
