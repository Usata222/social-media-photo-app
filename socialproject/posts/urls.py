from django.urls import path
from . import views
urlpatterns = [
    path('create', views.post_create, name='create'),
    path('feed', views.feed, name='feed'),
    path('<int:post_id>', views.post_detail, name='post_detail'),
    path('<int:post_id>/edit', views.post_edit, name='post_edit'),
    path('<int:post_id>/delete', views.post_delete, name='post_delete'),
    path('like', views.like_post, name='like'),
    path('bookmark', views.bookmark_toggle, name='bookmark_toggle'),
    path('bookmarks', views.bookmarks_list, name='bookmarks'),
    path('tag/<str:tag>', views.hashtag_feed, name='hashtag_feed'),
    path('comment/<int:comment_id>/edit', views.comment_edit, name='comment_edit'),
    path('comment/<int:comment_id>/delete', views.comment_delete, name='comment_delete'),
]