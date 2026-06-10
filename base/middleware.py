from django.utils import timezone

class ActiveUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            profile = request.user.profile
            now = timezone.now()
            if profile.last_active is None or (now - profile.last_active).seconds > 120:
                profile.last_active = now
                profile.save(update_fields=['last_active'])
        return self.get_response(request)
