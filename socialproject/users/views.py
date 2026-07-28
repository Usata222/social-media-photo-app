from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.views.decorators.http import require_POST
from django.http import JsonResponse, HttpResponseForbidden
from django.db.models import Q
from .forms import LoginForm, UserRegistartionForm, UserEditForm, ProfileEditForm
from .models import Profile, Follow, Notification
from posts.models import Post
from django.contrib.auth import logout

def privacy(request):
    return render(request, 'users/privacy.html')


def terms(request):
    return render(request, 'users/terms.html')


def user_logout(request):
    logout(request)
    return redirect('login')

def user_login(request):
    if request.method == "POST":
        form = LoginForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            user = authenticate(request, username=data['username'], password=data['password'])
            if user is not None:
                login(request, user)
                return redirect('feed')
            else:
                return render(request, 'users/login.html', {'form': form, 'error': 'Invalid credentials'})
    else:
        form = LoginForm()
    return render(request, 'users/login.html', {'form': form})


@login_required
def index(request):
    return redirect('profile_detail', username=request.user.username)


def register(request):
    if request.method == 'POST':
        user_form = UserRegistartionForm(request.POST)
        if user_form.is_valid():
            new_user = user_form.save(commit=False)
            new_user.set_password(user_form.cleaned_data['password'])
            new_user.save()
            Profile.objects.create(user=new_user)
            return render(request, 'users/register_done.html')
    else:
        user_form = UserRegistartionForm()
    return render(request, 'users/register.html', {'user_form': user_form})


@login_required
def edit(request):
    if request.method == 'POST':
        user_form = UserEditForm(instance=request.user, data=request.POST)
        profile_form = ProfileEditForm(
            instance=request.user.profile, data=request.POST, files=request.FILES)
        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('edit')
    else:
        user_form = UserEditForm(instance=request.user)
        profile_form = ProfileEditForm(instance=request.user.profile)
    return render(request, 'users/edit.html', {'user_form': user_form, 'profile_form': profile_form})


def profile_detail(request, username):
    profile_user = get_object_or_404(User, username=username)
    posts = Post.objects.filter(user=profile_user)
    is_following = False
    if request.user.is_authenticated and request.user != profile_user:
        is_following = Follow.objects.filter(
            follower=request.user, followed=profile_user).exists()
    return render(request, 'users/profile_detail.html', {
        'profile_user': profile_user,
        'posts': posts,
        'is_following': is_following,
    })


@login_required
@require_POST
def follow_toggle(request, username):
    target = get_object_or_404(User, username=username)
    if target == request.user:
        return HttpResponseForbidden("You can't follow yourself.")
    existing = Follow.objects.filter(follower=request.user, followed=target)
    if existing.exists():
        existing.delete()
        following = False
    else:
        Follow.objects.create(follower=request.user, followed=target)
        Notification.objects.create(
            recipient=target, actor=request.user, verb=Notification.FOLLOW)
        following = True
    return JsonResponse({
        'following': following,
        'followers_count': target.followers.count(),
    })


def followers_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    followers = User.objects.filter(following__followed=profile_user)
    return render(request, 'users/follow_list.html', {
        'profile_user': profile_user, 'users_list': followers, 'list_type': 'Followers',
    })


def following_list(request, username):
    profile_user = get_object_or_404(User, username=username)
    following = User.objects.filter(followers__follower=profile_user)
    return render(request, 'users/follow_list.html', {
        'profile_user': profile_user, 'users_list': following, 'list_type': 'Following',
    })


def search_users(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query)
        )[:25]
    return render(request, 'users/search.html', {'query': query, 'results': results})


@login_required
def notifications_list(request):
    notes = request.user.notifications.select_related('actor', 'post').all()[:50]
    request.user.notifications.filter(is_read=False).update(is_read=True)
    return render(request, 'users/notifications.html', {'notifications': notes})
