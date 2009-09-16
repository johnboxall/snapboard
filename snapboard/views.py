import logging
import datetime

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect, Http404, HttpResponseServerError
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST

try:
    from notification import models as notification
except ImportError:
    notification = None

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
        
def render(template_name, context, request=None):
    context_instance = RequestContext(request, processors=extra_processors)
    return render_to_response(template_name, context, 
        context_instance=context_instance)

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

def get_user_settings(user):
    if not user.is_authenticated():
        return DEFAULT_USER_SETTINGS
    try:
        return user.sb_usersettings
    except UserSettings.DoesNotExist:
        return DEFAULT_USER_SETTINGS

def user_settings_context(request):
    return {'user_settings': get_user_settings(request.user)}

if USE_SNAPBOARD_LOGIN_FORM:
    from snapboard.forms import LoginForm
    def login_context(request):
        """
        All content pages that have additional content for authenticated users but
        that are also publicly viewable should have a login form in the side panel.
        """
        response_dict = {}
        if not request.user.is_authenticated():
            response_dict.update({
                    'login_form': LoginForm(),
                    })

        return response_dict
    extra_processors = [user_settings_context, login_context]
else:
    extra_processors = [user_settings_context]

def rpc(request, mimetype='application/javascript'):
    """
    Delegates simple rpc requests.
    """
    if not request.POST or not request.user.is_authenticated():
        return HttpResponseServerError()

    ctx = {}

    action = request.POST.get('action', '').lower()
    rpc_func = RPC_ACTION_MAP.get(action)
    if rpc_func is None:
        raise HttpResponseServerError()

    if action == 'quote':
        try:
            return HttpResponse(simplejson.dumps(rpc_func(request, oid=int(request.POST['oid']))))
        except (KeyError, ValueError):
            return HttpResponseServerError()

    # oclass_str will be used as a keyword in a function call, so it must
    # be a string, not a unicode object (changed since Django went
    # unicode). Thanks to Peter Sheats for catching this.
    oclass_str = str(request.POST.get('oclass', '').lower())
    oclass = RPC_OBJECT_MAP.get(oclass_str)
    if oclass is None:
        return HttpResponseServerError()

    try:
        oid = int(request.POST['oid'])
        forum_object = oclass.objects.get(pk=oid)
    except KeyError:
        return HttpResponseServerError()
    except oclass.DoesNotExist:
        return HttpResponseServerError()
    else:
        ctx.update(rpc_func(request, **{oclass_str: forum_object}))
        return HttpResponse(simplejson.dumps(ctx), mimetype=mimetype)


def thread(request, cslug, tslug, template="snapboard/thread.html"):
    thr = get_object_or_404(Thread.view_manager.filter(category__slug=cslug), slug=tslug)
    if not thr.category.can_read(request.user):
        raise PermissionError
    
    ctx = {}
    
    if request.user.is_authenticated():
        ctx.update({"watched": WatchList.objects.filter(user=request.user, thread=thr).count() != 0})
    
    if request.POST:
        if not thr.category.can_post(request.user):
            raise PermissionError
        
        postform = PostForm(request.POST, request=request)
        if postform.is_valid():
            postobj = postform.save(thr)
            return HttpResponseRedirect(reverse('snapboard_locate_post', args=(postobj.id,)))
    else:
        postform = PostForm(request=request)
    
    # Comes after the post so new messages show up.
    post_list = Post.view_manager.posts_for_thread(thr.id, request.user)
    if get_user_settings(request.user).reverse_posts:
        post_list = post_list.order_by('-odate')
    
    ctx.update({'posts': post_list, 'thr': thr, 'postform': postform})
    return render(template, ctx, request)

@require_POST
def edit_post(request, post_id):
    """
    Edit an existing post.decorators in python
    """
    orig_post = get_object_or_404(Post.view_manager, pk=post_id)
    if orig_post.user != request.user or not orig_post.thread.category.can_post(request.user):
        raise PermissionError
    
    postform = PostForm(request.POST, request=request)
    if postform.is_valid():
        post = postform.edit(orig_post)
        div_id_num = post.id
    else:
        div_id_num = orig_post.id
    
    try:
        next = request.POST['next'].split('#')[0] + '#snap_post' + str(div_id_num)
    except KeyError:
        next = reverse('snapboard_locate_post', args=(orig_post.id,))

    return HttpResponseRedirect(next)

@login_required
def new_thread(request, slug, template="snapboard/newthread.html"):
    cat = get_object_or_404(Category, slug=slug)
    if not cat.can_create_thread(request.user):
        raise PermissionError

    threadform = ThreadForm(request.POST or None, request=request)
    if threadform.is_valid():
        thread = threadform.save(cat)
        next = reverse('snapboard_thread', args=[thread.category.slug,
            thread.slug])
        return HttpResponseRedirect(next)
    
    return render(template, {"form": threadform}, request)

@login_required
def favorite_index(request, template="snapboard/thread_index.html"):
    """
    Shows the threads/discussions that have been marked as 'watched'
    by the user.
    """
    qs = Thread.view_manager.get_favorites(request.user)
    threads = [thr for thr in qs if thr.category.can_view(request.user)]
    ctx = {'title': _("Watched Discussions"), 'threads': threads}
    return render(template, ctx, request)

