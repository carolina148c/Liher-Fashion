#funciones auxiliares

from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse
from django.conf import settings

def enviar_correo_usuario_existente(user, request):
    password_reset_url = request.build_absolute_uri(reverse('account_reset_password'))
    asunto = 'Ya existe una cuenta con tu correo'
    mensaje_html = render_to_string(
        'autenticacion/email/usuario_existente.html',
        {'user': user, 'password_reset_url': password_reset_url}
    )
    correo = EmailMultiAlternatives(
        asunto,
        '',  # texto plano opcional
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
    )
    correo.attach_alternative(mensaje_html, "text/html")
    correo.send()
