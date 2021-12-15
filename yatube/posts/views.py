import json
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.cache import cache_page
from django.db.models import Sum

from .forms import CommentForm, PostForm
from .models import Follow, Group, Post, User, Question, Choice


@cache_page(20)
def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all().select_related('group')
    paginator = Paginator(post_list, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    post_list = Post.objects.filter(group=group).select_related('group')
    paginator = Paginator(post_list, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    template = 'posts/group_list.html'
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    post_list = Post.objects.filter(author=author).select_related('group')
    paginator = Paginator(post_list, settings.PAGINATOR_OBJECTS_PER_PAGchoiE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    following = False
    if request.user.is_authenticated:
        if Follow.objects.filter(
           author=author).filter(user=request.user).exists():
            following = True
    template = 'posts/profile.html'
    post_amount = post_list.count()
    context = {
        'author': author,
        'page_obj': page_obj,
        'post_amount': post_amount,
        'following': following,
    }
    return render(request, template, context)


def post_detail(request, post_id):
    template = 'post_detail.html'
    post = get_object_or_404(Post, pk=post_id)
    post_amount = Post.objects.filter(author=post.author).count()
    form = CommentForm()
    context = {
        'post': post,
        'post_amount': post_amount,
        'form': form,
    }
    return render(request, template, context)


@login_required
def post_create(request):
    template = 'posts/create_post.html'
    groups = Group.objects.all()
    form = PostForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        return redirect('posts:profile', post.author.username)
    context = {
        'groups': groups,
        'form': PostForm()
    }
    return render(request, template, context)


@login_required
def post_edit(request, post_id):
    post = get_object_or_404(Post, pk=post_id)
    if request.user.pk != post.author.pk:
        return redirect('posts:post_detail', post_id)
    template = 'posts/create_post.html'
    groups = Group.objects.all()
    is_edit = True
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
        instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id)
    context = {
        'groups': groups,
        'form': form,
        'is_edit': is_edit,
        'post': post
    }
    return render(request, template, context)


@login_required
def add_comment(request, post_id):
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        post = get_object_or_404(Post, pk=post_id)
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    template = 'posts/follow.html'
    post_list = Post.objects.filter(author__following__user=request.user)
    paginator = Paginator(post_list, settings.PAGINATOR_OBJECTS_PER_PAGE)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, template, context)


@login_required
def profile_follow(request, username):
    post_author = User.objects.get(username=username)
    if request.user != post_author:
        Follow.objects.get_or_create(
            user=request.user,
            author=post_author
        )
    return redirect('posts:profile', username=username)


@login_required
def profile_unfollow(request, username):
    Follow.objects.filter(user=request.user).filter(
        author=get_object_or_404(User, username=username)).delete()
    return redirect('posts:profile', username=username)


def questions(request):
    questions_list = Question.objects.all()
    template = 'posts/question_list.html'
    context = {
        'questions_list': questions_list,
    }
    return render(request, template, context)


def question(request, pk):
    if request.method == 'POST':
        result = get_object_or_404(
            Choice, pk=int(request.POST['exampleRadios']))
        result.votes += 1
        result.save()
        return redirect('posts:question_visual', pk=pk)
    question = get_object_or_404(Question, pk=pk)
    choices = Choice.objects.filter(question__id=pk)
    template = 'posts/question.html'
    context = {
        'choices': choices,
        'question': question,
    }
    return render(request, template, context)


def grath_api(request, pk):
    choices = Choice.objects.filter(question__id=pk).values('choice_text', 'votes')
    question = get_object_or_404(Question, pk=pk)
    template = 'posts/grath.html'
    categories = []
    survived_series_data = []
    for entry in choices:
        categories.append(entry['choice_text'])
        survived_series_data.append(int(entry['votes']))
    survived_series = {
        'name': 'Количество голосов',
        'data': survived_series_data,
        'color': 'green'
    }
    chart = {
        'chart': {'type': 'column'},
        'title': {'text': f'Количество голосов в опросе {question.question_text}.'},
        'xAxis': {'categories': categories},
        'series': [survived_series]
    }
    dump = json.dumps(chart)
    return render(request, template, {'chart': dump})
