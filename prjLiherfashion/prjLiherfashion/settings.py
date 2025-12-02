"""
Django settings for prjLiherfashion project.
"""

from pathlib import Path
import os
from decouple import config
import dj_database_url

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = 'django-insecure-84)i^6msviz!woxtwm9@emvxhe6e#(avd8y^rlt(s$o+pa$4zx'
DEBUG = True
ALLOWED_HOSTS = []

# -------------------------------------------------------------------
# Apps instaladas
# -------------------------------------------------------------------
INSTALLED_APPS = [
    # Django apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # App local
    'appLiher',

    # Allauth
    'django.contrib.sites',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',

    'widget_tweaks',
    'crispy_forms',
    "crispy_bootstrap5",
]

SITE_ID = 1

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

]

ROOT_URLCONF = 'prjLiherfashion.urls'

CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = "bootstrap5"


# -------------------------------------------------------------------
# Templates
# -------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'appLiher', 'Templates')],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # necesario para allauth
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'prjLiherfashion.wsgi.application'

# -------------------------------------------------------------------
# Base de datos
# -------------------------------------------------------------------
# -------------------------------------------------------------------

# 1. Recuperamos la URL de conexión de la variable de entorno.
#    Esta variable (DATABASE_URL) será la que configurarás en Render.
DATABASE_URL = config('DATABASE_URL')

# 2. Usamos dj_database_url para parsear la URL y generar el diccionario
#    de conexión de Django.
DATABASES = {
    'default': dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,  # Opcional: mantiene conexiones persistentes
        # Esta opción es CRUCIAL para Aiven, ya que requiere SSL/TLS.
        # Le dice al driver mysqlclient que use SSL.
        ssl_require=True
    )
}

# 3. Aseguramos el motor correcto de MySQL.
#    dj-database-url a veces usa el motor por defecto. Aquí lo forzamos
DATABASES['default']['ENGINE'] = 'django.db.backends.mysql'

# -------------------------------------------------------------------
# Password validators
# -------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# -------------------------------------------------------------------
# Internacionalización
# -------------------------------------------------------------------
LANGUAGE_CODE = 'es'
TIME_ZONE = 'America/Bogota'
USE_I18N = True
USE_TZ = True

# -------------------------------------------------------------------
# Archivos estáticos
# -------------------------------------------------------------------
STATIC_URL = 'static/'
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# -------------------------------------------------------------------
# Modelo de usuario personalizado
# -------------------------------------------------------------------
AUTH_USER_MODEL = 'appLiher.Usuarios'

# -------------------------------------------------------------------
# Backends de autenticación
# -------------------------------------------------------------------
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',  # necesario para admin
    'appLiher.backends.EmailBackend',             # tu backend por email
    'allauth.account.auth_backends.AuthenticationBackend',  # allauth
]

# -------------------------------------------------------------------
# Configuración de Allauth (API nueva sin warnings 🚀)
# -------------------------------------------------------------------
ACCOUNT_USER_MODEL_USERNAME_FIELD = None   # 🚫 sin username en el modelo

# Métodos de login permitidos (solo email)
ACCOUNT_LOGIN_METHODS = {"email"}

# Campos requeridos en el formulario de registro
ACCOUNT_SIGNUP_FIELDS = ["email*", "password1*", "password2*"]

# Cómo mostrar al usuario en plantillas/mensajes
ACCOUNT_USER_DISPLAY = lambda user: user.email

# Verificación email para registros con correo/contraseña
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_UNIQUE_EMAIL = True

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/iniciar-sesion/'

# -------------------------------------------------------------------
# Configuración Social (Google)
# -------------------------------------------------------------------
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_EMAIL_VERIFICATION = "none"   # 🚫 no pedir verificación por google
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_ADAPTER = 'appLiher.adapters.CustomSocialAccountAdapter'
ACCOUNT_ADAPTER = 'appLiher.adapters.MyAccountAdapter'
ACCOUNT_FORMS = {
    "reset_password": "appLiher.forms.CustomPasswordResetForm"
}


SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_CLIENT_ID'),
            'secret': config('GOOGLE_CLIENT_SECRET'),
            'key': ''
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    }
}



# -------------------------------------------------------------------
# Email (SMTP)
# -------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER
