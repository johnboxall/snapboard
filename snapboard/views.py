from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.utils.translation import ugettext as _

from snapboard.forms import *
from snapboard.models import *
from snapboard.utils import *


# Ajax #########################################################################

@json_response
def preview(request):
    return {'preview': sanitize(request.raw_post_data)}

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

@login_required
@json_response
def edit(request):
    pk = request.POST.get("id")
    post = get_object_or_404(Post.objects.get_user_query_set(request.user), pk=pk)
#    import pdb;pdb.set_trace()
    form = PostForm(request.POST, request=request, instance=post)
    if form.is_valid():
        post = form.save()
        return {'preview': sanitize(post.text)}
    return dict(form.errors)

# Views ########################################################################

def category_list(request, template="snapboard/category_list.html"):
    ctx = {"categories": Category.objects.all()}    
    return render_and_cache(template, ctx, request)

def category(request, slug, template="snapboard/category.html"):
    category = get_object_or_404(Category, slug=slug)
    threads = category.thread_set.get_user_query_set(request.user)
    ctx = {'category': category, 'threads': threads}
    return render_and_cache(template, ctx, request)

# TODO: don't want sticky order here.
def thread_list(request, template="snapboard/thread_list.html"):
    threads = Thread.objects.get_user_query_set(request.user)
    return render_and_cache(template, {'threads': threads}, request)

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
        # TODO: select_related with null users can be bad :\
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
        threads = threads.filter(name__icontains=q)
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
def favorites(request, template="snapboard/favorites.html"):
    threads = Thread.objects.favorites(request.user)
    return render(template, {"threads": threads}, request)

@login_required
def edit_settings(request, template="snapboard/edit_settings.html"):
    settings, _ = UserSettings.objects.get_or_create(user=request.user)
    form = UserSettingsForm(request.POST or None, instance=settings, request=request)
    
    username_form = UserNameForm(request.POST or None, instance=request.user, request=request)
    if request.POST:
        are_forms_valid = False
        if form.is_valid() and username_form.is_valid():
            form.save()
            username_form.save()
            are_forms_valid = True
        if are_forms_valid:
            return HttpResponseRedirect("")
    return render(template, {"form": form, "username_form": username_form}, request)