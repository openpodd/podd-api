import datetime

from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.models import UserCode

class OneDayPasswordModelBackend(object):
    def authenticate(self, username=None, code=None, ignore_password=None):
        try:
            user_code = UserCode.objects.get(user__username=username, code=code, is_used=False)
            now = timezone.now()
            if not (user_code.created < now < user_code.expired):
                return None
            return user_code.user
        except:
            return None


    def get_user(self, user_id):
        User = get_user_model()

        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None