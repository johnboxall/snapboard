from django.core.exceptions import PermissionDenied
from django.http import HttpResponse
from django.template.defaultfilters import striptags
from django.utils import simplejson
from django.utils.translation import ugettext as _

from snapboard.models import Post, WatchList, AbuseReport, PermissionError
from snapboard.templatetags.extras import render_filter


def _sanitize(text):
    return render_filter(striptags(text), "safe")

def _toggle_boolean_field(obj, field):
    '''
    Switches the a boolean value and returns the new value.
    object should be a Django Model
    '''
    setattr(obj, field, (not getattr(obj, field)))
    object.save()
    return getattr(obj, field)
    
def JsonResponse(obj):
    return HttpResponse(simplejson.dumps(obj), mimetype='application/javascript')


def rpc_post(request):
    show_id = int(request.GET['show'])
    orig_id = int(request.GET['orig'])
    post = Post.objects.get(pk=show_id)
    if not post.thread.category.can_read(request.user):
        raise PermissionError

    prev_id = ''
    rev_id = ''
    if post.revision is not None:
        rev_id = str(post.revision.id)
    if post.previous is not None:
        prev_id = str(post.previous.id)

    return JsonResponse({
        'text': _sanitize(post.text),
        'prev_id': prev_id,
        'rev_id': rev_id,
    })

def rpc_preview(request):
    return JsonResponse({'preview': _sanitize(request.raw_post_data )})

def rpc_lookup(request, queryset, field, limit=5):
    # XXX We should probably restrict member (or other) lookups to registered users
    obj_list = []
    lookup = {'%s__icontains' % field: request.GET['query']}
    for obj in queryset.filter(**lookup)[:limit]:
        obj_list.append({"id": obj.id, "name": getattr(obj, field)}) 
    return JsonResponse({"ResultSet": { "total": str(limit), "Result": obj_list } })

def rpc_csticky(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['thread'], 'csticky'):
        return {'link':_('unset csticky'), 'msg':_('This thread is sticky in its category.')}
    else:
        return {'link':_('set csticky'), 'msg':_('Removed thread from category sticky list')}

def rpc_gsticky(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['thread'], 'gsticky'):
        return {'link':_('unset gsticky'), 'msg':_('This thread is now globally sticky.')}
    else:
        return {'link':_('set gsticky'), 'msg':_('Removed thread from global sticky list')}

def rpc_close(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['thread'], 'closed'):
        return {'link':_('open thread'), 'msg':_('This discussion is now CLOSED.')}
    else:
        return {'link':_('close thread'), 'msg':_('This discussion is now OPEN.')}

def rpc_watch(request, **kwargs):
    thr = kwargs['thread']
    if not thr.category.can_read(request.user):
        raise PermissionError
    try:
        # it exists, stop watching it
        WatchList.objects.get(user=request.user, thread=thr).delete()
        return {'link':_('watch'),
                'msg':_('This thread has been removed from your favorites.')}
    except WatchList.DoesNotExist:
        # create it
        WatchList.objects.create(user=request.user, thread=thr)
        return {'link':_('dont watch'),
                'msg':_('This thread has been added to your favorites.')}

def rpc_abuse(request, **kwargs):
    # TODO: test this
    AbuseReport.objects.get_or_create(submitter=request.user, post=kwargs['post'])
    return {'link': '',
            'msg':_('The moderators have been notified of possible abuse')}

def rpc_censor(request, **kwargs):
    if not request.user.is_staff:
        raise PermissionDenied
    if _toggle_boolean_field(kwargs['post'], 'censor'):
        return {'link':_('uncensor'), 'msg':_('This post is censored!')}
    else:
        return {'link':_('censor'), 'msg':_('This post is no longer censored.')}

def rpc_quote(request, **kwargs):
    post = Post.objects.select_related().get(pk=kwargs['oid'])
    if not post.thread.category.can_read(request.user):
        raise PermissionError
    if post.is_private and post.user != request.user and not post.private.filter(id=request.user.id).count():
        raise PermissionDenied
    return {'text': post.text, 'author': unicode(post.user)}