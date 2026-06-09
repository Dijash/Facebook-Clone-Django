from django.contrib import admin

from .models import Post, Timeline, Chat, Comment, Notification

admin.site.register(Post)
admin.site.register(Timeline)
admin.site.register(Chat)
admin.site.register(Comment)
admin.site.register(Notification)
