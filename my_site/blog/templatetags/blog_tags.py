from django import template
from django.db.models import Count
from django.utils.safestring import mark_safe

import markdown

from ..models import Post

register = template.Library()


#  @register.simple_tag(name='my_tag') - Если нужно зарегистририровать под другим именем.
@register.simple_tag
def total_posts():
    return Post.published.count()


# Тег включения, указанный шаблон будет прорисовываться на месте вызова тега
# Тег выводит последние опубликованные посты (опционально 5 тегов, можно указывать в шаблоне)
@register.inclusion_tag('blog/post/latest_posts.html')
def show_latest_posts(count=5):
    latest_posts = Post.published.order_by('-publish')[:count]
    return {'latest_posts': latest_posts}


# Тег, возвращающий самые закомментированные посты
@register.simple_tag
def get_most_commented_posts(count=5):
    return Post.published.annotate(total_comments=Count('comments')).order_by('total_comments')[:count]


# Тег, позволяющий пользоваться Markdown
@register.filter(name='markdown')
def markdown_format(text):
    print(markdown.markdown(text))
    return mark_safe(markdown.markdown(text ))