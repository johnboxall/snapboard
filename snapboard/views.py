# vim: ai ts=4 sts=4 et sw=4

from django import forms
from django.conf import settings
from django.contrib.auth import decorators
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _

from snapboard.forms import PostForm, ThreadForm, UserSettingsForm
from snapboard.models import *
from snapboard.rpc import *

DEFAULT_USER_SETTINGS  = UserSettings()

# USE_SNAPBOARD_LOGIN_FORM, USE_SNAPBOARD_SIGNIN should probably be removed
USE_SNAPBOARD_SIGNIN = getattr(settings, 'USE_SNAPBOARD_SIGNIN', False)
USE_SNAPBOARD_LOGIN_FORM = getattr(settings, 'USE_SNAPBOARD_LOGIN_FORM', False)

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
        "quote": rpc_quote,
        }

def snapboard_default_context(request):
    """
    Provides some default information for all templates.

    This should be added to the settings variable TEMPLATE_CONTEXT_PROCESSORS
    """
    return {
            'SNAP_MEDIA_PREFIX': SNAP_MEDIA_PREFIX,
            'SNAP_POST_FILTER': SNAP_POST_FILTER,
            'LOGIN_URL': settings.LOGIN_URL,
            'LOGOUT_URL': settings.LOGOUT_URL,
            }

def user_settings_context(request):
    return {'user_settings': get_user_settings(request.user)}

if USE_SNAPBOARD_LOGIN_FORM:
    from snapboard.forms import LoginForm
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
    extra_processors = [user_settings_context, login_context]
else:
    extra_processors = [user_settings_context]

def rpc(request):
    '''
    Delegates simple rpc requests.
    '''
    if not request.POST or not request.user.is_authenticated():
        return HttpResponseServerError()

    response_dict = {}

    try:
        action = request.POST['action'].lower()
        rpc_func = RPC_ACTION_MAP[action]
    except KeyError:
        raise HttpResponseServerError()

    if action == 'quote':
        try:
            return HttpResponse(simplejson.dumps(rpc_func(request, oid=int(request.POST['oid']))))
        except (KeyError, ValueError):
            return HttpResponseServerError()

    try:
        # oclass_str will be used as a keyword in a function call, so it must
        # be a string, not a unicode object (changed since Django went
        # unicode). Thanks to Peter Sheats for catching this.
        oclass_str =  str(request.POST['oclass'].lower())
        oclass = RPC_OBJECT_MAP[oclass_str]
    except KeyError:
        return HttpResponseServerError()

    try:
        oid = int(request.POST['oid'])

        forum_object = oclass.objects.get(pk=oid)

        response_dict.update(rpc_func(request, **{oclass_str:forum_object}))
        return HttpResponse(simplejson.dumps(response_dict), mimetype='application/javascript')

    except oclass.DoesNotExist:
        return HttpResponseServerError()
    except KeyError:
        return HttpResponseServerError()

def thread(request, thread_id):
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
                    text = postform.cleaned_data['post'],
                    #
                    )
            postobj.save() # this needs to happen before many-to-many private is assigned

            postobj.private = postform.cleaned_data['private']
            postobj.save()
            postform = PostForm()
    else:
        postform = PostForm()

    # this must come after the post so new messages show up
    post_list = Post.view_manager.posts_for_thread(thread_id, request.user)
    if get_user_settings(request.user).reverse_posts:
        post_list = post_list.order_by('-odate')

    render_dict.update({
            'posts': post_list,
            'thr': thr,
            'postform': postform,
            })
    
    return render_to_response('snapboard/thread.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

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
        
    if orig_post.user != request.user:
        raise Http404

    postform = PostForm(request.POST.copy())
    if postform.is_valid():
        # create the post
        post = Post(
                user = request.user,
                thread = orig_post.thread,
                text = postform.cleaned_data['post'],
                previous = orig_post,
                )
        post.save()
        post.private = orig_post.private.all()
        post.save()

        orig_post.revision = post
        orig_post.save()

        div_id_num = post.id
    else:
        div_id_num = orig_post.id

    try:
        next = request.POST['next'].split('#')[0] + '#snap_post' + str(div_id_num)
    except KeyError:
        next = reverse('snapboard_thread', args=(orig_post.thread.id,))

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
                    subject = threadform.cleaned_data['subject'],
                    category = Category.objects.get(pk=
                        threadform.cleaned_data['category']),
                    )
            thread.save()

            # create the post
            post = Post(
                    user = request.user,
                    thread = thread,
                    text = threadform.cleaned_data['post'],
                    )
            post.save()

            # redirect to new thread
            return HttpResponseRedirect(reverse('snapboard_thread', args=(thread.id,)))
    else:
        threadform = ThreadForm()

    return render_to_response('snapboard/newthread.html',
            {
            'form': threadform,
            },
            context_instance=RequestContext(request, processors=extra_processors))
new_thread = login_required(new_thread)


def favorite_index(request):
    '''
    This page shows the threads/discussions that have been marked as 'watched'
    by the user.
    '''
    thread_list = Thread.view_manager.get_favorites(request.user)

    render_dict = {'title': _("Watched Discussions"), 'threads': thread_list}

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
favorite_index = login_required(favorite_index)

def private_index(request):
    thread_list = Thread.view_manager.get_private(request.user)

    render_dict = {'title': _("Discussions with private messages to you"), 'threads': thread_list}

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
private_index = login_required(private_index)

def category_thread_index(request, cat_id):
    try:
        cat = Category.objects.get(pk=cat_id)
        thread_list = Thread.view_manager.get_category(cat_id)
        render_dict = ({'title': ''.join((_("Category: "), cat.label)), 'category': True, 'threads': thread_list})
    except Category.DoesNotExist:
        raise Http404
    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

def thread_index(request, cat_id=None):
    if request.user.is_authenticated():
        # filter on user prefs
        thread_list = Thread.view_manager.get_user_query_set(request.user)
    else:
        thread_list = Thread.view_manager.get_query_set()
    render_dict = {'title': _("Recent Discussions"), 'threads': thread_list}
    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

def category_index(request):
    return render_to_response('snapboard/category_index.html',
            {
            'cat_list': Category.objects.all(),
            },
            context_instance=RequestContext(request, processors=extra_processors))

def edit_settings(request):
    '''
    Allow user to edit his/her profile. Requires login.
    '''
    try:
        userdata = UserSettings.objects.get(user=request.user)
    except UserSettings.DoesNotExist:
        userdata = UserSettings.objects.create(user=request.user)
    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=userdata)
        if form.is_valid():
            form.save(commit=True)
    else:
        form = UserSettingsForm(instance=userdata)
    return render_to_response(
            'snapboard/edit_settings.html',
            {'form': form},
            context_instance=RequestContext(request, processors=extra_processors))
edit_settings = login_required(edit_settings)

def get_user_settings(user):
    if not user.is_authenticated():
        return DEFAULT_USER_SETTINGS
    try:
        return user.snapboard_usersettings
#       return UserSettings.objects.get(user=user)
    except UserSettings.DoesNotExist:
        return DEFAULT_USER_SETTINGS

def _brand_view(func):
    setattr(func, '_snapboard', True)

_brand_view(rpc)
_brand_view(thread)
_brand_view(edit_post)
_brand_view(new_thread)
_brand_view(favorite_index)
_brand_view(private_index)
_brand_view(category_thread_index)
_brand_view(thread_index)
_brand_view(category_index)
_brand_view(edit_settings)

# vim: ai ts=4 sts=4 et sw=4
