from django.contrib import admin
from .models import Post, Comment

@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    # Задаем отображаемые поля модели на админ-пане
    list_display = ['title', 'slug', 'author', 'publish', 'status']
    # Поля, по которым можно фильтровать
    list_filter = ['status', 'created', 'publish', 'author']
    # Поля, по которым можно осуществлять поиск
    search_fields = ['title', 'body']

    prepopulated_fields = {'slug': ('title',)}
    raw_id_fields = ['author']
    date_hierarchy = 'publish'
    ordering = ['status', 'publish']

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'post', 'created', 'active']
    list_filter = ['active', 'created', 'updated']
    search_fields = ['name', 'email', 'body']