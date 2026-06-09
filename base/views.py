from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import Chat, Profile

def login_view(request):
    page = 'login'
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username').lower()
        password = request.POST.get('password')
        
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password')
        
    context = {'page': page}
    return render(request, 'base/Auth/login.html', context)

def register_view(request):
    page = 'register'
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
    context = {}
    return render(request, 'base/homepage.html', context)

@login_required(login_url='login')
def search_view(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = User.objects.filter(
            Q(username__icontains=query) |
            Q(email__icontains=query)
        ).exclude(id=request.user.id)
    return render(request, 'base/Search/search_results.html', {'results': results, 'query': query})

@login_required(login_url='login')
def watch_view(request):
    return render(request, 'base/root/watch.html')

@login_required(login_url='login')
def marketplace_view(request):
    return render(request, 'base/root/marketplace.html')

@login_required(login_url='login')
def friends_view(request):
    return render(request, 'base/root/friends.html')

@login_required(login_url='login')
def profile_view(request):
    return render(request, 'base/root/profile.html')

@login_required(login_url='login')
def chat_view(request):
    users = User.objects.exclude(id=request.user.id)
    active_user = None
    chat_messages = []
    selected = request.GET.get('with') or request.POST.get('with')

    if selected:
        active_user = get_object_or_404(User, id=selected)
        chat_messages = Chat.objects.filter(
            sender__in=[request.user, active_user],
            receiver__in=[request.user, active_user]
        ).order_by('timestamp')

    if request.method == 'POST':
        msg = request.POST.get('message', '').strip()
        if msg and selected:
            Chat.objects.create(
                sender=request.user,
                receiver=active_user,
                message=msg
            )
            return redirect(f'/chat/?with={selected}')

    return render(request, 'base/chat/chat.html', {
        'users': users,
        'active_user': active_user,
        'messages': chat_messages,
    })


