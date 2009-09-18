import datetime

from django.conf import settings
# AJAX_REQURIED
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import (HttpResponse, HttpResponseRedirect, Http404, 
    HttpResponseServerError)
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils import simplejson
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST


from snapboard.forms import *
from snapboard.models import *
from snapboard.utils import *

try:
    from notification import models as notification
except ImportError:
    notification = None


# Ajax'd #######################################################################

def safe_int(s, default=None):
    try:
        return int(s)
    except ValueError:
        return default
        
#json_response ???

def json(view):
    def wrapper(*args, **kwargs):
        return JsonResponse(view(*args, **kwargs))
    return wrapper

# require_posts?
# @@@ STAFF REQUIRED IS NOT WHAT WE WANT WE NEED TO DEFINE OUR OWN THAT REIDRECTS SOEWHERE ELESZZ or that just returns an error in case shit goes shotoufsl


#@ajax_required
@json
def post_revision(request):
    show_id = safe_int(request.GET.get('show'))
    orig_id = safe_int(request.GET.get('orig'))
    post = get_object_or_404(Post, pk=show_id)
    if not post.thread.category.can_read(request.user):
        raise PermissionError

    rev_id = post.revision and str(post.revision.id) or ''
    prev_id = post.previous and str(post.previous.id) or ''
    return {'text': sanitize(post.text), 'prev_id': prev_id, 'rev_id': rev_id}

#@ajax_required
@json
def text_preview(request):
    return {'preview': sanitize(request.raw_post_data )}

#@ajax_required
@login_required
@json
def lookup(request, queryset, field, limit=5):
    # XXX We should probably restrict member (or other) lookups to registered users
    obj_list = []
    lookup = {'%s__icontains' % field: request.GET['query']}
    for obj in queryset.filter(**lookup)[:limit]:
        obj_list.append({"id": obj.id, "name": getattr(obj, field)}) 
    return JsonResponse({"ResultSet": {"total": str(limit), "Result": obj_list}})

#@ajax_required
@staff_member_required
@json
def category_sticky_thread(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("thread_id"))
    if toggle_boolean_field(thread, 'csticky'):
        return {'link':_('unset csticky'), 'msg':_('This thread is sticky in its category.')}
    else:
        return {'link':_('set csticky'), 'msg':_('Removed thread from category sticky list')}

#@ajax_required
@staff_member_required
@json
def global_sticky_thread(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("thread_id"))
    if toggle_boolean_field(thread, 'gsticky'):
        return {'link':_('unset gsticky'), 'msg':_('This thread is now globally sticky.')}
    else:
        return {'link':_('set gsticky'), 'msg':_('Removed thread from global sticky list')}

#@ajax_required
@staff_member_required
@json
def close_thread(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("thread_id"))
    if toggle_boolean_field(thread, 'closed'):
        return {'link':_('open thread'), 'msg':_('This discussion is now CLOSED.')}
    else:
        return {'link':_('close thread'), 'msg':_('This discussion is now OPEN.')}

#@ajax_required
@login_required
@json
def watch_thread(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("thread_id"))
    if not thr.category.can_read(request.user):
        raise PermissionError

    # If it exists watch it otherwise delete the watch.
    try:
        WatchList.objects.get(user=request.user, thread=thread).delete()
        return {'link':_('watch'),
                'msg':_('This thread has been removed from your favorites.')}
    except WatchList.DoesNotExist:
        WatchList.objects.create(user=request.user, thread=thread)
        return {'link':_('dont watch'),
                'msg':_('This thread has been added to your favorites.')}

@staff_member_required
@json
def report_post(request):
    post = get_object_or_404(Post, pk=request.POST.get("post_id"))
    AbuseReport.objects.get_or_create(submitter=request.user, post=post)
    return {'link': '', 'msg':_('The moderators have been notified of possible abuse')}

#@ajax_required
@staff_member_required
@json
def censor_post(request):
    post = get_object_or_404(Post, pk=request.POST.get("post_id"))
    if toggle_boolean_field(post, 'censor'):
        return {'link':_('uncensor'), 'msg':_('This post is censored!')}
    else:
        return {'link':_('censor'), 'msg':_('This post is no longer censored.')}

@json
def quote_post(request):
    post = get_object_or_404(Post.objects.selected_related(), pk=request.POST.get("post_id"))
    if not post.thread.category.can_read(request.user):
        raise PermissionError
    if post.is_private and post.user != request.user and not post.private.filter(id=request.user.id).count():
        raise PermissionDenied
    return {'text': post.text, 'author': unicode(post.user)}


# Views ########################################################################

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


#@@@ Haven't looked at group/invitation functions.

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

def _brand(iterable):
    """
    Mark an iterable of objects as belonging to SNAPboard.

    Allows the UserBanMiddleware to limit the ban to SNAPboard in larger 
    projects.
    """
    for obj in iterable:
        setattr(obj, '_snapboard', True)

_brand([
    post_revision, text_preview, lookup, category_sticky_thread, 
    global_sticky_thread, close_thread, watch_thread, censor_post, 
    report_post, quote_post, thread, edit_post, new_thread, favorite_index,
    private_index, category_thread_index, thread_index, locate_post,
    category_index, edit_settings, manage_group, invite_user_to_group, 
    remove_user_from_group, grant_group_admin_rights, discard_invitation,
    answer_invitation
])