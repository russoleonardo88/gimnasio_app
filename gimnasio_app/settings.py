import os
import dj_database_url 
from pathlib import Path

# --- RUTAS BÁSICAS ---
BASE_DIR = Path(__file__).resolve().parent.parent

# --- SEGURIDAD ---
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-3*r893bw)ik7h=!fd$x7ky$hiigyx@dy+*772wv^&e2t#hn#f&')

# IMPORTANTE: En Render, creá la Variable de Entorno DEBUG con valor False
DEBUG = os.environ.get('DEBUG', 'False') == 'True'

ALLOWED_HOSTS = ['*']

# --- APLICACIONES ---
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'alumnos',  # Tu app
]

# --- MIDDLEWARE ---
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gimnasio_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gimnasio_app.wsgi.application'

# --- BASE DE DATOS (Auto-detecta local o producción) ---
DATABASES = {
    'default': dj_database_url.config(
        default=os.environ.get('DATABASE_URL', f"sqlite:///{BASE_DIR / 'db.sqlite3'}"),
        conn_max_age=600
    )
}

# --- INTERNACIONALIZACIÓN ---
LANGUAGE_CODE = 'es-es'
TIME_ZONE = 'America/Argentina/Buenos_Aires'
USE_I18N = True
USE_TZ = True

# --- ARCHIVOS ESTÁTICOS ---
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_STORAGE = 'whitenoise.storage.CompressedStaticFilesStorage'

# --- CONFIGURACIÓN DE LOGIN (CORREGIDO) ---
LOGIN_REDIRECT_URL = 'dashboard_alumno'
LOGIN_URL = 'login'

# --- CONFIGURACIÓN DE SESIONES (PARA MANTENER EL LOGIN) ---
SESSION_ENGINE = 'django.contrib.sessions.backends.db'
SESSION_COOKIE_AGE = 31536000  # 1 año en segundos
SESSION_EXPIRE_AT_BROWSER_CLOSE = False
SESSION_SAVE_EVERY_REQUEST = True

# --- SEGURIDAD CSRF PARA RENDER ---
CSRF_TRUSTED_ORIGINS = [
    'https://gimnasio-app-ftq4.onrender.com',
    'https://*.onrender.com'
]

# --- EL BLOQUE MAESTRO PARA LA APK Y PRODUCCIÓN ---
if not DEBUG or os.environ.get('RENDER'):
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    
    # SameSite=None permite que el WebView de Android reciba la cookie desde el dominio de Render
    SESSION_COOKIE_SAMESITE = 'None'
    CSRF_COOKIE_SAMESITE = 'None'
    
    # HttpOnly=True es más seguro, pero dejamos CSRF en False para evitar bloqueos en Android
    SESSION_COOKIE_HTTPONLY = True
    CSRF_COOKIE_HTTPONLY = False 
    
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_SSL_REDIRECT = False 
    
    APPEND_SLASH = True 
else:
    # Desarrollo local
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_SAMESITE = 'Lax'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'