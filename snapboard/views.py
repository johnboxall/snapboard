from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
#from django.template import Context, loader
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson

from models import Thread, Post, Category, WatchList
from forms import PostForm, ThreadForm
from rpc import *


RPC_OBJECT_MAP = {
        "thread": Thread,
        "post": Post,
        }

RPC_ACTION_MAP = {
        "censor": rpc_censor,
        "gsticky": rpc_gsticky,
        "csticky": rpc_csticky,
        "abuse": rpc_abuse,
        }


# Create your views here.
def rpc(request):
    if not request.POST or not request.user.is_authenticated():
        return HttpResponseServerError

    response_dict = {}

    try:
        oid = int(request.POST['oid'])
        oclass = RPC_OBJECT_MAP[request.POST['oclass'].lower()]
        action = request.POST['action'].lower()

        forum_oject = oclass.objects.get(pk=oid)

        rpc_func = RPC_ACTION_MAP[action]

        return rpc_func(request, **{oclass:forum_object})

    except oclass.DoesNotExist:
        return HttpResponseServerError
    except KeyError:
        return HttpResponseServerError
    except AssertionError:
        return HttpResponseServerError

    return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')


def thread(request, thread_id):
    # return HttpResponse("You're looking at thread %s." % thread_id)
    try:
        thr = Thread.objects.get(pk=thread_id)
    except Thread.DoesNotExist:
        raise Http404

    render_dict = {}

    post_list = Post.objects.filter(thread=thr).order_by('-date').exclude(
            revision__isnull=False)

    if request.user.is_authenticated() and request.POST:
        postform = PostForm(request.POST.copy())

        try:
            wl = WatchList.objects.get(user=request.user, thread=thr)
            render_dict.update({"watched":True})
        except WatchList.DoesNotExist:
            pass

        if postform.is_valid():
            # reset post object
            postobj = Post(thread = thr,
                    user = request.user,
                    text = postform.clean_data['post'],
                    ip = request.META.get('REMOTE_ADDR', ''))
            postobj.save()
            postform = PostForm()
    else:
        postform = PostForm()

    render_dict.update({
            'thr': thr,
            'post_list': post_list,
            'postform': postform,
            })

    return render_to_response('thread.html',
            render_dict,
            context_instance = RequestContext(request))


def edit_post(request, original):
    '''
    Edit an original post.
    '''
    if not request.user.is_authenticated() or not request.POST:
        raise Http404

    try:
        orig_post = Post.objects.get(pk=int(original))
    except Post.DoesNotExist:
        raise Http404

    postform = PostForm(request.POST.copy())
    if postform.is_valid():
        # create the post
        post = Post(
                user = request.user,
                thread = orig_post.thread,
                text = postform.clean_data['post'],
                ip = request.META.get('REMOTE_ADDR', ''),
                previous = orig_post,
                )
        post.save()

        orig_post.revision = post
        orig_post.save()

        return HttpResponseRedirect('/forum/threads/id/'
                + str(orig_post.thread.id) + '/')
    else:
        return HttpResponseRedirect('/forum/threads/id/'
                + str(orig_post.thread.id) + '/')



def new_thread(request):
    if request.user.is_authenticated() and request.POST:
        threadform= ThreadForm(request.POST.copy())
        if threadform.is_valid():
            # create the thread
            thread = Thread(
                    subject = threadform.clean_data['subject'],
                    category = Category.objects.get(pk=
                        threadform.clean_data['category']),
                    )
            thread.save()

            # create the post
            post = Post(
                    user = request.user,
                    thread = thread,
                    text = threadform.clean_data['post'],
                    ip = request.META.get('REMOTE_ADDR', ''),
                    )
            post.save()

            # redirect to new thread
            return HttpResponseRedirect('/forum/threads/id/' + str(thread.id) + '/')
    else:
        threadform = ThreadForm()

    return render_to_response('newthread.html',
            {
            'form': threadform,
            },
            context_instance = RequestContext(request))


def thread_index(request, cat_id=None):
    if cat_id is None:
        thread_list = Thread.objects.all()
        page_title = "Recent Discussions"
    else:
        cat = Category.objects.get(pk=cat_id)
        thread_list = Thread.objects.filter(category=cat)
        page_title = ''.join(("Category: ", cat.label))

    # number of posts in thread
    extra_post_count = """
        SELECT COUNT(*) FROM forum_post
            WHERE forum_post.thread_id = forum_thread.id
            AND forum_post.revision_id IS NULL
        """
    # figure out who started the population
    extra_starter = """
        SELECT username FROM auth_user
            WHERE auth_user.id = (SELECT user_id
                FROM forum_post WHERE forum_post.thread_id = forum_thread.id
                ORDER BY forum_post.date ASC
                LIMIT 1)
        """
    extra_last_poster = """
        SELECT username FROM auth_user
            WHERE auth_user.id = (SELECT user_id
                FROM forum_post WHERE forum_post.thread_id = forum_thread.id
                ORDER BY forum_post.date DESC
                LIMIT 1)
        """
    extra_last_updated = """
        SELECT date FROM forum_post 
            WHERE forum_post.thread_id = forum_thread.id
            ORDER BY date DESC LIMIT 1
        """

    thread_list = thread_list.extra(
        select = {
            'post_count': extra_post_count,
            'starter': extra_starter,
            #'last_updated': extra_last_updated,  # bug: http://code.djangoproject.com/ticket/2210
            'date': extra_last_updated,
            'last_poster': extra_last_poster,
        },).order_by('-csticky', '-date')

    if cat_id:
        thread_list = thread_list.order_by('-gsticky', '-date')

    # the bug is that any extra columns must match their names
    # TODO: sorting on boolean fields is undefined in SQL theory

    return render_to_response('thread_index.html',
            {
            'thread_list': thread_list,
            'page_title': page_title,
            'category': cat_id,
            },
            context_instance = RequestContext(request))

def category_index(request):

    extra_post_count = """
        SELECT COUNT(*) FROM forum_thread
            WHERE forum_thread.category_id = forum_category.id
        """
    cat_list = Category.objects.all().extra(
        select = {'thread_count': extra_post_count},)

    return render_to_response('category_index.html',
            {
            'cat_list': cat_list,
            },
            context_instance = RequestContext(request))
