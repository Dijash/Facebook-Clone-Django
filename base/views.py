from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.cache import never_cache
from datetime import timedelta
from .models import Chat, Comment, Friend, Notification, Post, Profile


def get_friends(user):
    """Return a list of accepted friends for a user."""
    sent = Friend.objects.filter(from_user=user, status='accepted').values_list('to_user', flat=True)
    received = Friend.objects.filter(to_user=user, status='accepted').values_list('from_user', flat=True)
    friend_ids = list(sent) + list(received)
    return User.objects.filter(id__in=friend_ids).select_related('profile').annotate(
        unread_count=Count('sent_chats', filter=Q(sent_chats__receiver=user, sent_chats__is_read=False))
    )


def get_friend_status(user, other):
    """Return the friendship status dict: None or {'status': ..., 'request_id': ...}."""
    if user == other:
        return None
    rel = Friend.objects.filter(
        Q(from_user=user, to_user=other) | Q(from_user=other, to_user=user)
    ).first()
    if not rel:
        return None
    if rel.status == 'accepted':
        return {'status': 'accepted', 'request_id': rel.id}
    if rel.from_user == user:
        return {'status': 'pending_sent', 'request_id': rel.id}
    return {'status': 'pending_received', 'request_id': rel.id}

def login_view(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        credential = request.POST.get('username', '').lower().strip()
        password = request.POST.get('password')
        
        user = None
        if credential:
            user = authenticate(request, username=credential, password=password)
            if not user:
                try:
                    user_obj = User.objects.get(email=credential)
                    user = authenticate(request, username=user_obj.username, password=password)
                except User.DoesNotExist:
                    try:
                        user_obj = User.objects.get(profile__phone=credential)
                        user = authenticate(request, username=user_obj.username, password=password)
                    except User.DoesNotExist:
                        pass
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid credentials')
        
    context = {'page': page}
    return render(request, 'base/Auth/login.html', context)

def register_view(request):
    page = 'register'
    if request.user.is_authenticated:
        return redirect('home')
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        email = request.POST.get('email').lower()
        password = request.POST.get('password')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists')
            return redirect('register')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists')
            return redirect('register')
        
        user = User.objects.create_user(username=username, email=email, password=password)
        phone = request.POST.get('phone', '').strip()
        if phone:
            user.profile.phone = phone
        image = request.FILES.get('image')
        if image:
            user.profile.image = image
        user.profile.save()
        login(request, user)
        return redirect('home')
    context = {'page': page}
    return render(request, 'base/Auth/register.html', context)

def logout_view(request):
    logout(request)
    return redirect('home')

@login_required(login_url='login')
def homepage(request):
    friends = get_friends(request.user)
    friend_ids = list(friends.values_list('id', flat=True)) + [request.user.id]
    posts = Post.objects.filter(author_id__in=friend_ids).select_related('author__profile').prefetch_related(
        'comments__user__profile',
        'comments__replies__user__profile',
        'comments__likes',
        'comments__replies__likes',
        'likes',
    ).order_by('-created_at')
    now = timezone.now()
    online_cutoff = now - timedelta(minutes=15)
    active_cutoff = now - timedelta(days=7)
    
    online_friends = []
    recent_friends = []
    for u in friends[:40]:
        last_active = getattr(u.profile, 'last_active', None)
        if last_active and last_active >= online_cutoff:
            online_friends.append(u)
        elif last_active and last_active >= active_cutoff:
            recent_friends.append(u)
    
    context = {
        'posts': posts,
        'online_friends': online_friends[:10],
        'all_friends': recent_friends[:20],
        'now': now,
    }
    return render(request, 'base/homepage.html', context)


@login_required(login_url='login')
def create_post(request):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        image_file = request.FILES.get('image')
        video_file = request.FILES.get('video')
        if content:
            post = Post.objects.create(
                author=request.user,
                caption=content[:200],
                content=content,
                image=image_file,
                video=video_file,
            )
            post.participants.add(request.user)
            friends = get_friends(request.user)
            Notification.objects.bulk_create([
                Notification(
                    user=friend,
                    sender=request.user,
                    message=f"{request.user.username.title()} created a new post",
                    notification_type='new_post',
                )
                for friend in friends
            ])
    return redirect('home')


@login_required(login_url='login')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id, author=request.user)
    if request.method == 'POST':
        post.delete()
    return redirect('home')

