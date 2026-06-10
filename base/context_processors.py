from .models import Chat, Notification


def notifications(request):
    if request.user.is_authenticated:
        all_notifs = Notification.objects.filter(user=request.user).select_related('user__profile').order_by('-created_at')[:20]
        unread_count = sum(1 for n in all_notifs if not n.is_read)
        chat_unread_count = Chat.objects.filter(receiver=request.user, is_read=False).count()
        return {
            'notifications': all_notifs,
            'unread_count': unread_count,
            'chat_unread_count': chat_unread_count,
        }
    return {'notifications': [], 'unread_count': 0, 'chat_unread_count': 0}
