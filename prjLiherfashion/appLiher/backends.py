#backend de autenticación por email.

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

UserModel = get_user_model()

class EmailBackend(BaseBackend):
    """
    Backend simple para autenticación por email.
    """
    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None
        try:
            user = UserModel.objects.get(email__iexact=email)
        except UserModel.DoesNotExist:
            return None
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None

    def get_user(self, user_id):
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None

    def user_can_authenticate(self, user):
        return getattr(user, "is_active", True)