@login_required(login_url='login')
def add_comment(request):
    if request.method == 'POST':
        post_id = request.POST.get('post_id')
        content = request.POST.get('content', '').strip()
        if post_id and content:
            post = get_object_or_404(Post, id=post_id)
            comment = Comment.objects.create(user=request.user, post=post, content=content)
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': comment.id,
                    'author': comment.user.username,
                    'author_title': comment.user.username.title(),
                    'avatar': comment.user.profile.image.url if comment.user.profile.image else None,
                    'content': comment.content,
                    'created_at': 'just now',
                })
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Missing data'}, status=400)
        return redirect('home')
    return redirect('home')

@login_required(login_url='login')
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id, user=request.user)
    if request.method == 'POST':
        comment.delete()
    return redirect('home')


@login_required(login_url='login')
def like_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    liked = False
    if request.user in post.likes.all():
        post.likes.remove(request.user)
    else:
        post.likes.add(request.user)
        liked = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': post.likes.count()})
    return redirect('home')


@login_required(login_url='login')
def like_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)
    liked = False
    if request.user in comment.likes.all():
        comment.likes.remove(request.user)
    else:
        comment.likes.add(request.user)
        liked = True
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'liked': liked, 'count': comment.likes.count()})
    return redirect('home')


@login_required(login_url='login')
def reply_comment(request, comment_id):
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        parent = get_object_or_404(Comment, id=comment_id)
        if content:
            reply = Comment.objects.create(
                user=request.user,
                post=parent.post,
                content=content,
                parent=parent,
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': reply.id,
                    'author': reply.user.username,
                    'author_title': reply.user.username.title(),
                    'avatar': reply.user.profile.image.url if reply.user.profile.image else None,
                    'content': reply.content,
                    'created_at': 'just now',
                    'parent_id': parent.id,
                })
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'error': 'Missing data'}, status=400)
    return redirect('home')


@login_required(login_url='login')
def search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)
    result_data = [(u, get_friend_status(request.user, u)) for u in results]
    return render(request, 'base/Search/search_results.html', {'results': result_data, 'query': query})

@login_required(login_url='login')
def watch_view(request):
    return render(request, 'base/root/watch.html')

@login_required(login_url='login')
def marketplace_view(request):
    return render(request, 'base/root/marketplace.html')

@login_required(login_url='login')
def friends_view(request):
    friends = get_friends(request.user)
    pending_requests = Friend.objects.filter(to_user=request.user, status='pending').select_related('from_user__profile')
    return render(request, 'base/root/friends.html', {
        'friends': friends,
        'pending_requests': pending_requests,
    })

