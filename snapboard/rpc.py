from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from models import Thread, Post, Category, WatchList, AbuseList
from forms import PostForm, ThreadForm


def rpc_post(request, **kwargs):
    assert('post' in kwargs, 'rpc_gsticky() requires "post"')
    post = kwargs['post']
    
    # TODO

    #"""
    #%s
    #This post has been revised. < previous] [next >
    #""" % (post.text)

    prev_id = ''
    rev_id = ''
    if post.revision is not None:
        rev_id = post.revision.id
    if post.previous is not None:
        prev_id = post.previous.id

    return {'text': post.text,
            'prev_id': prev_id,
            'rev_id': rev_id,
            }
    pass

def rpc_csticky(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_csticky() requires "thread"')
    thr = kwargs['thread']

    thr.csticky = (not thr.csticky)
    thr.save()
    if thr.csticky:
        return {'link':'unset csticky',
                'msg':'This thread is sticky in its category.',
                }
    else:
        return {'link':'set csticky',
                'msg':'Removed thread from category sticky list',
                }


def rpc_gsticky(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_gsticky() requires "thread"')
    thr = kwargs['thread']

    thr.gsticky = (not thr.gsticky)
    thr.save()
    if thr.gsticky:
        return {'link':'unset gsticky',
                'msg':'This thread is now globally sticky.',
                }
    else:
        return {'link':'set gsticky',
                'msg':'Removed thread from global sticky list',
                }

def rpc_close(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_close() requires "thread"')
    thr = kwargs['thread']

    thr.closed = (not thr.closed)
    thr.save()
    if thr.closed:
        return {'link':'open thread',
                'msg':'This discussion is now CLOSED.',
                }
    else:
        return {'link':'close thread',
                'msg':'This discussion is now OPEN.',
                }


def rpc_watch(request, **kwargs):
    assert('thread' in kwargs, 'rpc_gsticky() requires "thread"')
    thr = kwargs['thread']
    try:
        # it exists, stop watching it
        wl = WatchList.objects.get(user=request.user, thread=thr)
        wl.delete()
        return {'link':'watch',
                'msg':'You are no longer monitoring this thread.'}
    except WatchList.DoesNotExist:
        # create it
        wl = WatchList(user=request.user, thread=thr)
        wl.save()
        return {'link':'dont watch',
                'msg':'You are now monitoring this thread.'}


def rpc_abuse(request, **kwargs):
    # TODO: test this
    assert('post' in kwargs, 'rpc_gsticky() requires "post"')
    abuse = AbuseList.objects.get_or_create(
            submitter = request.user,
            post = kwargs['post'],
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
