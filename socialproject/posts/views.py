import re
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from .forms import PostCreateForm, CommentForm, PostEditForm
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from django.utils.http import url_has_allowed_host_and_scheme
from users.models import Notification
# Create your views here.
from .models import Post, Comment, Bookmark

POSTS_PER_PAGE = 5


def _bookmarked_post_ids(request):
    if request.user.is_authenticated:
        return set(Bookmark.objects.filter(user=request.user).values_list('post_id', flat=True))
    return set()


@login_required
def post_create(request):
    if request.method == 'POST':
        form = PostCreateForm(data=request.POST, files=request.FILES)
        if form.is_valid():
            new_item = form.save(commit=False)
            new_item.user = request.user
            new_item.save()
            return redirect('feed')
    else:
        form = PostCreateForm()
    return render(request, 'posts/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user_id != request.user.id:
        return HttpResponseForbidden("You can only edit your own posts.")
    if request.method == 'POST':
        form = PostEditForm(data=request.POST, instance=post)
        if form.is_valid():
            form.save()
            return redirect('profile_detail', username=request.user.username)
    else:
        form = PostEditForm(instance=post)
    return render(request, 'posts/post_edit.html', {'form': form, 'post': post})


@login_required
@require_POST
def post_delete(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    if post.user_id != request.user.id:
        return HttpResponseForbidden("You can only delete your own posts.")
    post.delete()
    return redirect('profile_detail', username=request.user.username)


def hashtag_feed(request, tag):
    posts = Post.objects.filter(
        caption__iregex=r'(^|\s)#' + re.escape(tag) + r'(\s|$)')
    comment_form = CommentForm()
    return render(request, 'posts/hashtag_feed.html', {
        'posts': posts,
        'tag': tag,
        'comment_form': comment_form,
        'bookmarked_post_ids': _bookmarked_post_ids(request),
    })


@login_required
def bookmarks_list(request):
    posts = Post.objects.filter(bookmarked_by__user=request.user)
    comment_form = CommentForm()
    return render(request, 'posts/bookmarks.html', {
        'posts': posts,
        'comment_form': comment_form,
        'bookmarked_post_ids': _bookmarked_post_ids(request),
    })


def post_detail(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    comment_form = CommentForm()
    return render(request, 'posts/post_detail.html', {
        'post': post,
        'comment_form': comment_form,
        'bookmarked_post_ids': _bookmarked_post_ids(request),
    })


def feed(request):
    # Feed is viewable by guests (per spec: anyone can scroll the feed like
    # Facebook/Instagram). Only authenticated users can actually comment -
    # this is enforced server-side, not just hidden in the UI, since a
    # guest could otherwise POST directly to this view.
    if request.method == 'POST':
        if not request.user.is_authenticated:
            return HttpResponseForbidden('You must be logged in to comment.')
        comment_form = CommentForm(data=request.POST)
        if comment_form.is_valid():
            new_comment = comment_form.save(commit=False)
            post_id = request.POST.get('post_id')
            post = get_object_or_404(Post, id=post_id)
            new_comment.post = post
            new_comment.user = request.user
            new_comment.posted_by = request.user.username
            new_comment.save()
            if post.user_id != request.user.id:
                Notification.objects.create(
                    recipient=post.user, actor=request.user,
                    verb=Notification.COMMENT, post=post)
        # Send the user back to wherever they commented from (feed,
        # a hashtag page, or bookmarks) instead of always the main feed.
        # Validated so a spoofed Referer header can't be used as an open redirect.
        referer = request.META.get('HTTP_REFERER')
        if referer and url_has_allowed_host_and_scheme(
                referer, allowed_hosts={request.get_host()}, require_https=request.is_secure()):
            return redirect(referer)
        return redirect('feed')

    comment_form = CommentForm()
    all_posts = Post.objects.all()

    # AJAX infinite-scroll request: return just the rendered cards + paging
    # info as JSON, not a full HTML page.
    if request.GET.get('partial') == '1':
        page_number = request.GET.get('page', 1)
        paginator = Paginator(all_posts, POSTS_PER_PAGE)
        page_obj = paginator.get_page(page_number)
        html = render_to_string('posts/_posts_list.html', {
            'posts': page_obj,
            'comment_form': comment_form,
            'bookmarked_post_ids': _bookmarked_post_ids(request),
            'request': request,
        }, request=request)
        return JsonResponse({
            'html': html,
            'has_next': page_obj.has_next(),
            'next_page': page_obj.next_page_number() if page_obj.has_next() else None,
        })

    paginator = Paginator(all_posts, POSTS_PER_PAGE)
    page_obj = paginator.get_page(1)
    return render(request, 'posts/feed.html', {
        'posts': page_obj,
        'page_obj': page_obj,
        'logged_user': request.user,
        'comment_form': comment_form,
        'bookmarked_post_ids': _bookmarked_post_ids(request),
    })


@login_required
@require_POST
def like_post(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id)
    if post.liked_by.filter(id=request.user.id).exists():
        post.liked_by.remove(request.user)
        liked = False
    else:
        post.liked_by.add(request.user)
        liked = True
        if post.user_id != request.user.id:
            Notification.objects.create(
                recipient=post.user, actor=request.user,
                verb=Notification.LIKE, post=post)
    # Returns JSON so the front-end can update the like icon/count in place
    # instead of redirecting/reloading the whole feed (this was the "jumps
    # to top of page" bug).
    return JsonResponse({'liked': liked, 'like_count': post.like_count})


@login_required
@require_POST
def bookmark_toggle(request):
    post_id = request.POST.get('post_id')
    post = get_object_or_404(Post, id=post_id)
    existing = Bookmark.objects.filter(user=request.user, post=post)
    if existing.exists():
        existing.delete()
        bookmarked = False
    else:
        Bookmark.objects.create(user=request.user, post=post)
        bookmarked = True
    return JsonResponse({'bookmarked': bookmarked})


@login_required
@require_POST
def comment_edit(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user_id != request.user.id:
        return HttpResponseForbidden("You can only edit your own comments.")
    body = request.POST.get('body', '').strip()
    if body:
        comment.body = body
        comment.save()
    return JsonResponse({'body': comment.body})


@login_required
@require_POST
def comment_delete(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    if comment.user_id != request.user.id:
        return HttpResponseForbidden("You can only delete your own comments.")
    comment.delete()
    return JsonResponse({'deleted': True})