@login_required(login_url='login')
def profile_view(request, username=None):
    if username:
        profile_user = get_object_or_404(User, username=username)
    else:
        profile_user = request.user

    posts = Post.objects.filter(author=profile_user).select_related('author__profile').prefetch_related(
        'comments__user__profile',
        'comments__replies__user__profile',
        'comments__likes',
        'comments__replies__likes',
        'likes',
    ).order_by('-created_at')

    friends = get_friends(profile_user)
    friend_count = friends.count()

    friend_status = None
    if profile_user != request.user:
        friend_status = get_friend_status(request.user, profile_user)

    context = {
        'profile_user': profile_user,
        'posts': posts,
        'friends': friends,
        'friend_count': friend_count,
        'friend_status': friend_status,
        'now': timezone.now(),
    }
    return render(request, 'base/root/profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    if request.method == 'POST':
        user = request.user
        phone = request.POST.get('phone', '').strip()
        if phone:
            user.profile.phone = phone
        image = request.FILES.get('image')
        if image:
            user.profile.image = image
        cover = request.FILES.get('cover')
        if cover:
            user.profile.cover = cover
        first_name = request.POST.get('first_name', '').strip()
        if first_name:
            user.first_name = first_name
        last_name = request.POST.get('last_name', '').strip()
        if last_name:
            user.last_name = last_name
        email = request.POST.get('email', '').strip()
        if email:
            user.email = email
        user.save()
        user.profile.save()
        messages.success(request, 'Profile updated successfully')
        return redirect('profile')
    return redirect('profile')


@login_required(login_url='login')
def send_friend_request(request, user_id):
    to_user = get_object_or_404(User, id=user_id)
    if to_user == request.user:
        return redirect('home')
    existing = Friend.objects.filter(
        Q(from_user=request.user, to_user=to_user) | Q(from_user=to_user, to_user=request.user)
    ).first()
    if not existing:
        Friend.objects.create(from_user=request.user, to_user=to_user, status='pending')
        Notification.objects.create(
            user=to_user,
            sender=request.user,
            message=f"{request.user.username.title()} sent you a friend request",
            notification_type='friend_request',
        )
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def accept_friend_request(request, request_id):
    friend_req = get_object_or_404(Friend, id=request_id, to_user=request.user, status='pending')
    friend_req.status = 'accepted'
    friend_req.save()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def reject_friend_request(request, request_id):
    friend_req = get_object_or_404(Friend, id=request_id, to_user=request.user, status='pending')
    friend_req.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def cancel_friend_request(request, request_id):
    friend_req = get_object_or_404(Friend, id=request_id, from_user=request.user, status='pending')
    friend_req.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required(login_url='login')
def unfriend(request, user_id):
    other = get_object_or_404(User, id=user_id)
    rel = Friend.objects.filter(
        Q(from_user=request.user, to_user=other) | Q(from_user=other, to_user=request.user),
        status='accepted',
    ).first()
    if rel:
        rel.delete()
    return redirect(request.META.get('HTTP_REFERER', 'profile'))


@login_required(login_url='login')
def mark_notifications_read(request):
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
    return redirect(request.META.get('HTTP_REFERER', 'home'))

@login_required(login_url='login')
@never_cache
def chat_view(request):
    selected = request.GET.get('with')
    if selected:
        active_user = get_object_or_404(User, id=selected)
        friends = get_friends(request.user)
        if active_user in friends:
            Chat.objects.filter(
                sender=active_user, receiver=request.user, is_read=False
            ).update(is_read=True)
    friends = get_friends(request.user)

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        to_user_id = request.POST.get('with', '').strip()
        if msg and to_user_id:
            to_user = get_object_or_404(User, id=to_user_id)
            chat = Chat.objects.create(
                sender=request.user,
                receiver=to_user,
                message=msg
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'id': chat.id,
                    'message': chat.message,
                    'sender': chat.sender.username,
                    'timestamp': chat.timestamp.isoformat(),
                })
            return redirect(f'/chat/?with={to_user_id}')

    friend_ids = [u.id for u in friends]
    if friend_ids:
        chats = Chat.objects.filter(
            Q(sender__in=friend_ids, receiver=request.user) | Q(sender=request.user, receiver__in=friend_ids)
        ).order_by('-timestamp').select_related('sender')
        seen = set()
        for c in chats:
            other_id = c.sender_id if c.receiver_id == request.user.id else c.receiver_id
            if other_id not in seen:
                seen.add(other_id)
                for u in friends:
                    if u.id == other_id:
                        u.latest_msg = c.message
                        u.latest_is_own = c.sender_id == request.user.id
                        break

    now = timezone.now()
    return render(request, 'base/chat/chat.html', {
        'users': friends,
        'now': now,
        'online_cutoff': now - timedelta(minutes=15),
    })


@login_required(login_url='login')
@never_cache
def get_chat_messages(request, user_id):
    other = get_object_or_404(User, id=user_id)
    friends = get_friends(request.user)
    if other not in friends:
        return JsonResponse({'messages': []})
    since = request.GET.get('since', 0)
    messages = Chat.objects.filter(
        Q(sender=request.user, receiver=other) | Q(sender=other, receiver=request.user),
        id__gt=since,
    ).order_by('-timestamp')

    unread = messages.filter(sender=other, receiver=request.user, is_read=False)
    unread.update(is_read=True)

    data = [{
        'id': m.id,
        'message': m.message,
        'sender': m.sender.username,
        'timestamp': m.timestamp.isoformat(),
    } for m in messages]

    result = {'messages': data}
    result['unread_count'] = Chat.objects.filter(receiver=request.user, is_read=False).count()

    if request.GET.get('since') in (None, '0'):
        last_active = other.profile.last_active.isoformat() if hasattr(other, 'profile') else None
        result['other_user'] = {
            'id': other.id,
            'username': other.username,
            'avatar': other.profile.image.url if hasattr(other, 'profile') and other.profile.image else None,
            'last_active': last_active,
        }

    return JsonResponse(result)


