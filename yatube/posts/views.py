from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.views.decorators.cache import cache_page

from .forms import PostForm, CommentForm
from .models import Post, Group, User, Follow
from .utils import paginate

NUM_MAX: int = 10


@cache_page(20, key_prefix='index_page')
def index(request):
    post_list = Post.objects.all()
    page_obj = paginate(request, post_list)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    page_obj = paginate(request, posts_list)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    fullname = User.objects.get(username=username)
    post_list = Post.objects.filter(author=fullname)
    page_obj = paginate(request, post_list)
    if request.user.is_authenticated:
        follow = Follow.objects.filter(
            user=request.user, author=fullname
        ).exists()
    else:
        follow = False
    context = {
        'page_obj': page_obj,
        'fullname': fullname,
        'follow': follow
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    post = Post.objects.get(id=post_id)
    comments = post.comments.all
    context = {
        'page_obj': post,
        'comments': comments,
        'form': CommentForm()
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST or None,
                        files=request.FILES or None)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', request.user)
    else:
        form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if post_id and request.user != post.author:
        return redirect("posts:post_detail", post_id=post_id)
    form = PostForm(request.POST or None,
                    instance=post,
                    files=request.FILES or None)
    if form.is_valid():
        form.save()
        return redirect("posts:post_detail", post_id=post_id)
    else:
        form = PostForm(instance=post)
        context = {'form': form, 'is_edit': True, 'post': post, }
        return render(request, 'posts/create_post.html', context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    post = Post.objects.get(id=post_id)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    post_list = Post.objects.filter(author__following__user=request.user)
    page_obj = paginate(request, post_list)
    context = {'page_obj': page_obj}
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    author = User.objects.get(username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if request.user != author and not is_follower.exists():
        Follow.objects.create(user=request.user, author=author)
    return redirect(reverse('posts:profile', args=[username]))


@login_required
def profile_unfollow(request, username):
    author = get_object_or_404(User, username=username)
    is_follower = Follow.objects.filter(user=request.user, author=author)
    if is_follower.exists():
        is_follower.delete()
    return redirect('posts:profile', username=author)
