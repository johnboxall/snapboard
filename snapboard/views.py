import logging
import datetime

from django import forms
from django.conf import settings
from django.contrib.auth import decorators
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _

from snapboard.forms import *
from snapboard.models import *
from snapboard.rpc import *

_log = logging.getLogger('snapboard.views')

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

    if not thr.category.can_read(request.user):
        raise PermissionError

    render_dict = {}

    if request.user.is_authenticated():
        render_dict.update({"watched": WatchList.objects.filter(user=request.user, thread=thr).count() != 0})

    if request.POST:
        if not thr.category.can_post(request.user):
            raise PermissionError
        postform = PostForm(request.POST.copy()) # XXX Do we need to copy the dict?

        if postform.is_valid():
            # reset post object
            postobj = Post(thread = thr,
                    user = request.user,
                    text = postform.cleaned_data['post'],
                    )
            postobj.save() # this needs to happen before many-to-many private is assigned

            if len(postform.cleaned_data['private']) > 0:
                _log.debug('thread(): new post private = %s' % postform.cleaned_data['private'])
                postobj.private = postform.cleaned_data['private']
                postobj.save()
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
    if not request.POST:
        raise Http404

    try:
        orig_post = Post.view_manager.get(pk=int(original))
    except Post.DoesNotExist:
        raise Http404
        
    if orig_post.user != request.user or not orig_post.thread.category.can_post(request.user):
        raise PermissionError

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
def new_thread(request, cat_id):
    '''
    Start a new discussion.
    '''
    category = get_object_or_404(Category, pk=cat_id)
    if not category.can_create_thread(request.user):
        raise PermissionError

    if request.POST:
        threadform= ThreadForm(request.POST.copy())
        if threadform.is_valid():
            # create the thread
            thread = Thread(
                    subject = threadform.cleaned_data['subject'],
                    category = category,
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
    thread_list = [thr for thr in Thread.view_manager.get_private(request.user) if thr.category.can_read(request.user)]

    render_dict = {'title': _("Discussions with private messages to you"), 'threads': thread_list}

    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
private_index = login_required(private_index)

def category_thread_index(request, cat_id):
    try:
        cat = Category.objects.get(pk=cat_id)
        if not cat.can_read(request.user):
            raise PermissionError
        thread_list = Thread.view_manager.get_category(cat_id)
        render_dict = ({'title': ''.join((_("Category: "), cat.label)), 'category': cat, 'threads': thread_list})
    except Category.DoesNotExist:
        raise Http404
    return render_to_response('snapboard/thread_index.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

def thread_index(request):
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
            'cat_list': [c for c in Category.objects.all() if c.can_view(request.user)],
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
        form = UserSettingsForm(request.POST, instance=userdata, user=request.user)
        if form.is_valid():
            form.save(commit=True)
    else:
        form = UserSettingsForm(instance=userdata, user=request.user)
    return render_to_response(
            'snapboard/edit_settings.html',
            {'form': form},
            context_instance=RequestContext(request, processors=extra_processors))
edit_settings = login_required(edit_settings)

def manage_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    render_dict = {'group': group, 'invitation_form': InviteForm()}
    if request.GET.get('manage_users', False):
        render_dict['users'] = group.users.all()
    elif request.GET.get('manage_admins', False):
        render_dict['admins'] = group.admins.all()
    elif request.GET.get('pending_invitations', False):
        render_dict['pending_invitations'] = group.snapboard_invitation_set.filter(accepted=None)
    elif request.GET.get('answered_invitations', False):
        render_dict['answered_invitations'] = group.snapboard_invitation_set.exclude(accepted=None)
    return render_to_response(
            'snapboard/manage_group.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))
manage_group = login_required(manage_group)

def invite_user_to_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    if request.method == 'POST':
        form = InviteForm(request.POST)
        if form.is_valid():
            invitee = form.cleaned_data['user']
            if group.has_user(invitee):
                invitation = None
                request.user.message_set.create(message=_('The user %s is already a member of this group.') % invitee)
            else:
                invitation = Invitation.objects.create(
                        group=group,
                        sent_by=request.user,
                        sent_to=invitee)
                request.user.message_set.create(message=_('A invitation to join this group was sent to %s.') % invitee)
            return render_to_response('snapboard/invite_user.html',
                    {'invitation': invitation, 'form': InviteForm(), 'group': group},
                    context_instance=RequestContext(request, processors=extra_processors))
    else:
        form = InviteForm()
    return render_to_response('snapboard/invite_user.html',
            {'form': form, 'group': group},
            context_instance=RequestContext(request, processors=extra_processors))
invite_user_to_group = login_required(invite_user_to_group)

def remove_user_from_group(request, group_id):
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    if request.method == 'POST':
        done = False
        user = User.objects.get(pk=int(request.POST.get('user_id', 0)))
        only_admin = int(request.POST.get('only_admin', 0))
        if not only_admin and group.has_user(user):
            group.users.remove(user)
            done = True
        if group.has_admin(user):
            group.admins.remove(user)
            done = True
        if done:
            if only_admin:
                request.user.message_set.create(message=_('The admin rights of user %s were removed for the group.') % user)
            else:
                request.user.message_set.create(message=_('User %s was removed from the group.') % user)
        else:
            request.user.message_set.create(message=_('There was nothing to do for user %s.') % user)
    else:
        raise Http404
    return HttpResponse('ok')
remove_user_from_group = login_required(remove_user_from_group)

def grant_group_admin_rights(request, group_id):
    '''
    Although the Group model allows non-members to be admins, this view won't 
    let it.
    '''
    group = get_object_or_404(Group, pk=group_id)
    if not group.has_admin(request.user):
        raise PermissionError
    if request.method == 'POST':
        user = User.objects.get(pk=int(request.POST.get('user_id', 0)))
        if not group.has_user(user):
            request.user.message_set.create(message=_('The user %s is not a group member.') % user)
        elif group.has_admin(user):
            request.user.message_set.create(message=_('The user %s is already a group admin.') % user)
        else:
            group.admins.add(user)
            request.user.message_set.create(message=_('The user %s is now a group admin.') % user)
    else:
        raise Http404
    return HttpResponse('ok')#HttpResponseRedirect(reverse('snapboard_manage_group', args=(group_id,)))
grant_group_admin_rights = login_required(grant_group_admin_rights)

def discard_invitation(request, invitation_id):
    if not request.method == 'POST':
        raise Http404
    invitation = get_object_or_404(Invitation, pk=invitation_id)
    if not invitation.group.has_admin(request.user):
        raise PermissionError
    was_pending = invitation.accepted is not None
    invitation.delete()
    if was_pending:
        request.user.message_set.create(message=_('The invitation was cancelled.'))
    else:
        request.user.message_set.create(message=_('The invitation was discarded.'))
    return HttpResponse('ok')#HttpResponseRedirect(reverse('snapboard_manage_group', args=(invitation.group.id,)))
discard_invitation = login_required(discard_invitation)

def answer_invitation(request, invitation_id):
    invitation = get_object_or_404(Invitation, pk=invitation_id)
    if request.user != invitation.sent_to:
        raise Http404
    form = None
    if request.method == 'POST':
        if invitation.accepted is not None:
            return HttpResponseRedirect('')
        form = AnwserInvitationForm(request.POST)
        if form.is_valid():
            if int(form.cleaned_data['decision']):
                invitation.group.users.add(request.user)
                invitation.accepted = True
                request.user.message_set.create(message=_('You are now a member of the group %s.') % invitation.group.name)
            else:
                invitation.accepted = False
                request.user.message_set.create(message=_('The invitation has been declined.'))
            invitation.response_date = datetime.datetime.now()
            invitation.save()
    elif invitation.accepted is None:
        form = AnwserInvitationForm()
    return render_to_response('snapboard/invitation.html',
            {'form': form, 'invitation': invitation},
            context_instance=RequestContext(request, processors=extra_processors))
answer_invitation = login_required(answer_invitation)

def get_user_settings(user):
    if not user.is_authenticated():
        return DEFAULT_USER_SETTINGS
    try:
        return user.snapboard_usersettings
#       return UserSettings.objects.get(user=user)
    except UserSettings.DoesNotExist:
        return DEFAULT_USER_SETTINGS

def _brand_view(func):
    '''
    Mark a view as belonging to SNAPboard.

    Allows the UserBanMiddleware to limit the ban to SNAPboard in larger 
    projects.
    '''
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
_brand_view(manage_group)
_brand_view(invite_user_to_group)
_brand_view(remove_user_from_group)
_brand_view(grant_group_admin_rights)
_brand_view(discard_invitation)
_brand_view(answer_invitation)

# vim: ai ts=4 sts=4 et sw=4
