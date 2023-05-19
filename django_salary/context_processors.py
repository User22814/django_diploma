from django.contrib.auth.models import User
from django_salary import models


def user_access(request):
    if not request.user.is_anonymous:
        user_profile = models.UserProfile.objects.get(user=request.user)
        return user_profile.access
    else:
        return "anonymous"
