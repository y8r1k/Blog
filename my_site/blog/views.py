from django.shortcuts import render, get_object_or_404
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
# from django.views.generic import ListView
from django.views.decorators.http import require_POST
from django.core.mail import send_mail
from django.db.models import Count
from django.contrib.postgres.search import SearchVector, SearchQuery, SearchRank, TrigramSimilarity

from taggit.models import Tag

from .models import Post
from .form import EmailPostForm, CommentForm, SearchForm


# class PostListView(ListView):
#     """
#     Альтернативное представление списка постов
#     """
#     queryset = Post.published.all()
#     context_object_name = 'posts'
#     paginate_by = 3
#     template_name = 'blog/post/list.html'

def post_list(request, tag_slug=None):
    post_list = Post.published.all()
    tag = None
    if tag_slug:
        # Если тег передали, значит выводим все опубликованные посты содержащие нужный тег
        tag = get_object_or_404(Tag, slug=tag_slug)
        # Django понимает, что передали объект и возьмет id объекта
        post_list = post_list.filter(tags__in=[tag])

    # Постраничная разбивка с 3 постами на страницу
    page_number = request.GET.get('page', 1)
    paginator = Paginator(post_list, per_page=3)
    try:
        posts = paginator.page(page_number)
    except PageNotAnInteger:
        # Если page_number - не целое число,
        # то выдать первую страницу
        posts = paginator.page(1)
    except EmptyPage:
        # Если page_number находится вне диапазона,
        # то выдать последнюю страницу
        posts = paginator.page(paginator.num_pages)

    return render(request, template_name='blog/post/list.html',
                  context={'posts': posts,
                           'tag': tag})


def post_detail(request, year, month, day, post):
    post = get_object_or_404(Post,
                             status=Post.Status.PUBLISHED,
                             slug=post,
                             publish__year=year,
                             publish__month=month,
                             publish__day=day)
    # Список активных комментариев к этому посту
    comments = post.comments.filter(active=True)

    # Форма для комментирование пользователями
    form = CommentForm()

    # Список схожих постов
    # Получаем Python-список из id тегов данного поста,
    # Так как values_list возвращает список кортежей [(1,), (2,), (3,), ]
    # Параметр flat=True передается, чтобы получить одиночные значения [1, 2, 3]
    post_tags_ids = post.tags.values_list('id', flat=True)
    # Берутся все посты, содержащие любой из этих тегов, исключая текущий пост
    similar_posts = Post.published.filter(tags__in=post_tags_ids).exclude(id=post.id)
    # Функция annotate() добавляет к каждому объекту запроса новое вычисляемое поле
    # (в данном случае это поле same_tags), которое рассчитывается на основе данных в таблице.
    similar_posts = similar_posts.annotate(same_tags=Count('tags')).order_by('-same_tags', '-publish')[:4]
    return render(request, template_name='blog/post/detail.html',
                  context={'post': post,
                           'comments': comments,
                           'form': form,
                           'similar_posts': similar_posts})


def post_share(request, post_id):
    # Извлечь пост по идентификатору  id
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    sent = False

    if request.method == 'POST':
        # Форма была передана в обработку
        form = EmailPostForm(request.POST)
        if form.is_valid():
            # Поля формы успешно прошли валидацию
            cd = form.cleaned_data
            post_url = request.build_absolute_uri(post.get_absolute_url())
            subject = f"{cd['name']} recommends you read {post.title}"
            message = f"Read {post.title} at {post_url}\n\n" \
                      f"{cd['name']}\'s comments: {cd['comments']}"
            send_mail(subject, message, from_email='your_account@gmail.com', recipient_list=[cd['to']])
            sent = True
    else:
        form = EmailPostForm()
    return render(request, template_name='blog/post/share.html',
                  context={'post': post,
                           'form': form,
                           'sent': sent})


@require_POST
def post_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id, status=Post.Status.PUBLISHED)

    comment = None
    # Комментарий был отправлен
    form = CommentForm(data=request.POST)
    if form.is_valid():
        # Создать объект класса коммент, не сохраняя его в Базе Данных
        # Такой подход позволяет видоизменять форму перед ее сохраненим
        comment = form.save(commit=False)
        # Назначить пост комментарию
        comment.post = post
        # Сохранить комментарий 
        comment.save()
    return render(request, template_name='blog/post/comment.html',
                  context={'post': post,
                           'form': form,
                           'comment': comment})


def post_search(request):
    form = SearchForm()
    query = None
    results = []
    if 'query' in request.GET:
        form = SearchForm(request.GET)
    if form.is_valid():
        query = form.cleaned_data['query']
        # search_vector = SearchVector('title', weight='A') + SearchVector('body', weight='B')
        # search_query = SearchQuery(query)
        results = Post.published.annotate(similarity=TrigramSimilarity('title', query),
                                          ).filter(similarity__gt=0.1).order_by('-similarity')
    return render(request,
                  'blog/post/search.html',
                  {'form': form,
                   'query': query,
                   'results': results})
