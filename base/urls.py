from django.urls import path
from . import views

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('search/', views.search_view, name='search'),
    path('watch/', views.watch_view, name='watch'),
    path('marketplace/', views.marketplace_view, name='marketplace'),
    path('chat/', views.chat_view, name='chat'),
    path('chat/messages/<int:user_id>/', views.get_chat_messages, name='get_chat_messages'),
    path('friends/', views.friends_view, name='friends'),
    path('profile/', views.profile_view, name='profile'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<str:username>/', views.profile_view, name='user_profile'),
    path('post/create/', views.create_post, name='create_post'),
    path('post/<int:post_id>/delete/', views.delete_post, name='delete_post'),
    path('post/<int:post_id>/like/', views.like_post, name='like_post'),
    path('comment/', views.add_comment, name='add_comment'),
    path('comment/<int:comment_id>/delete/', views.delete_comment, name='delete_comment'),
    path('comment/<int:comment_id>/like/', views.like_comment, name='like_comment'),
    path('comment/<int:comment_id>/reply/', views.reply_comment, name='reply_comment'),
    path('friend/request/<int:user_id>/', views.send_friend_request, name='send_friend_request'),
    path('friend/accept/<int:request_id>/', views.accept_friend_request, name='accept_friend_request'),
    path('friend/reject/<int:request_id>/', views.reject_friend_request, name='reject_friend_request'),
    path('friend/cancel/<int:request_id>/', views.cancel_friend_request, name='cancel_friend_request'),
    path('notifications/read/', views.mark_notifications_read, name='mark_notifications_read'),
    path('', views.homepage, name='home'),
]

