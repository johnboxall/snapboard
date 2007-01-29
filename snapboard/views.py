from django.contrib.auth import decorators
from django.contrib.auth import login, logout
from django.core.paginator import ObjectPaginator, InvalidPage
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.views.generic.simple import redirect_to

from models import Thread, Post, Category, WatchList
from forms import PostForm, ThreadForm, LoginForm
from rpc import *

SB_LOGIN_URL = '/snapboard/signin'
TPP = 20                # (T)threads (P)er (P)age
PPP = 20                # P(osts) P(er) P(age)

RPC_OBJECT_MAP = {
        "thread": Thread,
        "post": Post,
        }

RPC_ACTION_MAP = {
        "censor": rpc_censor,
        "gsticky": rpc_gsticky,
        "csticky": rpc_csticky,
        "close": rpc_close,
        "abuse": rpc_abuse,
        "watch": rpc_watch,
        }

def login_context(request):
    response_dict = {}
    if not request.user.is_authenticated():
        response_dict.update({
                'login_form': LoginForm(),
                'login_next': request.META['PATH_INFO'],
                })

    return response_dict


# Create your views here.
def rpc(request):
    if not request.POST or not request.user.is_authenticated():
        return HttpResponseServerError

    response_dict = {}

    try:
        oclass_str =  request.POST['oclass'].lower()
        oclass = RPC_OBJECT_MAP[oclass_str]
    except KeyError:
        return HttpResponseServerError

    try:
        oid = int(request.POST['oid'])
        action = request.POST['action'].lower()

        forum_object = oclass.objects.get(pk=oid)

        rpc_func = RPC_ACTION_MAP[action]

        response_dict.update(rpc_func(request, **{oclass_str:forum_object}))
        return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')

    except oclass.DoesNotExist:
        return HttpResponseServerError
    except KeyError:
        return HttpResponseServerError
    except AssertionError:
        return HttpResponseServerError



def thread(request, thread_id, page="1"):
    # split results into pages
    page = int(page)        # indexed starting at 1
    pindex = page - 1       # indexed starting at 0

    try:
        thr = Thread.objects.get(pk=thread_id)
    except Thread.DoesNotExist:
        raise Http404

    render_dict = {}

    if request.user.is_authenticated():
        try:
            wl = WatchList.objects.get(user=request.user, thread=thr)
            print 'watched is true for', request.user, thr, wl
            render_dict.update({"watched":True})
        except WatchList.DoesNotExist:
            render_dict.update({"watched":False})

    if request.user.is_authenticated() and request.POST:
        postform = PostForm(request.POST.copy())

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

    # this must come after the post so new messages show up
    try:
        post_list = Post.objects.filter(thread=thr).order_by('odate').exclude(
                revision__isnull=False)

        # get any avatars
        extra_post_avatar = """
            SELECT avatar FROM snapboard_forumuserdata
                WHERE snapboard_forumuserdata.user_id = snapboard_post.user_id
            """
        post_list = post_list.extra( select = {
            'avatar': extra_post_avatar
            })

        if request.user.is_authenticated() and not request.user.is_staff:
            post_list = post_list.exclude(censor=True)

        paginator = ObjectPaginator(post_list, PPP)
        post_page = paginator.get_page(pindex)
    except InvalidPage:
        raise Http404

    # general info to render the page navigation (back/forward/etc)
    render_dict.update(paginate_context(paginator, page))


    render_dict.update({
            'thr': thr,
            'postform': postform,
            'post_page': post_page,
            'page_nav_urlbase': '/snapboard/threads/id/' + thread_id + '/',
            'page_nav_cssclass': 'thread_page_nav',
            })

    return render_to_response('snapboard/thread.html',
            render_dict,
            context_instance=RequestContext(request, processors=[login_context,]))


