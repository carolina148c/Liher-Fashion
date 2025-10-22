#reglas específicas de integración con Allauth

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model

User = get_user_model()

class MyAccountAdapter(DefaultAccountAdapter):
    """Adaptador para manejar el campo email en Allauth"""
    def get_email(self, user):
        return user.email


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Antes de guardar la cuenta social, verificamos si ya existe un usuario
        con el mismo email. Si existe y está inactivo, lo activamos automáticamente
        y asociamos la cuenta de Google a ese usuario.
        """
        email = sociallogin.account.extra_data.get('email')

        if not email:
            return

        try:
            user = User.objects.get(email=email)
            # Asociar cuenta social al usuario existente
            sociallogin.connect(request, user)
            # Activar si estaba inactivo
            if not user.is_active:
                user.is_active = True
                user.save()
        except User.DoesNotExist:
            # Si no existe, Allauth creará uno nuevo (is_active=True por defecto)
            pass