@login_required
def private_index(request, template="snapboard/thread_index.html"):
    qs = Thread.view_manager.get_private(request.user)
    threads = [thr for thr in qs if thr.category.can_read(request.user)]
    ctx = {
        'title': _("Discussions with private messages to you"),
        'threads': threads
    }
    return render(template, ctx, request)

def category_thread_index(request, slug, template="snapboard/thread_index.html"):
    cat = get_object_or_404(Category, slug=slug)
    if not cat.can_read(request.user):
        raise PermissionError
    
    threads = Thread.view_manager.get_category(cat.id)
    ctx = {
        'title': ''.join((_("Category: "), cat.label)), 
        'category': cat, 
        'threads': threads
    }
    return render(template, ctx, request)

def thread_index(request, template="snapboard/thread_index.html"):
    if request.user.is_authenticated():
        qs = Thread.view_manager.get_user_query_set(request.user)
    else:
        qs = Thread.view_manager.get_query_set()
    threads = [thr for thr in qs if thr.category.can_view(request.user)]
    ctx = {'title': _("Recent Discussions"), 'threads': threads}
    return render(template, ctx, request)

def locate_post(request, post_id):
    """
    Redirects to a post, given its ID.
    """
    post = get_object_or_404(Post, pk=post_id)
    if not post.thread.category.can_read(request.user):
        raise PermissionError
    if post.is_private and not (post.user == request.user or post.private.filter(pk=request.user.id).count()):
        raise PermissionError
    
    # Count the number of visible posts before the one we are looking for, 
    # as well as the total
    total = post.thread.count_posts(request.user)
    preceding_count = post.thread.count_posts(request.user, before=post.date)

    # Check the user's settings to locate the post in the various pages
    settings = get_user_settings(request.user)
    ppp = settings.ppp
    if total < ppp:
        page = 1
    elif settings.reverse_posts:
        page = (total - preceding_count - 1) // ppp + 1
    else:
        page = preceding_count // ppp + 1
    
    args = [post.thread.category.slug, post.thread.slug]
    path = reverse('snapboard_thread', args=args)
    next = '%s?page=%i#snap_post%i' % (path, page, post.id)
    return HttpResponseRedirect(next)

def category_index(request, template="snapboard/category_index.html"):
    qs = Category.objects.all()
    ctx = {'cat_list': [c for c in qs if c.can_view(request.user)]}
    return render(template, ctx, request)

@login_required
def edit_settings(request, template="snapboard/edit_settings.html"):
    """
    Allow user to edit his/her profile. Requires login.
    """
    userdata, _ = UserSettings.objects.get_or_create(user=request.user)
    data = request.POST or None
    form = UserSettingsForm(data, instance=userdata, request=request)
    if form.is_valid():
        form.save(commit=True)
        return HttpResponseRedirect("")
    return render(template, {"form": form}, request)


#@@@ Haven't looked at group functions.

#@@@
@login_required
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
        render_dict['pending_invitations'] = group.sb_invitation_set.filter(accepted=None)
    elif request.GET.get('answered_invitations', False):
        render_dict['answered_invitations'] = group.sb_invitation_set.exclude(accepted=None)
    return render_to_response(
            'snapboard/manage_group.html',
            render_dict,
            context_instance=RequestContext(request, processors=extra_processors))

#@@@
@login_required
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

#@@@
@login_required
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
            if notification:
                notification.send(
                    [user],
                    'group_admin_rights_removed',
                    {'group': group})
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

#@@@
@login_required
def grant_group_admin_rights(request, group_id):
    """
    Although the Group model allows non-members to be admins, this view won't 
    let it.
    """
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
            if notification:
                notification.send(
                    [user],
                    'group_admin_rights_granted',
                    {'group': group})
                notification.send(
                    list(group.admins.all()),
                    'new_group_admin',
                    {'new_admin': user, 'group': group})
    else:
        raise Http404
    return HttpResponse('ok')

#@@@
@login_required
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
    return HttpResponse('ok')

#@@@
@login_required
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
                if notification:
                    notification.send(
                        list(invitation.group.admins.all()),
                        'new_group_member',
                        {'new_member': request.user, 'group': invitation.group})
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

def _brand_view(func):
    """
    Mark a view as belonging to SNAPboard.

    Allows the UserBanMiddleware to limit the ban to SNAPboard in larger 
    projects.
    """
    setattr(func, '_snapboard', True)

_brand_view(rpc)
_brand_view(thread)
_brand_view(edit_post)
_brand_view(new_thread)
_brand_view(favorite_index)
_brand_view(private_index)
_brand_view(category_thread_index)
_brand_view(thread_index)
_brand_view(locate_post)
_brand_view(category_index)
_brand_view(edit_settings)
_brand_view(manage_group)
_brand_view(invite_user_to_group)
_brand_view(remove_user_from_group)
_brand_view(grant_group_admin_rights)
_brand_view(discard_invitation)
_brand_view(answer_invitation)