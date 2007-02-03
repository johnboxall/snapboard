from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

#from django.contrib.markup.templatetags.markup import textile
from django.template.defaultfilters import striptags

from forms import PostForm, ThreadForm
from models import Thread, Post, Category, WatchList, AbuseList
from templatetags.textile import textile


def rpc_post(request):
    show_id = int(request.GET['show'])
    orig_id = int(request.GET['orig'])
    post = Post.objects.get(pk=show_id)


    prev_id = ''
    rev_id = ''
    if post.revision is not None:
        rev_id = str(post.revision.id)
    if post.previous is not None:
        prev_id = str(post.previous.id)

    resp = {'text': textile(striptags(post.text)),
            'prev_id': prev_id,
            'rev_id': rev_id,
            }
    return HttpResponse(simplejson.dumps(resp), mimetype='application/javascript')


def rpc_lookup(request, queryset, field, limit=5):
    obj_list = []
    lookup = { '%s__icontains' % field: request.GET['query'],}
    for obj in queryset.filter(**lookup)[:limit]:
                obj_list.append({"id": obj.id, "name": getattr(obj, field)}) 
    object = {"ResultSet": { "total": str(limit), "Result": obj_list } }
    return HttpResponse(simplejson.dumps(object), mimetype='application/javascript')


def _toggle_boolean_field(object, field):
    '''
    Switches the a boolean value and returns the new value.
    object should be a Django Model
    '''
    setattr(object, field, (not getattr(object, field)))
    object.save()
    return getattr(object, field)


def rpc_csticky(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_csticky() requires "thread"')
    if _toggle_boolean_field(kwargs['thread'], 'csticky'):
        return {'link':'unset csticky', 'msg':'This thread is sticky in its category.'}
    else:
        return {'link':'set csticky', 'msg':'Removed thread from category sticky list'}


def rpc_gsticky(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_gsticky() requires "thread"')
    if _toggle_boolean_field(kwargs['thread'], 'gsticky'):
        return {'link':'unset gsticky', 'msg':'This thread is now globally sticky.'}
    else:
        return {'link':'set gsticky', 'msg':'Removed thread from global sticky list'}


def rpc_close(request, **kwargs):
    assert(request.user.is_staff)
    assert('thread' in kwargs, 'rpc_close() requires "thread"')
    if _toggle_boolean_field(kwargs['thread'], 'closed'):
        return {'link':'open thread', 'msg':'This discussion is now CLOSED.'}
    else:
        return {'link':'close thread', 'msg':'This discussion is now OPEN.'}


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
    if _toggle_boolean_field(kwargs['post'], 'censor'):
        return {'link':'uncensor', 'msg':'This post is censored!'}
    else:
        return {'link':'censor', 'msg':'This post is no longer censored.'}
# vim: ai ts=4 sts=4 et sw=4
