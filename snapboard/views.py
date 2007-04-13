# vim: ai ts=4 sts=4 et sw=4

from django import newforms as forms
from django.contrib.auth import decorators
from django.contrib.auth import login, logout
from django.core.paginator import ObjectPaginator, InvalidPage
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.views.generic.simple import redirect_to


#from models import Thread, Post, Category, WatchList
from models import *
from forms import PostForm, ThreadForm, LoginForm
from rpc import *


COOKIE_SNAP_PROFILE_KEY = 'SnapboardProfile'
DEFAULT_SNAPBOARD_PROFILE  = SnapboardProfile()

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


def _userdata(request, var):
    '''
    Try to get an attribute of the SnapboardProfile for a certain user.
    This function should not be called from outside snapboard views.

    If the setting was found, this function returns the default value.

    If 'var' is not the name of a field of SnapboardProfile, a KeyError
    will be raised.
    '''
    if not request.user.is_authenticated():
        return getattr(DEFAULT_SNAPBOARD_PROFILE, var)

    # profile dictionary
    pdict = request.session.get(COOKIE_SNAP_PROFILE_KEY, {})

    if var in pdict:
        return pdict[var]
    else:
        try:
            sp = SnapboardProfile.objects.get(user=request.user)
        except SnapboardProfile.DoesNotExist:
            sp = DEFAULT_SNAPBOARD_PROFILE
        pdict[var] = getattr(sp, var)
        request.session[COOKIE_SNAP_PROFILE_KEY] = pdict

    return pdict[var]


def snapboard_default_context(request):
    """
    Provides some default information for all templates.

    This should be added to the settings variable TEMPLATE_CONTEXT_PROCESSORS
    """
    return {
            'SNAP_PREFIX': SNAP_PREFIX,
            'SNAP_MEDIA_PREFIX': SNAP_MEDIA_PREFIX,
            }


def snapboard_require_signin(f):
    '''
    Equivalent to @login_required decorator, except that it defines a custom
    template path for login.
    '''
    return decorators.user_passes_test(
            lambda u: u.is_authenticated(),
            login_url = SNAP_LOGIN_URL
            )(f)


def login_context(request):
    '''
    All content pages that have additional content for authenticated users but
    that are also publicly viewable should have a login form in the side panel.
    '''
    response_dict = {}
    if not request.user.is_authenticated():
        response_dict.update({
                'login_form': LoginForm(),
                })

    return response_dict


def paginate_context(request, model, urlbase, object_list, page, **kwargs):
    '''
    Helper function to make standard pagination available for the template
    "snapboard/page_navigation.html"
    '''
    page = int(page)
    pindex = page - 1
    page_next = None
    page_prev = None
    page_range = None

    paginator = ObjectPaginator(object_list, _userdata(request, 'tpp'))
    try:
        object_page = paginator.get_page(pindex)
    except InvalidPage:
        raise InvalidPage

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
            model.__name__.lower() + '_page': object_page,
            'page_nav_urlbase': urlbase,
        }


# Create your views here.
def rpc(request):
    '''
    Delegates simple rpc requests.
    '''
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


def thread(request, thread_id, page=1):
    try:
        thr = Thread.view_manager.get(pk=thread_id)
    except Thread.DoesNotExist:
        raise Http404

    render_dict = {}

    if request.user.is_authenticated():
        try:
            wl = WatchList.objects.get(user=request.user, thread=thr)
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
                    #
                    )
            postobj.save() # this needs to happen before many-to-many private is assigned

            postobj.private = postform.clean_data['private']
            postobj.save()
            print postobj.private
            postform = PostForm()
    else:
        postform = PostForm()

    # this must come after the post so new messages show up
    post_list = Post.view_manager.posts_for_thread(thread_id, request.user)


    try:
        render_dict.update(paginate_context(request, Post,
            SNAP_PREFIX + '/threads/id/' + thread_id + '/',
            post_list,
            page,
            ))
    except InvalidPage:
        return HttpResponseRedirect(SNAP_PREFIX + '/threads/id/' + str(thread_id) + '/')

    render_dict.update({
            'thr': thr,
            'postform': postform,
            })
    
    return render_to_response('snapboard/thread.html',
            render_dict,
            context_instance=RequestContext(request, processors=[login_context,]))


