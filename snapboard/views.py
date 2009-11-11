from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.core.urlresolvers import reverse
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _
from django.views.decorators.http import require_POST



from snapboard.forms import *
from snapboard.models import *
from snapboard.utils import *


# Ajax #########################################################################

@json_response
def preview(request):
    return {'preview': sanitize(request.raw_post_data )}

@staff_member_required
@json_response
def sticky(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("id"))
    if toggle_boolean_field(thread, 'sticky'):
        return {'link':_('unstick'), 'msg':_('This topic is sticky!')}
    else:
        return {'link':_('stick'), 'msg':_('This topic is not sticky.')}


@staff_member_required
@json_response
def close(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("id"))
    if toggle_boolean_field(thread, 'closed'):
        return {'link':_('open'), 'msg':_('This topic is closed.')}
    else:
        return {'link':_('close'), 'msg':_('This topic is open.')}

@login_required
@json_response
def watch(request):
    thread = get_object_or_404(Thread, pk=request.POST.get("id"))
    try:
        WatchList.objects.get(user=request.user, thread=thread).delete()
        return {'link':_('watch'), 'msg':_('This topic has been removed from your favorites.')}
    except WatchList.DoesNotExist:
        WatchList.objects.create(user=request.user, thread=thread)
        return {'link':_('dont watch'), 'msg':_('This topic has been added to your favorites.')}


# Views ########################################################################

# TODO: invalidate on new post
def category_list(request, template="snapboard/category_list.html"):
    ctx = {"categories": Category.objects.all()}    
    return render_and_cache(template, ctx, request)

# TODO: invalidate on any new post in this category.
def category(request, slug, template="snapboard/category.html"):
    category = get_object_or_404(Category, slug=slug)
    threads = category.thread_set.get_user_query_set(request.user)
    ctx = {'category': category, 'threads': threads}
    return render_and_cache(template, ctx, request)

# TODO: invalidate on any new post.
# TODO: don't want sticky order here.
def thread_list(request, template="snapboard/thread_list.html"):
    threads = Thread.objects.get_user_query_set(request.user)
    return render_and_cache(template, {'threads': threads}, request)

# TODO: cache
def thread(request, cslug, tslug, template="snapboard/thread.html"):
    thread = get_object_or_404(Thread.objects.filter(category__slug=cslug), slug=tslug)
    form = PostForm(request.POST or None, request=request)
    if form.is_valid():
        post = form.save(thread)
        return HttpResponseRedirect(post.get_url())
    
    ctx = {}
    
    if request.user.is_authenticated():
        ctx["watched"] = thread.watchlist_set.filter(user=request.user).count() != 0
    
    ctx.update({
        'posts': thread.post_set.all(), #select_related("user"), 
        'thread': thread, 
        'form': form,  
        'category': thread.category
    })
    return render_and_cache(template, ctx, request)

# TODO: Ghetto search alert!
# TODO: Should we be caching this?  
def search(request, template="snapboard/search.html"):
    threads = Thread.objects.get_user_query_set(request.user)
    q = request.GET.get("q")
    if q is not None:
        threads = threads.filter(name__contains=q)
    return render(template, {'threads': threads}, request)
    # return render_and_cache(template, {'threads': threads}, request)

@login_required
def new_thread(request, slug=None, template="snapboard/new_thread.html"):
    category = None
    if slug is not None:
        category = get_object_or_404(Category, slug=slug)
    form = ThreadForm(request.POST or None, request=request, category=category)
    if form.is_valid():
        thread = form.save()
        return HttpResponseRedirect(thread.get_url())
    return render(template, {"form": form, "category": category}, request)

@login_required
def favorites(request, template="snapboard/thread_list.html"):
    """Show watch topics and ones you created."""
    threads = Thread.objects.favorites(request.user)
    return render(template, {"threads": threads}, request)

@login_required
def edit_settings(request, template="snapboard/edit_settings.html"):
    """
    Allow user to edit his/her profile.
    """
    userdata, _ = UserSettings.objects.get_or_create(user=request.user)    
    form = UserSettingsForm(request.POST or None, instance=userdata, request=request)
    if form.is_valid():
        form.save()
        return HttpResponseRedirect("")
    return render(template, {"form": form}, request)