def paginate_context(paginator, page):
    pindex = page - 1
    page_next = None
    page_prev = None
    page_range = None
    if paginator.has_next_page(pindex):
        page_next = page + 1
    if paginator.has_previous_page(pindex):
        page_prev = page - 1
    if paginator.pages > 2:
        page_range = range(1, paginator.pages+1)

    return {
            'page': page,
            'page_total': paginator.pages,
            'page_next': page_next,
            'page_prev': page_prev,
            'page_range': page_range,
        }


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

        return HttpResponseRedirect('/snapboard/threads/id/'
                + str(orig_post.thread.id) + '/')
    else:
        return HttpResponseRedirect('/snapboard/threads/id/'
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
            return HttpResponseRedirect('/snapboard/threads/id/' + str(thread.id) + '/')
    else:
        threadform = ThreadForm()

    return render_to_response('snapboard/newthread.html',
            {
            'form': threadform,
            },
            context_instance=RequestContext(request, processors=[login_context,]))


def base_thread_queryset(qset=None):
    '''
    This generates a QuerySet containing Threads and additional data used in
    generating a web page with a listing of discussions.

    qset allows the caller to specify an initial queryset to work with.  If this
    is not set, all Threads will be returned.
    '''

    # number of posts in thread
    # censored threads don't count toward the total
    extra_post_count = """
        SELECT COUNT(*) FROM snapboard_post
            WHERE snapboard_post.thread_id = snapboard_thread.id
            AND snapboard_post.revision_id IS NULL
            AND NOT snapboard_post.censor
        """

    # figure out who started the population
    extra_starter = """
        SELECT username FROM auth_user
            WHERE auth_user.id = (SELECT user_id
                FROM snapboard_post WHERE snapboard_post.thread_id = snapboard_thread.id
                ORDER BY snapboard_post.date ASC
                LIMIT 1)
        """
    extra_last_poster = """
        SELECT username FROM auth_user
            WHERE auth_user.id = (SELECT user_id
                FROM snapboard_post WHERE snapboard_post.thread_id = snapboard_thread.id
                ORDER BY snapboard_post.date DESC
                LIMIT 1)
        """
    extra_last_updated = """
        SELECT date FROM snapboard_post 
            WHERE snapboard_post.thread_id = snapboard_thread.id
            ORDER BY date DESC LIMIT 1
        """

    if qset == None:
        qset = Thread.objects

    return qset.extra(
        select = {
            'post_count': extra_post_count,
            'starter': extra_starter,
            #'last_updated': extra_last_updated,  # bug: http://code.djangoproject.com/ticket/2210
            # the bug is that any extra columns must match their names
            # TODO: sorting on boolean fields is undefined in SQL theory
            'date': extra_last_updated,
            'last_poster': extra_last_poster,
        },).order_by('-gsticky', '-date')


@decorators.user_passes_test(lambda u: u.is_authenticated(), login_url=SB_LOGIN_URL)
def favorite_index(request, page=1):
    '''
    This page shows the threads/discussions that have been marked as 'watched'
    by the user.
    '''
    page = int(page)
    pindex = page - 1

    wl = WatchList.objects.filter(user=request.user)
    thread_list = base_thread_queryset(
            Thread.objects.filter(pk__in=[x.id for x in wl])
            ).order_by('-date')
    title = request.user.username + "'s Watched Discussions"

    render_dict = {'title': title}
    page_nav_urlbase = "/snapboard/favorites/"

    try:
        paginator = ObjectPaginator(thread_list, TPP)
        thread_page = paginator.get_page(pindex)
        render_dict.update(paginate_context(paginator, page))
    except InvalidPage:
        raise Http404


    render_dict.update({
            'thread_page': thread_page,
            'page_nav_urlbase': page_nav_urlbase,
            'page_nav_cssclass': 'index_page_nav',
            })

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=[login_context,]))


@decorators.user_passes_test(lambda u: u.is_authenticated(), login_url=SB_LOGIN_URL)
def private_index(request, page=1):
    pass


def thread_index(request, cat_id=None, page=1):
    page = int(page)
    pindex = page - 1

    render_dict = {}
    try:
        if cat_id is None:
            #thread_list = Thread.objects.all()
            thread_list = base_thread_queryset()
            title = "Recent Discussions"
        else:
            cat = Category.objects.get(pk=cat_id)
            thread_list = base_thread_queryset().filter(category=cat)
            title = ''.join(("Category: ", cat.label))
    except Category.DoesNotExist:
        raise Http404

    render_dict.update({
        'category': cat_id,
        'title': title
        })

    if cat_id:
        thread_list = thread_list.order_by('-csticky', '-date')


    try:
        paginator = ObjectPaginator(thread_list, TPP)
        thread_page = paginator.get_page(pindex)
        render_dict.update(paginate_context(paginator, page))
    except InvalidPage:
        raise Http404

    if cat_id:
        page_nav_urlbase = "/snapboard/threads/category/" + str(cat_id) + '/'
    else:
        page_nav_urlbase = "/snapboard/threads/"

    render_dict.update({
            'thread_page': thread_page,
            'page_nav_urlbase': page_nav_urlbase,
            'page_nav_cssclass': 'index_page_nav',
            })

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=[login_context,]))

def category_index(request):

    extra_post_count = """
        SELECT COUNT(*) FROM snapboard_thread
            WHERE snapboard_thread.category_id = snapboard_category.id
        """
    cat_list = Category.objects.all().extra(
        select = {'thread_count': extra_post_count},)

    return render_to_response('snapboard/category_index.html',
            {
            'cat_list': cat_list,
            },
            context_instance=RequestContext(request, processors=[login_context,]))


def signout(request):
    logout(request)
    referrer = request.META.get('HTTP_REFERER', '/')
    # Redirect to the same page we're on
    return redirect_to(request, referrer)


def signin(request):
    try:
        next = request.POST['next']
    except KeyError:
        try:
            next = request.GET['next']
        except KeyError:
            next = '/'

    if request.POST:
        form_data = request.POST.copy()
        form = LoginForm(form_data)

        if form.is_valid():
            user = form.user
            login(request, user)
            form = LoginForm()
            return redirect_to(request, next)
    else:
        form = LoginForm()

    return render_to_response('snapboard/signin.html',
        {
        'login_form': form,
        'login_next': next,
        })