def edit_post(request, original, next=None):
    '''
    Edit an existing post.decorators in python
    '''
    if not request.user.is_authenticated() or not request.POST:
        raise Http404

    try:
        orig_post = Post.view_manager.get(pk=int(original))
    except Post.DoesNotExist:
        raise Http404


    postform = PostForm(request.POST.copy())
    if postform.is_valid():
        # create the post
        post = Post(
                user = request.user,
                thread = orig_post.thread,
                private = orig_post.private,
                text = postform.clean_data['post'],
                previous = orig_post,
                )
        post.save()

        orig_post.revision = post
        orig_post.save()

        div_id_num = post.id
    else:
        div_id_num = orig_post.id

    try:
        next = request.POST['next'].split('#')[0] + '#snap_post' + str(div_id_num)
    except KeyError:
        next = SNAP_PREFIX + '/threads/id/' + str(orig_post.thread.id) + '/'

    return HttpResponseRedirect(next)

##
# Should new discussions be allowed to be private?  Leaning toward no.
def new_thread(request):
    '''
    Start a new discussion.
    '''

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
                    )
            post.save()

            # redirect to new thread
            return HttpResponseRedirect(SNAP_PREFIX + '/threads/id/' + str(thread.id) + '/')
    else:
        threadform = ThreadForm()

    return render_to_response('snapboard/newthread.html',
            {
            'form': threadform,
            },
            context_instance=RequestContext(request, processors=[login_context,]))
new_thread = snapboard_require_signin(new_thread)


def favorite_index(request, page=1):
    '''
    This page shows the threads/discussions that have been marked as 'watched'
    by the user.
    '''
    thread_list = Thread.view_manager.get_favorites(request.user)

    render_dict = {'title': request.user.username + "'s Watched Discussions"}

    try:
        render_dict.update(paginate_context(request, Thread,
            SNAP_PREFIX + "/favorites/",
            thread_list,
            page,
            ))
    except InvalidPage:
        return HttpResponseRedirect(SNAP_PREFIX + '/categories')

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request))
favorite_index = snapboard_require_signin(favorite_index)


def private_index(request, page=1):
    thread_list = Thread.view_manager.get_private(request.user)

    render_dict = {'title': "Discussions with private messages to you"}

    try:
        render_dict.update(paginate_context(request, Thread,
            SNAP_PREFIX + "/private/", # urlbase
            thread_list,
            page,
            ))
    except InvalidPage:
        return HttpResponseRedirect(SNAP_PREFIX + '/categories')

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request))
private_index = snapboard_require_signin(private_index)


def thread_category_index(request, cat_id, page=1):
    try:
        cat = Category.objects.get(pk=cat_id)
        thread_list = Thread.view_manager.get_category(cat_id)
        render_dict = paginate_context(request, Thread,
            SNAP_PREFIX + "/threads/category/" + str(cat_id) + '/',
            thread_list,
            page)
        render_dict.update({'title': ''.join(("Category: ", cat.label))})
    except Category.DoesNotExist:
        raise Http404
    except InvalidPage:
        return HttpResponseRedirect(SNAP_PREFIX + '/threads/')
    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=[login_context,]))



def thread_index(request, cat_id=None, page=1):
    render_dict = {'title': "Recent Discussions"}
    if request.user.is_authenticated():
        # filter on user prefs
        thread_list = Thread.view_manager.get_user_query_set(request.user)
    else:
        thread_list = Thread.view_manager.get_query_set()

    try:
        render_dict.update(paginate_context(request, Thread,
            SNAP_PREFIX + "/threads/",
            thread_list,
            page))
    except InvalidPage:
        return HttpResponseRedirect(SNAP_PREFIX + '/threads/')

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=[login_context,]))

def category_index(request):
    return render_to_response('snapboard/category_index.html',
            {
            'cat_list': Category.objects.all(),
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
            next = SNAP_PREFIX

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
        },
        context_instance=RequestContext(request))


def profile(request, next=SNAP_PREFIX):
    '''
    Allow user to edit his/her profile.  Requires login.

    There are several newforms bugs that affect this.  See
        http://code.google.com/p/snapboard/issues/detail?id=7

    We'll use generic views to get around this for now.
    '''
    if COOKIE_SNAP_PROFILE_KEY in request.session:
        # reset any cookie variables
        request.session[COOKIE_SNAP_PROFILE_KEY] = {}
    
    try:
        userdata = SnapboardProfile.objects.get(user=request.user)
    except:
        userdata = SnapboardProfile(user=request.user)
        userdata.save()
    print dir(RequestContext(request).dicts)
    from django.views.generic.create_update import update_object
    return update_object(request,
            model=SnapboardProfile, object_id=userdata.id,
            template_name='snapboard/profile.html',
            post_save_redirect=next
            )
profile = snapboard_require_signin(profile)

# vim: ai ts=4 sts=4 et sw=4
