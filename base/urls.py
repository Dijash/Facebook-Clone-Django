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
    path('friends/', views.friends_view, name='friends'),
    path('profile/', views.profile_view, name='profile'),
    path('', views.homepage, name='home'),
]

